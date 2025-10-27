#!/bin/bash

###############################################################################
# SCRIPT PARA MATAR BRUTALMENTE TUDO NA PORTA 8000
# Roda DIRETAMENTE na VM como root
###############################################################################

set -x  # Debug mode

echo "============================================"
echo "MATANDO TUDO NA PORTA 8000 - SEM PIEDADE"
echo "============================================"

# Parar serviço primeiro E MATAR PROCESSOS ÓRFÃOS
echo "1. Parando serviço crewai e matando órfãos..."
systemctl stop crewai.service 2>/dev/null || true
systemctl kill --signal=SIGKILL crewai.service 2>/dev/null || true
systemctl disable crewai.service 2>/dev/null || true
systemctl reset-failed crewai.service 2>/dev/null || true
sleep 3

# RODADA 1: Matar processos por nome
echo "2. RODADA 1 - Matando processos por nome..."
pkill -9 -f "python.*8000" 2>/dev/null || true
pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
pkill -9 uvicorn 2>/dev/null || true
pkill -9 -f "python.*crewai" 2>/dev/null || true
pkill -9 -f "main:app" 2>/dev/null || true
pkill -9 -f "python.*main.py" 2>/dev/null || true
sleep 3

# RODADA 2: Matar por porta (força total) - 5 ROUNDS
echo "3. RODADA 2 - Matando por porta (5 rounds)..."
for i in {1..5}; do
    echo "Round $i de fuser..."
    fuser -k -9 8000/tcp 2>/dev/null || true
    sleep 1
done
sleep 3

# RODADA 3: Matar por PID
echo "4. RODADA 3 - Matando por PID..."
PIDS=$(lsof -ti :8000 2>/dev/null || true)
if [ ! -z "$PIDS" ]; then
    echo "PIDs encontrados: $PIDS"
    for pid in $PIDS; do
        echo "Matando PID $pid..."
        kill -9 $pid 2>/dev/null || true
    done
    sleep 3
fi

# RODADA 4: Verificação E FORÇA NUCLEAR se necessário
echo "5. RODADA 4 - Verificação final..."
REMAINING=$(lsof -ti :8000 2>/dev/null || true)
if [ ! -z "$REMAINING" ]; then
    echo "❌ AINDA HÁ PROCESSOS NA PORTA 8000!"
    lsof -i :8000
    echo ""
    echo "APLICANDO FORÇA NUCLEAR (kill -9 + fuser)..."

    # Força nuclear 1: kill -9
    for pid in $REMAINING; do
        kill -9 $pid 2>/dev/null || true
    done

    # Força nuclear 2: fuser 10 vezes
    for i in {1..10}; do
        fuser -k -9 8000/tcp 2>/dev/null || true
        sleep 0.5
    done

    sleep 5

    # Última verificação
    FINAL=$(lsof -ti :8000 2>/dev/null || true)
    if [ ! -z "$FINAL" ]; then
        echo ""
        echo "❌ IMPOSSÍVEL MATAR APÓS FORÇA NUCLEAR!"
        echo "Processos restantes:"
        lsof -i :8000
        ps aux | grep -E "$FINAL"
        echo ""
        echo "SUGESTÃO: Reinicie a VM com 'sudo reboot'"
        exit 1
    fi
fi

# Aguardar 5 segundos para garantir que kernel liberou a porta
echo ""
echo "Aguardando 5s para kernel liberar porta..."
sleep 5

# Verificação FINAL FINAL
echo ""
echo "6. Verificação FINAL..."
FINAL_CHECK=$(lsof -ti :8000 2>/dev/null || true)
if [ ! -z "$FINAL_CHECK" ]; then
    echo "❌ PORTA 8000 AINDA OCUPADA!"
    lsof -i :8000
    exit 1
fi

echo ""
echo "✅ PORTA 8000 100% LIBERADA E GARANTIDA!"
lsof -i :8000 2>&1 || echo "(Nenhum processo na porta 8000)"
echo "============================================"
