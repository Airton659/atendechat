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
  BelongsToMany
} from "sequelize-typescript";
import Team from "./Team";
import Company from "./Company";
import Agent from "./Agent";
import AgentKnowledgeBase from "./AgentKnowledgeBase";

@Table
class KnowledgeBase extends Model<KnowledgeBase> {
  @PrimaryKey
  @AutoIncrement
  @Column
  id: number;

  @ForeignKey(() => Team)
  @Column
  teamId: number;

  @BelongsTo(() => Team)
  team: Team;

  @ForeignKey(() => Company)
  @Column
  companyId: number;

  @BelongsTo(() => Company)
  company: Company;

  @Column({
    type: DataType.STRING(255),
    allowNull: false,
    unique: true
  })
  documentId: string;

  @Column({
    type: DataType.STRING(255),
    allowNull: false
  })
  filename: string;

  @Column({
    type: DataType.STRING(50),
    allowNull: false
  })
  fileType: string;

  @Column({
    type: DataType.INTEGER,
    allowNull: false
  })
  fileSize: number;

  @Column(DataType.TEXT)
  filePath: string;

  @Column({
    type: DataType.INTEGER,
    defaultValue: 0
  })
  chunksCount: number;

  @Column({
    type: DataType.INTEGER,
    defaultValue: 0
  })
  wordCount: number;

  @Column({
    type: DataType.STRING(50),
    defaultValue: "processing"
  })
  status: string;

  @Column(DataType.TEXT)
  errorMessage: string;

  @Column(DataType.DATE)
  uploadedAt: Date;

  @Column(DataType.DATE)
  processedAt: Date;

  @BelongsToMany(() => Agent, () => AgentKnowledgeBase)
  agents: Agent[];

  @CreatedAt
  createdAt: Date;

  @UpdatedAt
  updatedAt: Date;
}

export default KnowledgeBase;
