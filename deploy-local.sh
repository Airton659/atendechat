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
echo "Descartando alterações locais e pegando código mais recente..."
git fetch origin main
git reset --hard origin/main
git clean -fd
echo "✓ Código atualizado com sucesso!"
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

# Backend rebuild completo
ssh $VM_SSH "cd /home/airton/atendechat/codatendechat-main && docker-compose build --no-cache backend && docker-compose up -d --force-recreate backend"

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
echo "Recriando virtualenv do zero..."
rm -rf venv
python3 -m venv venv
echo "✓ Virtualenv criado!"

# Ativar venv e instalar/atualizar dependências
echo "Instalando dependências..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
echo "✓ Dependências instaladas!"

# MATANÇA TOTAL DE PROCESSOS NA PORTA 8000 - SEM PIEDADE
echo "============================================"
echo "INICIANDO LIMPEZA BRUTAL DA PORTA 8000..."
echo "============================================"

# RODADA 1: Para o serviço e mata processos
echo "Rodada 1: Parando serviço e matando processos..."
echo "$SUDO_PASSWORD" | sudo -S bash -c '
    systemctl stop crewai.service 2>/dev/null || true
    systemctl disable crewai.service 2>/dev/null || true
    systemctl reset-failed crewai.service 2>/dev/null || true
    sleep 2
    fuser -k -9 8000/tcp 2>/dev/null || true
    pkill -9 uvicorn 2>/dev/null || true
    pkill -9 -f "python.*crewai" 2>/dev/null || true
    pkill -9 -f "main:app" 2>/dev/null || true
    lsof -ti :8000 | xargs -r kill -9 2>/dev/null || true
    sleep 3
' || true

# RODADA 2: Verificação e limpeza adicional
echo "Rodada 2: Verificação e limpeza adicional..."
REMAINING=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
if [ ! -z "\$REMAINING" ]; then
    echo "⚠️  Ainda há processos na porta 8000: \$REMAINING"
    echo "Matando com força total..."
    echo "$SUDO_PASSWORD" | sudo -S bash -c '
        kill -9 '\$REMAINING' 2>/dev/null || true
        fuser -k -9 8000/tcp 2>/dev/null || true
        sleep 2
    ' || true
fi

# RODADA 3: Verificação final e mata qualquer coisa restante
echo "Rodada 3: Verificação final..."
sleep 2
FINAL_CHECK=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
if [ ! -z "\$FINAL_CHECK" ]; then
    echo "⚠️  PROCESSOS TEIMOSOS DETECTADOS: \$FINAL_CHECK"
    echo "Aplicando força nuclear..."
    echo "$SUDO_PASSWORD" | sudo -S bash -c '
        kill -9 '\$FINAL_CHECK' 2>/dev/null || true
        fuser -k -9 8000/tcp 2>/dev/null || true
        pkill -9 -f ":8000" 2>/dev/null || true
        sleep 3
        fuser -k -9 8000/tcp 2>/dev/null || true
    ' || true

    # Verificação DEFINITIVA
    sleep 2
    ULTRA_FINAL=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
    if [ ! -z "\$ULTRA_FINAL" ]; then
        echo ""
        echo "❌❌❌ FALHA CRÍTICA ❌❌❌"
        echo "Processos ainda ativos na porta 8000: \$ULTRA_FINAL"
        echo "Abortando deploy."
        echo ""
        echo "Execute manualmente na VM:"
        echo "  sudo systemctl stop crewai.service"
        echo "  sudo fuser -k -9 8000/tcp"
        echo "  sudo kill -9 \$ULTRA_FINAL"
        exit 1
    fi
fi

echo "============================================"
echo "✓ PORTA 8000 GARANTIDAMENTE LIBERADA!"
echo "============================================"

# Copiar arquivo de service atualizado
echo "$SUDO_PASSWORD" | sudo -S cp /home/airton/atendechat/codatendechat-main/crewai-service/crewai-service.service /etc/systemd/system/crewai.service

# Reload systemd daemon
echo "$SUDO_PASSWORD" | sudo -S systemctl daemon-reload

# REABILITAR e iniciar o serviço
echo "Habilitando e iniciando CrewAI service..."
echo "$SUDO_PASSWORD" | sudo -S systemctl enable crewai.service
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
