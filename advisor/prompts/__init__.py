"""Prompt templates and builders."""

__all__ = ["build_user_prompt", "load_system_prompt"]


def __getattr__(name: str):
    if name in __all__:
        from advisor.prompts import prompt_builder

        return getattr(prompt_builder, name)
    raise AttributeError(name)
