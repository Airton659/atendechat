#!/bin/bash

# Tentar carregar senhas do arquivo
if [ -f ~/.atendechat-credentials ]; then
    source ~/.atendechat-credentials
    echo "✅ Senhas carregadas de ~/.atendechat-credentials"
else
    echo "Digite a senha SSH da VM:"
    read -s SSH_PASSWORD
    echo ""

    echo "Digite a senha SUDO da VM:"
    read -s SUDO_PASSWORD
    echo ""
fi

echo "=== VERIFICANDO LOGS DO BACKEND NODE.JS ==="
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no airton@46.62.147.212 << ENDSSH
cd /home/airton/atendechat/codatendechat-main

echo "Últimos logs do backend relacionados a TOGGLE:"
docker-compose logs --tail=200 backend | grep -A 10 -B 5 "TOGGLE\|validation\|422" || echo "Nenhum log encontrado"

echo ""
echo "=== VERIFICANDO LOGS DO CREWAI SERVICE ==="
echo "$SUDO_PASSWORD" | sudo -S journalctl -u crewai.service -n 100 --no-pager | grep -A 5 -B 5 "toggle\|422\|validation\|ERROR" || echo "Nenhum erro encontrado"

echo ""
echo "=== TESTANDO ENDPOINT DIRETAMENTE ==="
curl -X PUT http://localhost:8000/api/v2/training/validation-rules/toggle \
  -H "Content-Type: application/json" \
  -d '{"teamId":"test123","tenantId":"company_1","agentId":"agent_1","enabled":true}' \
  2>&1

ENDSSH
