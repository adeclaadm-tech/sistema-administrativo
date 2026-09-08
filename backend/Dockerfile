# Imagen del backend. Sirve igual en Railway, en un droplet con docker compose
# o en local: lo único que cambia son las variables de entorno.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# libpq y build-essential los necesita psycopg; se instalan antes que el código
# para que la capa quede cacheada entre deploys.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuario sin privilegios: el contenedor no necesita root para servir HTTP.
RUN useradd --create-home --shell /bin/bash adecla && chown -R adecla:adecla /app
USER adecla

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/health || exit 1

# Railway inyecta $PORT; en local vale el 8000 del ENV.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
