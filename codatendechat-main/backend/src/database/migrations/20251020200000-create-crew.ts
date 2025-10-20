import { QueryInterface, DataTypes } from "sequelize";

module.exports = {
  up: (queryInterface: QueryInterface) => {
    return queryInterface.createTable("Crews", {
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
      description: {
        type: DataTypes.TEXT,
        allowNull: true
      },
      firestoreId: {
        type: DataTypes.STRING,
        allowNull: false,
        unique: true,
        comment: "ID do blueprint no Firestore"
      },
      status: {
        type: DataTypes.ENUM("draft", "active", "archived"),
        defaultValue: "draft",
        allowNull: false
      },
      industry: {
        type: DataTypes.STRING,
        allowNull: true
      },
      objective: {
        type: DataTypes.TEXT,
        allowNull: true
      },
      tone: {
        type: DataTypes.STRING,
        defaultValue: "professional",
        allowNull: false
      },
      totalConversations: {
        type: DataTypes.INTEGER,
        defaultValue: 0,
        allowNull: false
      },
      avgResponseTime: {
        type: DataTypes.FLOAT,
        defaultValue: 0,
        allowNull: false
      },
      satisfactionRate: {
        type: DataTypes.FLOAT,
        defaultValue: 0,
        allowNull: false
      },
      lastUsed: {
        type: DataTypes.DATE,
        allowNull: true
      },
      companyId: {
        type: DataTypes.INTEGER,
        references: { model: "Companies", key: "id" },
        onUpdate: "CASCADE",
        onDelete: "CASCADE",
        allowNull: false
      },
      createdBy: {
        type: DataTypes.INTEGER,
        references: { model: "Users", key: "id" },
        onUpdate: "SET NULL",
        onDelete: "SET NULL",
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
    return queryInterface.dropTable("Crews");
  }
};
