import express from "express";
import multer from "multer";
import isAuth from "../middleware/isAuth";

import * as KnowledgeBaseController from "../controllers/KnowledgeBaseController";

const knowledgeBaseRoutes = express.Router();

// Configurar multer para armazenar arquivos em memória
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB
  }
});

// Listar documentos de uma equipe
knowledgeBaseRoutes.get("/teams/:teamId/knowledge", isAuth, KnowledgeBaseController.index);

// Upload de documento
knowledgeBaseRoutes.post(
  "/teams/:teamId/knowledge/upload",
  isAuth,
  upload.single("file"),
  KnowledgeBaseController.upload
);

// Buscar documento específico
knowledgeBaseRoutes.get("/knowledge/:id", isAuth, KnowledgeBaseController.show);

// Deletar documento
knowledgeBaseRoutes.delete("/knowledge/:id", isAuth, KnowledgeBaseController.remove);

export default knowledgeBaseRoutes;
