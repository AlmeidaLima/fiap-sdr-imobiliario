from fastapi import FastAPI

app = FastAPI(
    title="Agente SDR Imobiliário API",
    description="Backend da POC do Agente SDR Imobiliário com IA - Hackathon FIAP",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "agente-sdr-imobiliario-api"
    }