import { QueryInterface, DataTypes } from "sequelize";

module.exports = {
  up: (queryInterface: QueryInterface) => {
    return queryInterface.createTable("Agents", {
      id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true,
        allowNull: false
      },
      name: {
        type: DataTypes.STRING,
        allowNull: false
      },
      function: {
        type: DataTypes.TEXT,
        allowNull: true,
        comment: "Função do agente"
      },
      objective: {
        type: DataTypes.TEXT,
        allowNull: true,
        comment: "Objetivo do agente"
      },
      backstory: {
        type: DataTypes.TEXT,
        allowNull: true,
        comment: "História/contexto do agente"
      },
      keywords: {
        type: DataTypes.JSONB,
        allowNull: true,
        defaultValue: [],
        comment: "Palavras-chave que ativam o agente"
      },
      customInstructions: {
        type: DataTypes.TEXT,
        allowNull: true,
        comment: "Instruções personalizadas"
      },
      persona: {
        type: DataTypes.TEXT,
        allowNull: true,
        comment: "Persona do agente"
      },
      doList: {
        type: DataTypes.JSONB,
        allowNull: true,
        defaultValue: [],
        comment: "Lista do que o agente deve fazer"
      },
      dontList: {
        type: DataTypes.JSONB,
        allowNull: true,
        defaultValue: [],
        comment: "Lista do que o agente NÃO deve fazer"
      },
      aiProvider: {
        type: DataTypes.ENUM("openai", "crewai"),
        allowNull: false,
        defaultValue: "openai",
        comment: "Provedor de IA: OpenAI ou CrewAI"
      },
      isActive: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
        defaultValue: true
      },
      companyId: {
        type: DataTypes.INTEGER,
        references: { model: "Companies", key: "id" },
        onUpdate: "CASCADE",
        onDelete: "CASCADE",
        allowNull: false
      },
      createdAt: {
        type: DataTypes.DATE,
        allowNull: false
      },
      updatedAt: {
        type: DataTypes.DATE,
        allowNull: false
      }
    });
  },

  down: (queryInterface: QueryInterface) => {
    return queryInterface.dropTable("Agents");
  }
};
