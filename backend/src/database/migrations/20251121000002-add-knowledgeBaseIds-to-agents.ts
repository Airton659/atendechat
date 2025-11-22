import { QueryInterface, DataTypes } from "sequelize";

module.exports = {
  up: async (queryInterface: QueryInterface) => {
    await queryInterface.addColumn("Agents", "knowledgeBaseIds", {
      type: DataTypes.ARRAY(DataTypes.INTEGER),
      allowNull: true,
      defaultValue: []
    });
  },

  down: async (queryInterface: QueryInterface) => {
    await queryInterface.removeColumn("Agents", "knowledgeBaseIds");
  }
};
