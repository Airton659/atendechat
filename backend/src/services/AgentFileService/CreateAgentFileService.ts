import AgentFile from "../../models/AgentFile";
import AppError from "../../errors/AppError";

interface Request {
  agentId: number;
  fileName: string;
  originalName: string;
  filePath: string;
  fileType: string;
  mimeType: string;
  fileSize?: number;
  description?: string;
}

const CreateAgentFileService = async ({
  agentId,
  fileName,
  originalName,
  filePath,
  fileType,
  mimeType,
  fileSize,
  description
}: Request): Promise<AgentFile> => {
  const agentFile = await AgentFile.create({
    agentId,
    fileName,
    originalName,
    filePath,
    fileType,
    mimeType,
    fileSize,
    description
  });

  return agentFile;
};

export default CreateAgentFileService;
