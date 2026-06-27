# RiceCare AI Backend

FastAPI backend for the RiceCare web demo.

For the complete web-demo flow, see `../README.md`.

## Path Layout

Run commands from this folder unless noted otherwise.

```text
../../advisor/                     Gemini RAG advisor module
../../rice_pest_crawler/            RAG source chunks
../DS107_CVModule-main/             YOLO inference module and weight
uploads/                            runtime uploaded images, ignored by git
../DS107_CVModule-main/cache/        runtime bbox/cache images, ignored by git
../../advisor/data/sessions/        runtime advisor sessions, ignored by git
```

`main.py` loads these paths through `paths.py`, so a fresh clone works as long as the repository layout above is kept intact.

## API Endpoints

```text
GET  /                  health/info response
GET  /models            available advisor response modes/models
POST /predict           upload one image and run YOLO
POST /predict-multiple  upload one or more images and run YOLO
POST /ask               ask the RAG advisor in a session
GET  /docs              FastAPI Swagger UI
```

Prediction endpoints create an advisor session when YOLO returns a pest class. The frontend reuses that session id for follow-up questions.

## Setup

```powershell
python -m pip install -r requirements.txt
```

Create or edit the repository-root API key file:

```text
../../advisor/api_key.py
```

```python
GEMINI_API_KEY = "your_gemini_api_key_here"
```

Build the advisor index from the repository root if it is missing:

```powershell
python advisor\gemini_rag.py build-index
python advisor\gemini_rag.py index-info
```

## Run

From this folder:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Or from the repository root:

```powershell
python -m uvicorn RiceDisease.backend.main:app --reload --host 127.0.0.1 --port 8000
```

Optional runtime path overrides can be relative to the repository root:

```powershell
$env:RICECARE_UPLOAD_DIR="RiceDisease/backend/uploads"
$env:RICECARE_CACHE_DIR="RiceDisease/DS107_CVModule-main/cache"
```

Runtime uploads, bbox cache images, and advisor session JSON files are generated during demo and should not be submitted.
