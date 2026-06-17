# DS107

RAG advisor cho sâu hại lúa.

Flow chính:

```text
YOLO class_id -> advisor session -> Gemini RAG answer
```

Path được tự dò từ cấu trúc repo, không cần sửa hard-code path sau khi clone.

## 1. Clone Và Cài Đặt

```powershell
git clone https://github.com/UIT-Entropy/DS107.git
cd DS107
python -m pip install -r advisor\requirements.txt
```

Nếu muốn chạy lại crawler:

```powershell
python -m pip install -r rice_pest_crawler\requirements.txt
```

## 2. Điền Gemini API Key

Chỉ điền key ở đúng file này:

```text
advisor/api_key.py
```

```python
GEMINI_API_KEY = "your_api_key_here"
```

Kiểm tra path, key, data:

```powershell
python advisor\gemini_rag.py doctor
```

## 3. Build Embedding Index

Index không commit lên GitHub. Sau khi pull code mới, build lại:

```powershell
python advisor\gemini_rag.py build-index
python advisor\gemini_rag.py index-info
```

Nguồn chunk mặc định:

```text
rice_pest_crawler\data\rag\all_chunks.jsonl
```

Index sinh ra tại:

```text
advisor\data\gemini_embeddings.jsonl
```

## 4. Tạo Session Từ YOLO

YOLO chỉ cần trả `class_id`.

```powershell
python advisor\gemini_rag.py sessions start ruong-a --class-id brown_plant_hopper
```

Nếu có confidence:

```powershell
python advisor\gemini_rag.py sessions start ruong-a --class-id brown_plant_hopper --confidence 0.91
```

Mapping class nằm ở:

```text
advisor\config.py -> YOLO_CLASS_LABELS
```

## 5. Hỏi Advisor

```powershell
python advisor\gemini_rag.py ask "Tôi nên xử lý thế nào?" --session ruong-a
```

Xem nguồn RAG:

```powershell
python advisor\gemini_rag.py ask "Tôi nên xử lý thế nào?" --session ruong-a --show-sources
```

Checklist ngắn:

```powershell
python advisor\gemini_rag.py ask "Nói ngắn gọn checklist việc cần làm sáng mai ngoài ruộng." --session ruong-a
```

## 6. Quản Lý Session

```powershell
python advisor\gemini_rag.py sessions list
python advisor\gemini_rag.py sessions show ruong-a
python advisor\gemini_rag.py sessions delete ruong-a
python advisor\gemini_rag.py sessions clear
```

## 7. Crawler RAG Data

Crawler tạo dữ liệu nguồn cho advisor:

```powershell
python rice_pest_crawler\scripts\run_discovery.py --all
python rice_pest_crawler\scripts\run_crawl.py --all
python rice_pest_crawler\scripts\run_extract.py --all
python rice_pest_crawler\scripts\build_chunks.py
python rice_pest_crawler\scripts\run_local_context.py
python rice_pest_crawler\scripts\build_all_chunks.py
python rice_pest_crawler\scripts\audit_sources.py
```

## 8. Test

```powershell
python -m pytest advisor\tests
python -m pytest rice_pest_crawler\tests
```
