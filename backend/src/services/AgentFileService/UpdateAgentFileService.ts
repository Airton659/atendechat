import AgentFile from "../../models/AgentFile";
import AppError from "../../errors/AppError";

interface Request {
  id: number;
  description?: string;
}

const UpdateAgentFileService = async ({
  id,
  description
}: Request): Promise<AgentFile> => {
  const agentFile = await AgentFile.findByPk(id);

  if (!agentFile) {
    throw new AppError("ERR_AGENT_FILE_NOT_FOUND", 404);
  }

  await agentFile.update({ description });

  return agentFile;
};

export default UpdateAgentFileService;
