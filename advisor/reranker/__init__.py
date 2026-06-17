"""Domain-aware reranking for rice pest advice."""

__all__ = ["DomainReranker"]


def __getattr__(name: str):
    if name == "DomainReranker":
        from advisor.reranker.domain_reranker import DomainReranker

        return DomainReranker
    raise AttributeError(name)
