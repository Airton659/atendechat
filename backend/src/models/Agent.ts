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
  DataType,
  Default
} from "sequelize-typescript";
import Company from "./Company";

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

  @Column(DataType.ENUM("openai", "crewai"))
  @Default("openai")
  aiProvider: "openai" | "crewai";

  @Column
  @Default(true)
  isActive: boolean;

  @ForeignKey(() => Company)
  @Column
  companyId: number;

  @BelongsTo(() => Company)
  company: Company;

  @CreatedAt
  createdAt: Date;

  @UpdatedAt
  updatedAt: Date;
}

export default Agent;
