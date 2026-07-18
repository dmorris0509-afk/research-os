from pathlib import Path

from research_os.config import get_settings


class Workspace:
    def __init__(self, root: Path | None = None):
        self.root = (root or get_settings().workspace_root).resolve()

    def resolve(self, relative: str) -> Path:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Only workspace-relative paths are allowed")
        candidate = (self.root / path).resolve()
        candidate.relative_to(self.root)
        return candidate
