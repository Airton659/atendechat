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

###############################################################################
# 2.5. MATAR PORTA 8000 ANTES DE QUALQUER COISA
###############################################################################
echo -e "\n${RED}============================================${NC}"
echo -e "${RED}  MATANDO PORTA 8000 NA VM ANTES DE TUDO  ${NC}"
echo -e "${RED}============================================${NC}"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_SSH bash << ENDKILL
set -e

echo "MASCARANDO serviço..."
echo "$SUDO_PASSWORD" | sudo -S systemctl mask crewai.service 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S systemctl stop crewai.service 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S systemctl kill --signal=SIGKILL crewai.service 2>/dev/null || true
sleep 2

echo "Matando processos por nome..."
echo "$SUDO_PASSWORD" | sudo -S pkill -9 -f "python.*8000" 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S pkill -9 -f "uvicorn" 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S pkill -9 -f "python.*crewai" 2>/dev/null || true
sleep 2

echo "Matando por porta com fuser (10 rounds)..."
for i in {1..10}; do
    echo "$SUDO_PASSWORD" | sudo -S fuser -k -9 8000/tcp 2>/dev/null || true
    sleep 0.5
done

echo "Matando por PID..."
PIDS=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
if [ ! -z "\$PIDS" ]; then
    for pid in \$PIDS; do
        echo "Matando PID \$pid..."
        echo "$SUDO_PASSWORD" | sudo -S kill -9 \$pid 2>/dev/null || true
    done
fi
sleep 3

# VERIFICAÇÃO FINAL - SE NÃO MORREU, ABORTA TUDO
FINAL_CHECK=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
if [ ! -z "\$FINAL_CHECK" ]; then
    echo ""
    echo "❌❌❌ FALHA CRÍTICA: PORTA 8000 NÃO FOI LIBERADA! ❌❌❌"
    echo ""
    echo "Processos que se recusam a morrer:"
    echo "$SUDO_PASSWORD" | sudo -S lsof -i :8000
    echo "$SUDO_PASSWORD" | sudo -S ps aux | grep -E "\$FINAL_CHECK"
    echo ""
    echo "ABORTANDO DEPLOY. Você precisa:"
    echo "1. SSH na VM: ssh $VM_SSH"
    echo "2. Rodar: sudo reboot"
    echo "3. Aguardar 2 minutos e rodar deploy novamente"
    exit 1
fi

echo ""
echo "✅✅✅ PORTA 8000 LIBERADA E CONFIRMADA! ✅✅✅"
echo ""
ENDKILL

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ DEPLOY ABORTADO: Porta 8000 não pôde ser liberada!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Porta 8000 garantidamente livre! Continuando deploy...${NC}"

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

# NÃO apagar venv e __pycache__ (são gerados automaticamente)
git clean -fd -e "codatendechat-main/crewai-service/venv/" -e "**/__pycache__/"

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

# Backend + Frontend rebuild completo (TUDO EM UM BLOCO)
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_SSH bash << 'ENDSSH'
set -e
set -x
cd /home/airton/atendechat/codatendechat-main

echo "===== BACKEND REBUILD ====="
echo "Parando backend..."
docker-compose stop backend

echo "Removendo container e imagem antiga do backend..."
docker-compose rm -f backend
docker rmi -f codatendechat-main-backend 2>/dev/null || true

echo "Rebuiltando backend SEM CACHE..."
docker-compose build --no-cache backend

echo "Subindo backend..."
docker-compose up -d backend

echo "Aguardando backend iniciar (10s)..."
sleep 10

echo "Status do backend:"
docker-compose ps backend
docker-compose logs --tail=20 backend

echo ""
echo "===== FRONTEND REBUILD ====="
echo "Parando frontend..."
docker-compose stop frontend

echo "Removendo container e imagem antiga do frontend..."
docker-compose rm -f frontend
docker rmi -f codatendechat-main-frontend 2>/dev/null || true
docker image prune -f

echo "Rebuiltando frontend com Dockerfile.production..."
docker build --no-cache -f frontend/Dockerfile.production -t codatendechat-main-frontend /home/airton/atendechat/codatendechat-main

echo "Subindo frontend..."
docker-compose up -d frontend

echo ""
echo "✓ Backend e Frontend rebuiltados e rodando!"
echo "Status final dos containers:"
docker-compose ps
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

# Verificar se venv existe e está OK
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo "Criando virtualenv do zero..."
    rm -rf venv
    python3 -m venv venv
    echo "✓ Virtualenv criado!"
    FORCE_INSTALL=true
else
    echo "✓ Virtualenv já existe, será atualizado"
    FORCE_INSTALL=false
fi

# Ativar venv e instalar/atualizar dependências
source venv/bin/activate
pip install --upgrade pip -q

if [ "\$FORCE_INSTALL" = true ]; then
    echo "Instalando todas as dependências..."
    pip install -r requirements.txt
else
    echo "Atualizando apenas dependências modificadas..."
    pip install -r requirements.txt --upgrade
fi

deactivate
echo "✓ Dependências instaladas!"

# MATAR PORTA 8000 NOVAMENTE LOGO ANTES DE SUBIR SERVIÇO
echo ""
echo "============================================"
echo "MATANDO PORTA 8000 NOVAMENTE (pré-start)"
echo "============================================"

# Matar tudo novamente
echo "$SUDO_PASSWORD" | sudo -S pkill -9 -f "python.*8000" 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S pkill -9 -f "uvicorn" 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S pkill -9 -f "python.*crewai" 2>/dev/null || true
sleep 2

# Fuser 5 vezes
for i in 1 2 3 4 5; do
    echo "$SUDO_PASSWORD" | sudo -S fuser -k -9 8000/tcp 2>/dev/null || true
    sleep 0.5
done

# Matar por PID
PIDS_FINAL=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
if [ ! -z "\$PIDS_FINAL" ]; then
    echo "Matando PIDs restantes: \$PIDS_FINAL"
    for pid in \$PIDS_FINAL; do
        echo "$SUDO_PASSWORD" | sudo -S kill -9 \$pid 2>/dev/null || true
    done
fi
sleep 3

# VERIFICAÇÃO OBRIGATÓRIA
CHECK_FINAL=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
if [ ! -z "\$CHECK_FINAL" ]; then
    echo ""
    echo "❌ PORTA 8000 AINDA OCUPADA APÓS SEGUNDA MATANÇA!"
    echo "$SUDO_PASSWORD" | sudo -S lsof -i :8000
    echo "$SUDO_PASSWORD" | sudo -S ps aux | grep -E "\$CHECK_FINAL"
    echo ""
    echo "ABORTANDO DEPLOY!"
    exit 1
fi

echo "✅ Porta 8000 confirmada livre (segunda verificação)"
echo ""

# Copiar arquivo de service atualizado
echo "$SUDO_PASSWORD" | sudo -S cp /home/airton/atendechat/codatendechat-main/crewai-service/crewai-service.service /etc/systemd/system/crewai.service

# DESMASCARAR o serviço (reverter o mask)
echo "DESMASCANDO serviço crewai (permitir rodar novamente)..."
echo "$SUDO_PASSWORD" | sudo -S systemctl unmask crewai.service

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
