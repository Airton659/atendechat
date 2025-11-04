import { QueryInterface, DataTypes } from "sequelize";

module.exports = {
  up: async (queryInterface: QueryInterface) => {
    await queryInterface.createTable("AgentLogs", {
      id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true,
        allowNull: false
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
      teamId: {
        type: DataTypes.INTEGER,
        allowNull: false,
        references: {
          model: "Teams",
          key: "id"
        },
        onUpdate: "CASCADE",
        onDelete: "CASCADE"
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
      message: {
        type: DataTypes.TEXT,
        allowNull: false
      },
      response: {
        type: DataTypes.TEXT,
        allowNull: false
      },
      agentConfig: {
        type: DataTypes.JSON,
        allowNull: true
      },
      teamConfig: {
        type: DataTypes.JSON,
        allowNull: true
      },
      promptUsed: {
        type: DataTypes.TEXT,
        allowNull: true
      },
      processingTime: {
        type: DataTypes.FLOAT,
        allowNull: true
      },
      success: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
        defaultValue: true
      },
      errorMessage: {
        type: DataTypes.TEXT,
        allowNull: true
      },
      contactPhone: {
        type: DataTypes.STRING,
        allowNull: true
      },
      ticketId: {
        type: DataTypes.INTEGER,
        allowNull: true
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

    // Criar índices para melhorar performance nas consultas
    await queryInterface.addIndex("AgentLogs", ["companyId"]);
    await queryInterface.addIndex("AgentLogs", ["teamId"]);
    await queryInterface.addIndex("AgentLogs", ["agentId"]);
    await queryInterface.addIndex("AgentLogs", ["createdAt"]);
  },

  down: async (queryInterface: QueryInterface) => {
    await queryInterface.dropTable("AgentLogs");
  }
};
