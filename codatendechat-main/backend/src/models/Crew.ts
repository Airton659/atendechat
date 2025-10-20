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
import Company from "./Company";

@Table
class Crew extends Model<Crew> {
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
    allowNull: false,
    unique: true,
    comment: "ID do blueprint no Firestore"
  })
  firestoreId: string;

  @Column({
    type: DataType.ENUM("draft", "active", "archived"),
    defaultValue: "draft"
  })
  status: string;

  @Column({
    type: DataType.STRING,
    allowNull: true
  })
  industry: string;

  @Column({
    type: DataType.TEXT,
    allowNull: true
  })
  objective: string;

  @Column({
    type: DataType.STRING,
    defaultValue: "professional"
  })
  tone: string;

  @Column({
    type: DataType.INTEGER,
    defaultValue: 0
  })
  totalConversations: number;

  @Column({
    type: DataType.FLOAT,
    defaultValue: 0
  })
  avgResponseTime: number;

  @Column({
    type: DataType.FLOAT,
    defaultValue: 0
  })
  satisfactionRate: number;

  @Column({
    type: DataType.DATE,
    allowNull: true
  })
  lastUsed: Date;

  @ForeignKey(() => Company)
  @Column
  companyId: number;

  @BelongsTo(() => Company)
  company: Company;

  @Column({
    type: DataType.INTEGER,
    allowNull: true
  })
  createdBy: number;

  @CreatedAt
  createdAt: Date;

  @UpdatedAt
  updatedAt: Date;
}

export default Crew;
