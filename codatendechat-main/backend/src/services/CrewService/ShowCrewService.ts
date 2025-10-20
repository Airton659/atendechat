import Crew from "../../models/Crew";
import Company from "../../models/Company";
import AppError from "../../errors/AppError";
import axios from "axios";

interface Request {
  id: string | number;
  companyId: number;
}

interface Response {
  crew: Crew;
  blueprint?: any;
}

const ShowCrewService = async ({ id, companyId }: Request): Promise<Response> => {
  const crew = await Crew.findOne({
    where: { id, companyId },
    include: [
      {
        model: Company,
        as: "company",
        attributes: ["id", "name"]
      }
    ]
  });

  if (!crew) {
    throw new AppError("ERR_NO_CREW_FOUND", 404);
  }

  // Buscar blueprint do Firestore via CrewAI API
  let blueprint = null;
  try {
    const crewaiUrl = process.env.CREWAI_API_URL || "http://localhost:8000";
    const response = await axios.get(
      `${crewaiUrl}/api/v2/crews/${crew.firestoreId}`,
      {
        params: { tenantId: `company_${companyId}` }
      }
    );
    blueprint = response.data;
  } catch (error) {
    console.error("Erro ao buscar blueprint do CrewAI:", error);
  }

  return { crew, blueprint };
};

export default ShowCrewService;
