#!/bin/bash

echo "=== SALVANDO SENHAS PARA ACESSO À VM ==="
echo ""
echo "Digite a senha SSH da VM (airton@46.62.147.212):"
read -s SSH_PASSWORD
echo ""

echo "Digite a senha SUDO da VM:"
read -s SUDO_PASSWORD
echo ""

# Criar arquivo com senhas
cat > ~/.atendechat-credentials << EOF
SSH_PASSWORD="$SSH_PASSWORD"
SUDO_PASSWORD="$SUDO_PASSWORD"
EOF

# Permissões restritas (só você pode ler)
chmod 600 ~/.atendechat-credentials

echo "✅ Senhas salvas em: ~/.atendechat-credentials"
echo "✅ Arquivo com permissões seguras (600)"
echo ""
echo "Agora execute: bash debug-toggle.sh"
