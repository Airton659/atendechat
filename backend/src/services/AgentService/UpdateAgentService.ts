import * as Yup from "yup";
import AppError from "../../errors/AppError";
import Agent from "../../models/Agent";
import AgentKnowledgeBase from "../../models/AgentKnowledgeBase";

interface AgentData {
  id: number;
  companyId: number;
  name?: string;
  function?: string;
  objective?: string;
  backstory?: string;
  keywords?: string[];
  customInstructions?: string;
  persona?: string;
  doList?: string[];
  dontList?: string[];
  aiProvider?: "openai" | "crewai";
  isActive?: boolean;
  teamId?: number;
  useKnowledgeBase?: boolean;
  knowledgeBaseIds?: number[];
}

const UpdateAgentService = async (agentData: AgentData): Promise<Agent> => {
  const agentSchema = Yup.object().shape({
    name: Yup.string().min(2, "ERR_AGENT_INVALID_NAME"),
    aiProvider: Yup.string().oneOf(["openai", "crewai"], "ERR_AGENT_INVALID_PROVIDER")
  });

  const { id, companyId, knowledgeBaseIds, ...updateData } = agentData;

  try {
    await agentSchema.validate(updateData);
  } catch (err: any) {
    throw new AppError(err.message);
  }

  const agent = await Agent.findOne({
    where: {
      id,
      companyId
    }
  });

  if (!agent) {
    throw new AppError("ERR_NO_AGENT_FOUND", 404);
  }

  await agent.update(updateData);

  // Atualizar relacionamentos com Knowledge Base
  if (knowledgeBaseIds !== undefined) {
    // Remover relacionamentos antigos
    await AgentKnowledgeBase.destroy({
      where: { agentId: id }
    });

    // Criar novos relacionamentos
    if (knowledgeBaseIds.length > 0) {
      const relations = knowledgeBaseIds.map(kbId => ({
        agentId: id,
        knowledgeBaseId: kbId
      }));
      await AgentKnowledgeBase.bulkCreate(relations);
    }
  }

  return agent;
};

export default UpdateAgentService;
