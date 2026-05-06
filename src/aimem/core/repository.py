"""LayerRepo — git-backed storage for one memory layer (design.md §3, R-001).

Phase 1 ships the ``personal`` layer only.  The parent index repo lives at
``~/.ai-memory/`` (or ``AIMEM_DIR``).  The ``personal/`` directory is a
regular git repository (Phase 2 will turn it into a submodule once remotes
are wired up).

Directory layout after ``aimem init``::

    ~/.ai-memory/
    ├── .aimem.yaml          ← config
    ├── .aimem.lock          ← flock sentinel (auto-created)
    ├── .gitignore
    ├── .keys/               ← ed25519 key pair (mode 0600 for private key)
    └── personal/            ← personal layer git repo
        ├── identity/
        ├── preference/
        ├── procedure/
        ├── observation/
        └── knowledge/
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from aimem.core.config import AimemConfig
from aimem.core.error import InvariantError, NotFoundError
from aimem.core import logging as _logging
from aimem.core.schema import Layer, MemoryRecord, MemoryType

log = _logging.get_logger(__name__)

_LAYER_DIRS: dict[Layer, str] = {
    Layer.PERSONAL: "personal",
    Layer.PROJECT: "projects",
    Layer.TEAM: "teams",
}

_TYPE_SUBDIRS: dict[MemoryType, str] = {
    MemoryType.IDENTITY: "identity",
    MemoryType.PREFERENCE: "preference",
    MemoryType.PROCEDURE: "procedure",
    MemoryType.OBSERVATION: "observation",
    MemoryType.KNOWLEDGE: "knowledge",
}

_GITIGNORE = """\
.aimem.lock
.keys/
*.pyc
__pycache__/
.index/
"""

_LAYER_GITIGNORE = """\
.inbox/
*.pyc
"""


class LayerRepo:
    """Manages the on-disk git repositories for all memory layers."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        from aimem.core.config import DEFAULT_MEMORY_DIR

        self.root = memory_dir or DEFAULT_MEMORY_DIR
        self.config = AimemConfig.load(self.root)

    # ------------------------------------------------------------------
    # State checks
    # ------------------------------------------------------------------

    @property
    def is_initialized(self) -> bool:
        return (self.root / ".aimem.yaml").exists()

    def layer_path(self, layer: Layer = Layer.PERSONAL) -> Path:
        return self.root / _LAYER_DIRS[layer]

    def record_path(self, record: MemoryRecord) -> Path:
        """Canonical on-disk path for a record (id-addressed)."""
        subdir = _TYPE_SUBDIRS[record.type]
        layer_root = self.layer_path(record.layer)
        return layer_root / subdir / f"{record.id}.md"

    # ------------------------------------------------------------------
    # Initialization (US-001)
    # ------------------------------------------------------------------

    def init(self, path: Path | None = None) -> Path:
        """Create the parent index repo and the personal layer repo.

        Raises ``InvariantError`` if the path is already initialised.
        Enforces HC2: refuses to write outside the given path.
        """
        target = path or self.root
        # HC2: refuse to write outside the passed-in path
        if path and not str(target).startswith(str(path)):
            raise InvariantError(
                "aimem init refuses to write outside --path (HC2).",
                detail=str(target),
            )

        if self.is_initialized:
            log.info(op="init", result="already-initialized", path=str(self.root))
            return self.root

        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / ".gitignore").write_text(_GITIGNORE, encoding="utf-8")

        # Create personal layer directory structure
        personal = self.layer_path(Layer.PERSONAL)
        personal.mkdir(parents=True, exist_ok=True)
        for subdir in _TYPE_SUBDIRS.values():
            (personal / subdir).mkdir(exist_ok=True)
        (personal / ".gitignore").write_text(_LAYER_GITIGNORE, encoding="utf-8")

        # Initialize git repo inside personal/
        self._git("init", cwd=personal)
        self._git("checkout", "-b", "main", cwd=personal)

        # Ensure signing key pair exists
        from aimem.core.signing import ensure_key_pair

        ensure_key_pair(self.root)

        # Save config
        self.config.save(self.root)

        # Initial commit in personal layer
        self._git("add", ".", cwd=personal)
        self._git("commit", "-m", "Initialize personal memory layer", cwd=personal)

        log.info(op="init", result="ok", path=str(self.root))
        return self.root

    # ------------------------------------------------------------------
    # Write (US-002)
    # ------------------------------------------------------------------

    def write(self, record: MemoryRecord) -> Path:
        """Persist a record to disk and commit it.  Caller must hold the lock."""
        path = self.record_path(record)
        record_with_path = record.model_copy(update={"path": path})
        record_with_path.to_file()

        layer_root = self.layer_path(record.layer)
        rel = path.relative_to(layer_root)
        self._git("add", str(rel), cwd=layer_root)
        self._git(
            "commit",
            "-m",
            f"op=add type={record.type.value} id={record.id}",
            cwd=layer_root,
        )
        log.info(op="add", layer=record.layer.value, record_id=record.id, result="ok")
        return path

    # ------------------------------------------------------------------
    # Read (US-003, US-004)
    # ------------------------------------------------------------------

    def get(self, record_id: str, layer: Layer = Layer.PERSONAL) -> MemoryRecord:
        """Fetch a record by ULID from *layer*."""
        layer_root = self.layer_path(layer)
        matches = list(layer_root.rglob(f"{record_id}.md"))
        if not matches:
            raise NotFoundError(
                f"Record {record_id!r} not found in layer '{layer.value}'."
            )
        return MemoryRecord.from_file(matches[0])

    def list_records(
        self,
        layer: Layer = Layer.PERSONAL,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
    ) -> list[MemoryRecord]:
        """Return all records matching filters."""
        layer_root = self.layer_path(layer)
        if not layer_root.exists():
            return []

        if memory_type:
            search_dirs = [layer_root / _TYPE_SUBDIRS[memory_type]]
        else:
            search_dirs = [layer_root / d for d in _TYPE_SUBDIRS.values()]

        records: list[MemoryRecord] = []
        for d in search_dirs:
            if not d.exists():
                continue
            for md in sorted(d.glob("*.md")):
                try:
                    rec = MemoryRecord.from_file(md)
                    if tags and not set(tags).intersection(rec.tags):
                        continue
                    records.append(rec)
                except Exception as exc:
                    log.warning(op="list", path=str(md), error=str(exc))
        return records

    def tag_record(
        self, record_id: str, tags_add: list[str], tags_remove: list[str]
    ) -> MemoryRecord:
        """Add/remove tags on a record and re-commit."""
        rec = self.get(record_id)
        new_tags = sorted(set(rec.tags).union(tags_add).difference(tags_remove))
        updated = rec.model_copy(update={"tags": new_tags})
        updated.to_file()
        layer_root = self.layer_path(rec.layer)
        rel = rec.path.relative_to(layer_root)  # type: ignore[arg-type]
        self._git("add", str(rel), cwd=layer_root)
        self._git("commit", "-m", f"op=tag id={record_id}", cwd=layer_root)
        log.info(op="tag", record_id=record_id)
        return updated

    def link_records(
        self,
        source_id: str,
        target_id: str,
        link_type: str = "causal",
    ) -> MemoryRecord:
        """Add a link from source to target and re-commit."""
        rec = self.get(source_id)
        links_data = rec.links.model_dump()
        existing: list[str] = links_data.get(link_type, [])
        if target_id not in existing:
            existing.append(target_id)
        from aimem.core.schema import Links

        new_links = Links.model_validate({**links_data, link_type: existing})
        updated = rec.model_copy(update={"links": new_links})
        updated.to_file()
        layer_root = self.layer_path(rec.layer)
        rel = rec.path.relative_to(layer_root)  # type: ignore[arg-type]
        self._git("add", str(rel), cwd=layer_root)
        self._git(
            "commit",
            "-m",
            f"op=link src={source_id} type={link_type}",
            cwd=layer_root,
        )
        log.info(op="link", source_id=source_id, target_id=target_id, link_type=link_type)
        return updated

    # ------------------------------------------------------------------
    # Sync (design.md §5)
    # ------------------------------------------------------------------

    def sync(self, layer: Layer = Layer.PERSONAL) -> bool:
        """git pull --rebase && git push."""
        layer_root = self.layer_path(layer)
        try:
            self._git("pull", "--rebase", cwd=layer_root)
            self._git("push", cwd=layer_root)
            log.info(op="sync", layer=layer.value, result="ok")
            return True
        except subprocess.CalledProcessError as exc:
            log.error(op="sync", layer=layer.value, result="fail", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _git(*args: str, cwd: Path) -> str:
        import os as _os

        env = _os.environ.copy()
        # Ensure git always has a valid identity even in CI / fresh environments
        env.setdefault("GIT_AUTHOR_NAME", "aimem")
        env.setdefault("GIT_AUTHOR_EMAIL", "aimem@localhost")
        env.setdefault("GIT_COMMITTER_NAME", "aimem")
        env.setdefault("GIT_COMMITTER_EMAIL", "aimem@localhost")
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        return result.stdout.strip()
