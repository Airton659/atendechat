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

# MATANÇA TOTAL DE PROCESSOS NA PORTA 8000
echo "============================================"
echo "INICIANDO LIMPEZA BRUTAL DA PORTA 8000..."
echo "============================================"

# PASSO 0: MASCARAR o serviço para IMPEDIR auto-restart
echo "0. MASCARANDO serviço crewai (IMPEDE auto-restart do systemd)..."
echo "$SUDO_PASSWORD" | sudo -S systemctl mask crewai.service 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S systemctl stop crewai.service 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S systemctl kill --signal=SIGKILL crewai.service 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S systemctl disable crewai.service 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S systemctl reset-failed crewai.service 2>/dev/null || true
sleep 5

# PASSO 1: Matar processos por nome
echo "1. Matando processos por nome..."
echo "$SUDO_PASSWORD" | sudo -S pkill -9 -f "python.*8000" 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S pkill -9 uvicorn 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S pkill -9 -f "python.*crewai" 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S pkill -9 -f "main:app" 2>/dev/null || true
echo "$SUDO_PASSWORD" | sudo -S pkill -9 -f "python.*main.py" 2>/dev/null || true
sleep 3

# PASSO 2: Matar por porta (força total)
echo "2. Matando por porta (3 rounds com fuser)..."
for i in 1 2 3; do
    echo "   Round \$i de fuser..."
    echo "$SUDO_PASSWORD" | sudo -S fuser -k -9 8000/tcp 2>/dev/null || true
    sleep 1
done
sleep 3

# PASSO 3: Matar por PID direto
echo "3. Matando processos por PID..."
PIDS=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
if [ ! -z "\$PIDS" ]; then
    echo "   PIDs encontrados: \$PIDS"
    for pid in \$PIDS; do
        echo "   Matando PID \$pid..."
        echo "$SUDO_PASSWORD" | sudo -S kill -9 \$pid 2>/dev/null || true
    done
    sleep 3
fi

# PASSO 4: Aguardar kernel liberar
echo "4. Aguardando 5s para kernel liberar porta..."
sleep 5

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

# AGUARDAR 15 SEGUNDOS MONITORANDO SE ALGO VOLTA
echo ""
echo "Aguardando 15 segundos e MONITORANDO se algo tenta ocupar a porta..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    sleep 1
    CHECK=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
    if [ ! -z "\$CHECK" ]; then
        echo ""
        echo "❌ ALERTA: Processo apareceu novamente no segundo \$i!"
        echo "$SUDO_PASSWORD" | sudo -S lsof -i :8000
        echo ""
        echo "Matando novamente..."
        echo "$SUDO_PASSWORD" | sudo -S kill -9 \$CHECK 2>/dev/null || true
        echo "$SUDO_PASSWORD" | sudo -S fuser -k -9 8000/tcp 2>/dev/null || true
        sleep 2
    fi
done

# Verificação extra antes de subir serviço
DOUBLE_CHECK=\$(echo "$SUDO_PASSWORD" | sudo -S lsof -ti :8000 2>/dev/null || true)
if [ ! -z "\$DOUBLE_CHECK" ]; then
    echo ""
    echo "❌ PORTA 8000 CONTINUA SENDO REOCUPADA!"
    echo "$SUDO_PASSWORD" | sudo -S lsof -i :8000
    echo ""
    echo "Verificando quem está iniciando o processo:"
    echo "$SUDO_PASSWORD" | sudo -S ps aux | grep -E "(\$DOUBLE_CHECK|python|uvicorn)" | grep -v grep
    echo ""
    echo "Verificando serviços do systemd:"
    echo "$SUDO_PASSWORD" | sudo -S systemctl list-units --state=running | grep -i crew
    echo ""
    echo "ABORTANDO. Algo está respawnando o processo!"
    exit 1
fi

echo ""
echo "✓ Porta 8000 confirmada livre (monitorada por 15s sem reocupação)!"
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
