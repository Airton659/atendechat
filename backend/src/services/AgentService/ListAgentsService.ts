import { Sequelize, Op } from "sequelize";
import Agent from "../../models/Agent";

interface Request {
  companyId: number;
  searchParam?: string;
  pageNumber?: string;
}

interface Response {
  agents: Agent[];
  count: number;
  hasMore: boolean;
}

const ListAgentsService = async ({
  companyId,
  searchParam = "",
  pageNumber = "1"
}: Request): Promise<Response> => {
  const whereCondition: any = {
    companyId,
    [Op.or]: [
      {
        name: Sequelize.where(
          Sequelize.fn("LOWER", Sequelize.col("name")),
          "LIKE",
          `%${searchParam.toLowerCase().trim()}%`
        )
      }
    ]
  };

  const limit = 20;
  const offset = limit * (+pageNumber - 1);

  const { count, rows: agents } = await Agent.findAndCountAll({
    where: whereCondition,
    limit,
    offset,
    order: [["name", "ASC"]]
  });

  const hasMore = count > offset + agents.length;

  return {
    agents,
    count,
    hasMore
  };
};

export default ListAgentsService;
