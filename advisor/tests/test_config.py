from advisor.config import AdvisorPaths, load_config


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
