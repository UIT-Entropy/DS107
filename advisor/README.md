# Advisor Module

`advisor/` implements the Gemini-based retrieval-augmented advisory component. It retrieves rice pest knowledge chunks, reranks them with domain signals, builds a grounded prompt, and generates a Vietnamese advisory response.

## Main Entry Point

Run commands from the repository root:

```powershell
python advisor\gemini_rag.py doctor
```

Linux/macOS:

```bash
python advisor/gemini_rag.py doctor
```

## API Key

The Gemini API key is loaded from:

```text
advisor/api_key.py
```

Example local file:

```python
GEMINI_API_KEY = "your_gemini_api_key_here"
```

Do not commit a real key.

## Model Profile

The active profile is configured in `advisor/config.py`:

```python
MODEL_PROFILE = "free"
```

Current profiles:

```text
free     gemini-embedding-001 + gemini-2.5-flash-lite
balanced gemini-embedding-2   + gemini-2.5-flash
quality  gemini-embedding-2   + gemini-3.5-flash
```

The paper and benchmark use the `free` profile unless explicitly overridden by a benchmark script.

## Build Index

Input chunks:

```text
rice_pest_crawler\data\rag\all_chunks.jsonl
```

Output index:

```text
advisor\data\gemini_embeddings.jsonl
advisor\data\gemini_embeddings.jsonl.meta.json
```

Commands:

```powershell
python advisor\gemini_rag.py build-index --limit 10
python advisor\gemini_rag.py build-index
python advisor\gemini_rag.py index-info
```

Use `--delay` if the embedding API is rate limited:

```powershell
python advisor\gemini_rag.py build-index --delay 2
```

## Retrieve Only

Inspect retrieved/reranked chunks without generation:

```powershell
python advisor\gemini_rag.py retrieve "Ray nau gay trieu chung gi tren cay lua?"
```

## YOLO Session Flow

Production flow:

```text
YOLO detection -> class_id -> advisor session -> retrieval prior -> RAG answer
```

Start a session:

```powershell
python advisor\gemini_rag.py sessions start field-001 ^
  --class-id brown_plant_hopper ^
  --confidence 0.91 ^
  --image runs/detect/predict/field_001.jpg
```

Ask with session context:

```powershell
python advisor\gemini_rag.py ask "Can xu ly ray nau nhu the nao?" --session field-001 --show-sources
```

Ask without a session:

```powershell
python advisor\gemini_rag.py ask "Sau cuon la lua gay trieu chung gi?" --show-sources
```

Session management:

```powershell
python advisor\gemini_rag.py sessions list
python advisor\gemini_rag.py sessions show field-001
python advisor\gemini_rag.py sessions delete field-001
python advisor\gemini_rag.py sessions clear
```

## Internal Structure

```text
advisor/
  api_key.py              local API key file
  config.py               model profiles, paths, class labels
  cli.py                  command-line interface
  gemini_rag.py           entry point
  core/                   advisor orchestration and sessions
  embedding/              embedding formatting, index storage, vector search
  gemini/                 Gemini client and retry logic
  prompts/                system prompt and prompt builder
  reranker/               domain reranker
  tests/                  offline tests
```

## Tests

```powershell
python -m pytest advisor\tests
```

Windows temp-directory workaround:

```powershell
$env:TMP="$PWD\.tmp_pytest"; $env:TEMP="$PWD\.tmp_pytest"
python -m pytest advisor\tests -q --basetemp=.tmp_pytest\pytest
```
