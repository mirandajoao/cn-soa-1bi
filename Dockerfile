# ---------------------------------------------------------------------------
# Pratica 1 - Virtualizacao leve por conteineres (Alpine Linux)
# Imagem final ~60 MB: Alpine + Python + Flask + Gunicorn, sem toolchain de build.
# ---------------------------------------------------------------------------
FROM python:3.11-alpine

# Boas praticas de container Python: sem .pyc e log sem buffer (vai direto pro stdout)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    RAG_ENABLED=false

WORKDIR /app

# Camada de dependencias separada do codigo -> aproveita cache do Docker nos rebuilds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Usuario sem privilegios (principio do menor privilegio)
RUN adduser -D -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Gunicorn: 2 processos worker x 8 threads = ate 16 requisicoes concorrentes por instancia.
# $PORT e injetado pelo PaaS (Render/Railway/Azure) em tempo de execucao.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 8 --worker-class gthread --timeout 60 --access-logfile - app:app"]
