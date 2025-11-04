import { QueryInterface, DataTypes } from "sequelize";

export = {
  up: async (queryInterface: QueryInterface) => {
    // Criar tabela KnowledgeBases
    await queryInterface.createTable("KnowledgeBases", {
      id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true,
        allowNull: false
      },
      teamId: {
        type: DataTypes.INTEGER,
        allowNull: false,
        references: { model: "Teams", key: "id" },
        onDelete: "CASCADE"
      },
      companyId: {
        type: DataTypes.INTEGER,
        allowNull: false,
        references: { model: "Companies", key: "id" },
        onDelete: "CASCADE"
      },
      documentId: {
        type: DataTypes.STRING(255),
        allowNull: false,
        unique: true
      },
      filename: {
        type: DataTypes.STRING(255),
        allowNull: false
      },
      fileType: {
        type: DataTypes.STRING(50),
        allowNull: false
      },
      fileSize: {
        type: DataTypes.INTEGER,
        allowNull: false
      },
      filePath: {
        type: DataTypes.TEXT
      },
      chunksCount: {
        type: DataTypes.INTEGER,
        defaultValue: 0
      },
      wordCount: {
        type: DataTypes.INTEGER,
        defaultValue: 0
      },
      status: {
        type: DataTypes.STRING(50),
        defaultValue: "processing"
      },
      errorMessage: {
        type: DataTypes.TEXT
      },
      uploadedAt: {
        type: DataTypes.DATE,
        defaultValue: DataTypes.NOW
      },
      processedAt: {
        type: DataTypes.DATE
      },
      createdAt: {
        type: DataTypes.DATE,
        defaultValue: DataTypes.NOW
      },
      updatedAt: {
        type: DataTypes.DATE,
        defaultValue: DataTypes.NOW
      }
    });

    // Índices para performance
    await queryInterface.addIndex("KnowledgeBases", ["teamId"]);
    await queryInterface.addIndex("KnowledgeBases", ["documentId"]);
    await queryInterface.addIndex("KnowledgeBases", ["companyId"]);

    // Criar tabela AgentKnowledgeBases (Many-to-Many)
    await queryInterface.createTable("AgentKnowledgeBases", {
      id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true
      },
      agentId: {
        type: DataTypes.INTEGER,
        allowNull: false,
        references: { model: "Agents", key: "id" },
        onDelete: "CASCADE"
      },
      knowledgeBaseId: {
        type: DataTypes.INTEGER,
        allowNull: false,
        references: { model: "KnowledgeBases", key: "id" },
        onDelete: "CASCADE"
      },
      createdAt: {
        type: DataTypes.DATE,
        defaultValue: DataTypes.NOW
      },
      updatedAt: {
        type: DataTypes.DATE,
        defaultValue: DataTypes.NOW
      }
    });

    // Índices para Many-to-Many
    await queryInterface.addIndex("AgentKnowledgeBases", ["agentId"]);
    await queryInterface.addIndex("AgentKnowledgeBases", ["knowledgeBaseId"]);

    // Unique index para evitar duplicatas
    await queryInterface.addIndex("AgentKnowledgeBases", ["agentId", "knowledgeBaseId"], {
      unique: true,
      name: "unique_agent_knowledge_base"
    });

    // Adicionar campos ao Agent
    await queryInterface.addColumn("Agents", "useKnowledgeBase", {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
      allowNull: false
    });
  },

  down: async (queryInterface: QueryInterface) => {
    // Remover campo do Agent
    await queryInterface.removeColumn("Agents", "useKnowledgeBase");

    // Remover constraint
    await queryInterface.removeConstraint(
      "AgentKnowledgeBases",
      "unique_agent_knowledge_base"
    );

    // Dropar tabelas
    await queryInterface.dropTable("AgentKnowledgeBases");
    await queryInterface.dropTable("KnowledgeBases");
  }
};
