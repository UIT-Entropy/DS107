"""Embedding and vector index utilities."""

__all__ = [
    "GeminiEmbedder",
    "format_document_for_embedding",
    "format_query_for_embedding",
    "load_chunks",
    "load_index",
    "save_index",
    "vector_search",
]


def __getattr__(name: str):
    if name == "GeminiEmbedder":
        from advisor.embedding.gemini_embedder import GeminiEmbedder

        return GeminiEmbedder
    if name in {"format_document_for_embedding", "format_query_for_embedding"}:
        from advisor.embedding import formatting

        return getattr(formatting, name)
    if name in {"load_chunks", "load_index", "save_index"}:
        from advisor.embedding import index_store

        return getattr(index_store, name)
    if name == "vector_search":
        from advisor.embedding.vector_search import vector_search

        return vector_search
    raise AttributeError(name)
