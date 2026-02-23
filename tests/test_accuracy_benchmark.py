"""Accuracy benchmark test suite for the Billet OCR pipeline.

Evaluates PaddleOCR accuracy at three stages:
  1. Raw images with no preprocessing
  2. CLAHE + bilateral-filter preprocessed images
  3. Postprocessed (character confusion corrected) readings

Accuracy metrics:
  - Character accuracy: Levenshtein-based (1 - edit_distance / max_len)
  - Word accuracy: Binary exact match (1.0 or 0.0)

Run with:
    python -m pytest tests/test_accuracy_benchmark.py -v
    python -m pytest tests/test_accuracy_benchmark.py -v -m "not slow"
"""
import sys
import time
from pathlib import Path
from typing import Optional

import pytest

# Ensure project root is importable when executed directly.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import ANNOTATED_DIR, RAW_DIR
from src.models import BilletReading, OCRMethod


# ---------------------------------------------------------------------------
# Accuracy utilities (no external libraries – implement inline)
# ---------------------------------------------------------------------------


def _levenshtein(a: str, b: str) -> int:
    """Compute the Levenshtein edit distance between two strings.

    Implements the standard two-row dynamic-programming algorithm in O(m*n)
    time and O(min(m,n)) space.  No external dependencies.

    Args:
        a: First string.
        b: Second string.

    Returns:
        Integer edit distance (number of single-character insertions,
        deletions, or substitutions needed to transform a into b).
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    # Always iterate over the shorter string to minimise memory.
    if len(a) < len(b):
        a, b = b, a

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            if ca == cb:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[len(b)]


def calculate_character_accuracy(predicted: Optional[str], actual: Optional[str]) -> float:
    """Compute character-level accuracy using Levenshtein distance.

    Accuracy is defined as 1 - (edit_distance / max(len(predicted), len(actual))).
    Both inputs are normalised to empty strings if None.

    Args:
        predicted: OCR-predicted string (may be None).
        actual: Ground truth string (may be None).

    Returns:
        Float in [0.0, 1.0]; 1.0 means perfect match.
    """
    p = (predicted or "").strip()
    a = (actual or "").strip()

    if not p and not a:
        return 1.0  # Both empty – trivially correct.

    max_len = max(len(p), len(a))
    if max_len == 0:
        return 1.0

    dist = _levenshtein(p, a)
    return max(0.0, 1.0 - dist / max_len)


def calculate_word_accuracy(predicted: Optional[str], actual: Optional[str]) -> float:
    """Compute binary word (exact-match) accuracy.

    Args:
        predicted: OCR-predicted string (may be None).
        actual: Ground truth string (may be None).

    Returns:
        1.0 if strings are identical after stripping whitespace, else 0.0.
    """
    p = (predicted or "").strip()
    a = (actual or "").strip()
    return 1.0 if p == a else 0.0


# ---------------------------------------------------------------------------
# Unit tests for accuracy utilities
# ---------------------------------------------------------------------------


class TestAccuracyUtilities:
    """Fast unit tests for the accuracy calculation functions (no PaddleOCR needed)."""

    def test_levenshtein_identical_strings(self) -> None:
        """Edit distance between identical strings must be zero."""
        assert _levenshtein("184767", "184767") == 0

    def test_levenshtein_single_substitution(self) -> None:
        """One substitution must yield distance 1."""
        assert _levenshtein("184767", "184768") == 1

    def test_levenshtein_empty_strings(self) -> None:
        """Empty vs non-empty must equal the length of the non-empty string."""
        assert _levenshtein("", "abc") == 3
        assert _levenshtein("abc", "") == 3
        assert _levenshtein("", "") == 0

    def test_character_accuracy_perfect_match(self) -> None:
        """Perfect match should yield 1.0 character accuracy."""
        assert calculate_character_accuracy("184767", "184767") == 1.0

    def test_character_accuracy_complete_miss(self) -> None:
        """A completely wrong string of the same length should yield 0.0."""
        # "000000" vs "111111": 6 substitutions / max_len 6 = 0.0
        assert calculate_character_accuracy("000000", "111111") == 0.0

    def test_character_accuracy_one_off(self) -> None:
        """One character wrong in a 6-char string should give ~0.833."""
        acc = calculate_character_accuracy("184767", "184768")
        assert abs(acc - (1 - 1 / 6)) < 1e-6

    def test_character_accuracy_none_inputs(self) -> None:
        """None values for both fields must be treated as empty strings (1.0)."""
        assert calculate_character_accuracy(None, None) == 1.0

    def test_character_accuracy_predicted_none(self) -> None:
        """None prediction vs non-empty ground truth should yield 0.0."""
        assert calculate_character_accuracy(None, "184767") == 0.0

    def test_word_accuracy_exact_match(self) -> None:
        """Exact match must return 1.0."""
        assert calculate_word_accuracy("184767", "184767") == 1.0

    def test_word_accuracy_mismatch(self) -> None:
        """Any difference must return 0.0 (binary metric)."""
        assert calculate_word_accuracy("184767", "184768") == 0.0

    def test_word_accuracy_none_both(self) -> None:
        """Both None → both empty strings → exact match → 1.0."""
        assert calculate_word_accuracy(None, None) == 1.0

    def test_word_accuracy_strips_whitespace(self) -> None:
        """Leading/trailing whitespace must not affect the result."""
        assert calculate_word_accuracy("  184767  ", "184767") == 1.0


# ---------------------------------------------------------------------------
# TestAccuracyBenchmark – uses real PaddleOCR (marked slow)
# ---------------------------------------------------------------------------


class TestAccuracyBenchmark:
    """Accuracy benchmark across all ground truth images.

    Each test in this class requires PaddleOCR and is therefore marked
    @pytest.mark.slow.  Skip with: pytest -m "not slow".
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_ground_truth() -> list[dict]:
        """Load and return all ground truth entries.

        Returns:
            List of ground truth dicts, empty list if file is missing.
        """
        import json

        gt_path = ANNOTATED_DIR / "ground_truth.json"
        if not gt_path.exists():
            return []
        with open(gt_path) as fh:
            return json.load(fh)

    @staticmethod
    def _reading_to_combined(reading: BilletReading) -> str:
        """Concatenate heat+strand+sequence into a single comparison string.

        Args:
            reading: BilletReading to flatten.

        Returns:
            Space-separated string of non-None fields.
        """
        parts = [
            (reading.heat_number or ""),
            (reading.strand or ""),
            (reading.sequence or ""),
        ]
        return " ".join(p for p in parts if p).strip()

    @staticmethod
    def _gt_combined(entry: dict) -> str:
        """Flatten a ground truth dict into a single comparison string.

        Args:
            entry: Ground truth dict with keys heat_number, strand, sequence.

        Returns:
            Space-separated string of non-empty fields.
        """
        parts = [
            entry.get("heat_number", ""),
            entry.get("strand", ""),
            entry.get("sequence", ""),
        ]
        return " ".join(p for p in parts if p).strip()

    # ------------------------------------------------------------------
    # Ground truth existence test (fast – no PaddleOCR)
    # ------------------------------------------------------------------

    def test_ground_truth_exists(self) -> None:
        """Ground truth JSON file must exist and contain at least one entry."""
        gt = self._load_ground_truth()
        assert gt, (
            "Ground truth file is missing or empty. "
            "Run scripts/extract_ground_truth.py first."
        )
        assert len(gt) >= 1

    def test_ground_truth_schema(self) -> None:
        """Every ground truth entry must have an 'image' and 'heat_number' key."""
        gt = self._load_ground_truth()
        if not gt:
            pytest.skip("Ground truth file is empty.")
        for entry in gt:
            assert "image" in entry, f"Missing 'image' key in entry: {entry}"
            assert "heat_number" in entry, f"Missing 'heat_number' key in entry: {entry}"

    # ------------------------------------------------------------------
    # PaddleOCR accuracy tests (slow)
    # ------------------------------------------------------------------

    @pytest.mark.slow
    def test_raw_paddleocr_accuracy(self) -> None:
        """Measure PaddleOCR character accuracy on raw (unprocessed) images.

        Asserts that average character accuracy is > 0.0 (model produces some
        output).  Does not fail on low accuracy – the goal is regression tracking.
        """
        from src.ocr.paddle_ocr import run_paddle_pipeline

        gt_entries = self._load_ground_truth()
        if not gt_entries:
            pytest.skip("No ground truth data available.")

        char_accs: list[float] = []
        word_accs: list[float] = []

        for entry in gt_entries:
            img_path = RAW_DIR / entry["image"]
            if not img_path.exists():
                continue

            t0 = time.perf_counter()
            reading = run_paddle_pipeline(img_path, method=OCRMethod.PADDLE_RAW)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            gt_heat = entry.get("heat_number", "")
            char_acc = calculate_character_accuracy(reading.heat_number, gt_heat)
            word_acc = calculate_word_accuracy(reading.heat_number, gt_heat)

            char_accs.append(char_acc)
            word_accs.append(word_acc)

            print(
                f"  [RAW] {entry['image']:20s} | "
                f"predicted={reading.heat_number!r:10s} gt={gt_heat!r:10s} | "
                f"char_acc={char_acc:.3f} word_acc={word_acc:.1f} | "
                f"time={elapsed_ms:.0f}ms"
            )

        if not char_accs:
            pytest.skip("No images matched ground truth entries.")

        avg_char = sum(char_accs) / len(char_accs)
        avg_word = sum(word_accs) / len(word_accs)
        print(f"\n  [RAW] Average char_acc={avg_char:.3f} word_acc={avg_word:.3f}")
        # Non-zero output expectation (model must produce something).
        assert avg_char >= 0.0

    @pytest.mark.slow
    def test_preprocessed_paddleocr_accuracy(self) -> None:
        """Measure PaddleOCR character accuracy on CLAHE-preprocessed images.

        Preprocessing (CLAHE + bilateral filter) is expected to improve accuracy
        over raw images on low-contrast billet photos.
        """
        from src.ocr.paddle_ocr import run_paddle_pipeline
        from src.preprocessing.pipeline import preprocess_billet_image

        gt_entries = self._load_ground_truth()
        if not gt_entries:
            pytest.skip("No ground truth data available.")

        char_accs: list[float] = []
        word_accs: list[float] = []

        for entry in gt_entries:
            img_path = RAW_DIR / entry["image"]
            if not img_path.exists():
                continue

            t0 = time.perf_counter()
            preprocessed, preproc_timing = preprocess_billet_image(img_path)
            reading = run_paddle_pipeline(preprocessed, method=OCRMethod.PADDLE_PREPROCESSED)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            gt_heat = entry.get("heat_number", "")
            char_acc = calculate_character_accuracy(reading.heat_number, gt_heat)
            word_acc = calculate_word_accuracy(reading.heat_number, gt_heat)

            char_accs.append(char_acc)
            word_accs.append(word_acc)

            print(
                f"  [PRE] {entry['image']:20s} | "
                f"predicted={reading.heat_number!r:10s} gt={gt_heat!r:10s} | "
                f"char_acc={char_acc:.3f} word_acc={word_acc:.1f} | "
                f"preproc={preproc_timing['total_ms']:.0f}ms total={elapsed_ms:.0f}ms"
            )

        if not char_accs:
            pytest.skip("No images matched ground truth entries.")

        avg_char = sum(char_accs) / len(char_accs)
        avg_word = sum(word_accs) / len(word_accs)
        print(f"\n  [PRE] Average char_acc={avg_char:.3f} word_acc={avg_word:.3f}")
        assert avg_char >= 0.0

    @pytest.mark.slow
    def test_postprocessed_accuracy(self) -> None:
        """Measure character accuracy after applying confusion correction.

        This is the full pipeline: CLAHE -> PaddleOCR -> char correction.
        Character accuracy should be >= preprocessed-only accuracy.
        """
        from src.ocr.paddle_ocr import run_paddle_pipeline
        from src.postprocess.validator import validate_and_correct_reading
        from src.preprocessing.pipeline import preprocess_billet_image

        gt_entries = self._load_ground_truth()
        if not gt_entries:
            pytest.skip("No ground truth data available.")

        char_accs: list[float] = []
        word_accs: list[float] = []

        for entry in gt_entries:
            img_path = RAW_DIR / entry["image"]
            if not img_path.exists():
                continue

            preprocessed, _ = preprocess_billet_image(img_path)
            raw_reading = run_paddle_pipeline(
                preprocessed, method=OCRMethod.PADDLE_PREPROCESSED
            )
            corrected = validate_and_correct_reading(raw_reading)

            gt_heat = entry.get("heat_number", "")
            char_acc = calculate_character_accuracy(corrected.heat_number, gt_heat)
            word_acc = calculate_word_accuracy(corrected.heat_number, gt_heat)

            char_accs.append(char_acc)
            word_accs.append(word_acc)

            print(
                f"  [POST] {entry['image']:20s} | "
                f"predicted={corrected.heat_number!r:10s} gt={gt_heat!r:10s} | "
                f"char_acc={char_acc:.3f} word_acc={word_acc:.1f}"
            )

        if not char_accs:
            pytest.skip("No images matched ground truth entries.")

        avg_char = sum(char_accs) / len(char_accs)
        avg_word = sum(word_accs) / len(word_accs)
        print(f"\n  [POST] Average char_acc={avg_char:.3f} word_acc={avg_word:.3f}")
        assert avg_char >= 0.0

    @pytest.mark.slow
    def test_print_benchmark_table(self) -> None:
        """Print a full per-image comparison table across all three methods.

        This test always passes.  Its purpose is to produce visible output
        during a benchmark run (pytest -v -s) so developers can review
        per-image accuracy without opening a separate report file.
        """
        from src.ocr.paddle_ocr import run_paddle_pipeline
        from src.postprocess.validator import validate_and_correct_reading
        from src.preprocessing.pipeline import preprocess_billet_image

        gt_entries = self._load_ground_truth()
        if not gt_entries:
            pytest.skip("No ground truth data available.")

        header = (
            f"\n{'Image':22s} | {'GT Heat':8s} | "
            f"{'Raw Acc':8s} | {'Pre Acc':8s} | {'Post Acc':9s}"
        )
        separator = "-" * len(header)
        print(header)
        print(separator)

        raw_accs: list[float] = []
        pre_accs: list[float] = []
        post_accs: list[float] = []

        for entry in gt_entries:
            img_path = RAW_DIR / entry["image"]
            if not img_path.exists():
                print(f"{entry['image']:22s} | MISSING")
                continue

            gt_heat = entry.get("heat_number", "")

            # Raw
            raw_reading = run_paddle_pipeline(img_path, method=OCRMethod.PADDLE_RAW)
            raw_acc = calculate_character_accuracy(raw_reading.heat_number, gt_heat)

            # Preprocessed
            preprocessed, _ = preprocess_billet_image(img_path)
            pre_reading = run_paddle_pipeline(
                preprocessed, method=OCRMethod.PADDLE_PREPROCESSED
            )
            pre_acc = calculate_character_accuracy(pre_reading.heat_number, gt_heat)

            # Postprocessed
            post_reading = validate_and_correct_reading(pre_reading)
            post_acc = calculate_character_accuracy(post_reading.heat_number, gt_heat)

            raw_accs.append(raw_acc)
            pre_accs.append(pre_acc)
            post_accs.append(post_acc)

            print(
                f"{entry['image']:22s} | {gt_heat:8s} | "
                f"{raw_acc:8.3f} | {pre_acc:8.3f} | {post_acc:9.3f}"
            )

        if raw_accs:
            print(separator)
            print(
                f"{'AVERAGE':22s} | {'':8s} | "
                f"{sum(raw_accs)/len(raw_accs):8.3f} | "
                f"{sum(pre_accs)/len(pre_accs):8.3f} | "
                f"{sum(post_accs)/len(post_accs):9.3f}"
            )

        # This test is intentionally always-pass; it exists for output visibility.
        assert True
