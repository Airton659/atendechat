import {
  Table,
  Column,
  CreatedAt,
  UpdatedAt,
  Model,
  PrimaryKey,
  AutoIncrement,
  ForeignKey,
  BelongsTo,
  DataType
} from "sequelize-typescript";
import Agent from "./Agent";

@Table({ tableName: "AgentFiles" })
class AgentFile extends Model<AgentFile> {
  @PrimaryKey
  @AutoIncrement
  @Column
  id: number;

  @ForeignKey(() => Agent)
  @Column
  agentId: number;

  @BelongsTo(() => Agent)
  agent: Agent;

  @Column
  fileName: string;

  @Column
  originalName: string;

  @Column
  filePath: string;

  @Column
  fileType: string;

  @Column
  mimeType: string;

  @Column(DataType.INTEGER)
  fileSize: number;

  @Column
  description: string;

  @CreatedAt
  createdAt: Date;

  @UpdatedAt
  updatedAt: Date;
}

export default AgentFile;
