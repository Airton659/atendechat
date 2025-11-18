import { Request, Response } from "express";
import AgentTrainingExample from "../models/AgentTrainingExample";
import Agent from "../models/Agent";
import Team from "../models/Team";
import { Op } from "sequelize";

// Listar exemplos de treinamento com filtros e paginação
export const index = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const {
    teamId,
    agentId,
    feedbackType,
    usedInPrompt,
    page = 1,
    limit = 50
  } = req.query;

  const whereClause: any = { companyId };

  if (teamId) {
    whereClause.teamId = teamId;
  }

  if (agentId) {
    whereClause.agentId = agentId;
  }

  if (feedbackType) {
    whereClause.feedbackType = feedbackType;
  }

  if (usedInPrompt !== undefined) {
    whereClause.usedInPrompt = usedInPrompt === 'true';
  }

  const offset = (Number(page) - 1) * Number(limit);

  const { count, rows: examples } = await AgentTrainingExample.findAndCountAll({
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
    order: [
      ["priority", "DESC"],
      ["createdAt", "DESC"]
    ],
    limit: Number(limit),
    offset
  });

  return res.json({
    examples,
    count,
    currentPage: Number(page),
    totalPages: Math.ceil(count / Number(limit))
  });
};

// Buscar exemplo específico
export const show = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;

  const example = await AgentTrainingExample.findOne({
    where: { id: parseInt(id), companyId },
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
    ]
  });

  if (!example) {
    return res.status(404).json({ error: "Exemplo não encontrado" });
  }

  return res.json({ example });
};

// Criar novo exemplo de treinamento (feedback)
export const store = async (req: Request, res: Response): Promise<Response> => {
  const { companyId, id: userId } = req.user;
  const {
    agentId,
    teamId,
    userMessage,
    agentResponse,
    correctedResponse,
    feedbackType,
    rating,
    feedbackNotes,
    priority,
    usedInPrompt,
    conversationContext
  } = req.body;

  // Validações
  if (!agentId || !userMessage || !agentResponse || !feedbackType) {
    return res.status(400).json({
      error: "Campos obrigatórios: agentId, userMessage, agentResponse, feedbackType"
    });
  }

  // Se feedbackType é "corrected", precisa ter correctedResponse
  if (feedbackType === "corrected" && !correctedResponse) {
    return res.status(400).json({
      error: "Campo correctedResponse é obrigatório quando feedbackType é 'corrected'"
    });
  }

  // Validar que o agente pertence à company
  const agent = await Agent.findOne({
    where: { id: agentId, companyId }
  });

  if (!agent) {
    return res.status(404).json({ error: "Agente não encontrado" });
  }

  // Determinar prioridade automaticamente se não fornecida
  let finalPriority = priority !== undefined ? priority : 5;

  if (feedbackType === "corrected") {
    finalPriority = priority !== undefined ? priority : 8;
  } else if (feedbackType === "rejected") {
    finalPriority = 0;
  }

  const example = await AgentTrainingExample.create({
    companyId,
    agentId,
    teamId: teamId || agent.teamId,
    userMessage,
    agentResponse,
    correctedResponse,
    feedbackType,
    rating,
    feedbackNotes,
    priority: finalPriority,
    usedInPrompt: feedbackType === "rejected" ? false : (usedInPrompt !== undefined ? usedInPrompt : true),
    conversationContext,
    createdBy: userId
  });

  return res.status(201).json({ example });
};

// Atualizar exemplo de treinamento
export const update = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;
  const {
    correctedResponse,
    feedbackType,
    rating,
    feedbackNotes,
    priority,
    usedInPrompt
  } = req.body;

  const example = await AgentTrainingExample.findOne({
    where: { id: parseInt(id), companyId }
  });

  if (!example) {
    return res.status(404).json({ error: "Exemplo não encontrado" });
  }

  // Atualizar campos
  if (correctedResponse !== undefined) example.correctedResponse = correctedResponse;
  if (feedbackType !== undefined) example.feedbackType = feedbackType;
  if (rating !== undefined) example.rating = rating;
  if (feedbackNotes !== undefined) example.feedbackNotes = feedbackNotes;
  if (priority !== undefined) example.priority = priority;
  if (usedInPrompt !== undefined) example.usedInPrompt = usedInPrompt;

  await example.save();

  return res.json({ example });
};

// Deletar exemplo de treinamento
export const remove = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;

  const example = await AgentTrainingExample.findOne({
    where: { id: parseInt(id), companyId }
  });

  if (!example) {
    return res.status(404).json({ error: "Exemplo não encontrado" });
  }

  await example.destroy();

  return res.json({ message: "Exemplo deletado com sucesso" });
};

// Exportar exemplos de um agente em formato JSON
export const exportExamples = async (req: Request, res: Response): Promise<Response> => {
  const { agentId } = req.params;
  const { companyId } = req.user;
  const { limit = 100 } = req.query;

  const agent = await Agent.findOne({
    where: { id: parseInt(agentId), companyId }
  });

  if (!agent) {
    return res.status(404).json({ error: "Agente não encontrado" });
  }

  const examples = await AgentTrainingExample.findAll({
    where: {
      agentId: parseInt(agentId),
      companyId,
      usedInPrompt: true
    },
    order: [
      ["priority", "DESC"],
      ["createdAt", "DESC"]
    ],
    limit: Number(limit)
  });

  const exportData = {
    agentId: agent.id,
    agentName: agent.name,
    exportedAt: new Date().toISOString(),
    totalExamples: examples.length,
    examples: examples.map(ex => ({
      userMessage: ex.userMessage,
      agentResponse: ex.agentResponse,
      correctedResponse: ex.correctedResponse,
      feedbackType: ex.feedbackType,
      feedbackNotes: ex.feedbackNotes,
      priority: ex.priority,
      createdAt: ex.createdAt
    }))
  };

  return res.json(exportData);
};

// Buscar exemplos relevantes para few-shot learning (usado pelo Python)
export const getRelevantExamples = async (req: Request, res: Response): Promise<Response> => {
  const { agentId } = req.params;
  const { limit = 5 } = req.query;

  const examples = await AgentTrainingExample.findAll({
    where: {
      agentId: parseInt(agentId),
      usedInPrompt: true,
      feedbackType: {
        [Op.in]: ["approved", "corrected"]
      }
    },
    attributes: [
      "id",
      "userMessage",
      "agentResponse",
      "correctedResponse",
      "feedbackType",
      "feedbackNotes",
      "priority"
    ],
    order: [
      ["priority", "DESC"],
      ["createdAt", "DESC"]
    ],
    limit: Number(limit)
  });

  return res.json({ examples });
};
