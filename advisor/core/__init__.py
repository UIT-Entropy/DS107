"""Core orchestration for the advisor."""

__all__ = [
    "AdvisorAnswer",
    "AdvisorSession",
    "IndexBuildReport",
    "RicePestAdvisor",
    "SearchResult",
    "SessionTurn",
]


def __getattr__(name: str):
    if name == "RicePestAdvisor":
        from advisor.core.advisor import RicePestAdvisor

        return RicePestAdvisor
    if name in {"AdvisorAnswer", "IndexBuildReport", "SearchResult"}:
        from advisor.core import models

        return getattr(models, name)
    if name in {"AdvisorSession", "SessionTurn"}:
        from advisor.core import session

        return getattr(session, name)
    raise AttributeError(name)
