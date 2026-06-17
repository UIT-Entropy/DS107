from advisor.config import load_config


def test_api_key_only_comes_from_api_key_module(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key-should-not-be-used")

    config = load_config()

    assert config.api_key != "env-key-should-not-be-used"
