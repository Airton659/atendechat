#!/bin/bash

###############################################################################
# CORRIGIR NGINX PARA SUPORTAR WEBSOCKET - VERSÃO FINAL
###############################################################################

set -e

echo "========================================="
echo "  CORRIGINDO WEBSOCKET NO NGINX"
echo "========================================="

# Remover configurações antigas
sudo rm -f /etc/nginx/sites-enabled/api.atendeaibr.com
sudo rm -f /etc/nginx/sites-enabled/www.atendeaibr.com
sudo rm -f /etc/nginx/sites-available/api.atendeaibr.com

# Criar configuração CORRETA com WebSocket
sudo tee /etc/nginx/sites-available/www.atendeaibr.com > /dev/null << 'EOF'
server {
    listen 80;
    server_name www.atendeaibr.com atendeaibr.com;

    client_max_body_size 100M;

    # Socket.io WebSocket (IMPORTANTE - ANTES das outras rotas!)
    location /socket.io/ {
        proxy_pass http://localhost:3000/socket.io/;
        proxy_http_version 1.1;

        # Headers essenciais para WebSocket
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts longos para WebSocket
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_connect_timeout 75s;

        # Desabilitar buffering
        proxy_buffering off;
    }

    # Backend API (sem WebSocket aqui)
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:3000/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Frontend (última rota - catch all)
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

# Ativar site
sudo ln -sf /etc/nginx/sites-available/www.atendeaibr.com /etc/nginx/sites-enabled/

echo "Testando configuração do Nginx..."
sudo nginx -t

echo "Recarregando Nginx..."
sudo systemctl reload nginx

echo ""
echo "Aplicando SSL..."
sudo certbot --nginx -d www.atendeaibr.com -d atendeaibr.com --non-interactive --agree-tos --email contato@atendeaibr.com --redirect --expand

echo ""
echo "========================================="
echo "  TUDO CONFIGURADO!"
echo "========================================="
echo ""
echo "WebSocket funcionando em: wss://www.atendeaibr.com/socket.io/"
echo "Frontend: https://www.atendeaibr.com"
echo "Backend: https://www.atendeaibr.com/api"
echo ""
