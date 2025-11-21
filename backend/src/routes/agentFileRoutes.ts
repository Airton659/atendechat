import express from "express";
import multer from "multer";
import isAuth from "../middleware/isAuth";
import uploadConfig from "../config/uploadAgentFiles";

import * as AgentFileController from "../controllers/AgentFileController";

const upload = multer(uploadConfig);

const agentFileRoutes = express.Router();

// Listar arquivos de um agente (autenticado - para frontend)
agentFileRoutes.get("/agents/:agentId/files", isAuth, AgentFileController.index);

// Listar arquivos de um agente (interno - para CrewAI sem auth)
agentFileRoutes.get("/agent-files/agent/:agentId", AgentFileController.index);

// Upload de arquivo para um agente
agentFileRoutes.post(
  "/agents/:agentId/files",
  isAuth,
  upload.single("file"),
  AgentFileController.store
);

// Mostrar arquivo específico
agentFileRoutes.get("/agent-files/:id", isAuth, AgentFileController.show);

// Atualizar descrição do arquivo
agentFileRoutes.put("/agent-files/:id", isAuth, AgentFileController.update);

// Deletar arquivo
agentFileRoutes.delete("/agent-files/:id", isAuth, AgentFileController.remove);

// Download de arquivo
agentFileRoutes.get("/agent-files/:id/download", isAuth, AgentFileController.download);

export default agentFileRoutes;
