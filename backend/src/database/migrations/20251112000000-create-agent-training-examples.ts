import { QueryInterface, DataTypes } from "sequelize";

module.exports = {
  up: (queryInterface: QueryInterface) => {
    return queryInterface.createTable("AgentTrainingExamples", {
      id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true,
        allowNull: false
      },
      agentId: {
        type: DataTypes.INTEGER,
        allowNull: false,
        references: {
          model: "Agents",
          key: "id"
        },
        onUpdate: "CASCADE",
        onDelete: "CASCADE"
      },
      teamId: {
        type: DataTypes.INTEGER,
        allowNull: true,
        references: {
          model: "Teams",
          key: "id"
        },
        onUpdate: "CASCADE",
        onDelete: "CASCADE"
      },
      companyId: {
        type: DataTypes.INTEGER,
        allowNull: false,
        references: {
          model: "Companies",
          key: "id"
        },
        onUpdate: "CASCADE",
        onDelete: "CASCADE"
      },
      userMessage: {
        type: DataTypes.TEXT,
        allowNull: false,
        comment: "Mensagem original do usuário"
      },
      agentResponse: {
        type: DataTypes.TEXT,
        allowNull: false,
        comment: "Resposta original do agente"
      },
      correctedResponse: {
        type: DataTypes.TEXT,
        allowNull: true,
        comment: "Resposta corrigida (se aplicável)"
      },
      feedbackType: {
        type: DataTypes.ENUM("approved", "corrected", "rejected"),
        allowNull: false,
        defaultValue: "approved",
        comment: "Tipo de feedback dado pelo usuário"
      },
      rating: {
        type: DataTypes.INTEGER,
        allowNull: true,
        defaultValue: null,
        comment: "Rating 1-5 (opcional)"
      },
      feedbackNotes: {
        type: DataTypes.TEXT,
        allowNull: true,
        comment: "Notas adicionais sobre o feedback"
      },
      priority: {
        type: DataTypes.INTEGER,
        allowNull: false,
        defaultValue: 5,
        comment: "Prioridade 0-10 (maior = mais importante)"
      },
      usedInPrompt: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
        defaultValue: true,
        comment: "Se deve ser usado como few-shot example"
      },
      conversationContext: {
        type: DataTypes.JSONB,
        allowNull: true,
        comment: "Contexto adicional da conversa"
      },
      createdBy: {
        type: DataTypes.INTEGER,
        allowNull: true,
        references: {
          model: "Users",
          key: "id"
        },
        onUpdate: "CASCADE",
        onDelete: "SET NULL"
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
    return queryInterface.dropTable("AgentTrainingExamples");
  }
};
