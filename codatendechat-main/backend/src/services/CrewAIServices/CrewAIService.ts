import axios from "axios";
import Message from "../../models/Message";
import Ticket from "../../models/Ticket";
import SendWhatsAppMessage from "../WbotServices/SendWhatsAppMessage";

interface CrewAIResponse {
  response: string;
  agent_used?: string;
}

interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

const CREWAI_SERVICE_URL = process.env.CREWAI_SERVICE_URL || "http://localhost:8000";

/**
 * Busca histórico de mensagens do ticket para enviar como contexto para o CrewAI
 */
const getConversationHistory = async (
  ticket: Ticket,
  limit: number = 10
): Promise<ConversationMessage[]> => {
  try {
    const messages = await Message.findAll({
      where: {
        ticketId: ticket.id
      },
      order: [["createdAt", "DESC"]],
      limit
    });

    // Inverte para ordem cronológica (mais antiga primeiro)
    const history: ConversationMessage[] = messages
      .reverse()
      .map(msg => ({
        role: (msg.fromMe ? "assistant" : "user") as "user" | "assistant",
        content: msg.body
      }))
      .filter(msg => msg.content && msg.content.trim() !== "");

    return history;
  } catch (error) {
    console.error("Erro ao buscar histórico de conversa:", error);
    return [];
  }
};

/**
 * Envia mensagem para o CrewAI Service e retorna a resposta
 */
export const sendMessageToCrewAI = async (
  message: string,
  crewId: string,
  companyId: number,
  ticket: Ticket
): Promise<string | null> => {
  try {
    console.log(`[CrewAI] Enviando mensagem para crew ${crewId}...`);
    console.log(`[CrewAI] Mensagem: ${message}`);

    // Busca histórico de conversa (excluindo a mensagem atual)
    const conversationHistory = await getConversationHistory(ticket, 10);

    console.log(`[CrewAI] Histórico: ${conversationHistory.length} mensagens`);

    const tenantId = `company_${companyId}`;

    const payload = {
      tenantId,
      teamId: crewId,
      message,
      conversationHistory
    };

    console.log(`[CrewAI] Payload:`, JSON.stringify(payload, null, 2));

    const response = await axios.post<CrewAIResponse>(
      `${CREWAI_SERVICE_URL}/api/v2/training/generate-response`,
      payload,
      {
        timeout: 30000, // 30 segundos
        headers: {
          "Content-Type": "application/json"
        }
      }
    );

    if (response.data && response.data.response) {
      console.log(`[CrewAI] Resposta recebida do agente: ${response.data.agent_used || "unknown"}`);
      console.log(`[CrewAI] Resposta: ${response.data.response.substring(0, 100)}...`);
      return response.data.response;
    }

    console.log("[CrewAI] Resposta vazia ou inválida do CrewAI Service");
    return null;
  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      if (error.code === "ECONNREFUSED") {
        console.error("[CrewAI] CrewAI Service está fora do ar (ECONNREFUSED)");
      } else if (error.response) {
        console.error(`[CrewAI] Erro HTTP ${error.response.status}:`, error.response.data);
      } else if (error.request) {
        console.error("[CrewAI] Timeout ou sem resposta do CrewAI Service");
      } else {
        console.error("[CrewAI] Erro ao fazer request:", error.message);
      }
    } else {
      console.error("[CrewAI] Erro desconhecido:", error);
    }
    return null;
  }
};

/**
 * Processa mensagem com CrewAI e retorna true se foi processada com sucesso
 */
export const handleCrewAIMessage = async (
  messageBody: string,
  ticket: Ticket,
  crewId: string,
  companyId: number
): Promise<boolean> => {
  try {
    if (!messageBody || messageBody.trim() === "") {
      console.log("[CrewAI] Mensagem vazia, ignorando CrewAI");
      return false;
    }

    // Envia para CrewAI
    const crewResponse = await sendMessageToCrewAI(
      messageBody,
      crewId,
      companyId,
      ticket
    );

    if (crewResponse && crewResponse.trim() !== "") {
      console.log("[CrewAI] ✅ Mensagem processada com sucesso pelo CrewAI");
      console.log("[CrewAI] Enviando resposta de volta para o WhatsApp...");

      // Envia resposta do CrewAI de volta para o WhatsApp
      try {
        await SendWhatsAppMessage({
          body: crewResponse,
          ticket
        });

        console.log("[CrewAI] ✅ Resposta enviada com sucesso para o WhatsApp!");
        return true;
      } catch (sendError) {
        console.error("[CrewAI] ❌ Erro ao enviar resposta para WhatsApp:", sendError);
        return false;
      }
    }

    console.log("[CrewAI] ⚠️ CrewAI não retornou resposta, caindo para fluxo normal");
    return false;
  } catch (error) {
    console.error("[CrewAI] ❌ Erro ao processar mensagem com CrewAI:", error);
    return false;
  }
};
