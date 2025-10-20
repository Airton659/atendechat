import { Request, Response } from "express";
import axios from "axios";

import ListCrewsService from "../services/CrewService/ListCrewsService";
import CreateCrewService from "../services/CrewService/CreateCrewService";
import Crew from "../models/Crew";
import AppError from "../errors/AppError";

const crewaiUrl = process.env.CREWAI_API_URL || "http://localhost:8000";

export const index = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;

  const crews = await ListCrewsService({ companyId });

  return res.status(200).json(crews);
};

export const store = async (req: Request, res: Response): Promise<Response> => {
  const { companyId, id: userId } = req.user;
  const { name, description, industry, objective, tone } = req.body;

  const crew = await CreateCrewService({
    name,
    description,
    companyId,
    userId,
    industry,
    objective,
    tone
  });

  return res.status(201).json(crew);
};

export const show = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { crewId } = req.params;

  const crew = await Crew.findOne({
    where: { id: crewId, companyId }
  });

  if (!crew) {
    throw new AppError("ERR_CREW_NOT_FOUND", 404);
  }

  // Buscar detalhes completos no CrewAI Service
  try {
    const response = await axios.get(
      `${crewaiUrl}/api/v2/crews/${crew.firestoreId}`
    );

    return res.status(200).json({
      ...crew.toJSON(),
      blueprint: response.data
    });
  } catch (error) {
    console.error("Erro ao buscar blueprint:", error);
    return res.status(200).json(crew);
  }
};

export const update = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { crewId } = req.params;
  const { name, description, status, blueprint } = req.body;

  const crew = await Crew.findOne({
    where: { id: crewId, companyId }
  });

  if (!crew) {
    throw new AppError("ERR_CREW_NOT_FOUND", 404);
  }

  // Atualizar no banco local
  await crew.update({
    name: name || crew.name,
    description: description || crew.description,
    status: status || crew.status
  });

  // Se forneceu blueprint, atualizar no CrewAI Service
  if (blueprint) {
    try {
      await axios.put(
        `${crewaiUrl}/api/v2/crews/${crew.firestoreId}`,
        blueprint
      );
    } catch (error) {
      console.error("Erro ao atualizar blueprint:", error);
      throw new AppError("ERR_UPDATING_CREW_BLUEPRINT", 500);
    }
  }

  return res.status(200).json(crew);
};

export const remove = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { crewId } = req.params;

  const crew = await Crew.findOne({
    where: { id: crewId, companyId }
  });

  if (!crew) {
    throw new AppError("ERR_CREW_NOT_FOUND", 404);
  }

  // Deletar do CrewAI Service
  try {
    await axios.delete(`${crewaiUrl}/api/v2/crews/${crew.firestoreId}`);
  } catch (error) {
    console.error("Erro ao deletar do CrewAI Service:", error);
  }

  await crew.destroy();

  return res.status(200).json({ message: "Crew deleted" });
};

// Gerar equipe usando o Arquiteto IA
export const generateTeam = async (req: Request, res: Response): Promise<Response> => {
  const { companyId, id: userId } = req.user;
  const { businessDescription, industry, teamName } = req.body;

  try {
    const response = await axios.post(
      `${crewaiUrl}/api/v2/architect/generate-team`,
      {
        businessDescription,
        industry,
        tenantId: `company_${companyId}`,
        teamName
      }
    );

    // Salvar no banco local
    const crew = await CreateCrewService({
      name: teamName || response.data.blueprint.name,
      description: businessDescription,
      companyId,
      userId,
      firestoreId: response.data.blueprint.id || `crew_${Date.now()}`,
      status: "draft",
      industry: industry || response.data.analysis?.industry,
      objective: businessDescription,
      tone: response.data.blueprint.config?.tone || "professional"
    });

    return res.status(201).json({
      crew,
      blueprint: response.data.blueprint,
      analysis: response.data.analysis,
      suggestions: response.data.suggestions
    });
  } catch (error: any) {
    console.error("Erro ao gerar equipe:", error);
    throw new AppError(
      error.response?.data?.message || "ERR_GENERATING_TEAM",
      error.response?.status || 500
    );
  }
};

// Treinar equipe
export const train = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { crewId } = req.params;
  const { message, conversationHistory } = req.body;

  const crew = await Crew.findOne({
    where: { id: crewId, companyId }
  });

  if (!crew) {
    throw new AppError("ERR_CREW_NOT_FOUND", 404);
  }

  try {
    const response = await axios.post(
      `${crewaiUrl}/api/v2/training/generate-response`,
      {
        tenantId: `company_${companyId}`,
        teamId: crew.firestoreId,
        message,
        conversationHistory: conversationHistory || []
      }
    );

    return res.status(200).json(response.data);
  } catch (error: any) {
    console.error("Erro ao treinar equipe:", error);
    throw new AppError(
      error.response?.data?.message || "ERR_TRAINING_CREW",
      error.response?.status || 500
    );
  }
};
