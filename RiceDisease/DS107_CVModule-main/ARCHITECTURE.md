# CV Module Architecture

The CV module is the visual front end of the DS107 system. It converts an uploaded rice image into a structured pest-recognition payload that the RAG advisor can use as retrieval context.

## Data Flow

```text
image_path / uploaded image
        |
        v
cv_module.inference.classify_image()
        |
        |-- load YOLO11s once through cv_module.model.get_model()
        |-- predict with imgsz=416, conf=0.25, iou=0.70
        |-- extract boxes, class ids, labels, and confidence scores
        |-- sort detections by confidence
        |-- choose the top detection as summary.predicted_label
        |-- draw bounding boxes into cache/bbox
        |-- build confidence_ir
        |-- build ds107_payload
        v
CV result dict
```

## Components

`cv_module/config.py`

Central configuration: weight path, image size, device, class ids, display labels, confidence thresholds, and cache folders.

`cv_module/model.py`

Loads the Ultralytics model with an `lru_cache`, so the backend process loads the detector only once.

`cv_module/inference.py`

Main inference entry point. It handles upload caching, model prediction, detection extraction, summary generation, bbox rendering, confidence IR, and DS107 payload creation.

`cv_module/confidence.py`

Converts detection confidence into an intermediate representation:

```json
{
  "level": "high | medium | ambiguous | low | no_detection",
  "top_confidence": 0.91,
  "second_confidence": 0.83,
  "confidence_margin": 0.08,
  "needs_llm_confirmation": true,
  "llm_strategy": "cautious_advice_with_confirmation_question",
  "reason": "..."
}
```

`cv_module/visualization.py`

Draws bounding boxes and saves annotated images into `cache/bbox/`.

`cv_module/ds107_bridge.py`

Builds the advisor payload:

```json
{
  "source": "cv_yolo",
  "class_id": "brown_plant_hopper",
  "disease": "ray nau",
  "confidence": 0.91,
  "image": "...",
  "annotated_image": "...",
  "needs_llm_confirmation": false,
  "llm_strategy": "direct_advice",
  "notes": "..."
}
```

## Backend Contract

The FastAPI backend calls:

```python
from cv_module.inference import classify_image

result = classify_image(
    image_path=image_path,
    cache_upload=True,
    include_ds107_payload=True,
)
```

It returns to the frontend:

```text
session_id
disease
class_id
confidence
has_detection
count
image_url
```

It stores the DS107 advisor session with:

```text
class_id
disease
confidence
image_path
notes
```

## Git Hygiene

Commit source code, docs, requirements, and the selected weight file if the team accepts storing the model in git.

Do not commit runtime uploads, bbox cache, generated JSON output, virtual environments, or `__pycache__`.
