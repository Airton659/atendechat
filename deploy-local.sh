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
LOCAL_CREDENTIALS="/Users/joseairton/Documents/atendechat/atendelimpo/backend/google-credentials.json"
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
# 4. FAZER GIT PULL NA VM
###############################################################################
echo -e "\n${YELLOW}[4/6] Fazendo git pull na VM...${NC}"

ssh $VM_SSH << 'ENDSSH'
cd /home/airton/atendechat
git pull origin main
echo "✓ Git pull concluído!"
ENDSSH

###############################################################################
# 5. BUILD FRONTEND LOCALMENTE E UPLOAD
###############################################################################
echo -e "\n${YELLOW}[5/6] Build frontend localmente e upload...${NC}"

cd codatendechat-main/frontend

echo "Instalando dependências do frontend..."
npm install

echo "Buildando frontend localmente..."
REACT_APP_BACKEND_URL=https://api.atendeaibr.com npm run build

echo "Fazendo upload do build para a VM..."
rsync -avz --delete build/ $VM_SSH:/home/airton/atendechat/codatendechat-main/frontend/build/

cd ../..

###############################################################################
# 6. REBUILD BACKEND E RESTART CONTAINERS
###############################################################################
echo -e "\n${YELLOW}[6/7] Rebuild backend e restart containers...${NC}"

ssh $VM_SSH << 'ENDSSH'
cd /home/airton/atendechat/codatendechat-main

# Rebuild backend TypeScript
echo "Rebuilding backend TypeScript..."
docker-compose exec -T backend npm run build

# Parar frontend e rebuildar imagem Docker sem cache
echo "Parando frontend..."
docker-compose stop frontend

echo "Rebuildando imagem Docker do frontend (sem cache)..."
docker build --no-cache -f frontend/Dockerfile.production -t codatendechat-main-frontend:latest .

# Restart containers
echo "Reiniciando containers..."
docker-compose up -d frontend backend

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

# Matar qualquer processo Python antigo na porta 8000
echo "Limpando processos antigos na porta 8000..."
OLD_PIDS=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
if [ ! -z "\$OLD_PIDS" ]; then
    echo "Matando processos: \$OLD_PIDS"
    echo "$SUDO_PASSWORD" | sudo -S kill -9 \$OLD_PIDS 2>/dev/null || true
    sleep 2
    echo "✓ Processos antigos finalizados!"
else
    echo "✓ Nenhum processo antigo encontrado!"
fi

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
