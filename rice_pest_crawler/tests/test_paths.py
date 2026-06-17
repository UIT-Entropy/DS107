from crawler.utils import PROJECT_ROOT, find_project_root, project_path


def test_crawler_root_is_detected_from_module_path():
    root = find_project_root()

    assert root == PROJECT_ROOT
    assert (root / "config" / "crawler.yaml").is_file()
    assert (root / "src" / "crawler").is_dir()


def test_project_path_resolves_from_crawler_root():
    resolved = project_path("data/rag/all_chunks.jsonl")

    assert resolved.is_absolute()
    assert resolved == PROJECT_ROOT / "data" / "rag" / "all_chunks.jsonl"
