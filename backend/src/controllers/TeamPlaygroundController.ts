import { Request, Response } from "express";
import axios from "axios";
import AppError from "../errors/AppError";
import Team from "../models/Team";
import Agent from "../models/Agent";

const crewaiServiceUrl = process.env.CREWAI_SERVICE_URL || "http://localhost:8001";

/**
 * Controller para o "Laboratório de Times" (Teams Playground)
 * Permite testar equipes sem salvar no banco de dados
 */

interface PlaygroundRunRequest {
  teamId?: number; // ID do time existente (opcional, se omitido usa teamDefinition)
  teamDefinition?: {
    name: string;
    description?: string;
    processType?: "sequential" | "hierarchical";
    temperature?: number;
    verbose?: boolean;
    managerLLM?: string;
    agents: Array<{
      id?: number;
      name: string;
      function: string;
      objective: string;
      backstory: string;
      keywords?: string[];
      customInstructions?: string;
      persona?: string;
      doList?: string[];
      dontList?: string[];
      isActive?: boolean;
      useKnowledgeBase?: boolean;
      knowledgeBaseIds?: number[];
    }>;
  };
  task: string; // Mensagem de teste
}

/**
 * POST /teams/playground/run
 * Executa uma equipe TEMPORÁRIA para testes
 */
export const run = async (req: Request, res: Response): Promise<Response> => {
  const { companyId } = req.user;
  const { teamId, teamDefinition, task }: PlaygroundRunRequest = req.body;

  console.log("\n" + "=".repeat(60));
  console.log("🧪 PLAYGROUND RUN - Backend Node.js");
  console.log("=".repeat(60));
  console.log(`Company ID: ${companyId}`);
  console.log(`Team ID: ${teamId || "N/A (usando teamDefinition)"}`);
  console.log(`Task: ${task}`);
  console.log("=".repeat(60) + "\n");

  // Validações
  if (!task || task.trim().length === 0) {
    throw new AppError("Tarefa é obrigatória", 400);
  }

  let finalTeamDefinition: any;

  // Caso 1: Carregar do banco se teamId foi fornecido
  if (teamId) {
    console.log(`📥 Carregando Team ${teamId} do banco de dados...`);

    const team = await Team.findOne({
      where: { id: teamId, companyId },
      include: [
        {
          model: Agent,
          as: "agents",
          order: [["id", "ASC"]]
        }
      ]
    });

    if (!team) {
      throw new AppError("Equipe não encontrada", 404);
    }

    // Converter do formato Sequelize para o formato esperado pelo Python
    finalTeamDefinition = {
      id: team.id,
      name: team.name,
      description: team.description,
      processType: team.processType,
      temperature: team.temperature,
      verbose: team.verbose,
      managerLLM: team.managerLLM,
      managerAgentId: team.managerAgentId,
      agents: team.agents.map((agent: any) => ({
        id: agent.id,
        name: agent.name,
        function: agent.function,
        objective: agent.objective,
        backstory: agent.backstory,
        keywords: agent.keywords || [],
        customInstructions: agent.customInstructions,
        persona: agent.persona,
        doList: agent.doList || [],
        dontList: agent.dontList || [],
        isActive: agent.isActive,
        useKnowledgeBase: agent.useKnowledgeBase,
        knowledgeBaseIds: agent.knowledgeBases?.map((kb: any) => kb.documentId) || []
      }))
    };

    console.log(`✅ Team carregado: ${finalTeamDefinition.agents.length} agentes`);
  }
  // Caso 2: Usar teamDefinition fornecida diretamente
  else if (teamDefinition) {
    console.log("📝 Usando teamDefinition enviada pelo frontend");
    finalTeamDefinition = teamDefinition;
  } else {
    throw new AppError("teamId ou teamDefinition é obrigatório", 400);
  }

  // Proxy para o CrewAI Service (Python)
  try {
    console.log(`🚀 Enviando para CrewAI Service: ${crewaiServiceUrl}/api/v2/playground/run`);

    const { data } = await axios.post(
      `${crewaiServiceUrl}/api/v2/playground/run`,
      {
        teamDefinition: finalTeamDefinition,
        task,
        companyId
      },
      {
        timeout: 120000, // 2 minutos (execuções podem demorar)
        headers: {
          "Content-Type": "application/json"
        }
      }
    );

    console.log("✅ Resposta recebida do CrewAI Service");
    console.log(`   Success: ${data.success}`);
    console.log(`   Agent Used: ${data.agent_used}`);
    console.log(`   Agent ID: ${data.agent_id}`);
    console.log(`   Processing Time: ${data.processing_time}s`);
    console.log(`   Logs Length: ${data.execution_logs?.length || 0} chars`);
    console.log(`   Training Examples Used: ${data.training_examples_count || 0}`);

    return res.status(200).json({
      success: data.success,
      final_output: data.final_output,
      execution_logs: data.execution_logs,
      agent_used: data.agent_used,
      agent_id: data.agent_id,
      config_used: data.config_used,
      processing_time: data.processing_time,
      timestamp: data.timestamp,
      prompt_used: data.prompt_used,
      training_examples_used: data.training_examples_used,
      training_examples_count: data.training_examples_count
    });

  } catch (error: any) {
    console.error("❌ Erro ao chamar CrewAI Service:", error.message);

    if (error.response) {
      console.error("   Status:", error.response.status);
      console.error("   Data:", error.response.data);

      throw new AppError(
        error.response.data?.detail || error.response.data?.message || "Erro ao executar playground",
        error.response.status || 500
      );
    }

    if (error.code === "ECONNREFUSED") {
      throw new AppError(
        "Serviço CrewAI não disponível. Verifique se o serviço Python está rodando.",
        503
      );
    }

    if (error.code === "ETIMEDOUT" || error.code === "ECONNABORTED") {
      throw new AppError(
        "Timeout ao executar playground. A tarefa pode ser muito complexa ou o serviço está sobrecarregado.",
        504
      );
    }

    throw new AppError(
      error.message || "Erro ao executar playground",
      500
    );
  }
};
