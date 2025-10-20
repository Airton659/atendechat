#!/bin/bash

###############################################################################
# SCRIPT DE DEPLOY COMPLETO - ATENDECHAT (COM GIT)
# Executa na VM: bash deploy-git.sh
# Faz TUDO automaticamente: clona do GitHub e sobe o sistema
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  DEPLOY ATENDECHAT - ATENDEAIBR.COM${NC}"
echo -e "${GREEN}========================================${NC}"

# Variáveis
DOMAIN_BACKEND="api.atendeaibr.com"
DOMAIN_FRONTEND="www.atendeaibr.com"
APP_DIR="$HOME"
PROJECT_DIR="$HOME/atendechat/codatendechat-main"
BACKEND_PORT=3000
FRONTEND_PORT=3001
GIT_REPO="git@github.com:Airton659/atendechat.git"

###############################################################################
# 1. INSTALAR DEPENDÊNCIAS
###############################################################################
echo -e "\n${YELLOW}[1/8] Instalando dependências do sistema...${NC}"

# Atualizar sistema
sudo apt-get update -y
sudo apt-get upgrade -y

# Instalar pacotes básicos
sudo apt-get install -y curl wget git build-essential software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Instalar Docker
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo "Docker já instalado"
fi

# Instalar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Instalando Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose já instalado"
fi

# Instalar Nginx
if ! command -v nginx &> /dev/null; then
    echo "Instalando Nginx..."
    sudo apt-get install -y nginx
else
    echo "Nginx já instalado"
fi

# Instalar Certbot
if ! command -v certbot &> /dev/null; then
    echo "Instalando Certbot..."
    sudo apt-get install -y certbot python3-certbot-nginx
else
    echo "Certbot já instalado"
fi

###############################################################################
# 2. CLONAR PROJETO DO GITHUB
###############################################################################
echo -e "\n${YELLOW}[2/8] Clonando projeto do GitHub...${NC}"

# Criar diretório no home do usuário
cd $APP_DIR

# Verificar se já existe o projeto
if [ -d "atendechat" ]; then
    echo "Projeto já existe, removendo para clonar novamente..."
    rm -rf atendechat
fi

echo "Clonando do GitHub..."
# Adicionar github.com aos known_hosts
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
git clone $GIT_REPO atendechat
cd atendechat

###############################################################################
# 3. CRIAR ARQUIVO .ENV
###############################################################################
echo -e "\n${YELLOW}[3/8] Criando arquivo .env de produção...${NC}"

cd $PROJECT_DIR

cat > .env << 'EOF'
# Produção - atendeaibr.com
NODE_ENV=production
BACKEND_URL=https://api.atendeaibr.com
FRONTEND_URL=https://www.atendeaibr.com
PROXY_PORT=443
PORT=3000

# Stack Configuration
STACK_NAME=atendeaibr
BACKEND_PORT=3000
FRONTEND_PORT=3001

# Database PostgreSQL
DB_DIALECT=postgres
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASS=postgres123
DB_NAME=codatende

# JWT Secrets
JWT_SECRET=kZaOTd+YZpjRUyyuQUpigJaEMk4vcW4YOymKPZX0Ts8=
JWT_REFRESH_SECRET=dBSXqFg9TaNUEDXVp6fhMTRLBysP+j2DSqf7+raxD3A=

# Redis
REDIS_URI=redis://redis:6379
REDIS_OPT_LIMITER_MAX=1
REDIS_OPT_LIMITER_DURATION=3000

# Limites
USER_LIMIT=10000
CONNECTIONS_LIMIT=100000
CLOSED_SEND_BY_ME=true

# Gerencianet PIX
ENABLE_FINANCIAL=false
GERENCIANET_SANDBOX=false
GERENCIANET_CLIENT_ID=Client_Id_Gerencianet
GERENCIANET_CLIENT_SECRET=Client_Secret_Gerencianet
GERENCIANET_PIX_CERT=production-cert
GERENCIANET_PIX_KEY=chave_pix_gerencianet

# EMAIL
MAIL_HOST=smtp.gmail.com
MAIL_USER=contato@atendeaibr.com
MAIL_PASS=SuaSenhaAqui
MAIL_FROM=contato@atendeaibr.com
MAIL_PORT=465

# Campanhas
CAMPAIGN_RATE_LIMIT=10000
CAMPAIGN_BATCH_SIZE=50

# Resource Limits
BACKEND_CPU_LIMIT=1.0
BACKEND_MEM_LIMIT=1024
BACKEND_CPU_RESERVE=0.5
BACKEND_MEM_RESERVE=512

FRONTEND_CPU_LIMIT=0.5
FRONTEND_MEM_LIMIT=512
FRONTEND_CPU_RESERVE=0.25
FRONTEND_MEM_RESERVE=256

POSTGRES_CPU_LIMIT=1.0
POSTGRES_MEM_LIMIT=1024
POSTGRES_CPU_RESERVE=0.5
POSTGRES_MEM_RESERVE=512

REDIS_CPU_LIMIT=0.5
REDIS_MEM_LIMIT=512
REDIS_CPU_RESERVE=0.25
REDIS_MEM_RESERVE=256

# Branding
COLOR=#0000FF
TAB_NAME=AtendeAI
EOF

echo "Arquivo .env criado!"

###############################################################################
# 4. CRIAR BACKEND .ENV
###############################################################################
echo -e "\n${YELLOW}[4/8] Criando .env do backend...${NC}"

cd $PROJECT_DIR/backend || { echo "Erro: diretório backend não encontrado"; exit 1; }

cat > .env << 'EOF'
NODE_ENV=production
BACKEND_URL=https://api.atendeaibr.com
FRONTEND_URL=https://www.atendeaibr.com
PROXY_PORT=443
PORT=3000

DB_DIALECT=postgres
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASS=postgres123
DB_NAME=codatende

JWT_SECRET=kZaOTd+YZpjRUyyuQUpigJaEMk4vcW4YOymKPZX0Ts8=
JWT_REFRESH_SECRET=dBSXqFg9TaNUEDXVp6fhMTRLBysP+j2DSqf7+raxD3A=

REDIS_URI=redis://redis:6379
REDIS_OPT_LIMITER_MAX=1
REDIS_OPT_LIMITER_DURATION=3000

USER_LIMIT=10000
CONNECTIONS_LIMIT=100000
CLOSED_SEND_BY_ME=true

ENABLE_FINANCIAL=false
GERENCIANET_SANDBOX=false
GERENCIANET_CLIENT_ID=Client_Id_Gerencianet
GERENCIANET_CLIENT_SECRET=Client_Secret_Gerencianet
GERENCIANET_PIX_CERT=production-cert
GERENCIANET_PIX_KEY=chave_pix_gerencianet

MAIL_HOST=smtp.gmail.com
MAIL_USER=contato@atendeaibr.com
MAIL_PASS=SuaSenhaAqui
MAIL_FROM=contato@atendeaibr.com
MAIL_PORT=465

CAMPAIGN_RATE_LIMIT=10000
CAMPAIGN_BATCH_SIZE=50

# CrewAI Service
CREWAI_API_URL=http://localhost:8000
EOF

###############################################################################
# 5. CRIAR FRONTEND .ENV
###############################################################################
echo -e "\n${YELLOW}[5/8] Criando .env do frontend...${NC}"

cd $PROJECT_DIR/frontend || { echo "Erro: diretório frontend não encontrado"; exit 1; }

cat > .env << 'EOF'
REACT_APP_BACKEND_URL=https://api.atendeaibr.com
REACT_APP_HOURS_CLOSE_TICKETS_AUTO=24
EOF

###############################################################################
# 6. SUBIR DOCKER COMPOSE
###############################################################################
echo -e "\n${YELLOW}[6/8] Subindo containers Docker...${NC}"

cd $PROJECT_DIR

# Parar containers antigos se existirem
docker-compose down 2>/dev/null || true

# Subir containers
docker-compose up -d --build

# Aguardar containers subirem
echo "Aguardando containers iniciarem..."
sleep 30

# Verificar status
docker-compose ps

###############################################################################
# 7. CONFIGURAR CREWAI SERVICE (STANDALONE - NÃO DOCKER)
###############################################################################
echo -e "\n${YELLOW}[7/9] Configurando CrewAI Service (Standalone)...${NC}"

# Instalar Python 3.11+ e pip
if ! command -v python3 &> /dev/null; then
    echo "Instalando Python 3..."
    sudo apt-get install -y python3 python3-pip python3-venv
else
    echo "Python já instalado"
fi

# Navegar para o diretório do CrewAI service
cd $PROJECT_DIR/crewai-service

# Criar ambiente virtual
echo "Criando ambiente virtual Python..."
python3 -m venv venv

# Ativar ambiente virtual e instalar dependências
echo "Instalando dependências Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Criar .env para CrewAI service
echo "Criando .env para CrewAI service..."
cat > .env << 'EOF'
GOOGLE_CLOUD_PROJECT=seu-projeto-gcp
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/opt/crewai/google-credentials.json
VERTEX_MODEL=gemini-2.0-flash-exp
PORT=8000
EOF

echo -e "${YELLOW}ATENÇÃO: Configure as credenciais do Google Cloud!${NC}"
echo "1. Coloque o arquivo google-credentials.json em /opt/crewai/"
echo "2. Atualize GOOGLE_CLOUD_PROJECT no arquivo .env"
echo "3. Certifique-se de ter ativado Vertex AI e Firestore no projeto"

# Criar diretório para credenciais (se não existir)
sudo mkdir -p /opt/crewai
echo -e "${YELLOW}Copie seu google-credentials.json para /opt/crewai/${NC}"

# Criar systemd service para CrewAI
echo "Criando systemd service para CrewAI..."
sudo tee /etc/systemd/system/crewai-service.service > /dev/null << EOF
[Unit]
Description=CrewAI API Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/crewai-service
Environment="PATH=$PROJECT_DIR/crewai-service/venv/bin"
ExecStart=$PROJECT_DIR/crewai-service/venv/bin/python3 -m uvicorn api.src.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Recarregar systemd e iniciar serviço
echo "Iniciando CrewAI service..."
sudo systemctl daemon-reload
sudo systemctl enable crewai-service
sudo systemctl start crewai-service

# Verificar status
echo "Verificando status do CrewAI service..."
sudo systemctl status crewai-service --no-pager || true

echo -e "${GREEN}CrewAI service configurado!${NC}"
echo "Use 'sudo systemctl status crewai-service' para verificar o status"
echo "Use 'sudo journalctl -u crewai-service -f' para ver os logs"

###############################################################################
# 8. CONFIGURAR NGINX
###############################################################################
echo -e "\n${YELLOW}[8/9] Configurando Nginx...${NC}"

# Remover configuração padrão
sudo rm -f /etc/nginx/sites-enabled/default

# Criar configuração para o backend
sudo tee /etc/nginx/sites-available/api.atendeaibr.com > /dev/null << 'EOF'
server {
    listen 80;
    server_name api.atendeaibr.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

# Criar configuração para o frontend
sudo tee /etc/nginx/sites-available/www.atendeaibr.com > /dev/null << 'EOF'
server {
    listen 80;
    server_name www.atendeaibr.com atendeaibr.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# Ativar sites
sudo ln -sf /etc/nginx/sites-available/api.atendeaibr.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/www.atendeaibr.com /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Recarregar Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

###############################################################################
# 9. CONFIGURAR SSL
###############################################################################
echo -e "\n${YELLOW}[9/9] Configurando SSL (Certbot)...${NC}"

# Obter certificados SSL
sudo certbot --nginx -d api.atendeaibr.com -d www.atendeaibr.com -d atendeaibr.com --non-interactive --agree-tos --email contato@atendeaibr.com --redirect --expand

# Configurar renovação automática
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

###############################################################################
# FINALIZAÇÃO
###############################################################################
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  DEPLOY CONCLUÍDO COM SUCESSO!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Frontend:${NC} https://www.atendeaibr.com"
echo -e "${GREEN}Backend:${NC} https://api.atendeaibr.com"
echo ""
echo -e "${YELLOW}Comandos úteis:${NC}"
echo "  - Ver logs: cd $PROJECT_DIR && docker-compose logs -f"
echo "  - Parar: cd $PROJECT_DIR && docker-compose down"
echo "  - Reiniciar: cd $PROJECT_DIR && docker-compose restart"
echo "  - Status: cd $PROJECT_DIR && docker-compose ps"
echo ""
echo -e "${GREEN}Acesse: https://www.atendeaibr.com${NC}"
echo ""
