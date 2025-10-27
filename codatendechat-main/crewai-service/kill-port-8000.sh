#!/bin/bash

###############################################################################
# SCRIPT PARA MATAR BRUTALMENTE TUDO NA PORTA 8000
# Roda DIRETAMENTE na VM como root
###############################################################################

set -x  # Debug mode

echo "============================================"
echo "MATANDO TUDO NA PORTA 8000 - SEM PIEDADE"
echo "============================================"

# Parar serviço primeiro
echo "1. Parando serviço crewai..."
systemctl stop crewai.service 2>/dev/null || true
systemctl disable crewai.service 2>/dev/null || true
systemctl reset-failed crewai.service 2>/dev/null || true
sleep 2

# Matar processos por nome
echo "2. Matando processos por nome..."
pkill -9 -f "python.*8000" 2>/dev/null || true
pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
pkill -9 uvicorn 2>/dev/null || true
pkill -9 -f "python.*crewai" 2>/dev/null || true
pkill -9 -f "main:app" 2>/dev/null || true
pkill -9 -f "python.*main.py" 2>/dev/null || true
sleep 2

# Matar por porta (força total)
echo "3. Matando por porta..."
fuser -k -9 8000/tcp 2>/dev/null || true
sleep 1
fuser -k -9 8000/tcp 2>/dev/null || true
sleep 1
fuser -k -9 8000/tcp 2>/dev/null || true
sleep 2

# Matar por PID
echo "4. Matando por PID..."
PIDS=$(lsof -ti :8000 2>/dev/null || true)
if [ ! -z "$PIDS" ]; then
    echo "PIDs encontrados: $PIDS"
    for pid in $PIDS; do
        kill -9 $pid 2>/dev/null || true
    done
    sleep 2
fi

# Verificação final
echo "5. Verificação final..."
REMAINING=$(lsof -ti :8000 2>/dev/null || true)
if [ ! -z "$REMAINING" ]; then
    echo "❌ AINDA HÁ PROCESSOS NA PORTA 8000:"
    lsof -i :8000
    echo ""
    echo "Tentando força NUCLEAR..."
    for pid in $REMAINING; do
        kill -9 $pid 2>/dev/null || true
    done
    sleep 3

    # Última verificação
    FINAL=$(lsof -ti :8000 2>/dev/null || true)
    if [ ! -z "$FINAL" ]; then
        echo "❌ IMPOSSÍVEL MATAR! Processos restantes:"
        lsof -i :8000
        ps aux | grep -E "$FINAL"
        exit 1
    fi
fi

echo ""
echo "✅ PORTA 8000 LIBERADA!"
lsof -i :8000 2>&1 || echo "(Nenhum processo na porta 8000)"
echo "============================================"
