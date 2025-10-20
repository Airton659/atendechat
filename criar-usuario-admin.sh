#!/bin/bash

###############################################################################
# CRIAR USUÁRIO ADMINISTRADOR
###############################################################################

set -e

echo "========================================="
echo "  CRIANDO USUÁRIO ADMINISTRADOR"
echo "========================================="
echo ""

# Gerar hash da senha usando Node.js dentro do container
PASSWORD_HASH=$(docker exec codatendechat-main-backend-1 node -e "const bcrypt = require('bcryptjs'); bcrypt.hash('@Delete@*', 8).then(hash => console.log(hash));")

echo "Hash gerado, criando usuário no banco..."

# Executar SQL no container do postgres
docker exec -i codatendechat-main-postgres-1 psql -U postgres -d codatende << EOF
-- Garantir que empresa existe
INSERT INTO "Companies" (id, name, email, "createdAt", "updatedAt")
VALUES (1, 'AtendeAI', 'whitetree.ia@gmail.com', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Deletar usuário se já existe
DELETE FROM "Users" WHERE email = 'whitetree.ia@gmail.com';

-- Criar usuário admin
INSERT INTO "Users" (name, email, "passwordHash", profile, "companyId", "createdAt", "updatedAt", super)
VALUES (
    'Admin',
    'whitetree.ia@gmail.com',
    '$PASSWORD_HASH',
    'admin',
    1,
    NOW(),
    NOW(),
    true
);

EOF

echo ""
echo "========================================="
echo "  USUÁRIO CRIADO COM SUCESSO!"
echo "========================================="
echo ""
echo "Email: whitetree.ia@gmail.com"
echo "Senha: @Delete@*"
echo ""
echo "Acesse: https://www.atendeaibr.com"
echo ""
