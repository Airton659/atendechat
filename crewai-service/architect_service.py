# architect_service.py - Serviço REST para o Agente Arquiteto com IA

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from architect import ArchitectAgent, BusinessContext

router = APIRouter(prefix="/architect", tags=["Architect"])

class GenerateTeamRequest(BaseModel):
    businessDescription: str
    industry: Optional[str] = ""
    companyId: int
    teamName: Optional[str] = ""

class AnalyzeBusinessRequest(BaseModel):
    description: str
    industry: Optional[str] = ""

# Instância global do agente arquiteto com IA
architect = ArchitectAgent()

@router.post("/analyze-business")
async def analyze_business(request: AnalyzeBusinessRequest = Body(...)):
    """
    Analisa a descrição do negócio
    """
    try:
        industry = request.industry or "other"

        return {
            "analysis": {
                "industry": industry,
                "size": "médio",
                "target_audience": "clientes",
                "main_goals": ["atendimento eficiente", "satisfação do cliente"],
                "description": request.description
            }
        }

    except Exception as e:
        print(f"Erro na análise do negócio: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao analisar negócio: {str(e)}")

@router.post("/generate-team")
async def generate_team(request: GenerateTeamRequest = Body(...)):
    """
    Gera automaticamente agentes de IA usando Vertex AI
    Retorna apenas o blueprint - o salvamento no PostgreSQL será feito pelo backend Node.js
    """
    try:
        print(f"[Architect AI] Gerando equipe para companyId: {request.companyId}")
        print(f"[Architect AI] Indústria: {request.industry}")
        print(f"[Architect AI] Descrição: {request.businessDescription[:100] if request.businessDescription else 'N/A'}...")

        industry = request.industry or "other"

        # Criar contexto do negócio
        business_context = BusinessContext(
            description=request.businessDescription,
            industry=industry
        )

        # Gerar agentes usando IA
        blueprint = architect.generate_team_blueprint(business_context)

        agents_count = len(blueprint.get("agents", []))
        print(f"[Architect AI] Gerados {agents_count} agentes com IA")

        # Gerar nome da equipe usando IA se não foi fornecido
        team_name = request.teamName
        if not team_name:
            team_name = architect.generate_team_name(business_context)
            print(f"[Architect AI] Nome gerado: {team_name}")

        # Retornar blueprint para o backend Node.js salvar no PostgreSQL
        return {
            "blueprint": blueprint,
            "teamName": team_name,
            "analysis": {
                "industry": industry,
                "detected_complexity": "médio",
                "agent_count": agents_count,
                "summary": f"Equipe de {agents_count} agentes para {industry}"
            },
            "suggestions": [
                "Revise os agentes gerados e personalize conforme necessário",
                "Adicione palavras-chave específicas do seu negócio",
                "Teste os agentes com cenários reais",
                "Ative os agentes quando estiver satisfeito"
            ],
            "next_steps": [
                "Revisar e personalizar agentes gerados",
                "Adicionar conhecimento específico da empresa",
                "Testar com cenários reais",
                "Ativar quando satisfeito"
            ]
        }

    except Exception as e:
        print(f"Erro na geração da equipe: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar equipe: {str(e)}")

@router.get("/templates")
async def get_industry_templates():
    """
    Retorna templates pré-configurados para diferentes setores
    """
    try:
        templates = {
            "healthcare": "Equipe para clínicas e hospitais",
            "retail": "Equipe para varejo e comércio",
            "services": "Equipe para prestadores de serviços",
            "education": "Equipe para instituições de ensino",
            "technology": "Equipe para empresas de tecnologia"
        }

        return {"templates": templates}

    except Exception as e:
        print(f"Erro ao buscar templates: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar templates: {str(e)}")
