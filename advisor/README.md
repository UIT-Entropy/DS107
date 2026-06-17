# Advisor Module

Module tư vấn RAG cho sâu bệnh lúa.

## Chạy Nhanh

```powershell
cd "C:\Users\nguye\OneDrive\Desktop\DS107_RAG"
python -m pip install -r advisor\requirements.txt
```

Điền key:

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

## YOLO -> Session -> Advisor

```powershell
python advisor\gemini_rag.py sessions start ruong-a --class-id brown_plant_hopper
python advisor\gemini_rag.py ask "Tôi nên xử lý thế nào?" --session ruong-a
```

Nếu YOLO có confidence:

```powershell
python advisor\gemini_rag.py sessions start ruong-a --class-id brown_plant_hopper --confidence 0.91
```

## Lệnh Hay Dùng

```powershell
python advisor\gemini_rag.py build-index
python advisor\gemini_rag.py index-info
python advisor\gemini_rag.py retrieve "Cách xử lý rầy nâu?"
python advisor\gemini_rag.py sessions list
python advisor\gemini_rag.py sessions show ruong-a
```

## Path Chính

```text
advisor/api_key.py       # API key
advisor/config.py        # path/model/class mapping
advisor/data/            # index + sessions sinh ra khi chạy
advisor/prompts/         # prompt
```

## Test

```powershell
python -m pytest advisor\tests
```
