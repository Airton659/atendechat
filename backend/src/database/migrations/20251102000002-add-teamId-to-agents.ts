import { QueryInterface, DataTypes } from "sequelize";

module.exports = {
  up: (queryInterface: QueryInterface) => {
    return queryInterface.addColumn("Agents", "teamId", {
      type: DataTypes.INTEGER,
      references: { model: "Teams", key: "id" },
      onUpdate: "CASCADE",
      onDelete: "SET NULL",
      allowNull: true,
      comment: "ID da equipe a qual o agente pertence"
    });
  },

  down: (queryInterface: QueryInterface) => {
    return queryInterface.removeColumn("Agents", "teamId");
  }
};
