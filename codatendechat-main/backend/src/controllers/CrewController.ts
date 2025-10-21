import { Request, Response } from "express";
import axios from "axios";
import FormData from "form-data";
import AppError from "../errors/AppError";

const crewaiUrl = process.env.CREWAI_API_URL || "http://localhost:8000";

// Listar todas as crews
export const index = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const tenantId = `company_${companyId}`;

  try {
    const { data } = await axios.get(`${crewaiUrl}/api/v2/crews`, {
      params: { tenantId }
    });

    return res.status(200).json(data);
  } catch (error: any) {
    console.error("Erro ao listar crews:", error);
    throw new AppError(
      error.response?.data?.message || "ERR_LISTING_CREWS",
      error.response?.status || 500
    );
  }
};

// Criar nova crew (manual)
export const store = async (req: Request, res: Response): Promise<Response> => {
  const { companyId, id: userId } = req.user;
  const tenantId = `company_${companyId}`;

  try {
    const { data } = await axios.post(`${crewaiUrl}/api/v2/crews`, {
      ...req.body,
      tenantId,
      createdBy: userId
    });

    return res.status(201).json(data);
  } catch (error: any) {
    console.error("Erro ao criar crew:", error);
    throw new AppError(
      error.response?.data?.message || "ERR_CREATING_CREW",
      error.response?.status || 500
    );
  }
};

// Buscar crew por ID
export const show = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { crewId } = req.params;
  const tenantId = `company_${companyId}`;

  try {
    const { data } = await axios.get(`${crewaiUrl}/api/v2/crews/${crewId}`, {
      params: { tenantId }
    });

    return res.status(200).json(data);
  } catch (error: any) {
    console.error("Erro ao buscar crew:", error);
    throw new AppError(
      error.response?.data?.message || "ERR_CREW_NOT_FOUND",
      error.response?.status || 404
    );
  }
};

// Atualizar crew
export const update = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { crewId } = req.params;
  const tenantId = `company_${companyId}`;

  try {
    const { data } = await axios.put(
      `${crewaiUrl}/api/v2/crews/${crewId}`,
      {
        ...req.body,
        tenantId
      }
    );

    return res.status(200).json(data);
  } catch (error: any) {
    console.error("Erro ao atualizar crew:", error);
    throw new AppError(
      error.response?.data?.message || "ERR_UPDATING_CREW",
      error.response?.status || 500
    );
  }
};

// Deletar crew
export const remove = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { crewId } = req.params;
  const tenantId = `company_${companyId}`;

  try {
    await axios.delete(`${crewaiUrl}/api/v2/crews/${crewId}`, {
      params: { tenantId }
    });

    return res.status(200).json({ message: "Crew deleted successfully" });
  } catch (error: any) {
    console.error("Erro ao deletar crew:", error);
    throw new AppError(
      error.response?.data?.message || "ERR_DELETING_CREW",
      error.response?.status || 500
    );
  }
};

// Gerar equipe usando o Arquiteto IA
export const generateTeam = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { businessDescription, industry } = req.body;
  const tenantId = `company_${companyId}`;

  try {
    const { data } = await axios.post(
      `${crewaiUrl}/api/v2/architect/generate-team`,
      {
        businessDescription,
        industry,
        tenantId
      }
    );

    // Transformar agents de objeto para array para o frontend
    const blueprint = {
      ...data.blueprint,
      agents: data.blueprint.agents
        ? Object.values(data.blueprint.agents)
        : []
    };

    return res.status(201).json({
      id: data.id,
      blueprint,
      analysis: data.analysis,
      suggestions: data.suggestions,
      next_steps: data.next_steps
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
  const tenantId = `company_${companyId}`;

  try {
    const { data } = await axios.post(
      `${crewaiUrl}/api/v2/training/generate-response`,
      {
        tenantId,
        teamId: crewId,
        message,
        conversationHistory: conversationHistory || []
      }
    );

    return res.status(200).json(data);
  } catch (error: any) {
    console.error("Erro ao treinar crew:", error);
    throw new AppError(
      error.response?.data?.message || "ERR_TRAINING_CREW",
      error.response?.status || 500
    );
  }
};

// Upload de arquivo de conhecimento
export const uploadKnowledge = async (
  req: Request,
  res: Response
): Promise<Response> => {
  const { companyId } = req.user;
  const { crewId } = req.params;
  const tenantId = `company_${companyId}`;

  if (!req.file) {
    throw new AppError("ERR_NO_FILE_UPLOADED", 400);
  }

  try {
    const formData = new FormData();
    formData.append("file", req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype,
    });
    formData.append("tenantId", tenantId);
    formData.append("teamId", crewId);

    const { data } = await axios.post(
      `${crewaiUrl}/api/v2/knowledge/upload`,
      formData,
      {
        headers: formData.getHeaders(),
      }
    );

    return res.status(200).json(data);
  } catch (error: any) {
    console.error("Erro ao fazer upload:", error);
    throw new AppError(
      error.response?.data?.message || "ERR_UPLOADING_FILE",
      error.response?.status || 500
    );
  }
};

// Deletar arquivo de conhecimento
export const deleteKnowledge = async (
  req: Request,
  res: Response
): Promise<Response> => {
  const { companyId } = req.user;
  const { crewId, fileId } = req.params;
  const tenantId = `company_${companyId}`;

  try {
    await axios.delete(
      `${crewaiUrl}/api/v2/knowledge/${fileId}`,
      {
        params: { tenantId, teamId: crewId }
      }
    );

    return res.status(200).json({ message: "Knowledge file deleted" });
  } catch (error: any) {
    console.error("Erro ao deletar conhecimento:", error);
    throw new AppError(
      error.response?.data?.message || "ERR_DELETING_KNOWLEDGE",
      error.response?.status || 500
    );
  }
};
