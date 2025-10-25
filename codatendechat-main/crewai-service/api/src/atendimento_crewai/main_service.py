# api/src/atendimento_crewai/main_service.py - Serviço Principal da Nova API CrewAI

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import time
from datetime import datetime

from .crew_engine_simple import SimpleCrewEngine
from .architect_service import router as architect_router
from .knowledge_service import router as knowledge_router
from .training_service import router as training_router

# Router principal
router = APIRouter()

# Instância do motor CrewAI simplificado
crew_engine = SimpleCrewEngine()

# Incluir sub-routers
router.include_router(architect_router)
router.include_router(knowledge_router)
router.include_router(training_router)

class ProcessMessageRequest(BaseModel):
    tenantId: str
    crewId: str
    message: str
    conversationHistory: Optional[List[Dict[str, Any]]] = []
    agentOverride: Optional[str] = None
    remoteJid: Optional[str] = None  # Número do WhatsApp do cliente
    contactId: Optional[int] = None  # ID do contato
    ticketId: Optional[int] = None  # ID do ticket

class ValidateCrewRequest(BaseModel):
    crewBlueprint: Dict[str, Any]

@router.get("/health")
async def health_check():
    """Verificação de saúde da API"""
    return {
        "status": "healthy",
        "service": "CrewAI API",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@router.post("/process-message")
async def process_message(request: ProcessMessageRequest = Body(...)):
    """
    Processa uma mensagem usando o sistema CrewAI
    """
    try:
        start_time = time.time()

        if not request.message or len(request.message.strip()) < 1:
            raise HTTPException(status_code=400, detail="Mensagem é obrigatória")

        if not request.tenantId or not request.crewId:
            raise HTTPException(status_code=400, detail="TenantId e CrewId são obrigatórios")

        # Processar mensagem
        result = await crew_engine.process_message(
            tenant_id=request.tenantId,
            crew_id=request.crewId,
            message=request.message,
            conversation_history=request.conversationHistory,
            agent_override=request.agentOverride,
            remote_jid=request.remoteJid,
            contact_id=request.contactId,
            ticket_id=request.ticketId
        )

        # Adicionar métricas
        processing_time = time.time() - start_time
        result["processing_time"] = round(processing_time, 2)
        result["timestamp"] = datetime.now().isoformat()

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/crews/{tenant_id}/{crew_id}/agents")
async def get_crew_agents(tenant_id: str, crew_id: str):
    """
    Retorna lista de agentes disponíveis na equipe
    """
    try:
        agents = await crew_engine.get_available_agents(tenant_id, crew_id)

        return {
            "agents": agents,
            "total": len(agents),
            "crew_id": crew_id
        }

    except Exception as e:
        print(f"Erro ao obter agentes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/validate-crew")
async def validate_crew(request: ValidateCrewRequest = Body(...)):
    """
    Valida configuração de uma equipe para CrewAI
    """
    try:
        validation = await crew_engine.validate_crew_config(request.crewBlueprint)

        return {
            "validation": validation,
            "compatible": validation["valid"],
            "recommendations": _generate_crew_recommendations(validation)
        }

    except Exception as e:
        print(f"Erro ao validar equipe: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/capabilities")
async def get_capabilities():
    """
    Retorna capacidades e recursos disponíveis da API
    """
    return {
        "features": {
            "crew_ai": True,
            "knowledge_base": True,
            "interactive_training": True,
            "architect_agent": True,
            "vector_search": True,
            "multi_tenant": True
        },
        "supported_tools": [
            "consultar_base_conhecimento"
        ],
        "supported_file_types": [
            "pdf", "docx", "txt", "xlsx", "csv"
        ],
        "llm_models": [
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-pro"
        ],
        "max_agents_per_crew": 20,
        "max_conversation_history": 50
    }

@router.get("/stats/{tenant_id}")
async def get_tenant_stats(tenant_id: str):
    """
    Obtém estatísticas gerais do tenant
    """
    try:
        from firebase_admin import firestore
        db = firestore.client()

        stats = {
            "crews": 0,
            "active_crews": 0,
            "total_agents": 0,
            "knowledge_documents": 0,
            "training_sessions": 0,
            "last_activity": None
        }

        # Contar equipes
        crews_query = db.collection('crew_blueprints').where('tenantId', '==', tenant_id).get()
        stats["crews"] = len(crews_query.docs)

        total_agents = 0
        active_crews = 0
        for crew_doc in crews_query:
            crew_data = crew_doc.to_dict()
            if crew_data.get('status') == 'active':
                active_crews += 1

            agents = crew_data.get('agents', {})
            total_agents += len(agents)

        stats["active_crews"] = active_crews
        stats["total_agents"] = total_agents

        # Contar documentos de conhecimento
        kb_query = db.collection('knowledge_bases').where('tenantId', '==', tenant_id).get()
        total_docs = 0
        for kb_doc in kb_query:
            kb_data = kb_doc.to_dict()
            documents = kb_data.get('documents', [])
            total_docs += len(documents)

        stats["knowledge_documents"] = total_docs

        # Contar sessões de treinamento
        training_query = db.collection('training_sessions').where('tenantId', '==', tenant_id).get()
        stats["training_sessions"] = len(training_query.docs)

        # Última atividade (simplificado)
        if crews_query.docs:
            latest_crew = max(crews_query.docs, key=lambda x: x.to_dict().get('updatedAt', datetime.min))
            stats["last_activity"] = latest_crew.to_dict().get('updatedAt')

        return stats

    except Exception as e:
        print(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/migrate-from-autogen")
async def migrate_from_autogen(
    tenant_id: str = Body(...),
    legacy_crew_id: str = Body(...),
    preserve_history: bool = Body(default=True)
):
    """
    Migra uma equipe do sistema AutoGen para CrewAI
    """
    try:
        from firebase_admin import firestore
        db = firestore.client()

        # Buscar equipe legacy
        legacy_doc = db.collection('crews').document(legacy_crew_id).get()

        if not legacy_doc.exists:
            raise HTTPException(status_code=404, detail="Equipe legacy não encontrada")

        legacy_data = legacy_doc.to_dict()

        if legacy_data.get('tenantId') != tenant_id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Converter para formato CrewAI
        migrated_blueprint = _convert_autogen_to_crewai(legacy_data)
        migrated_blueprint['tenantId'] = tenant_id
        migrated_blueprint['migratedFrom'] = 'autogen'
        migrated_blueprint['migratedAt'] = datetime.now()

        # Salvar nova equipe
        new_crew_ref = db.collection('crew_blueprints').add(migrated_blueprint)

        # Marcar legacy como migrada (opcional)
        if preserve_history:
            db.collection('crews').document(legacy_crew_id).update({
                'status': 'migrated',
                'migratedTo': new_crew_ref[1].id,
                'migratedAt': datetime.now()
            })

        return {
            "success": True,
            "new_crew_id": new_crew_ref[1].id,
            "migrated_blueprint": migrated_blueprint,
            "message": "Migração concluída com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro na migração: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/superadmin/tenants")
async def list_all_tenants():
    """
    Lista todos os tenants do sistema (superadmin)
    """
    try:
        from firebase_admin import firestore
        db = firestore.client()

        tenants = []
        tenants_ref = db.collection('tenants').stream()

        for tenant_doc in tenants_ref:
            tenant_data = tenant_doc.to_dict()
            tenants.append({
                "id": tenant_doc.id,
                "name": tenant_data.get('name', 'Sem nome'),
                "status": tenant_data.get('status', 'active'),
                "createdAt": tenant_data.get('createdAt'),
                "plan": tenant_data.get('plan', 'free')
            })

        return {"tenants": tenants}

    except Exception as e:
        print(f"Erro ao listar tenants: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/superadmin/crews")
async def list_all_crews():
    """
    Lista todas as equipes de todos os tenants (superadmin)
    """
    try:
        from firebase_admin import firestore
        db = firestore.client()

        crews = []
        crews_ref = db.collection('crew_blueprints').stream()

        for crew_doc in crews_ref:
            crew_data = crew_doc.to_dict()

            # Os agentes estão no nível raiz do documento, não dentro de blueprint
            # Estrutura: { agents: {...}, blueprint: {...}, ... }

            crews.append({
                "id": crew_doc.id,
                "name": crew_data.get('name', 'Sem nome'),
                "tenantId": crew_data.get('tenantId'),
                "status": crew_data.get('status', 'draft'),
                "createdAt": crew_data.get('createdAt'),
                "updatedAt": crew_data.get('updatedAt'),
                "agents": crew_data.get('agents', {}),  # Agentes no nível raiz
                "blueprint": crew_data.get('blueprint', {})  # Blueprint para outras configs
            })

        return {"crews": crews}

    except Exception as e:
        print(f"Erro ao listar equipes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Funções auxiliares

def _generate_crew_recommendations(validation: Dict[str, Any]) -> List[str]:
    """Gera recomendações baseadas na validação"""
    recommendations = []

    if validation["agent_count"] == 0:
        recommendations.append("Adicione pelo menos um agente à equipe")
    elif validation["agent_count"] > 10:
        recommendations.append("Considere reduzir o número de agentes para melhor performance")

    if validation["tools_count"] == 0:
        recommendations.append("Considere adicionar ferramentas aos agentes para maior funcionalidade")

    if validation["errors"]:
        recommendations.append("Corrija os erros listados antes de ativar a equipe")

    if validation["warnings"]:
        recommendations.append("Revise os avisos para otimizar a configuração")

    return recommendations

def _convert_autogen_to_crewai(legacy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Converte dados do AutoGen para formato CrewAI"""

    # Template base CrewAI
    crewai_blueprint = {
        "name": legacy_data.get('name', 'Equipe Migrada'),
        "description": legacy_data.get('description', ''),
        "status": "draft",
        "version": "2.0",
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),

        "config": {
            "industry": legacy_data.get('industry', ''),
            "objective": legacy_data.get('objective', ''),
            "tone": "friendly",
            "language": "pt-BR"
        },

        "agents": {},

        "workflow": {
            "entryPoint": "triagem",
            "fallbackAgent": "geral",
            "escalationRules": []
        },

        "metrics": {
            "totalConversations": 0,
            "avgResponseTime": 0,
            "satisfactionRate": 0,
            "lastUsed": None
        }
    }

    # Converter agentes
    legacy_agents = legacy_data.get('agentes', {})
    for agent_key, agent_config in legacy_agents.items():
        crewai_agent = {
            "name": agent_config.get('name', agent_key.title()),
            "role": agent_config.get('role', 'assistente'),
            "goal": agent_config.get('goal', 'ajudar o usuário'),
            "backstory": agent_config.get('backstory', ''),
            "personality": {
                "tone": "friendly",
                "traits": ["prestativo", "eficiente"],
                "customInstructions": ""
            },
            "tools": ["consultar_base_conhecimento"] if agent_config.get('usa_ferramentas') else [],
            "isActive": True,
            "order": len(crewai_blueprint["agents"]) + 1
        }

        crewai_blueprint["agents"][agent_key] = crewai_agent

    return crewai_blueprint