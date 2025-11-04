import { QueryInterface, DataTypes } from "sequelize";

module.exports = {
  up: async (queryInterface: QueryInterface) => {
    await queryInterface.addColumn("Teams", "processType", {
      type: DataTypes.ENUM("sequential", "hierarchical"),
      allowNull: false,
      defaultValue: "sequential"
    });

    await queryInterface.addColumn("Teams", "managerLLM", {
      type: DataTypes.STRING,
      allowNull: true,
      comment: "LLM usado pelo manager no modo hierarchical (ex: gemini-2.0-flash-lite)"
    });

    await queryInterface.addColumn("Teams", "temperature", {
      type: DataTypes.FLOAT,
      allowNull: false,
      defaultValue: 0.7
    });

    await queryInterface.addColumn("Teams", "verbose", {
      type: DataTypes.BOOLEAN,
      allowNull: false,
      defaultValue: true
    });

    await queryInterface.addColumn("Teams", "managerAgentId", {
      type: DataTypes.INTEGER,
      allowNull: true,
      comment: "Agente ID que atua como manager no modo hierarchical",
      references: {
        model: "Agents",
        key: "id"
      },
      onUpdate: "CASCADE",
      onDelete: "SET NULL"
    });
  },

  down: async (queryInterface: QueryInterface) => {
    await queryInterface.removeColumn("Teams", "managerAgentId");
    await queryInterface.removeColumn("Teams", "verbose");
    await queryInterface.removeColumn("Teams", "temperature");
    await queryInterface.removeColumn("Teams", "managerLLM");
    await queryInterface.removeColumn("Teams", "processType");
  }
};
