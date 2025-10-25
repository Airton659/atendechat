import AppError from "../../errors/AppError";
import GetTicketWbot from "../../helpers/GetTicketWbot";
import Ticket from "../../models/Ticket";
import ShowFileService from "../FileServices/ShowService";
import FilesOptions from "../../models/FilesOptions";
import { getMessageOptions } from "../WbotServices/SendWhatsAppMedia";
import path from "path";
import Contact from "../../models/Contact";
import Whatsapp from "../../models/Whatsapp";

interface Request {
  ticketId: number;
  fileId: number;
  companyId: number;
}

interface Response {
  success: boolean;
  fileName: string;
  message?: string;
}

const SendFileFromListService = async ({
  ticketId,
  fileId,
  companyId
}: Request): Promise<Response> => {
  // 1. Buscar o arquivo na File List (valida companyId)
  const fileList = await ShowFileService(fileId, companyId);

  if (!fileList) {
    throw new AppError("ERR_FILE_NOT_FOUND", 404);
  }

  // 2. Verificar se há opções (arquivos físicos) associados
  if (!fileList.options || fileList.options.length === 0) {
    throw new AppError("ERR_NO_FILE_OPTIONS", 404);
  }

  // 3. Pegar a primeira opção de arquivo (pode ser adaptado para enviar múltiplos)
  const fileOption = fileList.options[0] as FilesOptions;

  if (!fileOption.path) {
    throw new AppError("ERR_FILE_PATH_NOT_FOUND", 404);
  }

  // 4. Buscar o ticket (validar se pertence à companyId)
  const ticket = await Ticket.findOne({
    where: { id: ticketId },
    include: [
      {
        model: Contact,
        as: "contact"
      },
      {
        model: Whatsapp,
        as: "whatsapp"
      }
    ]
  });

  if (!ticket) {
    throw new AppError("ERR_TICKET_NOT_FOUND", 404);
  }

  if (ticket.companyId !== companyId) {
    throw new AppError("ERR_FORBIDDEN_TICKET", 403);
  }

  // 5. Obter conexão Wbot
  const wbot = await GetTicketWbot(ticket);

  // 6. Construir caminho absoluto do arquivo
  const publicFolder = path.resolve(__dirname, "..", "..", "..", "public");
  const filePath = path.join(publicFolder, fileOption.path);

  // 7. Preparar opções de mensagem usando a função do SendWhatsAppMedia
  const messageOptions = await getMessageOptions(
    fileOption.name,
    filePath,
    fileList.message || undefined  // Mensagem/caption configurada no File List
  );

  if (!messageOptions) {
    throw new AppError("ERR_INVALID_MEDIA_TYPE", 400);
  }

  // 8. Enviar arquivo via WhatsApp
  await wbot.sendMessage(
    `${ticket.contact.number}@${ticket.isGroup ? "g.us" : "s.whatsapp.net"}`,
    messageOptions
  );

  // 9. Atualizar lastMessage do ticket
  const lastMessageText = fileList.message || `Arquivo enviado: ${fileOption.name}`;
  await ticket.update({ lastMessage: lastMessageText });

  return {
    success: true,
    fileName: fileOption.name,
    message: lastMessageText
  };
};

export default SendFileFromListService;
