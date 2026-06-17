"""Gemini API integration."""

__all__ = ["GeminiGenerator", "create_client"]


def __getattr__(name: str):
    if name in __all__:
        from advisor.gemini import client

        return getattr(client, name)
    raise AttributeError(name)
