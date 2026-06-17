# Rice Pest Crawler

Crawler tạo dữ liệu RAG cho advisor sâu hại lúa.

Crawler chỉ phụ trách thu thập, trích xuất và build chunks. Phần hỏi đáp dùng Gemini nằm ở `advisor`.

## Cài Đặt

Chạy từ repo root:

```powershell
cd DS107
python -m pip install -r rice_pest_crawler\requirements.txt
```

## Chạy Pipeline

```powershell
python rice_pest_crawler\scripts\run_discovery.py --all
python rice_pest_crawler\scripts\run_crawl.py --all
python rice_pest_crawler\scripts\run_extract.py --all
python rice_pest_crawler\scripts\build_chunks.py
python rice_pest_crawler\scripts\run_local_context.py
python rice_pest_crawler\scripts\build_all_chunks.py
python rice_pest_crawler\scripts\audit_sources.py
```

Chạy riêng một class:

```powershell
python rice_pest_crawler\scripts\run_crawl.py --class-id brown_plant_hopper
```

## Output Chính

```text
rice_pest_crawler\data\parsed\documents.jsonl
rice_pest_crawler\data\parsed\pest_profiles.jsonl
rice_pest_crawler\data\rag\chunks.jsonl
rice_pest_crawler\data\rag\local_context_chunks.jsonl
rice_pest_crawler\data\rag\all_chunks.jsonl
rice_pest_crawler\data\logs\source_inventory.md
```

`all_chunks.jsonl` là file advisor dùng để build embedding index.

## Path

Path được tự resolve theo thư mục `rice_pest_crawler`, nên có thể chạy script từ repo root mà không cần `cd` vào crawler.

Config:

```text
rice_pest_crawler\config\crawler.yaml
rice_pest_crawler\config\manual_sources.yaml
rice_pest_crawler\config\local_context_sources.yaml
rice_pest_crawler\config\pest_taxonomy.yaml
```

## Guardrail Dữ Liệu

Chạy audit sau khi crawl:

```powershell
python rice_pest_crawler\scripts\audit_quality.py
python rice_pest_crawler\scripts\audit_sources.py
```

Ý nghĩa grade trong log:

```text
strong / usable   dùng tốt cho RAG
related_usable    nguồn cùng nhóm, cần xác nhận ngoài ruộng
weak              thiếu chi tiết, không nên trả lời quá chắc
taxonomy_only     chỉ đủ nhận diện class, chưa đủ tư vấn xử lý
```

## Test

```powershell
python -m pytest rice_pest_crawler\tests
```
