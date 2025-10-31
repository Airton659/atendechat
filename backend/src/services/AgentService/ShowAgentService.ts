import Agent from "../../models/Agent";
import AppError from "../../errors/AppError";

interface Request {
  id: number;
  companyId: number;
}

const ShowAgentService = async ({ id, companyId }: Request): Promise<Agent> => {
  const agent = await Agent.findOne({
    where: {
      id,
      companyId
    }
  });

  if (!agent) {
    throw new AppError("ERR_NO_AGENT_FOUND", 404);
  }

  return agent;
};

export default ShowAgentService;
