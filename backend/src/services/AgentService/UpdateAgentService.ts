import * as Yup from "yup";
import AppError from "../../errors/AppError";
import Agent from "../../models/Agent";

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
}

const UpdateAgentService = async (agentData: AgentData): Promise<Agent> => {
  const agentSchema = Yup.object().shape({
    name: Yup.string().min(2, "ERR_AGENT_INVALID_NAME"),
    aiProvider: Yup.string().oneOf(["openai", "crewai"], "ERR_AGENT_INVALID_PROVIDER")
  });

  const { id, companyId, ...updateData } = agentData;

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

  return agent;
};

export default UpdateAgentService;
