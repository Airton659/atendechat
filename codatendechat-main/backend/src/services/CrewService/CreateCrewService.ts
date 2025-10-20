import Crew from "../../models/Crew";
import AppError from "../../errors/AppError";
import axios from "axios";

interface Request {
  name: string;
  description?: string;
  companyId: number;
  userId: number;
  firestoreId?: string;
  status?: string;
  industry?: string;
  objective?: string;
  tone?: string;
}

const CreateCrewService = async ({
  name,
  description,
  companyId,
  userId,
  firestoreId,
  status = "draft",
  industry,
  objective,
  tone = "professional"
}: Request): Promise<Crew> => {
  // Verificar se já existe crew com esse nome para a empresa
  const crewExists = await Crew.findOne({
    where: { name, companyId }
  });

  if (crewExists) {
    throw new AppError("ERR_CREW_ALREADY_EXISTS", 400);
  }

  // Se não foi fornecido firestoreId, criar no CrewAI Service
  let finalFirestoreId = firestoreId;

  if (!finalFirestoreId) {
    try {
      const crewaiUrl = process.env.CREWAI_API_URL || "http://localhost:8000";
      const response = await axios.post(`${crewaiUrl}/api/v2/crews`, {
        tenantId: `company_${companyId}`,
        name,
        description,
        industry,
        objective,
        tone,
        status
      });

      finalFirestoreId = response.data.id;
    } catch (error) {
      console.error("Erro ao criar crew no CrewAI Service:", error);
      throw new AppError("ERR_CREATING_CREW_IN_CREWAI_SERVICE", 500);
    }
  }

  // Criar no banco local
  const crew = await Crew.create({
    name,
    description,
    companyId,
    createdBy: userId,
    firestoreId: finalFirestoreId,
    status,
    industry,
    objective,
    tone
  });

  return crew;
};

export default CreateCrewService;
