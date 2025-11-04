import { Request, Response } from "express";
import AgentLog from "../models/AgentLog";
import Agent from "../models/Agent";
import Team from "../models/Team";
import { Op, Sequelize } from "sequelize";
import sequelize from "../database";

// Listar logs com filtros e paginação
export const index = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const {
    teamId,
    agentId,
    page = 1,
    limit = 50,
    startDate,
    endDate,
    success
  } = req.query;

  const whereClause: any = { companyId };

  if (teamId) {
    whereClause.teamId = teamId;
  }

  if (agentId) {
    whereClause.agentId = agentId;
  }

  if (success !== undefined) {
    whereClause.success = success === 'true';
  }

  if (startDate || endDate) {
    whereClause.createdAt = {};
    if (startDate) {
      whereClause.createdAt[Op.gte] = new Date(startDate as string);
    }
    if (endDate) {
      whereClause.createdAt[Op.lte] = new Date(endDate as string);
    }
  }

  const offset = (Number(page) - 1) * Number(limit);

  const { count, rows: logs } = await AgentLog.findAndCountAll({
    where: whereClause,
    include: [
      {
        model: Agent,
        as: "agent",
        attributes: ["id", "name", "function"]
      },
      {
        model: Team,
        as: "team",
        attributes: ["id", "name"]
      }
    ],
    order: [["createdAt", "DESC"]],
    limit: Number(limit),
    offset
  });

  return res.json({
    logs,
    count,
    currentPage: Number(page),
    totalPages: Math.ceil(count / Number(limit))
  });
};

// Buscar log específico
export const show = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;

  const log = await AgentLog.findOne({
    where: { id: parseInt(id), companyId },
    include: [
      {
        model: Agent,
        as: "agent",
        attributes: ["id", "name", "function", "backstory", "persona"]
      },
      {
        model: Team,
        as: "team",
        attributes: ["id", "name", "processType", "temperature", "verbose"]
      }
    ]
  });

  if (!log) {
    return res.status(404).json({ error: "Log não encontrado" });
  }

  return res.json({ log });
};

// Criar novo log (será chamado pelo Python)
export const store = async (req: Request, res: Response): Promise<Response> => {
  const {
    companyId,
    teamId,
    agentId,
    message,
    response,
    agentConfig,
    teamConfig,
    promptUsed,
    processingTime,
    success,
    errorMessage,
    contactPhone,
    ticketId
  } = req.body;

  const log = await AgentLog.create({
    companyId,
    teamId,
    agentId,
    message,
    response,
    agentConfig,
    teamConfig,
    promptUsed,
    processingTime,
    success: success !== undefined ? success : true,
    errorMessage,
    contactPhone,
    ticketId
  });

  return res.status(201).json({ log });
};

// Deletar logs antigos (limpeza)
export const cleanup = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { daysOld = 30 } = req.body;

  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - Number(daysOld));

  const deletedCount = await AgentLog.destroy({
    where: {
      companyId,
      createdAt: {
        [Op.lt]: cutoffDate
      }
    }
  });

  return res.json({
    message: `${deletedCount} logs deletados com sucesso`,
    deletedCount
  });
};

// Estatísticas de logs
export const stats = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { teamId, startDate, endDate } = req.query;

  const whereClause: any = { companyId };

  if (teamId) {
    whereClause.teamId = teamId;
  }

  if (startDate || endDate) {
    whereClause.createdAt = {};
    if (startDate) {
      whereClause.createdAt[Op.gte] = new Date(startDate as string);
    }
    if (endDate) {
      whereClause.createdAt[Op.lte] = new Date(endDate as string);
    }
  }

  const totalLogs = await AgentLog.count({ where: whereClause });

  const successLogs = await AgentLog.count({
    where: { ...whereClause, success: true }
  });

  const failedLogs = await AgentLog.count({
    where: { ...whereClause, success: false }
  });

  const avgProcessingTime = await AgentLog.findOne({
    where: whereClause,
    attributes: [
      [Sequelize.fn('AVG', Sequelize.col('processingTime')), 'avgTime']
    ],
    raw: true
  }) as any;

  return res.json({
    totalLogs,
    successLogs,
    failedLogs,
    successRate: totalLogs > 0 ? ((successLogs / totalLogs) * 100).toFixed(2) : 0,
    avgProcessingTime: avgProcessingTime?.avgTime || 0
  });
};
