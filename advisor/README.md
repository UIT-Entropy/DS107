# Advisor

Module RAG tư vấn sâu hại lúa bằng Gemini.

Chạy từ repo root sau khi clone:

```powershell
cd DS107
python -m pip install -r advisor\requirements.txt
```

## API Key

Chỉ điền Gemini API key ở:

```text
advisor/api_key.py
```

```python
GEMINI_API_KEY = "your_api_key_here"
```

Kiểm tra:

```powershell
python advisor\gemini_rag.py doctor
```

## Build Index

```powershell
python advisor\gemini_rag.py build-index
python advisor\gemini_rag.py index-info
```

Mặc định advisor tự lấy chunks từ:

```text
rice_pest_crawler\data\rag\all_chunks.jsonl
```

Và ghi index vào:

```text
advisor\data\gemini_embeddings.jsonl
```

## YOLO -> Session -> Ask

```powershell
python advisor\gemini_rag.py sessions start ruong-a --class-id brown_plant_hopper
python advisor\gemini_rag.py ask "Tôi nên xử lý thế nào?" --session ruong-a
```

Có confidence:

```powershell
python advisor\gemini_rag.py sessions start ruong-a --class-id brown_plant_hopper --confidence 0.91
```

## Lệnh Hay Dùng

```powershell
python advisor\gemini_rag.py retrieve "Cách xử lý rầy nâu?"
python advisor\gemini_rag.py sessions list
python advisor\gemini_rag.py sessions show ruong-a
python advisor\gemini_rag.py sessions delete ruong-a
python advisor\gemini_rag.py sessions clear
```

## Path Chính

```text
advisor\api_key.py       # API key local, không commit key thật
advisor\config.py        # model, path, YOLO class mapping
advisor\data\            # index + sessions sinh ra khi chạy
advisor\prompts\         # system prompt + prompt builder
rice_pest_crawler\data\rag\all_chunks.jsonl  # chunks đầu vào
```

## Test

```powershell
python -m pytest advisor\tests
```
