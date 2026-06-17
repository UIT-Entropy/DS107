# DS107 RAG Rice Pest Advisor

Flow chính:

```text
YOLO class_id -> tạo session -> hỏi advisor
```

## 1. Cài Đặt

```powershell
cd "C:\Users\nguye\OneDrive\Desktop\DS107_RAG"
python -m pip install -r advisor\requirements.txt
```

## 2. Điền API Key

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

## 3. Build Embedding Index

Nếu chưa có index:

```powershell
python advisor\gemini_rag.py build-index
```

Kiểm tra:

```powershell
python advisor\gemini_rag.py index-info
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

Mapping class id nằm ở:

```text
advisor/config.py -> YOLO_CLASS_LABELS
```

## 5. Hỏi Advisor

```powershell
python advisor\gemini_rag.py ask "Tôi nên xử lý thế nào?" --session ruong-a
```

Checklist ngắn:

```powershell
python advisor\gemini_rag.py ask "Nói ngắn gọn cho tôi checklist việc cần làm sáng mai ngoài ruộng." --session ruong-a
```

Muốn xem nguồn RAG:

```powershell
python advisor\gemini_rag.py ask "Tôi nên xử lý thế nào?" --session ruong-a --show-sources
```

## 6. Quản Lý Session

```powershell
python advisor\gemini_rag.py sessions list
python advisor\gemini_rag.py sessions show ruong-a
python advisor\gemini_rag.py sessions delete ruong-a
python advisor\gemini_rag.py sessions clear
```

## 7. Debug

Xem context được retrieve, chưa gọi Gemini:

```powershell
python advisor\gemini_rag.py retrieve "Cách xử lý rầy nâu?"
```

Chạy test:

```powershell
python -m pytest advisor\tests
```
