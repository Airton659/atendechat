import { QueryInterface, DataTypes } from "sequelize";

module.exports = {
  up: (queryInterface: QueryInterface) => {
    return queryInterface.createTable("Teams", {
      id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true,
        allowNull: false
      },
      name: {
        type: DataTypes.STRING,
        allowNull: false,
        comment: "Nome da equipe"
      },
      description: {
        type: DataTypes.TEXT,
        allowNull: true,
        comment: "Descrição da equipe"
      },
      industry: {
        type: DataTypes.STRING,
        allowNull: true,
        comment: "Setor/indústria da equipe (ecommerce, services, etc)"
      },
      isActive: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
        defaultValue: true,
        comment: "Equipe ativa ou inativa"
      },
      generatedBy: {
        type: DataTypes.ENUM("manual", "architect"),
        allowNull: false,
        defaultValue: "manual",
        comment: "Como a equipe foi criada: manual ou pelo arquiteto IA"
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
    return queryInterface.dropTable("Teams");
  }
};
