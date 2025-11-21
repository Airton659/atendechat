import AgentFile from "../../models/AgentFile";

interface Request {
  agentId: number;
}

const ListAgentFilesService = async ({ agentId }: Request): Promise<AgentFile[]> => {
  const files = await AgentFile.findAll({
    where: { agentId },
    order: [["createdAt", "DESC"]]
  });

  return files;
};

export default ListAgentFilesService;
