import * as Yup from "yup";
import { Request, Response } from "express";
import axios from "axios";
import AppError from "../errors/AppError";

import ListAgentsService from "../services/AgentService/ListAgentsService";
import CreateAgentService from "../services/AgentService/CreateAgentService";
import ShowAgentService from "../services/AgentService/ShowAgentService";
import UpdateAgentService from "../services/AgentService/UpdateAgentService";
import DeleteAgentService from "../services/AgentService/DeleteAgentService";

const architectUrl = process.env.ARCHITECT_API_URL || "http://localhost:8001";

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

// Gerar agentes usando o Arquiteto IA
export const generateTeam = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { businessDescription, industry } = req.body;

  console.log("[AgentController.generateTeam] Iniciando geração de agentes");
  console.log(`  CompanyId: ${companyId}`);
  console.log(`  Industry: ${industry}`);
  console.log(`  Description: ${businessDescription?.substring(0, 100)}...`);

  if (!businessDescription) {
    throw new AppError("Descrição do negócio é obrigatória", 400);
  }

  try {
    // Chamar serviço Python Architect
    console.log(`[AgentController.generateTeam] Chamando Architect API: ${architectUrl}/api/v2/architect/generate-team`);

    const { data } = await axios.post(
      `${architectUrl}/api/v2/architect/generate-team`,
      {
        businessDescription,
        industry: industry || "other",
        companyId
      },
      {
        timeout: 60000 // 60 segundos timeout
      }
    );

    console.log(`[AgentController.generateTeam] Resposta do Architect recebida`);
    console.log(`  Agentes gerados: ${data.blueprint?.agents?.length || 0}`);

    // Salvar cada agente no PostgreSQL
    const savedAgents = [];

    if (data.blueprint?.agents && Array.isArray(data.blueprint.agents)) {
      for (const agentData of data.blueprint.agents) {
        console.log(`[AgentController.generateTeam] Salvando agente: ${agentData.name}`);

        const agent = await CreateAgentService({
          name: agentData.name,
          function: agentData.function || agentData.role,
          objective: agentData.objective || agentData.goal,
          backstory: agentData.backstory,
          keywords: agentData.keywords || [],
          customInstructions: agentData.customInstructions,
          persona: agentData.persona,
          doList: agentData.doList || [],
          dontList: agentData.dontList || [],
          aiProvider: "crewai",
          isActive: agentData.isActive !== false,
          companyId
        });

        savedAgents.push(agent);
      }
    }

    console.log(`[AgentController.generateTeam] Salvos ${savedAgents.length} agentes no PostgreSQL`);

    // Retornar resposta formatada para o frontend
    return res.status(201).json({
      blueprint: {
        agents: savedAgents,
        customTools: data.blueprint?.customTools || []
      },
      analysis: data.analysis,
      suggestions: data.suggestions,
      next_steps: data.next_steps
    });

  } catch (error: any) {
    console.error("[AgentController.generateTeam] Erro:", error.message);

    if (error.response) {
      console.error("  Response status:", error.response.status);
      console.error("  Response data:", error.response.data);

      throw new AppError(
        error.response.data?.detail || error.response.data?.message || "Erro ao gerar agentes com IA",
        error.response.status || 500
      );
    }

    if (error.code === "ECONNREFUSED") {
      throw new AppError(
        "Serviço de IA não disponível. Verifique se o Architect API está rodando.",
        503
      );
    }

    throw new AppError(
      error.message || "Erro ao gerar agentes com IA",
      500
    );
  }
};
