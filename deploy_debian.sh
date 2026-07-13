#!/usr/bin/env bash
# ==============================================================================
# Script de déploiement automatisé pour Debian Linux
# Pennylane MCP Server V2 (Mode SSE Réseau)
# ==============================================================================

set -e

# Couleurs pour le terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}     Déploiement de Pennylane MCP Server sur Debian Linux           ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Vérification du répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Variables par défaut
MCP_PORT=${MCP_PORT:-8000}
MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN:-"secret_cabinet_2026"}

echo -e "${YELLOW}Port configuré : ${MCP_PORT}${NC}"
echo -e "${YELLOW}Jeton d'authentification : ${MCP_AUTH_TOKEN}${NC}"
echo ""

# 1. Vérification de Docker
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo -e "${GREEN}✔ Docker et Docker Compose ont été détectés sur ce serveur Debian.${NC}"
    read -p "Souhaitez-vous déployer via Docker (Recommandé) ? [Y/n] : " USE_DOCKER
    USE_DOCKER=${USE_DOCKER:-Y}

    if [[ "$USE_DOCKER" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🚀 Lancement du build et du conteneur Docker...${NC}"
        
        # Création du fichier .env pour Docker Compose si non existant
        cat <<EOF > .env
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=${MCP_PORT}
MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}
EOF

        docker compose up -d --build
        echo ""
        echo -e "${GREEN}✅ Serveur déployé avec succès via Docker !${NC}"
        echo -e "${GREEN}Conteneur en cours d'exécution : pennylane-mcp-server${NC}"
        docker ps | grep pennylane-mcp-server || true
        exit 0
    fi
fi

# 2. Déploiement natif Linux (Systemd Service + Python Virtualenv)
echo -e "${BLUE}📦 Configuration d'un déploiement natif Python + Service Systemd...${NC}"

# Vérification de Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}✘ python3 est requis mais non installé. Installation via apt...${NC}"
    sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip
fi

echo -e "${BLUE}🔧 Création de l'environnement virtuel et installation du package...${NC}"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .

# Récupération de l'utilisateur courant et du chemin absolu
CURRENT_USER=$(whoami)
VENV_PYTHON="${SCRIPT_DIR}/.venv/bin/pennylane-mcp-server"

echo -e "${BLUE}⚙️ Création du service Systemd /etc/systemd/system/pennylane-mcp.service...${NC}"

SERVICE_CONTENT="[Unit]
Description=Pennylane MCP Server (SSE Mode)
After=network.target

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${SCRIPT_DIR}
Environment=\"MCP_TRANSPORT=sse\"
Environment=\"MCP_HOST=0.0.0.0\"
Environment=\"MCP_PORT=${MCP_PORT}\"
Environment=\"MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}\"
ExecStart=${VENV_PYTHON}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target"

echo "$SERVICE_CONTENT" | sudo tee /etc/systemd/system/pennylane-mcp.service > /dev/null

echo -e "${BLUE}🔄 Activation et démarrage du service Systemd...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable --now pennylane-mcp
sudo systemctl restart pennylane-mcp

# Vérification du pare-feu UFW si présent
if command -v ufw >/dev/null 2>&1; then
    echo -e "${BLUE}🛡️ Ouverture du port ${MCP_PORT} dans le pare-feu UFW...${NC}"
    sudo ufw allow "${MCP_PORT}/tcp" || true
fi

echo ""
echo -e "${GREEN}====================================================================${NC}"
echo -e "${GREEN}✅ Le serveur Pennylane MCP est actif sur ce serveur Debian !       ${NC}"
echo -e "${GREEN}====================================================================${NC}"
echo -e "État du service : sudo systemctl status pennylane-mcp"
echo -e "Logs en direct  : sudo journalctl -u pennylane-mcp -f"
echo ""
echo -e "${YELLOW}URL à configurer chez les collaborateurs dans Claude Desktop :${NC}"
echo -e "http://$(hostname -I | awk '{print $1}'):${MCP_PORT}/sse"
echo -e "Header Authorization: Bearer ${MCP_AUTH_TOKEN}"
