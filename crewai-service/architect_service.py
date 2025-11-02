# crewai-service/architect_service.py - Serviço REST para o Agente Arquiteto

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json

from architect import ArchitectAgent, BusinessContext

router = APIRouter(prefix="/architect", tags=["Architect"])

class GenerateTeamRequest(BaseModel):
    businessDescription: str
    industry: Optional[str] = ""
    companyId: int

class AnalyzeBusinessRequest(BaseModel):
    description: str
    industry: Optional[str] = ""

# Instância global do agente arquiteto
architect = ArchitectAgent()

@router.post("/analyze-business")
async def analyze_business(request: AnalyzeBusinessRequest = Body(...)):
    """
    Analisa a descrição do negócio e extrai contexto estruturado
    """
    try:
        business_context = architect.analyze_business(
            request.description,
            request.industry
        )

        return {
            "analysis": {
                "industry": business_context.industry,
                "size": business_context.size,
                "target_audience": business_context.target_audience,
                "main_goals": business_context.main_goals,
                "description": business_context.description
            }
        }

    except Exception as e:
        print(f"Erro na análise do negócio: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao analisar negócio: {str(e)}")

@router.post("/generate-team")
async def generate_team(request: GenerateTeamRequest = Body(...)):
    """
    Gera automaticamente agentes de IA baseado na descrição do negócio
    Retorna apenas o blueprint - o salvamento no PostgreSQL será feito pelo backend Node.js
    """
    try:
        print(f"[Architect] Gerando agentes para companyId: {request.companyId}")
        print(f"[Architect] Indústria: {request.industry}")
        print(f"[Architect] Descrição: {request.businessDescription[:100]}...")

        # Analisar contexto do negócio
        business_context = BusinessContext(
            description=request.businessDescription,
            industry=request.industry or "other"
        )

        # Gerar blueprint dos agentes
        agents = architect.generate_agents_blueprint(business_context)

        print(f"[Architect] Gerados {len(agents)} agentes com sucesso")

        # Retornar blueprint para o backend Node.js salvar no PostgreSQL
        return {
            "blueprint": {
                "agents": agents,
                "customTools": []  # Por enquanto, sem ferramentas customizadas
            },
            "analysis": {
                "industry": business_context.industry,
                "detected_complexity": "médio",
                "agent_count": len(agents),
                "summary": f"Equipe de {len(agents)} agentes para {business_context.industry}"
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
            "templates": architect.industry_templates,
            "available_industries": list(architect.industry_templates.keys()),
            "total_templates": len(architect.industry_templates)
        }

    except Exception as e:
        print(f"Erro ao obter templates: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter templates: {str(e)}")

# Funções auxiliares
def _get_recommended_agents(industry: str) -> List[str]:
    """Retorna agentes recomendados para o setor"""
    recommendations = {
        "real_estate": ["triagem", "vendas", "agendamento", "suporte"],
        "ecommerce": ["triagem", "vendas", "suporte", "pos_venda"],
        "health": ["triagem", "agendamento", "emergencia", "suporte"],
        "education": ["triagem", "informacoes", "matriculas", "suporte"],
        "services": ["triagem", "orcamento", "agendamento", "suporte"],
        "technology": ["triagem", "suporte_tecnico", "vendas", "consultoria"],
        "finance": ["triagem", "consultoria", "suporte", "cobranca"],
        "retail": ["triagem", "vendas", "estoque", "suporte"]
    }
    return recommendations.get(industry, ["triagem", "geral", "suporte"])
