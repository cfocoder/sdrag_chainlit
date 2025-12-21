FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copiar archivos de proyecto
COPY pyproject.toml .
COPY .python-version .

# Instalar dependencias con uv (mucho más rápido que pip)
RUN uv pip install --system -e .

# Copiar aplicación
COPY app.py .
COPY .chainlit/ .chainlit/

# Exponer puerto
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Ejecutar Chainlit
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000", "--headless"]
