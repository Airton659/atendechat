import { Request, Response } from "express";
import * as path from "path";
import * as fs from "fs";
import AppError from "../errors/AppError";

import CreateAgentFileService from "../services/AgentFileService/CreateAgentFileService";
import ListAgentFilesService from "../services/AgentFileService/ListAgentFilesService";
import ShowAgentFileService from "../services/AgentFileService/ShowAgentFileService";
import UpdateAgentFileService from "../services/AgentFileService/UpdateAgentFileService";
import DeleteAgentFileService from "../services/AgentFileService/DeleteAgentFileService";

// Listar arquivos de um agente
export const index = async (req: Request, res: Response): Promise<Response> => {
  const { agentId } = req.params;

  const files = await ListAgentFilesService({
    agentId: parseInt(agentId)
  });

  return res.json(files);
};

// Upload de arquivo para um agente
export const store = async (req: Request, res: Response): Promise<Response> => {
  const { agentId } = req.params;
  const { description } = req.body;

  if (!req.file) {
    throw new AppError("Nenhum arquivo enviado", 400);
  }

  const file = req.file;
  const originalName = file.originalname;
  const fileName = file.filename;
  const filePath = `agent-files/${fileName}`;
  const mimeType = file.mimetype;
  const fileSize = file.size;

  // Determinar tipo do arquivo
  let fileType = "other";
  if (mimeType === "application/pdf") {
    fileType = "pdf";
  } else if (mimeType.startsWith("image/")) {
    fileType = "image";
  }

  // Validar tipos permitidos
  const allowedMimeTypes = [
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg"
  ];

  if (!allowedMimeTypes.includes(mimeType)) {
    // Remove arquivo se não for permitido
    const fullPath = path.join(__dirname, "..", "..", "public", filePath);
    if (fs.existsSync(fullPath)) {
      fs.unlinkSync(fullPath);
    }
    throw new AppError("Tipo de arquivo não permitido. Use PDF, PNG ou JPG.", 400);
  }

  const agentFile = await CreateAgentFileService({
    agentId: parseInt(agentId),
    fileName,
    originalName,
    filePath,
    fileType,
    mimeType,
    fileSize,
    description
  });

  return res.status(201).json(agentFile);
};

// Mostrar um arquivo específico
export const show = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;

  const agentFile = await ShowAgentFileService(parseInt(id));

  return res.json(agentFile);
};

// Atualizar descrição do arquivo
export const update = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;
  const { description } = req.body;

  const agentFile = await UpdateAgentFileService({
    id: parseInt(id),
    description
  });

  return res.json(agentFile);
};

// Deletar arquivo
export const remove = async (req: Request, res: Response): Promise<Response> => {
  const { id } = req.params;

  await DeleteAgentFileService(parseInt(id));

  return res.json({ message: "Arquivo deletado com sucesso" });
};

// Download de arquivo
export const download = async (req: Request, res: Response): Promise<void> => {
  const { id } = req.params;

  const agentFile = await ShowAgentFileService(parseInt(id));
  const filePath = path.join(__dirname, "..", "..", "public", agentFile.filePath);

  if (!fs.existsSync(filePath)) {
    throw new AppError("Arquivo não encontrado no servidor", 404);
  }

  res.download(filePath, agentFile.originalName);
};
