import Crew from "../../models/Crew";
import Company from "../../models/Company";

interface Request {
  companyId: number;
}

const ListCrewsService = async ({ companyId }: Request): Promise<Crew[]> => {
  const crews = await Crew.findAll({
    where: { companyId },
    include: [
      {
        model: Company,
        as: "company",
        attributes: ["id", "name"]
      }
    ],
    order: [["createdAt", "DESC"]]
  });

  return crews;
};

export default ListCrewsService;
