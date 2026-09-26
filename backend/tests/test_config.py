from app.core.config import Settings


def test_llm_settings_can_be_overridden_by_environment(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://llm.example:9000")
    monkeypatch.setenv("LLM_MODEL", "model-alias")
    monkeypatch.setenv("LLM_TIMEOUT", "45.5")

    settings = Settings()

    assert settings.llm_base_url == "http://llm.example:9000"
    assert settings.llm_model == "model-alias"
    assert settings.llm_timeout == 45.5