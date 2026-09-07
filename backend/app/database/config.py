import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://sdr:sdr@postgres:5432/sdr_imobiliario",
)