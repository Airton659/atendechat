#!/bin/bash

###############################################################################
# SCRIPT PARA RESETAR SENHA DO ADMIN
###############################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  RESETANDO SENHA DO ADMIN${NC}"
echo -e "${GREEN}========================================${NC}"

PROJECT_DIR="$HOME/atendechat/codatendechat-main"

cd $PROJECT_DIR

echo -e "\n${YELLOW}Gerando novo hash bcrypt para senha '123456'...${NC}"

# Gerar hash usando Node.js no container do backend
NEW_HASH=$(docker-compose exec -T backend node -e "const bcrypt = require('bcryptjs'); console.log(bcrypt.hashSync('123456', 8));")

echo "Hash gerado: $NEW_HASH"

echo -e "\n${YELLOW}Atualizando senha no banco de dados...${NC}"

docker-compose exec -T postgres psql -U postgres -d codatende -c "
UPDATE \"Users\"
SET \"passwordHash\" = '$NEW_HASH',
    \"updatedAt\" = NOW()
WHERE email = 'admin@admin.com';
"

echo -e "\n${GREEN}✓ Senha resetada com sucesso!${NC}"

echo -e "\n${YELLOW}Verificando usuário:${NC}"
docker-compose exec -T postgres psql -U postgres -d codatende -c "SELECT id, name, email, profile FROM \"Users\" WHERE email = 'admin@admin.com';"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Teste o login agora:${NC}"
echo -e "${GREEN}    Email: admin@admin.com${NC}"
echo -e "${GREEN}    Senha: 123456${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Testando login via API...${NC}"
sleep 2

RESPONSE=$(curl -s -X POST https://api.atendeaibr.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"123456"}')

echo "Resposta da API:"
echo "$RESPONSE"

if echo "$RESPONSE" | grep -q "token"; then
    echo -e "\n${GREEN}✓ LOGIN FUNCIONANDO!${NC}"
else
    echo -e "\n${RED}✗ Login ainda com erro${NC}"
fi
