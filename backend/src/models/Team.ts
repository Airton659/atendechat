import {
  Table,
  Column,
  CreatedAt,
  UpdatedAt,
  Model,
  DataType,
  PrimaryKey,
  AutoIncrement,
  ForeignKey,
  BelongsTo,
  HasMany
} from "sequelize-typescript";
import Company from "./Company";
import Agent from "./Agent";

@Table
class Team extends Model<Team> {
  @PrimaryKey
  @AutoIncrement
  @Column
  id: number;

  @Column({
    type: DataType.STRING,
    allowNull: false
  })
  name: string;

  @Column({
    type: DataType.TEXT,
    allowNull: true
  })
  description: string;

  @Column({
    type: DataType.STRING,
    allowNull: true
  })
  industry: string;

  @Column({
    type: DataType.BOOLEAN,
    allowNull: false,
    defaultValue: true
  })
  isActive: boolean;

  @Column({
    type: DataType.ENUM("manual", "architect"),
    allowNull: false,
    defaultValue: "manual"
  })
  generatedBy: "manual" | "architect";

  // Configurações avançadas CrewAI
  @Column({
    type: DataType.ENUM("sequential", "hierarchical"),
    allowNull: false,
    defaultValue: "sequential"
  })
  processType: "sequential" | "hierarchical";

  @Column({
    type: DataType.STRING,
    allowNull: true,
    comment: "LLM usado pelo manager no modo hierarchical (ex: gemini-2.0-flash-lite)"
  })
  managerLLM: string;

  @Column({
    type: DataType.FLOAT,
    allowNull: false,
    defaultValue: 0.7,
    validate: {
      min: 0,
      max: 2
    }
  })
  temperature: number;

  @Column({
    type: DataType.BOOLEAN,
    allowNull: false,
    defaultValue: true
  })
  verbose: boolean;

  @Column({
    type: DataType.INTEGER,
    allowNull: true,
    comment: "Agente ID que atua como manager no modo hierarchical"
  })
  managerAgentId: number;

  @ForeignKey(() => Company)
  @Column
  companyId: number;

  @BelongsTo(() => Company)
  company: Company;

  @HasMany(() => Agent, "teamId")
  agents: Agent[];

  @CreatedAt
  createdAt: Date;

  @UpdatedAt
  updatedAt: Date;
}

export default Team;
