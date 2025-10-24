import express from "express";
import isAuth from "../middleware/isAuth";
import uploadConfig from "../config/upload";
import multer from "multer";

import * as CrewController from "../controllers/CrewController";

const upload = multer(uploadConfig);
// Upload para knowledge base usa memoryStorage para enviar buffer ao CrewAI
const knowledgeUpload = multer({ storage: multer.memoryStorage() });
const crewRoutes = express.Router();

// Listar equipes
crewRoutes.get("/crews", isAuth, CrewController.index);

// Criar equipe
crewRoutes.post("/crews", isAuth, CrewController.store);

// Gerar equipe com IA (Arquiteto)
crewRoutes.post("/crews/generate", isAuth, CrewController.generateTeam);

// Detalhes da equipe
crewRoutes.get("/crews/:crewId", isAuth, CrewController.show);

// Atualizar equipe
crewRoutes.put("/crews/:crewId", isAuth, CrewController.update);

// Deletar equipe
crewRoutes.delete("/crews/:crewId", isAuth, CrewController.remove);

// Treinar equipe
crewRoutes.post("/crews/:crewId/train", isAuth, CrewController.train);

// Listar knowledge
crewRoutes.get("/crews/:crewId/knowledge", isAuth, CrewController.listKnowledge);

// Upload knowledge
crewRoutes.post("/crews/:crewId/knowledge/upload", isAuth, knowledgeUpload.single("file"), CrewController.uploadKnowledge);

// Delete knowledge
crewRoutes.delete("/crews/:crewId/knowledge/:fileId", isAuth, CrewController.deleteKnowledge);

// Training endpoints - proxy direto para CrewAI service
crewRoutes.post("/training/generate-response", isAuth, CrewController.generateTrainingResponse);
crewRoutes.post("/training/save-correction", isAuth, CrewController.saveCorrection);
crewRoutes.post("/training/save-metrics", isAuth, CrewController.saveTrainingMetrics);

export default crewRoutes;
