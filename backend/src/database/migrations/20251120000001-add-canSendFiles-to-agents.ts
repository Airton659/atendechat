import { QueryInterface, DataTypes } from "sequelize";

module.exports = {
  up: (queryInterface: QueryInterface) => {
    return queryInterface.addColumn("Agents", "canSendFiles", {
      type: DataTypes.BOOLEAN,
      allowNull: false,
      defaultValue: false,
      comment: "Se o agente pode enviar arquivos do File List"
    });
  },

  down: (queryInterface: QueryInterface) => {
    return queryInterface.removeColumn("Agents", "canSendFiles");
  }
};
