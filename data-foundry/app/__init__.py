import sys
from pathlib import Path


def _discover_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "shared_kb").exists():
            return candidate
    return current.parents[2]


ROOT_DIR = _discover_repo_root()
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

