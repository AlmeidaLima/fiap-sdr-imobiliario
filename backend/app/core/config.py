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


settings = Settings()