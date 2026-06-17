from advisor.config import MODEL_PROFILES, load_config


def test_free_profile_is_default_and_budget_friendly():
    config = load_config()

    assert config.model_profile == "free"
    assert config.embedding_model == MODEL_PROFILES["free"]["embedding_model"]
    assert config.generation_model == MODEL_PROFILES["free"]["generation_model"]
    assert config.generation_fallback_models
    assert config.top_k <= MODEL_PROFILES["balanced"]["top_k"]
    assert config.candidate_k <= MODEL_PROFILES["balanced"]["candidate_k"]
    assert config.embedding_delay_seconds >= MODEL_PROFILES["balanced"]["embedding_delay_seconds"]
