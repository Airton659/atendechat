import express from "express";
import isAuth from "../middleware/isAuth";

import * as ScheduleController from "../controllers/ScheduleController";
import multer from "multer";
import uploadConfig from "../config/upload";

const upload = multer(uploadConfig);

const scheduleRoutes = express.Router();

scheduleRoutes.get("/schedules", isAuth, ScheduleController.index);

scheduleRoutes.post("/schedules", isAuth, ScheduleController.store);

// === ENDPOINTS NÃO AUTENTICADOS PARA CREWAI ===
// Endpoint para agendamento criado por IA (sem autenticação pois vem do serviço Python)
scheduleRoutes.post("/schedules/agent", ScheduleController.storeFromAgent);

// Listar agendamentos do contato (para IA consultar status)
scheduleRoutes.get("/schedules/agent/:contactId", ScheduleController.listFromAgent);

// Cancelar agendamento (para IA cancelar se cliente solicitar)
scheduleRoutes.delete("/schedules/agent/:scheduleId", ScheduleController.cancelFromAgent);

// Atualizar agendamento (para IA alterar data/hora/descrição)
scheduleRoutes.put("/schedules/agent/:scheduleId", ScheduleController.updateFromAgent);

// Endpoints para confirmação/rejeição de agendamentos pendentes
scheduleRoutes.put("/schedules/:scheduleId/confirm", isAuth, ScheduleController.confirm);
scheduleRoutes.put("/schedules/:scheduleId/reject", isAuth, ScheduleController.reject);

scheduleRoutes.put("/schedules/:scheduleId", isAuth, ScheduleController.update);

scheduleRoutes.get("/schedules/:scheduleId", isAuth, ScheduleController.show);

scheduleRoutes.delete("/schedules/:scheduleId", isAuth, ScheduleController.remove);

scheduleRoutes.post("/schedules/:id/media-upload", isAuth, upload.array("file"), ScheduleController.mediaUpload);

scheduleRoutes.delete("/schedules/:id/media-upload", isAuth, ScheduleController.deleteMedia);

export default scheduleRoutes;
