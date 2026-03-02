"""LoRA fine-tuning of Florence-2-base on billet stamp OCR images.

Trains a lightweight LoRA adapter on top of the frozen Florence-2-base model
so that it learns the specific visual patterns of dot-matrix and paint-stenciled
billet stamp codes.  The adapter weights are saved separately and can be loaded
at inference time via ``FLORENCE2_LORA_PATH`` in ``src/config.py``.

Dataset layout expected under ``data/training/florence2/``::

    train/
        metadata.jsonl          # {"file_name": "img.jpg", "text": "<OCR>60008\\n5383"}
        img.jpg
        ...
    val/
        metadata.jsonl
        img.jpg
        ...

Usage:
    python scripts/finetune_florence2.py
    python scripts/finetune_florence2.py --epochs 20 --batch-size 2 --lr 5e-5
    python scripts/finetune_florence2.py --data-dir data/training/florence2 --device cuda

Requirements (beyond the base project):
    pip install peft>=0.14.0 accelerate>=0.34.0
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

# ---------------------------------------------------------------------------
# Project-root bootstrap (same pattern as other scripts/ files)
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.config import FLORENCE2_DEVICE, FLORENCE2_MODEL_ID  # noqa: E402


# ---------------------------------------------------------------------------
# Levenshtein-based character accuracy (no external deps)
# ---------------------------------------------------------------------------

def _levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings.

    Uses the standard two-row DP algorithm (O(min(m,n)) space).

    Args:
        s1: First string.
        s2: Second string.

    Returns:
        Integer edit distance.
    """
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def character_accuracy(prediction: str, ground_truth: str) -> float:
    """Compute character-level accuracy between prediction and ground truth.

    Accuracy = 1 - (edit_distance / max(len(pred), len(gt))).
    Returns 1.0 when both strings are empty, 0.0 when one is empty.

    Args:
        prediction: Predicted text string.
        ground_truth: Ground truth text string.

    Returns:
        Float accuracy in [0.0, 1.0].
    """
    if not prediction and not ground_truth:
        return 1.0
    if not prediction or not ground_truth:
        return 0.0
    max_len = max(len(prediction), len(ground_truth))
    dist = _levenshtein_distance(prediction, ground_truth)
    return 1.0 - (dist / max_len)


# ---------------------------------------------------------------------------
# Training metrics dataclass
# ---------------------------------------------------------------------------

@dataclass
class TrainingMetrics:
    """Container for training metrics logged during fine-tuning.

    Attributes:
        epoch: Current epoch number (1-indexed).
        train_loss: Average training loss for the epoch.
        val_loss: Average validation loss for the epoch.
        val_char_acc: Average character accuracy on the validation set.
        learning_rate: Learning rate at end of epoch.
        epoch_time_sec: Wall-clock time for the epoch in seconds.
    """
    epoch: int
    train_loss: float
    val_loss: float
    val_char_acc: float
    learning_rate: float
    epoch_time_sec: float


# ---------------------------------------------------------------------------
# Custom Dataset
# ---------------------------------------------------------------------------

class BilletOCRDataset(Dataset):
    """PyTorch dataset for Florence-2 billet stamp fine-tuning.

    Loads images and OCR labels from a ``metadata.jsonl`` file.  Each JSON
    line must have the keys ``file_name`` (image filename relative to
    ``data_dir``) and ``text`` (the label string, e.g. ``"<OCR>60008\\n5383"``).

    The processor converts the image and task prompt into model inputs while
    the label text is tokenised into target ``labels`` for the causal-LM head.

    Args:
        data_dir: Directory containing ``metadata.jsonl`` and the images.
        processor: Florence-2 ``AutoProcessor`` instance.
        task: Florence-2 task prompt (default ``"<OCR>"``).
    """

    def __init__(
        self,
        data_dir: str | Path,
        processor: Any,
        task: str = "<OCR>",
    ) -> None:
        from PIL import Image as _PILImage  # noqa: F811 -- local import to avoid top-level dep

        self._pil_mod = _PILImage
        self.data_dir = Path(data_dir)
        self.processor = processor
        self.task = task

        metadata_path = self.data_dir / "metadata.jsonl"
        if not metadata_path.exists():
            raise FileNotFoundError(
                f"metadata.jsonl not found at {metadata_path}. "
                "Run the dataset preparation script first."
            )

        self.samples: list[dict[str, str]] = []
        with open(metadata_path, "r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    print(f"[WARNING] Skipping malformed JSON at line {line_no}: {exc}")
                    continue
                if "file_name" not in record or "text" not in record:
                    print(
                        f"[WARNING] Skipping line {line_no}: missing 'file_name' or 'text' key"
                    )
                    continue
                img_path = self.data_dir / record["file_name"]
                if not img_path.exists():
                    print(f"[WARNING] Image not found, skipping: {img_path}")
                    continue
                self.samples.append(record)

        print(f"[Dataset] Loaded {len(self.samples)} samples from {metadata_path}")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        """Load a single sample and return model-ready tensors.

        Args:
            idx: Sample index.

        Returns:
            Dict with keys ``pixel_values``, ``input_ids``, ``labels``.
        """
        record = self.samples[idx]
        img_path = self.data_dir / record["file_name"]
        image = self._pil_mod.open(img_path).convert("RGB")

        # The text field may already include the task token (e.g. "<OCR>60008\n5383").
        # Strip the task prefix so we have only the ground-truth text as the label.
        label_text = record["text"]
        if label_text.startswith(self.task):
            label_text = label_text[len(self.task):]

        # Process image + task prompt -> pixel_values, input_ids
        inputs = self.processor(
            text=self.task,
            images=image,
            return_tensors="pt",
        )

        # Tokenise the label text for the decoder target
        labels = self.processor.tokenizer(
            label_text,
            return_tensors="pt",
            padding=False,
            truncation=True,
            max_length=128,
        ).input_ids

        # Squeeze batch dim (DataLoader adds it back)
        return {
            "pixel_values": inputs["pixel_values"].squeeze(0),
            "input_ids": inputs["input_ids"].squeeze(0),
            "labels": labels.squeeze(0),
        }


def _collate_fn(
    batch: list[dict[str, torch.Tensor]],
) -> dict[str, torch.Tensor]:
    """Collate function that pads variable-length sequences.

    Pads ``input_ids`` and ``labels`` to the longest sequence in the batch
    using ``-100`` for labels (ignored by cross-entropy loss) and ``0`` for
    input_ids.

    Args:
        batch: List of sample dicts from ``BilletOCRDataset.__getitem__``.

    Returns:
        Batched dict with padded tensors.
    """
    pixel_values = torch.stack([s["pixel_values"] for s in batch])

    # Pad input_ids
    max_input_len = max(s["input_ids"].size(0) for s in batch)
    input_ids = torch.zeros(len(batch), max_input_len, dtype=torch.long)
    for i, s in enumerate(batch):
        length = s["input_ids"].size(0)
        input_ids[i, :length] = s["input_ids"]

    # Pad labels with -100 (ignore index for cross-entropy)
    max_label_len = max(s["labels"].size(0) for s in batch)
    labels = torch.full((len(batch), max_label_len), -100, dtype=torch.long)
    for i, s in enumerate(batch):
        length = s["labels"].size(0)
        labels[i, :length] = s["labels"]

    return {
        "pixel_values": pixel_values,
        "input_ids": input_ids,
        "labels": labels,
    }


# ---------------------------------------------------------------------------
# Device + dtype helpers
# ---------------------------------------------------------------------------

def resolve_device(requested: str) -> str:
    """Resolve compute device, falling back to CPU if CUDA is unavailable.

    Args:
        requested: Requested device string (``"cuda"`` or ``"cpu"``).

    Returns:
        Actual device string that can be used.
    """
    if requested == "cuda" and not torch.cuda.is_available():
        print(
            "[WARNING] CUDA requested but not available -- falling back to CPU. "
            "Training will be significantly slower."
        )
        return "cpu"
    return requested


def get_dtype(device: str) -> torch.dtype:
    """Return the appropriate dtype for the given device.

    Uses bfloat16 on CUDA for memory efficiency, float32 on CPU.

    Args:
        device: Device string (``"cuda"`` or ``"cpu"``).

    Returns:
        ``torch.bfloat16`` for CUDA, ``torch.float32`` for CPU.
    """
    return torch.bfloat16 if device == "cuda" else torch.float32


def print_gpu_memory(prefix: str = "") -> None:
    """Print current GPU memory usage if CUDA is available.

    Args:
        prefix: Optional prefix string for the log line.
    """
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / (1024 ** 3)
        reserved = torch.cuda.memory_reserved() / (1024 ** 3)
        print(f"{prefix}GPU memory: allocated={allocated:.2f}GB, reserved={reserved:.2f}GB")


# ---------------------------------------------------------------------------
# Model + LoRA setup
# ---------------------------------------------------------------------------

def load_model_and_processor(
    model_id: str,
    device: str,
    lora_r: int = 16,
    lora_alpha: int = 32,
    lora_dropout: float = 0.1,
) -> tuple[Any, Any]:
    """Load Florence-2 model with LoRA adapters and the processor.

    The base model weights are frozen; only LoRA adapter parameters are
    trainable.  Prints the number of trainable vs total parameters.

    Args:
        model_id: HuggingFace model ID for Florence-2.
        device: Compute device (``"cuda"`` or ``"cpu"``).
        lora_r: LoRA rank (number of low-rank dimensions).
        lora_alpha: LoRA alpha scaling factor.
        lora_dropout: Dropout probability for LoRA layers.

    Returns:
        Tuple of ``(model, processor)``.

    Raises:
        ImportError: If ``peft`` is not installed.
    """
    from peft import LoraConfig, get_peft_model
    from transformers import AutoProcessor, Florence2ForConditionalGeneration

    print(f"[Model] Loading {model_id} ...")
    t0 = time.perf_counter()

    dtype = get_dtype(device)

    model = Florence2ForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=dtype,
    )

    # Configure LoRA
    lora_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.to(device)

    # Print parameter summary
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(
        f"[Model] LoRA applied | trainable={trainable_params:,} "
        f"({100 * trainable_params / total_params:.2f}%) | total={total_params:,}"
    )

    processor = AutoProcessor.from_pretrained(model_id)

    elapsed = time.perf_counter() - t0
    print(f"[Model] Loaded in {elapsed:.1f}s | device={device} | dtype={dtype}")
    print_gpu_memory("[Model] ")

    return model, processor


# ---------------------------------------------------------------------------
# Learning rate schedule (cosine with warmup)
# ---------------------------------------------------------------------------

def get_cosine_schedule_with_warmup(
    optimizer: torch.optim.Optimizer,
    num_warmup_steps: int,
    num_training_steps: int,
) -> torch.optim.lr_scheduler.LambdaLR:
    """Create a cosine learning rate schedule with linear warmup.

    During warmup the LR linearly increases from 0 to the base LR.
    After warmup it follows a cosine decay to 0.

    Args:
        optimizer: The optimizer whose LR will be scheduled.
        num_warmup_steps: Number of warmup steps.
        num_training_steps: Total number of training steps.

    Returns:
        A ``LambdaLR`` scheduler.
    """

    def lr_lambda(current_step: int) -> float:
        """Compute LR multiplier for the given step."""
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        progress = float(current_step - num_warmup_steps) / float(
            max(1, num_training_steps - num_warmup_steps)
        )
        return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))

    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@torch.no_grad()
def run_validation(
    model: Any,
    processor: Any,
    val_loader: DataLoader,
    device: str,
    dtype: torch.dtype,
    task: str = "<OCR>",
) -> tuple[float, float]:
    """Run validation and compute loss and character accuracy.

    Iterates over the validation set in inference mode.  For each batch it
    computes the forward-pass loss and then runs greedy decoding to produce
    predictions for character-accuracy calculation.

    Args:
        model: The Florence-2 model (with LoRA).
        processor: Florence-2 processor / tokenizer.
        val_loader: Validation DataLoader.
        device: Compute device.
        dtype: Model dtype.
        task: Florence-2 task prompt.

    Returns:
        Tuple of ``(avg_val_loss, avg_char_accuracy)``.
    """
    model.eval()
    total_loss = 0.0
    total_char_acc = 0.0
    num_batches = 0
    num_samples = 0

    for batch in val_loader:
        pixel_values = batch["pixel_values"].to(device, dtype)
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)

        # Forward pass for loss
        outputs = model(
            pixel_values=pixel_values,
            input_ids=input_ids,
            labels=labels,
        )
        total_loss += outputs.loss.item()
        num_batches += 1

        # Greedy decoding for character accuracy
        generated_ids = model.generate(
            pixel_values=pixel_values,
            input_ids=input_ids,
            max_new_tokens=128,
        )
        predictions = processor.batch_decode(generated_ids, skip_special_tokens=True)

        # Decode ground-truth labels (replace -100 with pad token before decoding)
        label_ids = labels.clone()
        pad_token_id = processor.tokenizer.pad_token_id
        if pad_token_id is None:
            pad_token_id = 0
        label_ids[label_ids == -100] = pad_token_id
        references = processor.batch_decode(label_ids, skip_special_tokens=True)

        for pred, ref in zip(predictions, references):
            # Strip the task prompt from predictions if present
            pred_clean = pred.strip()
            if pred_clean.startswith(task):
                pred_clean = pred_clean[len(task):]
            ref_clean = ref.strip()

            total_char_acc += character_accuracy(pred_clean, ref_clean)
            num_samples += 1

    avg_loss = total_loss / max(1, num_batches)
    avg_char_acc = total_char_acc / max(1, num_samples)

    model.train()
    return avg_loss, avg_char_acc


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def train(
    model: Any,
    processor: Any,
    train_loader: DataLoader,
    val_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LambdaLR,
    device: str,
    dtype: torch.dtype,
    epochs: int,
    grad_accum_steps: int,
    output_dir: Path,
    task: str = "<OCR>",
) -> list[TrainingMetrics]:
    """Run the full training loop with validation and checkpointing.

    After each epoch:
    1. Logs training loss and learning rate.
    2. Runs validation to compute val_loss and val_char_acc.
    3. Saves the LoRA adapter if val_char_acc improves (best checkpoint).
    4. Saves the latest checkpoint unconditionally.

    Args:
        model: Florence-2 model with LoRA adapters.
        processor: Florence-2 processor / tokenizer.
        train_loader: Training DataLoader.
        val_loader: Validation DataLoader.
        optimizer: Optimizer.
        scheduler: Learning rate scheduler.
        device: Compute device.
        dtype: Model dtype.
        epochs: Number of training epochs.
        grad_accum_steps: Gradient accumulation steps.
        output_dir: Directory to save checkpoints and logs.
        task: Florence-2 task prompt.

    Returns:
        List of ``TrainingMetrics`` (one per epoch).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    best_dir = output_dir / "best"
    best_dir.mkdir(parents=True, exist_ok=True)
    latest_dir = output_dir / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)

    best_char_acc = -1.0
    all_metrics: list[TrainingMetrics] = []
    global_step = 0

    print(f"\n{'='*70}")
    print(f"  Starting LoRA fine-tuning for {epochs} epochs")
    print(f"  Train samples: {len(train_loader.dataset)}")
    print(f"  Val samples:   {len(val_loader.dataset)}")
    print(f"  Batch size:    {train_loader.batch_size}")
    print(f"  Grad accum:    {grad_accum_steps}")
    print(f"  Effective BS:  {train_loader.batch_size * grad_accum_steps}")
    print(f"  Output dir:    {output_dir}")
    print(f"{'='*70}\n")

    for epoch in range(1, epochs + 1):
        epoch_start = time.perf_counter()
        model.train()

        epoch_loss = 0.0
        num_steps = 0
        optimizer.zero_grad()

        for batch_idx, batch in enumerate(train_loader):
            pixel_values = batch["pixel_values"].to(device, dtype)
            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(
                pixel_values=pixel_values,
                input_ids=input_ids,
                labels=labels,
            )

            loss = outputs.loss / grad_accum_steps
            loss.backward()

            epoch_loss += outputs.loss.item()
            num_steps += 1

            if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == len(train_loader):
                # Gradient clipping for stability
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                global_step += 1

                # Log every 10 effective steps
                if global_step % 10 == 0:
                    current_lr = scheduler.get_last_lr()[0]
                    avg_loss_so_far = epoch_loss / num_steps
                    print(
                        f"  [Epoch {epoch}/{epochs}] step={global_step} | "
                        f"loss={avg_loss_so_far:.4f} | lr={current_lr:.2e}"
                    )

        avg_train_loss = epoch_loss / max(1, num_steps)

        # Validation
        val_loss, val_char_acc = run_validation(
            model, processor, val_loader, device, dtype, task
        )

        epoch_time = time.perf_counter() - epoch_start
        current_lr = scheduler.get_last_lr()[0]

        metrics = TrainingMetrics(
            epoch=epoch,
            train_loss=avg_train_loss,
            val_loss=val_loss,
            val_char_acc=val_char_acc,
            learning_rate=current_lr,
            epoch_time_sec=epoch_time,
        )
        all_metrics.append(metrics)

        is_best = val_char_acc > best_char_acc
        best_marker = " ** BEST **" if is_best else ""
        print(
            f"\n  Epoch {epoch}/{epochs} | "
            f"train_loss={avg_train_loss:.4f} | "
            f"val_loss={val_loss:.4f} | "
            f"val_char_acc={val_char_acc:.4f} | "
            f"lr={current_lr:.2e} | "
            f"time={epoch_time:.1f}s{best_marker}\n"
        )
        print_gpu_memory("  ")

        # Save latest checkpoint
        _save_lora_adapter(model, latest_dir)

        # Save best checkpoint
        if is_best:
            best_char_acc = val_char_acc
            _save_lora_adapter(model, best_dir)
            print(f"  -> Best model saved (char_acc={best_char_acc:.4f})\n")

        # Save metrics log after each epoch
        _save_metrics_log(all_metrics, output_dir / "training_metrics.json")

    print(f"\n{'='*70}")
    print(f"  Training complete!")
    print(f"  Best val_char_acc: {best_char_acc:.4f}")
    print(f"  Best checkpoint:   {best_dir}")
    print(f"  Latest checkpoint: {latest_dir}")
    print(f"{'='*70}\n")

    return all_metrics


# ---------------------------------------------------------------------------
# Checkpoint saving helpers
# ---------------------------------------------------------------------------

def _save_lora_adapter(model: Any, save_dir: Path) -> None:
    """Save LoRA adapter weights to disk.

    Uses peft's ``save_pretrained`` which saves only the adapter
    weights and config (not the full base model).

    Args:
        model: The PeftModel to save.
        save_dir: Directory to save adapter weights into.
    """
    save_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(save_dir))


def _save_metrics_log(
    metrics: list[TrainingMetrics],
    path: Path,
) -> None:
    """Save training metrics as a JSON file.

    Args:
        metrics: List of per-epoch training metrics.
        path: Path to write the JSON file.
    """
    data = [asdict(m) for m in metrics]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def _save_training_config(args: argparse.Namespace, output_dir: Path) -> None:
    """Save the training configuration (CLI args) as JSON for reproducibility.

    Args:
        args: Parsed CLI arguments.
        output_dir: Directory to save the config file into.
    """
    config = vars(args)
    # Convert Path objects to strings for JSON serialisation
    config = {k: str(v) if isinstance(v, Path) else v for k, v in config.items()}
    path = output_dir / "training_config.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)
    print(f"[Config] Saved training config to {path}")


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for fine-tuning.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="LoRA fine-tuning of Florence-2-base on billet stamp OCR images.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=_PROJECT_ROOT / "data" / "training" / "florence2",
        help="Root directory containing train/ and val/ subdirectories.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_PROJECT_ROOT / "models" / "florence2_billet_lora",
        help="Directory to save LoRA adapter weights and training logs.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=10,
        help="Number of training epochs.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Batch size per device (adjust for VRAM).",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-4,
        help="Peak learning rate.",
    )
    parser.add_argument(
        "--lora-r",
        type=int,
        default=16,
        help="LoRA rank (number of low-rank dimensions).",
    )
    parser.add_argument(
        "--lora-alpha",
        type=int,
        default=32,
        help="LoRA alpha scaling factor.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=FLORENCE2_DEVICE,
        help="Compute device ('cuda' or 'cpu').",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--grad-accum-steps",
        type=int,
        default=4,
        help="Gradient accumulation steps (effective batch = batch-size * grad-accum).",
    )
    parser.add_argument(
        "--warmup-ratio",
        type=float,
        default=0.1,
        help="Fraction of total steps used for LR warmup.",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=FLORENCE2_MODEL_ID,
        help="HuggingFace model ID for Florence-2.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility across Python, NumPy, and PyTorch.

    Args:
        seed: The seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: parse args, load data, train, save."""
    args = parse_args()

    set_seed(args.seed)

    # Resolve device
    device = resolve_device(args.device)
    dtype = get_dtype(device)

    print(f"\n[Config] device={device} | dtype={dtype} | seed={args.seed}")
    print(f"[Config] model_id={args.model_id}")
    print(f"[Config] data_dir={args.data_dir}")
    print(f"[Config] output_dir={args.output_dir}")
    print(f"[Config] epochs={args.epochs} | batch_size={args.batch_size} | lr={args.lr}")
    print(f"[Config] lora_r={args.lora_r} | lora_alpha={args.lora_alpha}")
    print(f"[Config] grad_accum={args.grad_accum_steps} | warmup_ratio={args.warmup_ratio}")

    if device == "cuda":
        print_gpu_memory("[Config] ")

    # Validate data directory
    train_dir = args.data_dir / "train"
    val_dir = args.data_dir / "val"
    if not train_dir.exists():
        print(f"\n[ERROR] Training data directory not found: {train_dir}")
        print("Please prepare the dataset first. Expected structure:")
        print(f"  {args.data_dir}/")
        print("    train/")
        print('      metadata.jsonl   ({"file_name": "img.jpg", "text": "<OCR>60008\\n5383"})')
        print("      img.jpg")
        print("    val/")
        print("      metadata.jsonl")
        print("      img.jpg")
        sys.exit(1)
    if not val_dir.exists():
        print(f"\n[ERROR] Validation data directory not found: {val_dir}")
        sys.exit(1)

    # Load model and processor
    model, processor = load_model_and_processor(
        model_id=args.model_id,
        device=device,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
    )

    # Create datasets
    print("\n[Data] Loading training dataset ...")
    train_dataset = BilletOCRDataset(train_dir, processor)
    print("[Data] Loading validation dataset ...")
    val_dataset = BilletOCRDataset(val_dir, processor)

    if len(train_dataset) == 0:
        print("[ERROR] Training dataset is empty. Check your metadata.jsonl and images.")
        sys.exit(1)
    if len(val_dataset) == 0:
        print("[ERROR] Validation dataset is empty. Check your metadata.jsonl and images.")
        sys.exit(1)

    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=_collate_fn,
        num_workers=0,  # Windows compatibility
        pin_memory=(device == "cuda"),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=_collate_fn,
        num_workers=0,
        pin_memory=(device == "cuda"),
    )

    # Optimizer
    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr,
        weight_decay=0.01,
    )

    # Scheduler
    steps_per_epoch = math.ceil(len(train_loader) / args.grad_accum_steps)
    total_steps = steps_per_epoch * args.epochs
    warmup_steps = int(total_steps * args.warmup_ratio)

    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    print(
        f"\n[Schedule] steps_per_epoch={steps_per_epoch} | "
        f"total_steps={total_steps} | warmup_steps={warmup_steps}"
    )

    # Save training config for reproducibility
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _save_training_config(args, args.output_dir)

    # Train
    metrics = train(
        model=model,
        processor=processor,
        train_loader=train_loader,
        val_loader=val_loader,
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        dtype=dtype,
        epochs=args.epochs,
        grad_accum_steps=args.grad_accum_steps,
        output_dir=args.output_dir,
    )

    # Final summary
    if metrics:
        best_epoch = max(metrics, key=lambda m: m.val_char_acc)
        print(f"\nBest epoch: {best_epoch.epoch}")
        print(f"  train_loss:   {best_epoch.train_loss:.4f}")
        print(f"  val_loss:     {best_epoch.val_loss:.4f}")
        print(f"  val_char_acc: {best_epoch.val_char_acc:.4f}")
        print(f"\nLoRA adapter saved to: {args.output_dir / 'best'}")
        print(
            f"\nTo use the fine-tuned model, set in src/config.py:\n"
            f'  FLORENCE2_LORA_PATH = "{args.output_dir / "best"}"'
        )


if __name__ == "__main__":
    main()
