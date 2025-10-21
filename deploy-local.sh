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
echo -e "\n${YELLOW}[1/5] Verificando credenciais do Google Cloud...${NC}"

if [ ! -f "$LOCAL_CREDENTIALS" ]; then
    echo -e "${RED}ERRO: google-credentials.json não encontrado em:${NC}"
    echo "$LOCAL_CREDENTIALS"
    exit 1
fi

echo -e "${GREEN}✓ Credenciais encontradas!${NC}"

###############################################################################
# 2. COPIAR CREDENCIAIS PARA A VM
###############################################################################
echo -e "\n${YELLOW}[2/5] Copiando credenciais para a VM...${NC}"

# Copiar arquivo para home do usuário primeiro (não precisa sudo)
scp "$LOCAL_CREDENTIALS" $VM_SSH:~/google-credentials.json

echo -e "${GREEN}✓ Credenciais copiadas com sucesso!${NC}"

###############################################################################
# 3. FAZER GIT PULL NA VM
###############################################################################
echo -e "\n${YELLOW}[3/5] Fazendo git pull na VM...${NC}"

ssh $VM_SSH << 'ENDSSH'
cd /home/airton/atendechat
git pull origin main
echo "✓ Git pull concluído!"
ENDSSH

###############################################################################
# 4. REBUILD BACKEND E RESTART DOCKER
###############################################################################
echo -e "\n${YELLOW}[4/5] Rebuild backend e restart Docker...${NC}"

ssh $VM_SSH << 'ENDSSH'
cd /home/airton/atendechat/codatendechat-main

# Rebuild backend TypeScript
echo "Rebuilding backend TypeScript..."
docker-compose exec -T backend npm run build

# Restart backend container
echo "Reiniciando container backend..."
docker-compose restart backend

echo "✓ Backend atualizado!"
ENDSSH

###############################################################################
# 5. RESTART CREWAI SERVICE
###############################################################################
echo -e "\n${YELLOW}[5/5] Reiniciando CrewAI service...${NC}"
echo -e "${YELLOW}Digite a senha do sudo quando solicitado...${NC}"

ssh -t $VM_SSH << 'ENDSSH'
# Copiar credenciais para /opt/crewai
sudo cp ~/google-credentials.json /opt/crewai/
sudo chown airton:airton /opt/crewai/google-credentials.json
sudo chmod 600 /opt/crewai/google-credentials.json
rm -f ~/google-credentials.json

# Restart CrewAI service
sudo systemctl restart crewai.service

# Verificar status
echo ""
echo "Status do CrewAI service:"
sudo systemctl status crewai.service --no-pager | head -20

echo "✓ CrewAI service reiniciado!"
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
