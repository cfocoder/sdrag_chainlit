FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copiar solo pyproject.toml para instalar dependencias
COPY pyproject.toml .

# Instalar dependencias directamente (sin modo editable)
RUN uv pip install --system chainlit httpx pandas plotly python-dotenv

# Copiar toda la aplicación
COPY app.py .
COPY .chainlit/ .chainlit/

# Exponer puerto 8001 (8000 ya ocupado en cfocoder3)
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Ejecutar Chainlit en puerto 8001
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8001", "--headless"]
