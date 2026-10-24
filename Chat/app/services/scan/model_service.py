"""
Model Service — EfficientNet-B0 Disease Detection
Lazy-loaded singleton: model loaded on first prediction, reused across requests.
Thread-safe initialization prevents duplicate loads from concurrent requests.
"""

import json
import logging
import threading
from pathlib import Path
from io import BytesIO
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# ── Paths (relative to this file's parent → app/ml/) ──
_APP_DIR = Path(__file__).resolve().parent.parent.parent  # Backend/Chat/app
_MODEL_PATH = _APP_DIR / "ml" / "efficientnet_fixed.pth"
_LABEL_PATH = _APP_DIR / "ml" / "efficientnet_labels.json"

# ── Singleton state ──
_model = None
_class_names = None
_transform = None
_device = None
_init_lock = threading.Lock()


def _get_device():
    """Lazily determine the compute device."""
    import torch
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _get_transform():
    """Lazily build the preprocessing pipeline (must match training)."""
    from torchvision import transforms
    return transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])


def load_model() -> None:
    """
    Load the EfficientNet-B0 model and class labels into memory.
    Thread-safe: uses a lock so concurrent first requests don't load duplicates.
    """
    global _model, _class_names, _transform, _device

    # Fast path: already loaded
    if _model is not None:
        logger.info("[ScanModel] Model already loaded, skipping.")
        return

    with _init_lock:
        # Double-check after acquiring lock
        if _model is not None:
            return

        import torch
        from torchvision import models

        _device = _get_device()
        _transform = _get_transform()

        # Load labels
        if not _LABEL_PATH.exists():
            raise FileNotFoundError(f"Label file not found: {_LABEL_PATH}")

        with open(_LABEL_PATH, "r") as f:
            _class_names = json.load(f)
        logger.info(f"[ScanModel] Loaded {len(_class_names)} class labels from {_LABEL_PATH.name}")

        # Load model
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {_MODEL_PATH}")

        model = models.efficientnet_b0(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = torch.nn.Sequential(
            torch.nn.Dropout(0.4),
            torch.nn.Linear(in_features, 512),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.4),
            torch.nn.Linear(512, len(_class_names)),
        )

        checkpoint = torch.load(_MODEL_PATH, map_location=_device, weights_only=False)
        state_dict = (
            checkpoint["model_state_dict"]
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint
            else checkpoint
        )
        model.load_state_dict(state_dict)
        model.to(_device).eval()

        _model = model
        logger.info(f"[ScanModel] EfficientNet-B0 loaded on {_device}")


def _parse_label(raw_label: str) -> Tuple[str, str, bool]:
    """
    Parse a raw label like 'tomato_early_blight' into:
      crop_name='Tomato', disease_name='Early Blight', is_healthy=False
    """
    parts = raw_label.split("_")
    crop_name = parts[0].capitalize()
    disease_parts = parts[1:]
    disease_name = " ".join(p.capitalize() for p in disease_parts)
    is_healthy = "healthy" in raw_label.lower()
    return crop_name, disease_name, is_healthy


def predict(image_bytes: bytes) -> dict:
    """
    Run inference on raw image bytes.
    Lazily loads the model on first call if not already loaded.
    Returns dict with: disease_label, crop_name, disease_name, confidence, is_healthy
    """
    # Lazy-load model on first predict call
    if _model is None:
        load_model()

    if _model is None or _class_names is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    import torch
    from PIL import Image

    # Open image from bytes (no disk write)
    img = Image.open(BytesIO(image_bytes)).convert("RGB")

    # Preprocess
    img_tensor = _transform(img).unsqueeze(0).to(_device)

    # Inference
    with torch.no_grad():
        output = _model(img_tensor)
        probs = torch.nn.functional.softmax(output[0], dim=0)
        confidence, index = torch.max(probs, 0)

    raw_label = _class_names[index.item()]
    crop_name, disease_name, is_healthy = _parse_label(raw_label)

    return {
        "disease_label": raw_label,
        "crop_name": crop_name,
        "disease_name": disease_name,
        "confidence": round(confidence.item(), 4),
        "is_healthy": is_healthy,
    }
