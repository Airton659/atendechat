import AgentFile from "../../models/AgentFile";
import AppError from "../../errors/AppError";

const ShowAgentFileService = async (id: number): Promise<AgentFile> => {
  const agentFile = await AgentFile.findByPk(id);

  if (!agentFile) {
    throw new AppError("ERR_AGENT_FILE_NOT_FOUND", 404);
  }

  return agentFile;
};

export default ShowAgentFileService;
