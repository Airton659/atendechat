import express from "express";
import isAuth from "../middleware/isAuth";

import * as ScheduleController from "../controllers/ScheduleController";
import multer from "multer";
import uploadConfig from "../config/upload";

const upload = multer(uploadConfig);

const scheduleRoutes = express.Router();

scheduleRoutes.get("/schedules", isAuth, ScheduleController.index);

scheduleRoutes.post("/schedules", isAuth, ScheduleController.store);

// Endpoint para agendamento criado por IA (sem autenticação pois vem do serviço Python)
scheduleRoutes.post("/schedules/agent", ScheduleController.storeFromAgent);

// Endpoints para confirmação/rejeição de agendamentos pendentes
scheduleRoutes.put("/schedules/:scheduleId/confirm", isAuth, ScheduleController.confirm);
scheduleRoutes.put("/schedules/:scheduleId/reject", isAuth, ScheduleController.reject);

scheduleRoutes.put("/schedules/:scheduleId", isAuth, ScheduleController.update);

scheduleRoutes.get("/schedules/:scheduleId", isAuth, ScheduleController.show);

scheduleRoutes.delete("/schedules/:scheduleId", isAuth, ScheduleController.remove);

scheduleRoutes.post("/schedules/:id/media-upload", isAuth, upload.array("file"), ScheduleController.mediaUpload);

scheduleRoutes.delete("/schedules/:id/media-upload", isAuth, ScheduleController.deleteMedia);

export default scheduleRoutes;
