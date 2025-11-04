import express from "express";
import * as AgentLogController from "../controllers/AgentLogController";
import isAuth from "../middleware/isAuth";

const agentLogRoutes = express.Router();

agentLogRoutes.get("/agent-logs", isAuth, AgentLogController.index);
agentLogRoutes.get("/agent-logs/stats", isAuth, AgentLogController.stats);
agentLogRoutes.get("/agent-logs/:id", isAuth, AgentLogController.show);
agentLogRoutes.post("/agent-logs", AgentLogController.store); // Sem auth - Python vai chamar
agentLogRoutes.post("/agent-logs/cleanup", isAuth, AgentLogController.cleanup);

export default agentLogRoutes;
