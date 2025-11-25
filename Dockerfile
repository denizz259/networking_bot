FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# requirements находятся в src/
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# исходники приложения
COPY src/ ./src/

# health-endpoint работает на 8000, проверяем его
HEALTHCHECK --interval=30s --timeout=3s --retries=5 CMD \
  python -c "import urllib.request,sys; u=urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=2); sys.exit(0 if u.status==200 else 1)" || exit 1


CMD ["python", "-m", "bot.main"]
