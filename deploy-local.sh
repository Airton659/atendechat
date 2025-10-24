#!/bin/bash

###############################################################################
# SCRIPT DE DEPLOY LOCAL - Roda na sua máquina e faz tudo na VM
# Executa: bash deploy-local.sh
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  DEPLOY ATENDECHAT - DA MÁQUINA LOCAL${NC}"
echo -e "${GREEN}========================================${NC}"

# Configurações
VM_USER="airton"
VM_HOST="46.62.147.212"
VM_SSH="$VM_USER@$VM_HOST"
LOCAL_CREDENTIALS="/Users/joseairton/Documents/atendechat/google-credentials.json"
PROJECT_DIR="/home/airton/atendechat/codatendechat-main"

###############################################################################
# 1. VERIFICAR CREDENCIAIS LOCAIS
###############################################################################
echo -e "\n${YELLOW}[1/6] Verificando credenciais do Google Cloud...${NC}"

if [ ! -f "$LOCAL_CREDENTIALS" ]; then
    echo -e "${RED}ERRO: google-credentials.json não encontrado em:${NC}"
    echo "$LOCAL_CREDENTIALS"
    exit 1
fi

echo -e "${GREEN}✓ Credenciais encontradas!${NC}"

###############################################################################
# 2. PEDIR SENHA SUDO UMA VEZ
###############################################################################
echo -e "\n${YELLOW}[2/6] Digite a senha do sudo da VM:${NC}"
read -s SUDO_PASSWORD
echo ""

###############################################################################
# 3. COPIAR CREDENCIAIS PARA A VM
###############################################################################
echo -e "\n${YELLOW}[3/6] Copiando credenciais para a VM...${NC}"

# Copiar arquivo para home do usuário primeiro (não precisa sudo)
scp "$LOCAL_CREDENTIALS" $VM_SSH:~/google-credentials.json

echo -e "${GREEN}✓ Credenciais copiadas com sucesso!${NC}"

###############################################################################
# 4. FAZER GIT PULL NA VM (com stash de alterações locais)
###############################################################################
echo -e "\n${YELLOW}[4/6] Fazendo git pull na VM...${NC}"

ssh $VM_SSH << 'ENDSSH'
cd /home/airton/atendechat
echo "Salvando alterações locais (stash)..."
git stash
echo "Fazendo git pull..."
git pull origin main
echo "✓ Git pull concluído!"
ENDSSH

###############################################################################
# 5. BUILD FRONTEND LOCALMENTE E UPLOAD
###############################################################################
echo -e "\n${YELLOW}[5/6] Build frontend localmente e upload...${NC}"

cd codatendechat-main/frontend

echo "LIMPANDO ABSOLUTAMENTE TUDO (build, node_modules, caches, lock)..."
rm -rf build node_modules node_modules/.cache .cache package-lock.json
npm cache clean --force

echo "Instalando dependências do ZERO (fresh install)..."
npm install --force --no-cache

echo "Buildando frontend LIMPO (sem nenhum cache)..."
rm -rf build
REACT_APP_BACKEND_URL=https://api.atendeaibr.com npm run build

echo "Fazendo upload do build para a VM..."
rsync -avz --delete build/ $VM_SSH:/home/airton/atendechat/codatendechat-main/frontend/build/

cd ../..

###############################################################################
# 6. REBUILD BACKEND E RESTART CONTAINERS
###############################################################################
echo -e "\n${YELLOW}[6/7] Rebuild backend e restart containers...${NC}"

# Backend rebuild completo - LIMPAR TUDO ANTES
ssh $VM_SSH bash << 'ENDSSH'
cd /home/airton/atendechat/codatendechat-main
echo "Parando backend..."
docker-compose stop backend
echo "Removendo container e imagem antiga..."
docker-compose rm -f backend
docker rmi -f codatendechat-main-backend 2>/dev/null || true
echo "Limpando cache do Docker..."
docker builder prune -f
echo "Rebuild backend SEM CACHE..."
docker-compose build --no-cache --pull backend
echo "Subindo backend..."
docker-compose up -d backend
echo "✓ Backend reconstruído do zero!"
ENDSSH

# Frontend rebuild completo
ssh $VM_SSH bash << 'ENDSSH'
set -e
set -x
cd /home/airton/atendechat/codatendechat-main

echo "Parando e removendo container frontend..."
docker-compose stop frontend
docker-compose rm -f frontend

echo "Removendo imagem antiga do frontend..."
docker rmi -f codatendechat-main-frontend 2>/dev/null || true
docker image prune -f

echo "Rebuildando frontend com Dockerfile.production..."
docker build --no-cache -f frontend/Dockerfile.production -t codatendechat-main-frontend /home/airton/atendechat/codatendechat-main

echo "Subindo containers..."
docker-compose up -d --force-recreate frontend
docker-compose up -d backend

echo "✓ Frontend e Backend atualizados!"
ENDSSH

###############################################################################
# 7. ATUALIZAR E RESTART CREWAI SERVICE
###############################################################################
echo -e "\n${YELLOW}[7/7] Atualizando e reiniciando CrewAI service...${NC}"

ssh $VM_SSH bash << ENDSSH
# Copiar credenciais para /opt/crewai
echo "$SUDO_PASSWORD" | sudo -S cp ~/google-credentials.json /opt/crewai/
echo "$SUDO_PASSWORD" | sudo -S chown airton:airton /opt/crewai/google-credentials.json
echo "$SUDO_PASSWORD" | sudo -S chmod 600 /opt/crewai/google-credentials.json
rm -f ~/google-credentials.json

# Criar/Atualizar virtualenv do CrewAI
cd /home/airton/atendechat/codatendechat-main/crewai-service
echo "Criando/atualizando virtualenv..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtualenv criado!"
else
    echo "✓ Virtualenv já existe!"
fi

# Ativar venv e instalar/atualizar dependências
echo "Instalando dependências..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
echo "✓ Dependências instaladas!"

# Parar o service e matar processos antigos na porta 8000
echo "Parando CrewAI service..."
echo "$SUDO_PASSWORD" | sudo -S systemctl stop crewai.service

# Aguardar um pouco para o systemd parar
sleep 2

# Matar qualquer processo Python antigo na porta 8000 (múltiplas tentativas)
echo "Limpando processos antigos na porta 8000..."
for i in {1..3}; do
    OLD_PIDS=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
    if [ ! -z "\$OLD_PIDS" ]; then
        echo "Tentativa \$i: Matando processos: \$OLD_PIDS"
        echo "$SUDO_PASSWORD" | sudo -S kill -9 \$OLD_PIDS 2>/dev/null || true
        sleep 1
    else
        echo "✓ Nenhum processo na porta 8000!"
        break
    fi
done

# Verificação final
REMAINING_PIDS=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
if [ ! -z "\$REMAINING_PIDS" ]; then
    echo "⚠️ AVISO: Ainda existem processos na porta 8000: \$REMAINING_PIDS"
    echo "Tentando matar com SIGKILL forcado..."
    echo "$SUDO_PASSWORD" | sudo -S kill -9 \$REMAINING_PIDS 2>/dev/null || true
    sleep 2
fi

echo "✓ Porta 8000 liberada!"

# Copiar arquivo de service atualizado
echo "$SUDO_PASSWORD" | sudo -S cp /home/airton/atendechat/codatendechat-main/crewai-service/crewai-service.service /etc/systemd/system/crewai.service

# Reload systemd daemon
echo "$SUDO_PASSWORD" | sudo -S systemctl daemon-reload

# Restart CrewAI service
echo "Iniciando CrewAI service..."
echo "$SUDO_PASSWORD" | sudo -S systemctl start crewai.service

# Aguardar 3 segundos para o service iniciar
sleep 3

# Verificar status
echo ""
echo "Status do CrewAI service:"
echo "$SUDO_PASSWORD" | sudo -S systemctl status crewai.service --no-pager | head -20

echo "✓ CrewAI service atualizado e reiniciado!"
ENDSSH

###############################################################################
# FINALIZADO
###############################################################################
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  DEPLOY CONCLUÍDO COM SUCESSO!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Sistema disponível em:"
echo "  Frontend: https://www.atendeaibr.com"
echo "  Backend:  https://api.atendeaibr.com"
echo ""
echo "Para verificar logs:"
echo "  ssh $VM_SSH"
echo "  sudo journalctl -u crewai.service -f"
echo ""
