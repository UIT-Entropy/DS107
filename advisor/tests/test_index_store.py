from advisor.embedding.index_store import (
    load_index,
    load_index_metadata,
    metadata_path,
    save_index,
)


def test_save_index_writes_rows_and_metadata(tmp_path):
    index_path = tmp_path / "index.jsonl"
    rows = [{"chunk": {"chunk_id": "c1"}, "embedding": [0.1, 0.2]}]
    metadata = {"chunk_count": 1, "embedding_model": "test-model"}

    save_index(index_path, rows, metadata=metadata)

    assert load_index(index_path) == rows
    assert load_index_metadata(index_path) == metadata
    assert metadata_path(index_path).name == "index.jsonl.meta.json"

