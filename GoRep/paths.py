from __future__ import annotations

import sys
from pathlib import Path


GOREP_DIR = Path(__file__).resolve().parent


def _find_repo_root() -> Path:
    """Find the GoCCvA project root from either the old or new GoRep location."""
    candidates = [
        GOREP_DIR.parent,
        GOREP_DIR.parent / "work-GoCCvA-2026",
        Path(r"C:\Users\jcavi\Desktop\Juanita_Kogi"),
        Path(r"C:\Users\jcavi\Desktop\Juanita_Kogi\work-GoCCvA-2026"),
    ]
    required_huba_inputs = [
        Path("content/TUEReimbursement/gm_huba_new_actor2.txt"),
        Path("content/TUEReimbursement/domestic_declaration_ilpn_updated.pnml"),
        Path("content/TUEReimbursement/mapping_huba_new_actor.csv"),
    ]
    for candidate in candidates:
        if all((candidate / rel_path).exists() for rel_path in required_huba_inputs):
            return candidate
    for candidate in candidates:
        if (
            (candidate / "content").is_dir()
            and (candidate / "Semantics").is_dir()
            and (candidate / "Ui").is_dir()
        ):
            return candidate
    return GOREP_DIR.parent


REPO_ROOT = _find_repo_root()


def ensure_repo_root_on_path() -> Path:
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    return REPO_ROOT
