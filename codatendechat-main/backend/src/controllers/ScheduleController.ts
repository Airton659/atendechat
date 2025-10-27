import { Request, Response } from "express";
import { getIO } from "../libs/socket";

import AppError from "../errors/AppError";

import CreateService from "../services/ScheduleServices/CreateService";
import ListService from "../services/ScheduleServices/ListService";
import UpdateService from "../services/ScheduleServices/UpdateService";
import ShowService from "../services/ScheduleServices/ShowService";
import DeleteService from "../services/ScheduleServices/DeleteService";
import Schedule from "../models/Schedule";
import path from "path";
import fs from "fs";
import { head } from "lodash";

type IndexQuery = {
  searchParam?: string;
  contactId?: number | string;
  userId?: number | string;
  pageNumber?: string | number;
};

export const index = async (req: Request, res: Response): Promise<Response> => {
  const { contactId, userId, pageNumber, searchParam } = req.query as IndexQuery;
  const { companyId } = req.user;

  const { schedules, count, hasMore } = await ListService({
    searchParam,
    contactId,
    userId,
    pageNumber,
    companyId
  });

  return res.json({ schedules, count, hasMore });
};

export const store = async (req: Request, res: Response): Promise<Response> => {
  const {
    body,
    sendAt,
    contactId,
    userId
  } = req.body;
  const { companyId } = req.user;

  // Validar data: NÃO pode ser no passado
  const sendAtDate = new Date(sendAt);
  const now = new Date();

  if (sendAtDate < now) {
    throw new AppError("ERR_PAST_DATE: Data do agendamento não pode ser no passado", 400);
  }

  const schedule = await CreateService({
    body,
    sendAt,
    contactId,
    companyId,
    userId
  });

  const io = getIO();
  io.to(`company-${companyId}-mainchannel`).emit("schedule", {
    action: "create",
    schedule
  });

  return res.status(200).json(schedule);
};

// Endpoint para agendamento criado por IA (CrewAI)
export const storeFromAgent = async (req: Request, res: Response): Promise<Response> => {
  const {
    body,
    sendAt,
    contactId,
    userId,
    status,
    tenantId
  } = req.body;

  // tenantId vem como "company_X" do CrewAI, extrair X
  const companyId = tenantId ? parseInt(tenantId.replace('company_', '')) : null;

  if (!companyId) {
    throw new AppError("ERR_INVALID_TENANT_ID", 400);
  }

  // Validar data: NÃO pode ser no passado
  const sendAtDate = new Date(sendAt);
  const now = new Date();

  if (sendAtDate < now) {
    throw new AppError("ERR_PAST_DATE: Data do agendamento não pode ser no passado", 400);
  }

  const schedule = await CreateService({
    body,
    sendAt,
    contactId,
    companyId,
    userId,
    status: status || 'pending_confirmation' // Default para pending_confirmation
  });

  const io = getIO();

  // Emitir evento específico para agendamento criado por IA
  io.to(`company-${companyId}-mainchannel`).emit("schedule", {
    action: "create",
    schedule,
    createdByAgent: true
  });

  // Se for pending_confirmation, emitir evento adicional para notificação
  if (schedule.status === 'pending_confirmation') {
    const eventName = `company${companyId}-schedule:pending_confirmation`;
    console.log(`📢 Emitindo evento de notificação: ${eventName}`);
    console.log(`   Schedule ID: ${schedule.id}`);
    console.log(`   Contact: ${schedule.contact?.name || 'N/A'}`);
    console.log(`   SendAt: ${schedule.sendAt}`);

    io.to(`company-${companyId}-mainchannel`).emit(eventName, {
      schedule
    });
  }

  return res.status(200).json(schedule);
};

// Endpoint para confirmar agendamento pendente
export const confirm = async (req: Request, res: Response): Promise<Response> => {
  const { scheduleId } = req.params;
  const { companyId } = req.user;

  const schedule = await UpdateService({
    scheduleData: { status: 'scheduled' },
    id: scheduleId,
    companyId
  });

  const io = getIO();
  io.to(`company-${companyId}-mainchannel`).emit("schedule", {
    action: "update",
    schedule
  });

  return res.status(200).json(schedule);
};

// Endpoint para rejeitar agendamento pendente
export const reject = async (req: Request, res: Response): Promise<Response> => {
  const { scheduleId } = req.params;
  const { companyId } = req.user;

  const schedule = await UpdateService({
    scheduleData: { status: 'cancelled' },
    id: scheduleId,
    companyId
  });

  const io = getIO();
  io.to(`company-${companyId}-mainchannel`).emit("schedule", {
    action: "update",
    schedule
  });

  return res.status(200).json(schedule);
};

export const show = async (req: Request, res: Response): Promise<Response> => {
  const { scheduleId } = req.params;
  const { companyId } = req.user;

  const schedule = await ShowService(scheduleId, companyId);

  return res.status(200).json(schedule);
};

export const update = async (
  req: Request,
  res: Response
): Promise<Response> => {
  if (req.user.profile !== "admin") {
    throw new AppError("ERR_NO_PERMISSION", 403);
  }

  const { scheduleId } = req.params;
  const scheduleData = req.body;
  const { companyId } = req.user;

  const schedule = await UpdateService({ scheduleData, id: scheduleId, companyId });

  const io = getIO();
  io.to(`company-${companyId}-mainchannel`).emit("schedule", {
    action: "update",
    schedule
  });

  return res.status(200).json(schedule);
};

export const remove = async (
  req: Request,
  res: Response
): Promise<Response> => {
  const { scheduleId } = req.params;
  const { companyId } = req.user;

  await DeleteService(scheduleId, companyId);

  const io = getIO();
  io.to(`company-${companyId}-mainchannel`).emit("schedule", {
    action: "delete",
    scheduleId
  });

  return res.status(200).json({ message: "Schedule deleted" });
};

export const mediaUpload = async (
  req: Request,
  res: Response
): Promise<Response> => {
  const { id } = req.params;
  const files = req.files as Express.Multer.File[];
  const file = head(files);

  try {
    const schedule = await Schedule.findByPk(id);
    schedule.mediaPath = file.filename;
    schedule.mediaName = file.originalname;

    await schedule.save();
    return res.send({ mensagem: "Arquivo Anexado" });
    } catch (err: any) {
      throw new AppError(err.message);
  }
};

export const deleteMedia = async (
  req: Request,
  res: Response
): Promise<Response> => {
  const { id } = req.params;

  try {
    const schedule = await Schedule.findByPk(id);
    const filePath = path.resolve("public", schedule.mediaPath);
    const fileExists = fs.existsSync(filePath);
    if (fileExists) {
      fs.unlinkSync(filePath);
    }
    schedule.mediaPath = null;
    schedule.mediaName = null;
    await schedule.save();
    return res.send({ mensagem: "Arquivo Excluído" });
    } catch (err: any) {
      throw new AppError(err.message);
  }
};

// === ENDPOINTS NÃO AUTENTICADOS PARA CREWAI ===

// GET /schedules/agent/:contactId - Lista agendamentos do contato
export const listFromAgent = async (req: Request, res: Response): Promise<Response> => {
  const { contactId } = req.params;
  const { tenantId } = req.query;

  if (!tenantId) {
    throw new AppError("ERR_INVALID_TENANT_ID", 400);
  }

  // tenantId vem como "company_X" do CrewAI, extrair X
  const companyId = parseInt(tenantId.toString().replace('company_', ''));

  if (!companyId) {
    throw new AppError("ERR_INVALID_TENANT_ID", 400);
  }

  const { schedules, count, hasMore } = await ListService({
    contactId: parseInt(contactId),
    pageNumber: 1,
    companyId
  });

  return res.json({ schedules, count, hasMore });
};

// GET /schedules/agent/company/all - Lista TODOS agendamentos da empresa (para verificar conflitos)
export const listAllFromAgent = async (req: Request, res: Response): Promise<Response> => {
  const { tenantId } = req.query;

  if (!tenantId) {
    throw new AppError("ERR_INVALID_TENANT_ID", 400);
  }

  // tenantId vem como "company_X" do CrewAI, extrair X
  const companyId = parseInt(tenantId.toString().replace('company_', ''));

  if (!companyId) {
    throw new AppError("ERR_INVALID_TENANT_ID", 400);
  }

  // Buscar TODOS os agendamentos da empresa (sem filtrar por contactId)
  const { schedules, count, hasMore } = await ListService({
    pageNumber: 1,
    companyId
  });

  return res.json({ schedules, count, hasMore });
};

// DELETE /schedules/agent/:scheduleId - Cancela agendamento
export const cancelFromAgent = async (req: Request, res: Response): Promise<Response> => {
  const { scheduleId } = req.params;
  const { tenantId } = req.query;

  if (!tenantId) {
    throw new AppError("ERR_INVALID_TENANT_ID", 400);
  }

  // tenantId vem como "company_X" do CrewAI, extrair X
  const companyId = parseInt(tenantId.toString().replace('company_', ''));

  if (!companyId) {
    throw new AppError("ERR_INVALID_TENANT_ID", 400);
  }

  // Verificar se o agendamento pertence à empresa correta
  const schedule = await ShowService(scheduleId, companyId);

  if (!schedule) {
    throw new AppError("ERR_SCHEDULE_NOT_FOUND", 404);
  }

  // Cancelar (atualizar status para cancelled)
  const cancelledSchedule = await UpdateService({
    scheduleData: { status: 'cancelled' },
    id: scheduleId,
    companyId
  });

  const io = getIO();
  io.to(`company-${companyId}-mainchannel`).emit("schedule", {
    action: "update",
    schedule: cancelledSchedule
  });

  return res.status(200).json(cancelledSchedule);
};

// PUT /schedules/agent/:scheduleId - Atualiza agendamento
export const updateFromAgent = async (req: Request, res: Response): Promise<Response> => {
  const { scheduleId } = req.params;
  const { tenantId, sendAt, body, status } = req.body;

  if (!tenantId) {
    throw new AppError("ERR_INVALID_TENANT_ID", 400);
  }

  // tenantId vem como "company_X" do CrewAI, extrair X
  const companyId = parseInt(tenantId.replace('company_', ''));

  if (!companyId) {
    throw new AppError("ERR_INVALID_TENANT_ID", 400);
  }

  // Verificar se o agendamento pertence à empresa correta
  const schedule = await ShowService(scheduleId, companyId);

  if (!schedule) {
    throw new AppError("ERR_SCHEDULE_NOT_FOUND", 404);
  }

  // Montar dados de atualização
  const scheduleData: any = {};

  if (sendAt) {
    // Validar data: NÃO pode ser no passado
    const sendAtDate = new Date(sendAt);
    const now = new Date();

    if (sendAtDate < now) {
      throw new AppError("ERR_PAST_DATE: Data do agendamento não pode ser no passado", 400);
    }

    scheduleData.sendAt = sendAt;
  }

  if (body) {
    scheduleData.body = body;
  }

  if (status) {
    scheduleData.status = status;
  }

  const updatedSchedule = await UpdateService({
    scheduleData,
    id: scheduleId,
    companyId
  });

  const io = getIO();
  io.to(`company-${companyId}-mainchannel`).emit("schedule", {
    action: "update",
    schedule: updatedSchedule
  });

  return res.status(200).json(updatedSchedule);
};