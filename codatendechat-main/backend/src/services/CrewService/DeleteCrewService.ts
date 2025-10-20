import Crew from "../../models/Crew";
import AppError from "../../errors/AppError";
import axios from "axios";

interface Request {
  id: string | number;
  companyId: number;
}

const DeleteCrewService = async ({ id, companyId }: Request): Promise<void> => {
  const crew = await Crew.findOne({
    where: { id, companyId }
  });

  if (!crew) {
    throw new AppError("ERR_NO_CREW_FOUND", 404);
  }

  // Deletar blueprint do Firestore via CrewAI API
  try {
    const crewaiUrl = process.env.CREWAI_API_URL || "http://localhost:8000";
    await axios.delete(
      `${crewaiUrl}/api/v2/crews/${crew.firestoreId}`,
      {
        params: { tenantId: `company_${companyId}` }
      }
    );
  } catch (error) {
    console.error("Erro ao deletar blueprint do CrewAI:", error);
    // Continua com a deleção local mesmo se falhar no CrewAI
  }

  // Deletar do banco local
  await crew.destroy();
};

export default DeleteCrewService;
