import express from "express";
import isAuth from "../middleware/isAuth";

import * as AgentController from "../controllers/AgentController";

const agentRoutes = express.Router();

agentRoutes.get("/agents", isAuth, AgentController.index);
agentRoutes.post("/agents", isAuth, AgentController.store);
agentRoutes.get("/agents/:id", isAuth, AgentController.show);
agentRoutes.put("/agents/:id", isAuth, AgentController.update);
agentRoutes.delete("/agents/:id", isAuth, AgentController.remove);

export default agentRoutes;
