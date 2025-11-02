# crewai-service/architect_service_simple.py - Serviço REST para o Agente Arquiteto (versão simples)

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from architect_simple import SimpleArchitectAgent

router = APIRouter(prefix="/architect", tags=["Architect"])

class GenerateTeamRequest(BaseModel):
    businessDescription: str
    industry: Optional[str] = ""
    companyId: int

class AnalyzeBusinessRequest(BaseModel):
    description: str
    industry: Optional[str] = ""

# Instância global do agente arquiteto simples
architect = SimpleArchitectAgent()

@router.post("/analyze-business")
async def analyze_business(request: AnalyzeBusinessRequest = Body(...)):
    """
    Analisa a descrição do negócio (versão simplificada)
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
    Gera automaticamente agentes de IA baseado na indústria
    Retorna apenas o blueprint - o salvamento no PostgreSQL será feito pelo backend Node.js
    """
    try:
        print(f"[SimpleArchitect] Gerando agentes para companyId: {request.companyId}")
        print(f"[SimpleArchitect] Indústria: {request.industry}")
        print(f"[SimpleArchitect] Descrição: {request.businessDescription[:100] if request.businessDescription else 'N/A'}...")

        industry = request.industry or "other"

        # Gerar agentes usando templates
        agents = architect.generate_agents(industry, request.businessDescription)

        print(f"[SimpleArchitect] Gerados {len(agents)} agentes com sucesso")

        # Retornar blueprint para o backend Node.js salvar no PostgreSQL
        return {
            "blueprint": {
                "agents": agents,
                "customTools": []  # Por enquanto, sem ferramentas customizadas
            },
            "analysis": {
                "industry": industry,
                "detected_complexity": "médio",
                "agent_count": len(agents),
                "summary": f"Equipe de {len(agents)} agentes para {industry}"
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
        return {
            "templates": {},
            "available_industries": ["ecommerce", "services", "technology", "health", "education", "finance", "retail", "real_estate", "other"],
            "total_templates": 9
        }

    except Exception as e:
        print(f"Erro ao obter templates: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter templates: {str(e)}")
