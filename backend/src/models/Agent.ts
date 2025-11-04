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
  BelongsToMany,
  DataType,
  Default
} from "sequelize-typescript";
import Company from "./Company";
import KnowledgeBase from "./KnowledgeBase";
import AgentKnowledgeBase from "./AgentKnowledgeBase";

@Table
class Agent extends Model<Agent> {
  @PrimaryKey
  @AutoIncrement
  @Column
  id: number;

  @Column
  name: string;

  @Column(DataType.TEXT)
  function: string;

  @Column(DataType.TEXT)
  objective: string;

  @Column(DataType.TEXT)
  backstory: string;

  @Column(DataType.JSONB)
  keywords: string[];

  @Column(DataType.TEXT)
  customInstructions: string;

  @Column(DataType.TEXT)
  persona: string;

  @Column(DataType.JSONB)
  doList: string[];

  @Column(DataType.JSONB)
  dontList: string[];

  @Default("openai")
  @Column(DataType.ENUM("openai", "crewai"))
  aiProvider: "openai" | "crewai";

  @Default(true)
  @Column
  isActive: boolean;

  @Default(false)
  @Column
  useKnowledgeBase: boolean;

  @ForeignKey(() => Company)
  @Column
  companyId: number;

  @BelongsTo(() => Company)
  company: Company;

  @ForeignKey(() => require("./Team").default)
  @Column
  teamId: number;

  @BelongsTo(() => require("./Team").default)
  team: any;

  @BelongsToMany(() => KnowledgeBase, () => AgentKnowledgeBase)
  knowledgeBases: KnowledgeBase[];

  @CreatedAt
  createdAt: Date;

  @UpdatedAt
  updatedAt: Date;
}

export default Agent;
