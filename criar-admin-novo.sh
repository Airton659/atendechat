#!/bin/bash

###############################################################################
# SCRIPT PARA CRIAR USUÁRIO ADMIN - VERSÃO CORRIGIDA
# Roda dentro do container: bash criar-admin-novo.sh
###############################################################################

set -e

echo "==========================================="
echo "  CRIANDO USUÁRIO ADMINISTRADOR"
echo "==========================================="

# Pedir dados do usuário
read -p "Digite o email do admin: " ADMIN_EMAIL
read -p "Digite o nome do admin: " ADMIN_NAME
read -sp "Digite a senha do admin: " ADMIN_PASSWORD
echo ""

# Entrar no container backend
docker exec -it codatendechat-main-backend-1 bash -c "
cd /app

# Script Node.js para criar usuário
node <<'EOJS'
const { Sequelize } = require('sequelize');
const bcrypt = require('bcryptjs');

// Configuração do banco
const sequelize = new Sequelize('codatende', 'postgres', 'postgres123', {
  host: 'postgres',
  dialect: 'postgres',
  logging: false
});

async function createAdmin() {
  try {
    await sequelize.authenticate();
    console.log('✓ Conectado ao banco de dados');

    // Buscar ou criar company
    const [company] = await sequelize.query(
      \"SELECT id FROM \\\"Companies\\\" WHERE name = 'Default Company' LIMIT 1\",
      { type: Sequelize.QueryTypes.SELECT }
    );

    let companyId;
    if (company) {
      companyId = company.id;
      console.log('✓ Company encontrada: ID', companyId);
    } else {
      const [result] = await sequelize.query(
        \"INSERT INTO \\\"Companies\\\" (name, \\\"createdAt\\\", \\\"updatedAt\\\") VALUES ('Default Company', NOW(), NOW()) RETURNING id\",
        { type: Sequelize.QueryTypes.INSERT }
      );
      companyId = result[0].id;
      console.log('✓ Company criada: ID', companyId);
    }

    // Verificar se usuário já existe
    const [existingUser] = await sequelize.query(
      \"SELECT id FROM \\\"Users\\\" WHERE email = '${ADMIN_EMAIL}' LIMIT 1\",
      { type: Sequelize.QueryTypes.SELECT }
    );

    if (existingUser) {
      console.log('⚠ Usuário já existe! Atualizando senha...');

      const passwordHash = bcrypt.hashSync('${ADMIN_PASSWORD}', 10);
      await sequelize.query(
        \"UPDATE \\\"Users\\\" SET \\\"passwordHash\\\" = '\${passwordHash}', profile = 'admin' WHERE email = '${ADMIN_EMAIL}'\",
        { type: Sequelize.QueryTypes.UPDATE }
      );
      console.log('✓ Senha atualizada!');
    } else {
      console.log('Criando novo usuário admin...');

      const passwordHash = bcrypt.hashSync('${ADMIN_PASSWORD}', 10);
      await sequelize.query(
        \"INSERT INTO \\\"Users\\\" (name, email, \\\"passwordHash\\\", profile, \\\"companyId\\\", \\\"createdAt\\\", \\\"updatedAt\\\") VALUES ('${ADMIN_NAME}', '${ADMIN_EMAIL}', '\${passwordHash}', 'admin', \${companyId}, NOW(), NOW())\",
        { type: Sequelize.QueryTypes.INSERT }
      );
      console.log('✓ Usuário criado com sucesso!');
    }

    console.log('');
    console.log('=========================================');
    console.log('  DADOS DE LOGIN');
    console.log('=========================================');
    console.log('Email: ${ADMIN_EMAIL}');
    console.log('Senha: ${ADMIN_PASSWORD}');
    console.log('URL: https://www.atendeaibr.com');
    console.log('=========================================');

    await sequelize.close();
  } catch (error) {
    console.error('Erro:', error.message);
    process.exit(1);
  }
}

createAdmin();
EOJS
"

echo ""
echo "✓ Processo concluído!"
