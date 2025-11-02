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

  @ForeignKey(() => Company)
  @Column
  companyId: number;

  @BelongsTo(() => Company)
  company: Company;

  @HasMany(() => Agent)
  agents: Agent[];

  @CreatedAt
  createdAt: Date;

  @UpdatedAt
  updatedAt: Date;
}

export default Team;
