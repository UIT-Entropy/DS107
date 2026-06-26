# DS107 Rice Pest Detection and Advisory System

This repository contains the implementation and paper artifacts for a DS107 project on rice pest detection and retrieval-augmented advisory support. The system combines a YOLO-based pest detector with a Gemini-powered RAG advisor for Vietnamese rice pest management questions.

## Repository Layout

```text
DS107.tex                    ACL-style paper source
Training_Yolo/               Kaggle notebook for YOLO experiments
Benchmark/                   Advisory retrieval and generation benchmark
advisor/                     Gemini RAG advisor module
rice_pest_crawler/           Knowledge-base crawler and chunk builder
```

## Current Paper Scope

The paper evaluates:

- Rice pest detection on a 3,156-image bounding-box dataset.
- YOLOv8, YOLO11, and YOLO26 model variants.
- A knowledge base built from agricultural extension and pest-management sources.
- A 40-question advisory benchmark covering 10 pest classes and 4 intents.
- Retrieval metrics: Class Hit@5, Section Hit@5, and MRR@5.
- Generation metrics: ROUGE-L, BERTScore, and semantic similarity.

The latest paper source is in `DS107.tex`.

## Setup

From the repository root:

```powershell
python -m pip install -r advisor\requirements.txt
python -m pip install -r rice_pest_crawler\requirements.txt
```

On Linux/macOS:

```bash
python -m pip install -r advisor/requirements.txt
python -m pip install -r rice_pest_crawler/requirements.txt
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

Benchmark artifacts are stored in `Benchmark/`.

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
