import express from "express";
import * as AgentTrainingExamplesController from "../controllers/AgentTrainingExamplesController";
import isAuth from "../middleware/isAuth";

const agentTrainingExamplesRoutes = express.Router();

// Rotas com autenticação (frontend)
agentTrainingExamplesRoutes.get("/agent-training-examples", isAuth, AgentTrainingExamplesController.index);
agentTrainingExamplesRoutes.get("/agent-training-examples/export/:agentId", isAuth, AgentTrainingExamplesController.exportExamples);
agentTrainingExamplesRoutes.get("/agent-training-examples/:id", isAuth, AgentTrainingExamplesController.show);
agentTrainingExamplesRoutes.post("/agent-training-examples", isAuth, AgentTrainingExamplesController.store);
agentTrainingExamplesRoutes.put("/agent-training-examples/:id", isAuth, AgentTrainingExamplesController.update);
agentTrainingExamplesRoutes.delete("/agent-training-examples/:id", isAuth, AgentTrainingExamplesController.remove);

// Rota sem auth - Python vai chamar para buscar exemplos
agentTrainingExamplesRoutes.get("/agent-training-examples/relevant/:agentId", AgentTrainingExamplesController.getRelevantExamples);

export default agentTrainingExamplesRoutes;
