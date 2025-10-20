import Crew from "../../models/Crew";
import AppError from "../../errors/AppError";
import axios from "axios";

interface Request {
  crewId: string | number;
  companyId: number;
  name?: string;
  description?: string;
  isActive?: boolean;
  blueprint?: any;
}

const UpdateCrewService = async ({
  crewId,
  companyId,
  name,
  description,
  isActive,
  blueprint
}: Request): Promise<Crew> => {
  const crew = await Crew.findOne({
    where: { id: crewId, companyId }
  });

  if (!crew) {
    throw new AppError("ERR_NO_CREW_FOUND", 404);
  }

  // Atualizar blueprint no CrewAI se fornecido
  if (blueprint) {
    try {
      const crewaiUrl = process.env.CREWAI_API_URL || "http://localhost:8000";
      await axios.put(
        `${crewaiUrl}/api/v2/crews/${crew.firestoreId}`,
        {
          tenantId: `company_${companyId}`,
          blueprint
        }
      );
    } catch (error) {
      console.error("Erro ao atualizar blueprint no CrewAI:", error);
      throw new AppError("ERR_UPDATING_CREW_BLUEPRINT", 500);
    }
  }

  // Atualizar campos locais
  const updateData: any = {};
  if (name !== undefined) updateData.name = name;
  if (description !== undefined) updateData.description = description;
  if (isActive !== undefined) updateData.isActive = isActive;

  await crew.update(updateData);
  await crew.reload();

  return crew;
};

export default UpdateCrewService;
