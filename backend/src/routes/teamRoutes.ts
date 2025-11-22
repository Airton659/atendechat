import express from "express";
import isAuth from "../middleware/isAuth";

import * as TeamController from "../controllers/TeamController";
// import * as TeamPlaygroundController from "../controllers/TeamPlaygroundController";

const teamRoutes = express.Router();

teamRoutes.get("/teams", isAuth, TeamController.index);
teamRoutes.post("/teams", isAuth, TeamController.store);
teamRoutes.post("/teams/generate", isAuth, TeamController.generateTeam);
teamRoutes.get("/teams/:id", isAuth, TeamController.show);
teamRoutes.put("/teams/:id", isAuth, TeamController.update);
teamRoutes.delete("/teams/:id", isAuth, TeamController.remove);

// Playground: REMOVIDO DO SISTEMA
// import * as TeamPlaygroundController from "../controllers/TeamPlaygroundController";
// teamRoutes.post("/teams/playground/run", isAuth, TeamPlaygroundController.run);

export default teamRoutes;
