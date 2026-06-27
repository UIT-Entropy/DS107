# RiceCare Web Demo

`RiceDisease/` is the integrated web demo for the DS107 rice pest detection and advisory system. It connects the YOLO pest detector with the Gemini RAG advisor and exposes the result through a React chat UI.

## Folder Map

```text
RiceDisease/
  README.md                     this web-demo guide
  backend/                      FastAPI API layer
    main.py                     endpoints for prediction, chat, and model list
    paths.py                    shared repo path resolution
    requirements.txt            backend, CV, and advisor dependencies
  frontend/                     React + Vite interface
    src/                        chat UI, upload flow, and API client
    public/                     favicon and icons
    package.json                npm scripts and dependencies
  DS107_CVModule-main/          YOLO11s inference module
    cv_module/                  detector, visualization, confidence logic
    E08_yolo11s_img416_default_best.pt
```

The web backend uses the repository-root modules:

```text
../advisor/                     Gemini RAG advisor
../rice_pest_crawler/           RAG chunks and crawler outputs
```

Do not use or recreate the old copied folder `RiceDisease/DS107-main/`; the root modules above are the source of truth.

## Runtime Files

These folders/files are created while running the demo and should not be submitted:

```text
backend/uploads/
DS107_CVModule-main/cache/
frontend/node_modules/
frontend/dist/
../advisor/data/gemini_embeddings.jsonl
../advisor/data/gemini_embeddings.jsonl.meta.json
../advisor/data/sessions/
```

## Setup

Run from the repository root unless a command says otherwise.

Install backend dependencies:

```powershell
python -m pip install -r RiceDisease\backend\requirements.txt
```

Install frontend dependencies:

```powershell
cd RiceDisease\frontend
npm install
cd ..\..
```

Create the Gemini key file:

```text
advisor/api_key.py
```

```python
GEMINI_API_KEY = "your_real_gemini_api_key"
```

Build the advisor index before a full RAG demo:

```powershell
python advisor\gemini_rag.py build-index
python advisor\gemini_rag.py index-info
```

## Run Demo

Terminal 1, start FastAPI:

```powershell
python -m uvicorn RiceDisease.backend.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2, start Vite:

```powershell
cd RiceDisease\frontend
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run dev -- --host 127.0.0.1 --port 5173
```

Open the app:

```text
http://127.0.0.1:5173
```

Useful backend pages:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/models
```

## Demo Flow

1. Upload one rice pest image in the chat.
2. The backend saves the upload, runs YOLO, returns the predicted pest, confidence, and annotated image.
3. The backend starts an advisor session using the YOLO class as the pest prior.
4. Ask a follow-up question in the same chat, for example `Nen xu ly sau nay nhu the nao?`.
5. The advisor retrieves relevant pest chunks and returns a grounded Vietnamese response with sources.

If the backend starts but chat generation fails, check that `advisor/api_key.py` contains a valid Gemini key and that the advisor index exists in `advisor/data/`.
