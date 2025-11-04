import * as Yup from "yup";
import { Request, Response } from "express";
import axios from "axios";
import FormData from "form-data";
import AppError from "../errors/AppError";
import KnowledgeBase from "../models/KnowledgeBase";
import Team from "../models/Team";

const crewaiApiUrl = process.env.CREWAI_API_URL || "http://localhost:8001";

// Listar documentos de uma equipe
export const index = async (req: Request, res: Response): Promise<Response> => {
  const { teamId } = req.params;
  const { companyId } = req.user;

  // Verificar se a equipe pertence à empresa
  const team = await Team.findOne({
    where: { id: parseInt(teamId), companyId }
  });

  if (!team) {
    throw new AppError("Equipe não encontrada", 404);
  }

  const knowledgeBases = await KnowledgeBase.findAll({
    where: { teamId: parseInt(teamId), companyId },
    order: [["createdAt", "DESC"]]
  });

  return res.json({ knowledgeBases, count: knowledgeBases.length });
};

// Upload de documento para a base de conhecimento
export const upload = async (req: Request, res: Response): Promise<Response> => {
  const { teamId } = req.params;
  const { companyId } = req.user;

  // Verificar se a equipe pertence à empresa
  const team = await Team.findOne({
    where: { id: parseInt(teamId), companyId }
  });

  if (!team) {
    throw new AppError("Equipe não encontrada", 404);
  }

  // Verificar se foi enviado um arquivo
  if (!req.file) {
    throw new AppError("Nenhum arquivo foi enviado", 400);
  }

  const file = req.file;

  // Validar tipo de arquivo
  const allowedTypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain"
  ];

  if (!allowedTypes.includes(file.mimetype)) {
    throw new AppError("Tipo de arquivo não permitido. Use PDF, DOCX ou TXT.", 400);
  }

  // Validar tamanho (max 10MB)
  if (file.size > 10 * 1024 * 1024) {
    throw new AppError("Arquivo muito grande. Tamanho máximo: 10MB", 400);
  }

  try {
    // Criar FormData para enviar ao Python service
    const formData = new FormData();
    formData.append("file", file.buffer, {
      filename: file.originalname,
      contentType: file.mimetype
    });
    formData.append("team_id", teamId);
    formData.append("company_id", companyId.toString());

    // Enviar para o serviço Python
    const response = await axios.post(
      `${crewaiApiUrl}/api/v2/knowledge/upload`,
      formData,
      {
        headers: formData.getHeaders(),
        timeout: 60000 // 60 segundos
      }
    );

    const { document_id, chunks_count, word_count } = response.data;

    // Determinar tipo de arquivo
    let fileType = "txt";
    if (file.mimetype === "application/pdf") {
      fileType = "pdf";
    } else if (file.mimetype === "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
      fileType = "docx";
    }

    // Criar registro no banco de dados
    const knowledgeBase = await KnowledgeBase.create({
      teamId: parseInt(teamId),
      companyId,
      documentId: document_id,
      filename: file.originalname,
      fileType,
      fileSize: file.size,
      chunksCount: chunks_count,
      wordCount: word_count,
      status: "ready"
    });

    return res.status(201).json(knowledgeBase);
  } catch (error: any) {
    console.error("Erro ao processar documento:", error);

    if (error.response) {
      throw new AppError(
        error.response.data?.error || "Erro ao processar documento",
        error.response.status
      );
    }

    throw new AppError("Erro ao processar documento", 500);
  }
};

// Deletar documento da base de conhecimento
export const remove = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;

  const knowledgeBase = await KnowledgeBase.findOne({
    where: { id: parseInt(id), companyId }
  });

  if (!knowledgeBase) {
    throw new AppError("Documento não encontrado", 404);
  }

  try {
    // Deletar do serviço Python (Firestore)
    await axios.delete(
      `${crewaiApiUrl}/api/v2/knowledge/documents/${knowledgeBase.documentId}`,
      { timeout: 30000 }
    );
  } catch (error: any) {
    console.error("Erro ao deletar documento do Firestore:", error);
    // Continuar mesmo se falhar, para limpar o banco
  }

  // Deletar do banco de dados
  await knowledgeBase.destroy();

  return res.status(200).json({ message: "Documento deletado com sucesso" });
};

// Buscar documento por ID
export const show = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { companyId } = req.user;

  const knowledgeBase = await KnowledgeBase.findOne({
    where: { id: parseInt(id), companyId }
  });

  if (!knowledgeBase) {
    throw new AppError("Documento não encontrado", 404);
  }

  return res.status(200).json(knowledgeBase);
};
