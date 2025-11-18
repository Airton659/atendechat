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
import Agent from "./Agent";
import Team from "./Team";
import User from "./User";

@Table
class AgentTrainingExample extends Model<AgentTrainingExample> {
  @PrimaryKey
  @AutoIncrement
  @Column
  id: number;

  @ForeignKey(() => Agent)
  @Column
  agentId: number;

  @BelongsTo(() => Agent)
  agent: Agent;

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
    type: DataType.TEXT,
    allowNull: false,
    comment: "Mensagem original do usuário"
  })
  userMessage: string;

  @Column({
    type: DataType.TEXT,
    allowNull: false,
    comment: "Resposta original do agente"
  })
  agentResponse: string;

  @Column({
    type: DataType.TEXT,
    allowNull: true,
    comment: "Resposta corrigida (se aplicável)"
  })
  correctedResponse: string;

  @Default("approved")
  @Column({
    type: DataType.ENUM("approved", "corrected", "rejected"),
    allowNull: false,
    comment: "Tipo de feedback dado pelo usuário"
  })
  feedbackType: "approved" | "corrected" | "rejected";

  @Column({
    type: DataType.INTEGER,
    allowNull: true,
    comment: "Rating 1-5 (opcional)"
  })
  rating: number;

  @Column({
    type: DataType.TEXT,
    allowNull: true,
    comment: "Notas adicionais sobre o feedback"
  })
  feedbackNotes: string;

  @Default(5)
  @Column({
    type: DataType.INTEGER,
    allowNull: false,
    comment: "Prioridade 0-10 (maior = mais importante)"
  })
  priority: number;

  @Default(true)
  @Column({
    type: DataType.BOOLEAN,
    allowNull: false,
    comment: "Se deve ser usado como few-shot example"
  })
  usedInPrompt: boolean;

  @Column({
    type: DataType.JSONB,
    allowNull: true,
    comment: "Contexto adicional da conversa"
  })
  conversationContext: any;

  @ForeignKey(() => User)
  @Column
  createdBy: number;

  @BelongsTo(() => User)
  creator: User;

  @CreatedAt
  createdAt: Date;

  @UpdatedAt
  updatedAt: Date;
}

export default AgentTrainingExample;
