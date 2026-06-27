# DS107 Rice Pest Detection and Advisory System

This repository contains the implementation and paper artifacts for a DS107 project on rice pest detection and retrieval-augmented advisory support. The system combines a YOLO-based pest detector with a Gemini-powered RAG advisor for Vietnamese rice pest management questions.

## Repository Layout

```text
README.md                         top-level setup, demo, and submission guide
Training_Yolo/                    Kaggle notebook for YOLO training experiments
Benchmark/                        retrieval/generation benchmark scripts and CSV results
advisor/                          Gemini RAG advisor package
  core/                           advisor orchestration and chat sessions
  embedding/                      embedding index storage and vector search
  gemini/                         Gemini client and retry helpers
  prompts/                        system prompt and prompt builder
  reranker/                       pest-domain reranking logic
  tests/                          offline advisor tests
rice_pest_crawler/                crawler and RAG knowledge-base builder
  config/                         source, crawler, and pest taxonomy configs
  scripts/                        runnable crawl/extract/chunk/audit scripts
  src/crawler/                    crawler implementation
  data/parsed/                    parsed source documents used by the project
  data/rag/                       final RAG chunks consumed by the advisor
  tests/                          crawler tests
RiceDisease/                      integrated web demo
  backend/                        FastAPI API for YOLO prediction and RAG chat
  frontend/                       React + Vite chat UI
  DS107_CVModule-main/            YOLO11s inference module and selected weight
```

Source of truth:

- RAG code lives in root `advisor/`.
- Knowledge-base chunks live in root `rice_pest_crawler/data/rag/`.
- Web code lives in `RiceDisease/backend/` and `RiceDisease/frontend/`.
- YOLO inference code and the selected weight live in `RiceDisease/DS107_CVModule-main/`.

The old nested copy `RiceDisease/DS107-main/` is not part of the submission source and should not be used.

## Submission Package

Keep these items in the zip/package:

```text
README.md
Training_Yolo/
Benchmark/
advisor/
rice_pest_crawler/
RiceDisease/backend/
RiceDisease/frontend/
RiceDisease/DS107_CVModule-main/
```

Do not include generated local files:

```text
.venv/
venv/
.pytest_cache/
__pycache__/
RiceDisease/frontend/node_modules/
RiceDisease/frontend/dist/
RiceDisease/backend/uploads/
RiceDisease/DS107_CVModule-main/cache/
advisor/data/gemini_embeddings.jsonl
advisor/data/gemini_embeddings.jsonl.meta.json
advisor/data/sessions/
rice_pest_crawler/data/raw/
rice_pest_crawler/data/logs/*.jsonl
RiceDisease/DS107-main/
```

`advisor/api_key.py` must contain only the placeholder in the submitted package. Put a real Gemini API key there only on the demo machine, and do not commit or submit the real key.

## Current Paper Scope

The paper evaluates:

- Rice pest detection on a 3,156-image bounding-box dataset.
- YOLOv8, YOLO11, and YOLO26 model variants.
- A knowledge base built from agricultural extension and pest-management sources.
- A 40-question advisory benchmark covering 10 pest classes and 4 intents.
- Retrieval metrics: Class Hit@5, Section Hit@5, and MRR@5.
- Generation metrics: ROUGE-L, BERTScore, and semantic similarity.

The report source is not included in the submission package; this repository focuses on code, data artifacts, and reproducible demo/benchmark instructions.

## Setup

From the repository root:

```powershell
python -m pip install -r advisor\requirements.txt
python -m pip install -r rice_pest_crawler\requirements.txt
python -m pip install -r Benchmark\requirements.txt
```

On Linux/macOS:

```bash
python -m pip install -r advisor/requirements.txt
python -m pip install -r rice_pest_crawler/requirements.txt
python -m pip install -r Benchmark/requirements.txt
```

## Gemini API Key

The Gemini API key is read only from:

```text
advisor/api_key.py
```

Create or edit that file locally:

```python
GEMINI_API_KEY = "your_gemini_api_key_here"
```

Do not commit a real API key.

Check the advisor configuration:

```powershell
python advisor\gemini_rag.py doctor
```

## Build the Advisory Index

The advisor uses chunks from:

```text
rice_pest_crawler\data\rag\all_chunks.jsonl
```

Build a small test index:

```powershell
python advisor\gemini_rag.py build-index --limit 10
```

Build the full index:

```powershell
python advisor\gemini_rag.py build-index
python advisor\gemini_rag.py index-info
```

If the free tier rate limits embedding calls, increase delay:

```powershell
python advisor\gemini_rag.py build-index --delay 2
```

## YOLO to Advisor Flow

Start an advisor session with a detector-provided class id:

```powershell
python advisor\gemini_rag.py sessions start field-001 ^
  --class-id brown_plant_hopper ^
  --confidence 0.91 ^
  --image runs/detect/predict/field_001.jpg ^
  --crop-stage tillering ^
  --location "An Giang"
```

Ask follow-up questions using the same session:

```powershell
python advisor\gemini_rag.py ask "Ray nau gay trieu chung gi tren lua?" --session field-001 --show-sources
python advisor\gemini_rag.py ask "Nen xu ly nhu the nao?" --session field-001 --show-sources
```

Useful session commands:

```powershell
python advisor\gemini_rag.py sessions list
python advisor\gemini_rag.py sessions show field-001
python advisor\gemini_rag.py sessions delete field-001
```

## Advisory Benchmark

Benchmark artifacts are stored in `Benchmark/`. See `Benchmark/README.md` for the folder-level reproduction guide.

Important files:

```text
Benchmark/benchmark_questions.csv   40 class-intent questions
Benchmark/reference_answer.csv      manually prepared reference answers
Benchmark/retrieval_results.csv     top-5 retrieval outputs
Benchmark/retrieval_metrics.csv     Class Hit@5, Section Hit@5, MRR@5
Benchmark/answer_rag_results.csv    RAG generated answers
Benchmark/no_rag_answers.csv        No-RAG baseline answers
Benchmark/generation_metrics.csv    ROUGE-L, BERTScore, semantic similarity
```

Run retrieval evaluation from the benchmark directory:

```powershell
cd Benchmark
python retrieval_eval.py
python metrics_eval.py
```

Run generation metric evaluation after answer files exist:

```powershell
cd Benchmark
python evaluate_generation.py
```

The current benchmark uses the canonical section labels `damage_symptoms`, `field_diagnosis`, `management_ipm`, and `warnings`.

## YOLO Training Notebook

The training and ablation notebook is:

```text
Training_Yolo/train-yolo-rice-pest.ipynb
```

It is designed for Kaggle. The notebook automatically locates a YOLO-format dataset under `/kaggle/input`, patches `data.yaml`, runs selected YOLO experiments, validates on `val` and `test`, and exports summary CSV files/checkpoints.

Key settings reflected in the paper:

- Seed: `42`
- Device: Kaggle NVIDIA Tesla T4 when available
- Epochs: 120 for most experiments, 100 for YOLOv8n-320
- Patience: 15
- Image sizes: 320 and 416
- Batch: automatic Ultralytics batch sizing (`batch=-1`)
- Optimizer: `auto`
- Inference/error-analysis confidence: 0.25

## Web App Integration

The integrated demo app is in `RiceDisease/`. For folder-level details, see `RiceDisease/README.md`.

```text
RiceDisease/backend/                 FastAPI API for YOLO prediction and RAG chat
RiceDisease/frontend/                React + Vite chat UI
RiceDisease/DS107_CVModule-main/     YOLO11s inference wrapper and selected weight
```

Path convention:

```text
advisor/                         source of truth for Gemini RAG
rice_pest_crawler/                source of truth for RAG chunks
RiceDisease/DS107_CVModule-main/  source of truth for YOLO inference
RiceDisease/backend/uploads/      runtime upload folder, ignored by git
RiceDisease/DS107_CVModule-main/cache/ runtime bbox/cache folder, ignored by git
advisor/data/sessions/            runtime chat sessions, ignored by git
```

The backend imports the repository-root `advisor/` and `rice_pest_crawler/` modules directly.

### Web Demo Prerequisites

- Python 3.10+ with `pip`
- Node.js and npm
- A Gemini API key in `advisor/api_key.py`
- The selected YOLO weight at `RiceDisease/DS107_CVModule-main/E08_yolo11s_img416_default_best.pt`
- RAG chunks at `rice_pest_crawler/data/rag/all_chunks.jsonl`

Install backend dependencies from the repository root:

```powershell
python -m pip install -r RiceDisease\backend\requirements.txt
```

Install frontend dependencies:

```powershell
cd RiceDisease\frontend
npm install
cd ..\..
```

Build the advisor index once before the first full RAG demo:

```powershell
python advisor\gemini_rag.py build-index
python advisor\gemini_rag.py index-info
```

For a quick smoke test, use a tiny index:

```powershell
python advisor\gemini_rag.py build-index --limit 10
```

### Run The Web Demo

Terminal 1, backend:

```powershell
python -m uvicorn RiceDisease.backend.main:app --reload --host 127.0.0.1 --port 8000
```

Backend checks:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/models
```

Terminal 2, frontend:

```powershell
cd RiceDisease\frontend
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

Suggested demo script:

1. Upload one rice pest image in the chat.
2. Show the YOLO class, confidence, and annotated image returned by the backend.
3. Ask a follow-up question such as `Nen xu ly sau nay nhu the nao?`.
4. Show that the answer uses the same session, pest prior, and RAG sources.
5. Open `http://127.0.0.1:8000/docs` if the teacher wants to inspect the API.

Optional runtime path overrides:

```powershell
$env:RICECARE_UPLOAD_DIR="RiceDisease/backend/uploads"
$env:RICECARE_CACHE_DIR="RiceDisease/DS107_CVModule-main/cache"
```

Relative override paths are resolved from the repository root.

## Knowledge Base Crawler

The crawler builds the RAG source chunks. See `rice_pest_crawler/README.md` for details.

Common pipeline:

```powershell
python rice_pest_crawler\scripts\run_discovery.py --all
python rice_pest_crawler\scripts\run_crawl.py --all
python rice_pest_crawler\scripts\run_extract.py --all
python rice_pest_crawler\scripts\build_chunks.py
python rice_pest_crawler\scripts\run_local_context.py
python rice_pest_crawler\scripts\build_all_chunks.py
python rice_pest_crawler\scripts\audit_sources.py
```

## Tests

Advisor tests:

```powershell
python -m pytest advisor\tests
```

If Windows blocks the default pytest temp directory, use a local base temp:

```powershell
$env:TMP="$PWD\.tmp_pytest"; $env:TEMP="$PWD\.tmp_pytest"
python -m pytest advisor\tests -q --basetemp=.tmp_pytest\pytest
```

Crawler tests:

```powershell
python -m pytest rice_pest_crawler\tests
```
