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
  BelongsTo
} from "sequelize-typescript";
import Company from "./Company";
import Team from "./Team";
import Agent from "./Agent";

@Table
class AgentLog extends Model<AgentLog> {
  @PrimaryKey
  @AutoIncrement
  @Column
  id: number;

  @ForeignKey(() => Company)
  @Column
  companyId: number;

  @BelongsTo(() => Company)
  company: Company;

  @ForeignKey(() => Team)
  @Column
  teamId: number;

  @BelongsTo(() => Team)
  team: Team;

  @ForeignKey(() => Agent)
  @Column
  agentId: number;

  @BelongsTo(() => Agent)
  agent: Agent;

  @Column({
    type: DataType.TEXT,
    allowNull: false
  })
  message: string;

  @Column({
    type: DataType.TEXT,
    allowNull: false
  })
  response: string;

  @Column({
    type: DataType.JSON,
    allowNull: true
  })
  agentConfig: any;

  @Column({
    type: DataType.JSON,
    allowNull: true
  })
  teamConfig: any;

  @Column({
    type: DataType.TEXT,
    allowNull: true
  })
  promptUsed: string;

  @Column({
    type: DataType.FLOAT,
    allowNull: true
  })
  processingTime: number;

  @Column({
    type: DataType.BOOLEAN,
    allowNull: false,
    defaultValue: true
  })
  success: boolean;

  @Column({
    type: DataType.TEXT,
    allowNull: true
  })
  errorMessage: string;

  @Column({
    type: DataType.STRING,
    allowNull: true
  })
  contactPhone: string;

  @Column({
    type: DataType.INTEGER,
    allowNull: true
  })
  ticketId: number;

  @CreatedAt
  createdAt: Date;

  @UpdatedAt
  updatedAt: Date;
}

export default AgentLog;
