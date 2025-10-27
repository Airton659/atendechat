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
# 2. PEDIR SENHAS UMA VEZ SÓ
###############################################################################
echo -e "\n${YELLOW}[2/6] Digite a senha SSH da VM (airton@46.62.147.212):${NC}"
read -s SSH_PASSWORD
echo ""

echo -e "\n${YELLOW}Digite a senha do SUDO da VM (pode ser a mesma):${NC}"
read -s SUDO_PASSWORD
echo ""

# Verificar se sshpass está instalado
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}ERRO: sshpass não está instalado!${NC}"
    echo "Instalando sshpass..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install hudochenkov/sshpass/sshpass
    else
        sudo apt-get install -y sshpass
    fi
fi

###############################################################################
# 3. COPIAR CREDENCIAIS PARA A VM
###############################################################################
echo -e "\n${YELLOW}[3/6] Copiando credenciais para a VM...${NC}"

# Copiar arquivo para home do usuário primeiro (não precisa sudo)
sshpass -p "$SSH_PASSWORD" scp -o StrictHostKeyChecking=no "$LOCAL_CREDENTIALS" $VM_SSH:~/google-credentials.json

echo -e "${GREEN}✓ Credenciais copiadas com sucesso!${NC}"

###############################################################################
# 4. FAZER GIT PULL NA VM (com stash de alterações locais)
###############################################################################
echo -e "\n${YELLOW}[4/6] Fazendo git pull na VM...${NC}"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_SSH << 'ENDSSH'
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
sshpass -p "$SSH_PASSWORD" rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" build/ $VM_SSH:/home/airton/atendechat/codatendechat-main/frontend/build/

cd ../..

###############################################################################
# 6. REBUILD BACKEND E RESTART CONTAINERS
###############################################################################
echo -e "\n${YELLOW}[6/7] Rebuild backend e restart containers...${NC}"

# Backend rebuild completo
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_SSH "cd /home/airton/atendechat/codatendechat-main && docker-compose build --no-cache backend && docker-compose up -d --force-recreate backend"

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

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_SSH bash << ENDSSH
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

# MATANÇA TOTAL DE PROCESSOS NA PORTA 8000 - USANDO SCRIPT DEDICADO
echo "============================================"
echo "INICIANDO LIMPEZA BRUTAL DA PORTA 8000..."
echo "============================================"

# Executar script de limpeza como root
echo "$SUDO_PASSWORD" | sudo -S bash /home/airton/atendechat/codatendechat-main/crewai-service/kill-port-8000.sh

# Verificar se realmente liberou
REMAINING=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
if [ ! -z "\$REMAINING" ]; then
    echo ""
    echo "❌ FALHA CRÍTICA: Script não conseguiu liberar porta 8000!"
    echo "Processos restantes:"
    echo "$SUDO_PASSWORD" | sudo -S lsof -i :8000
    echo "$SUDO_PASSWORD" | sudo -S ps aux | grep -E "\$REMAINING"
    echo ""
    echo "Abortando deploy. Sugestão: reinicie a VM manualmente."
    exit 1
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

# Aguardar o service iniciar (com múltiplas tentativas)
echo "Aguardando CrewAI service iniciar..."
MAX_ATTEMPTS=12  # 12 tentativas x 5 segundos = 60 segundos
ATTEMPT=0
SERVICE_RUNNING=false

while [ \$ATTEMPT -lt \$MAX_ATTEMPTS ]; do
    ATTEMPT=\$((ATTEMPT + 1))
    echo "Tentativa \$ATTEMPT/\$MAX_ATTEMPTS..."

    # Verificar se porta 8000 está aberta
    if echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 > /dev/null 2>&1; then
        echo "✅ Porta 8000 aberta!"

        # Verificar se o log tem "Uvicorn running"
        if echo "$SUDO_PASSWORD" | sudo -S journalctl -u crewai.service -n 20 --no-pager | grep -q "Uvicorn running"; then
            echo "✅ CrewAI service RODANDO e pronto!"
            SERVICE_RUNNING=true
            break
        else
            echo "⏳ Porta aberta, mas ainda inicializando..."
        fi
    else
        echo "⏳ Aguardando porta 8000 abrir..."
    fi

    sleep 5
done

# Verificar resultado final
echo ""
echo "Status do CrewAI service:"
echo "$SUDO_PASSWORD" | sudo -S systemctl status crewai.service --no-pager | head -20

if [ "\$SERVICE_RUNNING" = true ]; then
    echo ""
    echo "✅ CrewAI service RODANDO na porta 8000!"
    echo "Processo:"
    echo "$SUDO_PASSWORD" | sudo -S lsof -i :8000
else
    echo ""
    echo "❌ ERRO: CrewAI service NÃO iniciou corretamente após 60 segundos!"
    echo ""
    echo "Últimos 100 logs do serviço:"
    echo "$SUDO_PASSWORD" | sudo -S journalctl -u crewai.service -n 100 --no-pager
    exit 1
fi

# Verificar se o código foi atualizado (check na data de modificação do arquivo)
echo ""
echo "Verificando versão do código Python..."
MOD_TIME=\$(stat -c %Y /home/airton/atendechat/codatendechat-main/crewai-service/api/src/atendimento_crewai/training_service.py 2>/dev/null || stat -f %m /home/airton/atendechat/codatendechat-main/crewai-service/api/src/atendimento_crewai/training_service.py)
echo "Última modificação do training_service.py: \$(date -d @\$MOD_TIME 2>/dev/null || date -r \$MOD_TIME)"

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
