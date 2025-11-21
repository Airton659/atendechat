import {
  Table,
  Column,
  CreatedAt,
  UpdatedAt,
  Model,
  PrimaryKey,
  AutoIncrement,
  ForeignKey
} from "sequelize-typescript";
import Agent from "./Agent";
import Files from "./Files";

@Table
class AgentFileList extends Model<AgentFileList> {
  @PrimaryKey
  @AutoIncrement
  @Column
  id: number;

  @ForeignKey(() => Agent)
  @Column
  agentId: number;

  @ForeignKey(() => Files)
  @Column
  fileListId: number;

  @CreatedAt
  createdAt: Date;

  @UpdatedAt
  updatedAt: Date;
}

export default AgentFileList;
