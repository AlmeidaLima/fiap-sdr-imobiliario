from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Agente SDR Imobiliário API"
    app_description: str = (
        "Backend da POC do Agente SDR Imobiliário com IA - Hackathon FIAP"
    )
    app_version: str = "0.1.0"

    database_url: str = (
        "postgresql+psycopg://sdr:sdr@postgres:5432/sdr_imobiliario"
    )

    llm_base_url: str = "http://localhost:8080"
    llm_model: str = "local-model"
    llm_timeout: float = 30.0

    business_timezone: str = "America/Sao_Paulo"


settings = Settings()
