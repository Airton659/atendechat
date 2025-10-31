import * as Yup from "yup";
import { Request, Response } from "express";
import AppError from "../errors/AppError";

import ListAgentsService from "../services/AgentService/ListAgentsService";
import CreateAgentService from "../services/AgentService/CreateAgentService";
import ShowAgentService from "../services/AgentService/ShowAgentService";
import UpdateAgentService from "../services/AgentService/UpdateAgentService";
import DeleteAgentService from "../services/AgentService/DeleteAgentService";

type IndexQuery = {
  searchParam: string;
  pageNumber: string;
};

type AgentData = {
  name: string;
  function?: string;
  objective?: string;
  backstory?: string;
  keywords?: string[];
  customInstructions?: string;
  persona?: string;
  doList?: string[];
  dontList?: string[];
  aiProvider: "openai" | "crewai";
  isActive?: boolean;
};

export const index = async (req: Request, res: Response): Promise<Response> => {
  const { searchParam, pageNumber } = req.query as IndexQuery;
  const { companyId } = req.user;

  const { agents, count, hasMore } = await ListAgentsService({
    companyId,
    searchParam,
    pageNumber
  });

  return res.json({ agents, count, hasMore });
};

export const store = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const agentData: AgentData = req.body;

  const schema = Yup.object().shape({
    name: Yup.string().required("Nome é obrigatório"),
    aiProvider: Yup.string()
      .oneOf(["openai", "crewai"], "Provedor inválido")
      .required("Provedor é obrigatório")
  });

  try {
    await schema.validate(agentData);
  } catch (err: any) {
    throw new AppError(err.message);
  }

  const agent = await CreateAgentService({
    ...agentData,
    companyId
  });

  return res.status(200).json(agent);
};

export const show = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;

  const agent = await ShowAgentService({
    id: parseInt(id),
    companyId
  });

  return res.status(200).json(agent);
};

export const update = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;
  const agentData: AgentData = req.body;

  const schema = Yup.object().shape({
    name: Yup.string(),
    aiProvider: Yup.string().oneOf(["openai", "crewai"], "Provedor inválido")
  });

  try {
    await schema.validate(agentData);
  } catch (err: any) {
    throw new AppError(err.message);
  }

  const agent = await UpdateAgentService({
    id: parseInt(id),
    companyId,
    ...agentData
  });

  return res.status(200).json(agent);
};

export const remove = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;

  await DeleteAgentService({
    id: parseInt(id),
    companyId
  });

  return res.status(200).json({ message: "Agent deleted successfully" });
};
