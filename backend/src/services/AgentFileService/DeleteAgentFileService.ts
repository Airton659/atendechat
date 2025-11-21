import AgentFile from "../../models/AgentFile";
import AppError from "../../errors/AppError";
import * as fs from "fs";
import * as path from "path";

const DeleteAgentFileService = async (id: number): Promise<void> => {
  const agentFile = await AgentFile.findByPk(id);

  if (!agentFile) {
    throw new AppError("ERR_AGENT_FILE_NOT_FOUND", 404);
  }

  // Remove o arquivo físico
  const filePath = path.join(__dirname, "..", "..", "..", "public", agentFile.filePath);
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
  }

  await agentFile.destroy();
};

export default DeleteAgentFileService;
