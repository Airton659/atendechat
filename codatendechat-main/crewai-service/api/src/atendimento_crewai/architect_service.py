# api/src/atendimento_crewai/architect_service.py - Serviço REST para o Agente Arquiteto

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json

from .architect import ArchitectAgent, BusinessContext

router = APIRouter(prefix="/architect", tags=["Architect"])

class GenerateTeamRequest(BaseModel):
    businessDescription: str
    industry: Optional[str] = ""
    tenantId: str
    teamName: Optional[str] = ""

class AnalyzeBusinessRequest(BaseModel):
    description: str

class ImprovementRequest(BaseModel):
    currentBlueprint: Dict[str, Any]
    performanceData: Optional[Dict[str, Any]] = None

class AdaptIndustryRequest(BaseModel):
    baseBlueprint: Dict[str, Any]
    targetIndustry: str

# Instância global do agente arquiteto
architect = ArchitectAgent()

@router.post("/analyze-business")
async def analyze_business(request: AnalyzeBusinessRequest = Body(...)):
    """
    Analisa a descrição do negócio e extrai contexto estruturado
    """
    try:
        business_context = architect.analyze_business(request.description)

        return {
            "analysis": {
                "industry": business_context.industry,
                "size": business_context.size,
                "target_audience": business_context.target_audience,
                "main_goals": business_context.main_goals,
                "description": business_context.description
            },
            "suggestions": {
                "recommended_agents": _get_recommended_agents(business_context.industry),
                "tone_suggestion": _get_tone_suggestion(business_context.industry),
                "key_features": _get_key_features(business_context.industry)
            }
        }

    except Exception as e:
        print(f"Erro na análise do negócio: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao analisar negócio: {str(e)}")

@router.post("/generate-team")
async def generate_team(request: GenerateTeamRequest = Body(...)):
    """
    Gera automaticamente uma equipe de IA baseada na descrição do negócio e salva no Firestore
    """
    try:
        from firebase_admin import firestore
        from datetime import datetime

        db = firestore.client()

        # Analisar contexto do negócio
        business_context = BusinessContext(
            description=request.businessDescription,
            industry=request.industry or "outro"
        )

        # Gerar blueprint da equipe
        blueprint = architect.generate_team_blueprint(business_context)

        # Adicionar metadados
        blueprint["tenantId"] = request.tenantId
        blueprint["createdBy"] = "architect_ai"
        blueprint["version"] = "1.0"
        blueprint["status"] = "draft"
        blueprint["createdAt"] = datetime.utcnow().isoformat()
        blueprint["updatedAt"] = datetime.utcnow().isoformat()

        if request.teamName:
            blueprint["name"] = request.teamName

        # Salvar no Firestore
        doc_ref = db.collection('crews').document()
        doc_ref.set(blueprint)
        blueprint["id"] = doc_ref.id

        # Incluir sugestões de melhorias
        suggestions = architect.suggest_improvements(blueprint)

        return {
            "id": doc_ref.id,
            "blueprint": blueprint,
            "analysis": {
                "industry": business_context.industry,
                "detected_complexity": _assess_complexity(blueprint),
                "agent_count": len(blueprint.get("agents", {})),
                "recommended_tools": _extract_recommended_tools(blueprint),
                "summary": f"Equipe de {len(blueprint.get('agents', {}))} agentes para {business_context.industry}"
            },
            "suggestions": suggestions,
            "next_steps": [
                "Revise os agentes gerados e personalize conforme necessário",
                "Adicione conhecimento específico da sua empresa",
                "Teste a equipe com cenários reais",
                "Ative a equipe quando estiver satisfeito"
            ]
        }

    except Exception as e:
        print(f"Erro na geração da equipe: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar equipe: {str(e)}")

@router.post("/suggest-improvements")
async def suggest_improvements(request: ImprovementRequest = Body(...)):
    """
    Sugere melhorias para uma equipe existente baseado em performance
    """
    try:
        suggestions = architect.suggest_improvements(
            request.currentBlueprint,
            request.performanceData
        )

        # Análise detalhada
        detailed_analysis = _analyze_blueprint_details(request.currentBlueprint)

        return {
            "suggestions": suggestions,
            "analysis": detailed_analysis,
            "score": _calculate_blueprint_score(request.currentBlueprint),
            "optimization_opportunities": _find_optimization_opportunities(request.currentBlueprint)
        }

    except Exception as e:
        print(f"Erro ao sugerir melhorias: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao sugerir melhorias: {str(e)}")

@router.post("/adapt-industry")
async def adapt_for_industry(request: AdaptIndustryRequest = Body(...)):
    """
    Adapta uma equipe existente para um setor específico
    """
    try:
        adapted_blueprint = architect.adapt_for_industry(
            request.baseBlueprint,
            request.targetIndustry
        )

        return {
            "adapted_blueprint": adapted_blueprint,
            "changes_made": _compare_blueprints(request.baseBlueprint, adapted_blueprint),
            "industry_insights": _get_industry_insights(request.targetIndustry)
        }

    except Exception as e:
        print(f"Erro ao adaptar para setor: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao adaptar para setor: {str(e)}")

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

@router.post("/validate-blueprint")
async def validate_blueprint(blueprint: Dict[str, Any] = Body(...)):
    """
    Valida a estrutura e completude de um blueprint
    """
    try:
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "completeness_score": 0,
            "missing_elements": []
        }

        # Validações básicas
        required_fields = ["name", "agents", "workflow"]
        for field in required_fields:
            if field not in blueprint:
                validation_result["errors"].append(f"Campo obrigatório '{field}' não encontrado")

        # Validar agentes
        if "agents" in blueprint:
            agents = blueprint["agents"]
            if not agents:
                validation_result["errors"].append("Pelo menos um agente é obrigatório")

            for agent_key, agent in agents.items():
                required_agent_fields = ["name", "role", "goal"]
                for field in required_agent_fields:
                    if field not in agent:
                        validation_result["errors"].append(f"Agente '{agent_key}' está sem o campo '{field}'")

        # Validar workflow
        if "workflow" in blueprint:
            workflow = blueprint["workflow"]
            if "entryPoint" not in workflow:
                validation_result["warnings"].append("Ponto de entrada não definido no workflow")

            entry_point = workflow.get("entryPoint")
            if entry_point and entry_point not in blueprint.get("agents", {}):
                validation_result["errors"].append("Agente de entrada não existe na equipe")

        # Calcular score de completude
        total_elements = 10
        completed_elements = 0

        if blueprint.get("name"): completed_elements += 1
        if blueprint.get("description"): completed_elements += 1
        if blueprint.get("config"): completed_elements += 1
        if blueprint.get("agents"): completed_elements += 2
        if blueprint.get("workflow"): completed_elements += 1

        # Verificar qualidade dos agentes
        agents = blueprint.get("agents", {})
        if agents:
            agent_quality = sum(1 for agent in agents.values()
                              if agent.get("personality") and agent.get("backstory"))
            completed_elements += min(4, agent_quality)

        validation_result["completeness_score"] = (completed_elements / total_elements) * 100
        validation_result["valid"] = len(validation_result["errors"]) == 0

        return validation_result

    except Exception as e:
        print(f"Erro ao validar blueprint: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao validar blueprint: {str(e)}")

# Funções auxiliares
def _get_recommended_agents(industry: str) -> List[str]:
    """Retorna agentes recomendados para o setor"""
    recommendations = {
        "imobiliaria": ["triagem", "vendas", "agendamento", "suporte"],
        "restaurante": ["triagem", "cardapio", "pedidos", "suporte"],
        "e-commerce": ["triagem", "vendas", "suporte", "pos_venda"],
        "saude": ["triagem", "agendamento", "emergencia", "suporte"],
        "educacao": ["triagem", "informacoes", "matriculas", "suporte"],
        "servicos": ["triagem", "orcamento", "agendamento", "suporte"],
        "tecnologia": ["triagem", "suporte_tecnico", "vendas", "consultoria"]
    }
    return recommendations.get(industry, ["triagem", "geral", "suporte"])

def _get_tone_suggestion(industry: str) -> str:
    """Sugere tom apropriado para o setor"""
    tone_map = {
        "saude": "professional",
        "educacao": "friendly",
        "tecnologia": "technical",
        "imobiliaria": "professional",
        "restaurante": "friendly"
    }
    return tone_map.get(industry, "friendly")

def _get_key_features(industry: str) -> List[str]:
    """Retorna características chave para o setor"""
    features = {
        "imobiliaria": ["qualificação de leads", "agendamento de visitas", "follow-up"],
        "restaurante": ["consulta de cardápio", "pedidos online", "suporte"],
        "e-commerce": ["consulta de produtos", "suporte pós-venda", "rastreamento"],
        "saude": ["agendamento de consultas", "triagem de sintomas", "emergências"],
        "educacao": ["informações sobre cursos", "processo de matrícula", "suporte acadêmico"]
    }
    return features.get(industry, ["atendimento geral", "suporte", "informações"])

def _assess_complexity(blueprint: Dict[str, Any]) -> str:
    """Avalia a complexidade do blueprint"""
    agent_count = len(blueprint.get("agents", {}))

    if agent_count <= 3:
        return "simples"
    elif agent_count <= 6:
        return "médio"
    else:
        return "complexo"

def _extract_recommended_tools(blueprint: Dict[str, Any]) -> List[str]:
    """Extrai ferramentas recomendadas do blueprint"""
    tools = set()
    for agent in blueprint.get("agents", {}).values():
        agent_tools = agent.get("tools", [])
        tools.update(agent_tools)
    return list(tools)

def _analyze_blueprint_details(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    """Análise detalhada do blueprint"""
    agents = blueprint.get("agents", {})

    return {
        "agent_count": len(agents),
        "agents_with_tools": sum(1 for agent in agents.values() if agent.get("tools")),
        "agents_with_personality": sum(1 for agent in agents.values() if agent.get("personality")),
        "workflow_complexity": len(blueprint.get("workflow", {}).get("escalationRules", [])),
        "has_fallback": bool(blueprint.get("workflow", {}).get("fallbackAgent")),
        "active_agents": sum(1 for agent in agents.values() if agent.get("isActive", True))
    }

def _calculate_blueprint_score(blueprint: Dict[str, Any]) -> int:
    """Calcula score de qualidade do blueprint"""
    score = 0

    # Pontuação base
    if blueprint.get("name"): score += 10
    if blueprint.get("description"): score += 10

    # Pontuação por agentes
    agents = blueprint.get("agents", {})
    score += len(agents) * 5

    # Qualidade dos agentes
    for agent in agents.values():
        if agent.get("personality"): score += 5
        if agent.get("backstory"): score += 3
        if agent.get("tools"): score += 2

    # Workflow
    workflow = blueprint.get("workflow", {})
    if workflow.get("entryPoint"): score += 10
    if workflow.get("fallbackAgent"): score += 5

    return min(score, 100)

def _find_optimization_opportunities(blueprint: Dict[str, Any]) -> List[str]:
    """Encontra oportunidades de otimização"""
    opportunities = []

    agents = blueprint.get("agents", {})

    # Verificar agentes sem ferramentas
    agents_without_tools = [name for name, agent in agents.items()
                           if not agent.get("tools")]
    if len(agents_without_tools) > len(agents) * 0.5:
        opportunities.append("Muitos agentes sem ferramentas. Considere adicionar ferramentas relevantes.")

    # Verificar agentes sem personalidade
    agents_without_personality = [name for name, agent in agents.items()
                                 if not agent.get("personality")]
    if agents_without_personality:
        opportunities.append("Alguns agentes não têm personalidade definida.")

    # Verificar workflow
    workflow = blueprint.get("workflow", {})
    if not workflow.get("escalationRules"):
        opportunities.append("Considere adicionar regras de escalação para melhor fluxo.")

    return opportunities

def _compare_blueprints(original: Dict[str, Any], adapted: Dict[str, Any]) -> List[str]:
    """Compara dois blueprints e lista as mudanças"""
    changes = []

    original_agents = set(original.get("agents", {}).keys())
    adapted_agents = set(adapted.get("agents", {}).keys())

    added_agents = adapted_agents - original_agents
    removed_agents = original_agents - adapted_agents

    if added_agents:
        changes.append(f"Agentes adicionados: {', '.join(added_agents)}")
    if removed_agents:
        changes.append(f"Agentes removidos: {', '.join(removed_agents)}")

    # Comparar workflow
    original_workflow = original.get("workflow", {})
    adapted_workflow = adapted.get("workflow", {})

    if original_workflow != adapted_workflow:
        changes.append("Workflow modificado")

    return changes

def _get_industry_insights(industry: str) -> Dict[str, Any]:
    """Retorna insights específicos do setor"""
    insights = {
        "imobiliaria": {
            "key_metrics": ["tempo de resposta", "leads qualificados", "agendamentos"],
            "common_challenges": ["qualificação de leads", "agendamento de visitas"],
            "best_practices": ["resposta rápida", "qualificação detalhada"]
        },
        "restaurante": {
            "key_metrics": ["pedidos processados", "tempo de atendimento", "satisfação"],
            "common_challenges": ["horário de pico", "mudanças no cardápio"],
            "best_practices": ["cardápio sempre atualizado", "opções de entrega"]
        }
    }

    return insights.get(industry, {
        "key_metrics": ["satisfação do cliente", "tempo de resposta"],
        "common_challenges": ["volume de atendimento"],
        "best_practices": ["resposta rápida", "atendimento personalizado"]
    })