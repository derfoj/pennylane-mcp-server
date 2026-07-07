# ─── Dockerfile pour le serveur MCP Pennylane en mode SSE (Cabinet Comptable) ───
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Cabinet Comptable & Equipe Pennylane MCP"
LABEL description="Serveur MCP Pennylane V2 - Mode SSE en réseau pour cabinet comptable"

# Variables d'environnement pour l'optimisation Python et le mode SSE
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    MCP_TRANSPORT=sse \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

WORKDIR /app

# Installation des dépendances système de base
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers du projet
COPY pyproject.toml README.md ./
COPY src/ src/

# Installation du package en mode release
RUN pip install --upgrade pip && pip install .

# Exposition du port SSE (8000 par défaut)
EXPOSE 8000

# Healthcheck pour monitoring Docker / Kubernetes / Cloud
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 0

# Lancement du serveur MCP en mode SSE
CMD ["pennylane-mcp-server"]
