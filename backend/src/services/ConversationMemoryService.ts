import { Firestore, Timestamp, FieldValue } from '@google-cloud/firestore';
import path from 'path';

interface Message {
  role: 'user' | 'agent';
  content: string;
  timestamp: Timestamp;
}

interface ConversationDocument {
  companyId: number;
  contactPhone: string;
  messages: Message[];
  summary?: string;
  entities?: Record<string, any>;
  lastUpdated: Timestamp;
  expiresAt: Timestamp; // TTL field
}

class ConversationMemoryService {
  private firestore: Firestore;
  private collectionName = 'conversationMemory';

  constructor() {
    const credentialsPath = path.join(__dirname, '../../atendechat-credentials.json');

    this.firestore = new Firestore({
      projectId: 'atende-saas',
      keyFilename: credentialsPath,
    });

    console.log('✅ ConversationMemoryService inicializado com Firestore');
  }

  /**
   * Gera ID do documento baseado em companyId e contactPhone
   */
  private getDocumentId(companyId: number, contactPhone: string): string {
    // Remove caracteres especiais do telefone
    const cleanPhone = contactPhone.replace(/\D/g, '');
    return `${companyId}_${cleanPhone}`;
  }

  /**
   * Salva uma mensagem no histórico da conversa
   */
  async saveMessage(
    companyId: number,
    contactPhone: string,
    content: string,
    role: 'user' | 'agent'
  ): Promise<void> {
    try {
      const docId = this.getDocumentId(companyId, contactPhone);
      const docRef = this.firestore.collection(this.collectionName).doc(docId);

      const message: Message = {
        role,
        content,
        timestamp: Timestamp.now(),
      };

      // Calcular data de expiração (30 dias)
      const expiresAt = Timestamp.fromDate(
        new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
      );

      // Verificar se documento existe
      const doc = await docRef.get();

      if (doc.exists) {
        // Atualizar documento existente
        await docRef.update({
          messages: FieldValue.arrayUnion(message),
          lastUpdated: Timestamp.now(),
          expiresAt,
        });
      } else {
        // Criar novo documento
        const newDoc: ConversationDocument = {
          companyId,
          contactPhone,
          messages: [message],
          lastUpdated: Timestamp.now(),
          expiresAt,
        };
        await docRef.set(newDoc);
      }

      console.log(`✅ Mensagem salva no Firestore: ${docId} (${role})`);
    } catch (error) {
      console.error('❌ Erro ao salvar mensagem no Firestore:', error);
      throw error;
    }
  }

  /**
   * Busca as últimas N mensagens da conversa
   */
  async getRecentMessages(
    companyId: number,
    contactPhone: string,
    limit: number = 10
  ): Promise<Message[]> {
    try {
      const docId = this.getDocumentId(companyId, contactPhone);
      const docRef = this.firestore.collection(this.collectionName).doc(docId);

      const doc = await docRef.get();

      if (!doc.exists) {
        console.log(`📭 Nenhuma conversa encontrada para: ${docId}`);
        return [];
      }

      const data = doc.data() as ConversationDocument;
      const messages = data.messages || [];

      // Retornar últimas N mensagens
      const recentMessages = messages.slice(-limit);

      console.log(`📬 ${recentMessages.length} mensagens recuperadas do Firestore: ${docId}`);
      return recentMessages;
    } catch (error) {
      console.error('❌ Erro ao buscar mensagens no Firestore:', error);
      return [];
    }
  }

  /**
   * Busca o resumo da conversa (se existir)
   */
  async getSummary(companyId: number, contactPhone: string): Promise<string | null> {
    try {
      const docId = this.getDocumentId(companyId, contactPhone);
      const docRef = this.firestore.collection(this.collectionName).doc(docId);

      const doc = await docRef.get();

      if (!doc.exists) {
        return null;
      }

      const data = doc.data() as ConversationDocument;
      return data.summary || null;
    } catch (error) {
      console.error('❌ Erro ao buscar resumo no Firestore:', error);
      return null;
    }
  }

  /**
   * Atualiza entidades rastreadas na conversa
   */
  async updateEntities(
    companyId: number,
    contactPhone: string,
    entities: Record<string, any>
  ): Promise<void> {
    try {
      const docId = this.getDocumentId(companyId, contactPhone);
      const docRef = this.firestore.collection(this.collectionName).doc(docId);

      await docRef.update({
        entities,
        lastUpdated: Timestamp.now(),
      });

      console.log(`✅ Entidades atualizadas no Firestore: ${docId}`);
    } catch (error) {
      console.error('❌ Erro ao atualizar entidades no Firestore:', error);
      throw error;
    }
  }

  /**
   * Gera resumo da conversa (a cada 20 mensagens, por exemplo)
   * TODO: Implementar chamada à IA para gerar resumo inteligente
   */
  async generateAndSaveSummary(
    companyId: number,
    contactPhone: string,
    messages: Message[]
  ): Promise<void> {
    try {
      const docId = this.getDocumentId(companyId, contactPhone);
      const docRef = this.firestore.collection(this.collectionName).doc(docId);

      // Por enquanto, resumo simples (TODO: usar IA)
      const summary = `Conversa iniciada em ${messages[0]?.timestamp.toDate().toLocaleDateString()}. Total de ${messages.length} mensagens trocadas.`;

      await docRef.update({
        summary,
        lastUpdated: Timestamp.now(),
      });

      console.log(`✅ Resumo gerado e salvo no Firestore: ${docId}`);
    } catch (error) {
      console.error('❌ Erro ao gerar resumo no Firestore:', error);
      throw error;
    }
  }

  /**
   * Busca entidades rastreadas
   */
  async getEntities(
    companyId: number,
    contactPhone: string
  ): Promise<Record<string, any> | null> {
    try {
      const docId = this.getDocumentId(companyId, contactPhone);
      const docRef = this.firestore.collection(this.collectionName).doc(docId);

      const doc = await docRef.get();

      if (!doc.exists) {
        return null;
      }

      const data = doc.data() as ConversationDocument;
      return data.entities || null;
    } catch (error) {
      console.error('❌ Erro ao buscar entidades no Firestore:', error);
      return null;
    }
  }

  /**
   * Limpa conversa antiga manualmente (TTL automático já faz isso)
   */
  async deleteConversation(companyId: number, contactPhone: string): Promise<void> {
    try {
      const docId = this.getDocumentId(companyId, contactPhone);
      const docRef = this.firestore.collection(this.collectionName).doc(docId);

      await docRef.delete();

      console.log(`🗑️ Conversa deletada do Firestore: ${docId}`);
    } catch (error) {
      console.error('❌ Erro ao deletar conversa no Firestore:', error);
      throw error;
    }
  }

  /**
   * Formata mensagens para enviar ao CrewAI
   */
  formatMessagesForCrewAI(messages: Message[]): Array<{ role: string; body: string; fromMe: boolean }> {
    return messages.map(msg => ({
      role: msg.role === 'user' ? 'Cliente' : 'Você',
      body: msg.content,
      fromMe: msg.role === 'agent',
    }));
  }

  /**
   * Verifica se deve gerar resumo (a cada 20 mensagens)
   */
  async checkAndGenerateSummary(
    companyId: number,
    contactPhone: string
  ): Promise<void> {
    try {
      const messages = await this.getRecentMessages(companyId, contactPhone, 100);

      // Gerar resumo a cada 20 mensagens
      if (messages.length > 0 && messages.length % 20 === 0) {
        await this.generateAndSaveSummary(companyId, contactPhone, messages);
      }
    } catch (error) {
      console.error('❌ Erro ao verificar/gerar resumo:', error);
    }
  }
}

// Singleton
const conversationMemoryService = new ConversationMemoryService();
export default conversationMemoryService;
