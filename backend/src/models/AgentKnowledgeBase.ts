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
import KnowledgeBase from "./KnowledgeBase";

@Table
class AgentKnowledgeBase extends Model<AgentKnowledgeBase> {
  @PrimaryKey
  @AutoIncrement
  @Column
  id: number;

  @ForeignKey(() => Agent)
  @Column
  agentId: number;

  @ForeignKey(() => KnowledgeBase)
  @Column
  knowledgeBaseId: number;

  @CreatedAt
  createdAt: Date;

  @UpdatedAt
  updatedAt: Date;
}

export default AgentKnowledgeBase;
