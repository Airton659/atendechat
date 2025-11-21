import { QueryInterface, DataTypes } from "sequelize";

module.exports = {
  up: (queryInterface: QueryInterface) => {
    return queryInterface.createTable("AgentFiles", {
      id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true,
        allowNull: false
      },
      agentId: {
        type: DataTypes.INTEGER,
        references: { model: "Agents", key: "id" },
        onUpdate: "CASCADE",
        onDelete: "CASCADE",
        allowNull: false
      },
      fileName: {
        type: DataTypes.STRING,
        allowNull: false
      },
      originalName: {
        type: DataTypes.STRING,
        allowNull: false
      },
      filePath: {
        type: DataTypes.STRING,
        allowNull: false
      },
      fileType: {
        type: DataTypes.STRING,
        allowNull: false
      },
      mimeType: {
        type: DataTypes.STRING,
        allowNull: false
      },
      fileSize: {
        type: DataTypes.INTEGER,
        allowNull: true
      },
      description: {
        type: DataTypes.STRING,
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
  },

  down: (queryInterface: QueryInterface) => {
    return queryInterface.dropTable("AgentFiles");
  }
};
