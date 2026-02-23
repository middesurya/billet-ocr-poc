"""Shared test fixtures for billet OCR tests."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

# Ensure the project root is importable regardless of how pytest is invoked.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import RAW_DIR, ANNOTATED_DIR, SUPPORTED_FORMATS


# ---------------------------------------------------------------------------
# Windows / OneDrive symlink cleanup workaround
# ---------------------------------------------------------------------------
# pytest 9.x calls Path.resolve() inside cleanup_dead_symlinks() during
# session teardown.  On Windows 11 with OneDrive-synced project directories,
# previously created temp symlinks in AppData\Local\Temp raise WinError 448
# ("untrusted mount point").  We patch both the _pytest.pathlib function AND
# the _pytest.tmpdir session-finish hook to swallow OSError.
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    try:
        import _pytest.pathlib as _ppl
        import _pytest.tmpdir as _ppt

        _orig_cleanup_symlinks = _ppl.cleanup_dead_symlinks

        def _safe_cleanup_symlinks(p: Path) -> None:  # type: ignore[misc]
            """Wrap symlink cleaner to ignore Windows OneDrive mount errors."""
            try:
                _orig_cleanup_symlinks(p)
            except OSError:
                pass

        _ppl.cleanup_dead_symlinks = _safe_cleanup_symlinks

        # Also patch the session-finish hook that calls it.
        _orig_session_finish = _ppt.TempPathFactory.cleanup
        if hasattr(_ppt, "TempPathFactory") and hasattr(_ppt.TempPathFactory, "cleanup"):

            def _safe_factory_cleanup(self) -> None:  # type: ignore[misc]
                """Wrap TempPathFactory.cleanup to ignore WinError 448."""
                try:
                    _orig_session_finish(self)
                except OSError:
                    pass

            _ppt.TempPathFactory.cleanup = _safe_factory_cleanup

    except Exception:  # noqa: BLE001 – best-effort, never break test collection
        pass


@pytest.fixture
def sample_image_path() -> Path:
    """Return path to a known test image (largest file for best quality)."""
    return RAW_DIR / "image_22.png"


@pytest.fixture
def sample_image_array(sample_image_path: Path) -> np.ndarray:
    """Return a loaded test image as numpy array in BGR format."""
    img = cv2.imread(str(sample_image_path))
    assert img is not None, f"Failed to load {sample_image_path}"
    return img


@pytest.fixture
def all_raw_image_paths() -> list[Path]:
    """Return paths to all raw billet images, sorted by name."""
    paths = []
    for fmt in SUPPORTED_FORMATS:
        paths.extend(RAW_DIR.glob(f"*{fmt}"))
    return sorted(set(paths), key=lambda p: p.name)


@pytest.fixture
def ground_truth() -> list[dict]:
    """Load ground truth annotations from JSON.

    Returns empty list if ground truth file doesn't exist yet.
    """
    gt_path = ANNOTATED_DIR / "ground_truth.json"
    if not gt_path.exists():
        return []
    with open(gt_path, "r") as f:
        return json.load(f)


@pytest.fixture
def synthetic_digit_image() -> np.ndarray:
    """Create a synthetic image with known text for deterministic testing.

    Generates a 200x100 dark image with white text "184767" drawn on it,
    mimicking a billet stamp appearance.
    """
    img = np.zeros((100, 200), dtype=np.uint8)
    img[:] = 40  # dark gray background (like oxidized steel)
    cv2.putText(
        img, "184767", (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX, 1.2, 200, 2,
    )
    return img
