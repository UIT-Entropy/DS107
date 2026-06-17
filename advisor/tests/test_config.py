from advisor.config import AdvisorPaths, find_workspace_root, load_config


def test_workspace_root_is_detected_from_module_path():
    root = find_workspace_root()

    assert (root / "advisor").is_dir()
    assert (root / "rice_pest_crawler").is_dir()


def test_path_overrides_resolve_from_workspace_root():
    paths = AdvisorPaths.default().with_overrides(
        chunks_path="rice_pest_crawler/data/rag/all_chunks.jsonl",
        index_path="advisor/data/test_index.jsonl",
    )

    assert paths.chunks_path.is_absolute()
    assert paths.index_path.is_absolute()
    assert paths.chunks_path.name == "all_chunks.jsonl"
    assert paths.index_path.name == "test_index.jsonl"


def test_load_config_accepts_path_overrides():
    config = load_config(index_path="advisor/data/custom.jsonl")

    assert config.paths.index_path.is_absolute()
    assert config.paths.index_path.name == "custom.jsonl"
