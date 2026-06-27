# Advisory Benchmark

`Benchmark/` contains the retrieval and generation evaluation artifacts for the DS107 RAG advisor.

## Files

```text
benchmark_questions.csv    40 in-scope benchmark questions
reference_answer.csv       reference answers for generation metrics
retrieval_results.csv      saved top-5 retrieval outputs
retrieval_metrics.csv      Class Hit@5, Section Hit@5, MRR@5
answer_rag_results.csv     RAG generated answers
no_rag_answers.csv         No-RAG baseline answers
generation_metrics.csv     ROUGE-L, BERTScore, semantic similarity
oos_questions.csv          out-of-scope/ambiguous probe questions
```

Scripts:

```text
retrieval_eval.py          rerun retrieval and write retrieval_results.csv
metrics_eval.py            compute retrieval_metrics.csv from retrieval_results.csv
benchmark_answer_rag.py    regenerate RAG answers with Gemini
benchmark_no_rag.py        regenerate No-RAG answers with Gemini
evaluate_generation.py     compute generation metrics
advisor_no_rag.py          No-RAG baseline helper
```

## Setup

From the repository root:

```powershell
python -m pip install -r advisor\requirements.txt
python -m pip install -r Benchmark\requirements.txt
```

Generation and retrieval reruns need:

```text
advisor/api_key.py                         real Gemini API key
advisor/data/gemini_embeddings.jsonl       advisor embedding index
rice_pest_crawler/data/rag/all_chunks.jsonl
```

Build the advisor index from the repository root if it is missing:

```powershell
python advisor\gemini_rag.py build-index
```

## Reproduce Retrieval Metrics

```powershell
cd Benchmark
python retrieval_eval.py
python metrics_eval.py
```

`metrics_eval.py` can be rerun using the saved `retrieval_results.csv` without calling Gemini.

## Reproduce Generation Metrics

Use the saved answer CSV files:

```powershell
cd Benchmark
python evaluate_generation.py
```

Regenerate answers before evaluating:

```powershell
cd Benchmark
python benchmark_answer_rag.py
python benchmark_no_rag.py
python evaluate_generation.py
```

Regenerating answers calls Gemini, so results may vary slightly across model versions and API settings.
