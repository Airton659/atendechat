#!/bin/bash
# Script de inicialização do CrewAI que garante que a porta 8000 está livre

echo "🔄 Iniciando CrewAI Service..."

# Mata qualquer processo na porta 8000
echo "🧹 Limpando porta 8000..."
fuser -k -9 8000/tcp 2>/dev/null || true
sleep 1

# Verifica se a porta está livre
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ ERRO: Porta 8000 ainda está ocupada!"
    lsof -i :8000
    exit 1
fi

echo "✅ Porta 8000 livre, iniciando serviço..."

# Inicia o uvicorn
cd /home/airton/atendechat/codatendechat-main/crewai-service/api/src
exec /home/airton/atendechat/codatendechat-main/crewai-service/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
