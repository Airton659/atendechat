import * as Yup from "yup";
import AppError from "../../errors/AppError";
import Agent from "../../models/Agent";

interface AgentData {
  name: string;
  function?: string;
  objective?: string;
  backstory?: string;
  keywords?: string[];
  customInstructions?: string;
  persona?: string;
  doList?: string[];
  dontList?: string[];
  aiProvider: "openai" | "crewai";
  isActive?: boolean;
  companyId: number;
}

const CreateAgentService = async (agentData: AgentData): Promise<Agent> => {
  const agentSchema = Yup.object().shape({
    name: Yup.string()
      .min(2, "ERR_AGENT_INVALID_NAME")
      .required("ERR_AGENT_INVALID_NAME"),
    aiProvider: Yup.string()
      .oneOf(["openai", "crewai"], "ERR_AGENT_INVALID_PROVIDER")
      .required("ERR_AGENT_INVALID_PROVIDER"),
    companyId: Yup.number()
      .required("ERR_AGENT_INVALID_COMPANY")
  });

  try {
    await agentSchema.validate({
      name: agentData.name,
      aiProvider: agentData.aiProvider,
      companyId: agentData.companyId
    });
  } catch (err: any) {
    throw new AppError(err.message);
  }

  const agent = await Agent.create({
    name: agentData.name,
    function: agentData.function || "",
    objective: agentData.objective || "",
    backstory: agentData.backstory || "",
    keywords: agentData.keywords || [],
    customInstructions: agentData.customInstructions || "",
    persona: agentData.persona || "",
    doList: agentData.doList || [],
    dontList: agentData.dontList || [],
    aiProvider: agentData.aiProvider,
    isActive: agentData.isActive !== undefined ? agentData.isActive : true,
    companyId: agentData.companyId
  });

  return agent;
};

export default CreateAgentService;
