# === Stage 1: Build ===
FROM python:3.10-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# === Stage 2: Runtime ===
FROM python:3.10-slim

# Bezpečnost: ne-root uživatel
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Kopírování nainstalovaných balíčků z build stage
COPY --from=builder /install /usr/local

# Kopírování zdrojového kódu
COPY app/ ./app/

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" || exit 1

# Přepnutí na ne-root uživatele
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
