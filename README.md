# DS107 RAG Rice Pest Advisor

## 1. Cài Đặt

Từ thư mục project:

```powershell
cd "C:\Users\nguye\OneDrive\Desktop\DS107_RAG"
python -m pip install -r advisor\requirements.txt
```

Nếu chạy trên Linux/Vast:

```bash
cd /path/to/DS107_RAG
python -m pip install -r advisor/requirements.txt
```

## 2. Điền Gemini API Key

Chỉ điền API key ở đúng một file:

```text
advisor/api_key.py
```

Mở file đó và sửa:

```python
GEMINI_API_KEY = "your_gemini_api_key_here"
```

Kiểm tra project đã nhận key và đúng path chưa:

```powershell
python advisor\gemini_rag.py doctor
```

Kỳ vọng thấy:

```text
API key loaded: yes
Chunks exists: yes
Prompt exists: yes
Model profile: free
```

## 3. Build Embedding Index

Index là phần nhúng sẵn toàn bộ chunks. Nếu mới pull code về thì cần build một lần.

Test nhanh 10 chunks trước:

```powershell
python advisor\gemini_rag.py build-index --limit 10
```

Build toàn bộ:

```powershell
python advisor\gemini_rag.py build-index
```

Free tier có thể bị rate limit, tăng delay nếu cần:

```powershell
python advisor\gemini_rag.py build-index --delay 2
```

Kiểm tra đã đủ chưa:

```powershell
python advisor\gemini_rag.py index-info
```

## 4. Nhận Kết Quả YOLO Và Mở Session

YOLO chạy ở bước trước, output tối thiểu cần có:

- tên bệnh/sâu hoặc class id
- confidence nếu có
- đường dẫn ảnh nếu có

Ví dụ YOLO phát hiện đạo ôn lá:

```powershell
python advisor\gemini_rag.py sessions start ruong-a ^
  --disease "đạo ôn lá" ^
  --class-id "rice_blast" ^
  --confidence 0.91 ^
  --image "runs/detect/predict/field_001.jpg" ^
  --crop-stage "làm đòng" ^
  --location "An Giang" ^
  --notes "Trời âm u, ruộng bón đạm hơi nhiều"
```

Trên Linux/Vast dùng dấu `\`:

```bash
python advisor/gemini_rag.py sessions start ruong-a \
  --disease "đạo ôn lá" \
  --class-id "rice_blast" \
  --confidence 0.91 \
  --image "runs/detect/predict/field_001.jpg" \
  --crop-stage "làm đòng" \
  --location "An Giang" \
  --notes "Trời âm u, ruộng bón đạm hơi nhiều"
```

## 5. Hỏi Tư Vấn Theo Session

Dùng cùng `--session` để advisor nhớ bệnh YOLO phát hiện và lịch sử hội thoại:

```powershell
python advisor\gemini_rag.py ask "Hôm nay tôi nên ưu tiên xử lý gì?" --session ruong-a --show-sources
```

Hỏi tiếp:

```powershell
python advisor\gemini_rag.py ask "Nếu bệnh mới khoảng 5% lá thì có nên phun chưa?" --session ruong-a --show-sources
```

## 6. Các Chế Độ CLI

Kiểm tra cấu hình:

```powershell
python advisor\gemini_rag.py doctor
```

Build embedding index:

```powershell
python advisor\gemini_rag.py build-index
```

Retrieve/rerank context mà chưa gọi Gemini:

```powershell
python advisor\gemini_rag.py retrieve "Cách xử lý đạo ôn lá?"
```

Hỏi advisor:

```powershell
python advisor\gemini_rag.py ask "Cách xử lý đạo ôn lá?" --show-sources
```

Xem index:

```powershell
python advisor\gemini_rag.py index-info
```

Quản lý session:

```powershell
python advisor\gemini_rag.py sessions list
python advisor\gemini_rag.py sessions show ruong-a
python advisor\gemini_rag.py sessions delete ruong-a
python advisor\gemini_rag.py sessions clear
```

## 7. Model Profile

Mặc định dùng profile tiết kiệm cho free tier trong `advisor/config.py`:

```python
MODEL_PROFILE = "free"
```

Các profile:

```text
free     -> gemini-embedding-001 + gemini-2.5-flash-lite
balanced -> gemini-embedding-2   + gemini-2.5-flash
quality  -> gemini-embedding-2   + gemini-3.5-flash
```

Nếu xài hàng free thì giữ `free`.

## 8. Quy Ước Path Và Module

Path/config tập trung ở:

```text
advisor/config.py
```

API key chỉ ở:

```text
advisor/api_key.py
```

Cấu trúc module:

```text
advisor/
  api_key.py      # nơi duy nhất chứa Gemini API key
  config.py       # root/path/model/profile
  cli.py          # CLI commands
  gemini_rag.py   # entrypoint
  core/           # orchestration, session
  embedding/      # embedding, vector index
  reranker/       # rerank theo domain nông nghiệp
  prompts/        # prompt chuyên gia
  gemini/         # Gemini client
  data/           # index/session sinh ra khi chạy
```

Không tự hardcode path trong module nghiệp vụ. Nếu cần đổi path, đổi qua `AdvisorConfig` hoặc CLI args. 

## 9. Test

Test offline không gọi Gemini:

```powershell
python -m pytest advisor\tests
```

