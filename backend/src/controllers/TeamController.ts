import * as Yup from "yup";
import { Request, Response } from "express";
import axios from "axios";
import AppError from "../errors/AppError";
import Team from "../models/Team";
import Agent from "../models/Agent";

const architectUrl = process.env.ARCHITECT_API_URL || "http://localhost:8001";

// Listar todas as equipes
export const index = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;

  const teams = await Team.findAll({
    where: { companyId },
    include: [
      {
        model: Agent,
        as: "agents"
      }
    ],
    order: [["createdAt", "DESC"]]
  });

  return res.json({ teams, count: teams.length });
};

// Criar equipe manualmente
export const store = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { name, description, industry } = req.body;

  const schema = Yup.object().shape({
    name: Yup.string().required("Nome é obrigatório")
  });

  try {
    await schema.validate({ name });
  } catch (err: any) {
    throw new AppError(err.message);
  }

  const team = await Team.create({
    name,
    description: description || "",
    industry: industry || "other",
    isActive: true,
    generatedBy: "manual",
    companyId
  });

  return res.status(201).json(team);
};

// Buscar equipe por ID com seus agentes
export const show = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;

  const team = await Team.findOne({
    where: { id: parseInt(id), companyId },
    include: [
      {
        model: Agent,
        as: "agents"
      }
    ]
  });

  if (!team) {
    throw new AppError("Equipe não encontrada", 404);
  }

  return res.status(200).json({ team });
};

// Atualizar equipe
export const update = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;
  const { name, description, industry, isActive } = req.body;

  const team = await Team.findOne({
    where: { id: parseInt(id), companyId }
  });

  if (!team) {
    throw new AppError("Equipe não encontrada", 404);
  }

  await team.update({
    name: name || team.name,
    description: description !== undefined ? description : team.description,
    industry: industry || team.industry,
    isActive: isActive !== undefined ? isActive : team.isActive
  });

  return res.status(200).json(team);
};

// Deletar equipe
export const remove = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;

  const team = await Team.findOne({
    where: { id: parseInt(id), companyId }
  });

  if (!team) {
    throw new AppError("Equipe não encontrada", 404);
  }

  // Deletar todos os agentes da equipe também
  await Agent.destroy({
    where: { teamId: parseInt(id) }
  });

  await team.destroy();

  return res.status(200).json({ message: "Equipe deletada com sucesso" });
};

// Gerar equipe usando o Arquiteto IA
export const generateTeam = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { businessDescription, industry, teamName } = req.body;

  console.log("[TeamController.generateTeam] Iniciando geração de equipe");
  console.log(`  CompanyId: ${companyId}`);
  console.log(`  Industry: ${industry}`);
  console.log(`  TeamName: ${teamName}`);

  if (!businessDescription) {
    throw new AppError("Descrição do negócio é obrigatória", 400);
  }

  try {
    // Chamar serviço Python Architect
    console.log(`[TeamController.generateTeam] Chamando Architect API: ${architectUrl}/api/v2/architect/generate-team`);

    const { data } = await axios.post(
      `${architectUrl}/api/v2/architect/generate-team`,
      {
        businessDescription,
        industry: industry || "other",
        companyId
      },
      {
        timeout: 60000
      }
    );

    console.log(`[TeamController.generateTeam] Resposta do Architect recebida`);
    console.log(`  Agentes gerados: ${data.blueprint?.agents?.length || 0}`);

    // Criar a equipe
    const team = await Team.create({
      name: teamName || `Equipe ${industry || "Geral"}`,
      description: businessDescription.substring(0, 500),
      industry: industry || "other",
      isActive: true,
      generatedBy: "architect",
      companyId
    });

    console.log(`[TeamController.generateTeam] Equipe criada: ${team.id}`);

    // Salvar cada agente no PostgreSQL vinculado à equipe
    const savedAgents = [];

    if (data.blueprint?.agents && Array.isArray(data.blueprint.agents)) {
      for (const agentData of data.blueprint.agents) {
        console.log(`[TeamController.generateTeam] Salvando agente: ${agentData.name}`);

        const agent = await Agent.create({
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
          companyId,
          teamId: team.id
        });

        savedAgents.push(agent);
      }
    }

    console.log(`[TeamController.generateTeam] Salvos ${savedAgents.length} agentes no PostgreSQL`);

    // Buscar equipe com agentes para retornar
    const teamWithAgents = await Team.findByPk(team.id, {
      include: [{ model: Agent, as: "agents" }]
    });

    return res.status(201).json({
      team: teamWithAgents,
      analysis: data.analysis,
      suggestions: data.suggestions,
      next_steps: data.next_steps
    });

  } catch (error: any) {
    console.error("[TeamController.generateTeam] Erro:", error.message);

    if (error.response) {
      console.error("  Response status:", error.response.status);
      console.error("  Response data:", error.response.data);

      throw new AppError(
        error.response.data?.detail || error.response.data?.message || "Erro ao gerar equipe com IA",
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
      error.message || "Erro ao gerar equipe com IA",
      500
    );
  }
};
