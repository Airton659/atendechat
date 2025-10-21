# api/src/atendimento_crewai/crews_service.py - CRUD de Crews no Firestore

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from firebase_admin import firestore

router = APIRouter(prefix="/crews", tags=["Crews"])

# Firestore client
db = firestore.client()

class CreateCrewRequest(BaseModel):
    tenantId: str
    name: str
    description: str
    industry: Optional[str] = None
    objective: Optional[str] = None
    tone: Optional[str] = "professional"
    createdBy: Optional[str] = None
    agents: Optional[Dict[str, Any]] = None

class UpdateCrewRequest(BaseModel):
    tenantId: str
    name: Optional[str] = None
    description: Optional[str] = None
    agents: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    workflow: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    customTools: Optional[List[Any]] = None
    training: Optional[Dict[str, Any]] = None

@router.get("")
async def list_crews(tenantId: str = Query(...)):
    """
    Lista todas as crews de um tenant
    """
    try:
        crews_ref = db.collection('crews')
        query = crews_ref.where('tenantId', '==', tenantId)

        crews = []
        for doc in query.stream():
            crew_data = doc.to_dict()
            crew_data['id'] = doc.id
            crews.append(crew_data)

        return crews
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing crews: {str(e)}")

@router.get("/{crew_id}")
async def get_crew(crew_id: str, tenantId: str = Query(...)):
    """
    Busca uma crew por ID
    """
    try:
        doc_ref = db.collection('crews').document(crew_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Crew not found")

        crew_data = doc.to_dict()

        # Verificar se pertence ao tenant
        if crew_data.get('tenantId') != tenantId:
            raise HTTPException(status_code=403, detail="Access denied")

        crew_data['id'] = doc.id
        return crew_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching crew: {str(e)}")

@router.post("")
async def create_crew(request: CreateCrewRequest):
    """
    Cria uma nova crew
    """
    try:
        crew_data = {
            "tenantId": request.tenantId,
            "name": request.name,
            "description": request.description,
            "status": "draft",
            "version": "1.0",
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
            "config": {
                "industry": request.industry or "",
                "objective": request.objective or request.description,
                "tone": request.tone,
                "language": "pt-BR"
            },
            "agents": request.agents if request.agents else {},
            "workflow": {
                "entryPoint": "geral",
                "fallbackAgent": "geral",
                "escalationRules": []
            },
            "customTools": [],
            "training": {
                "guardrails": {
                    "do": [],
                    "dont": []
                },
                "persona": request.description,
                "examples": []
            },
            "metrics": {
                "totalConversations": 0,
                "avgResponseTime": 0,
                "satisfactionRate": 0,
                "lastUsed": None
            }
        }

        if request.createdBy:
            crew_data["createdBy"] = request.createdBy

        # Adicionar ao Firestore
        doc_ref = db.collection('crews').document()
        doc_ref.set(crew_data)

        crew_data['id'] = doc_ref.id
        return crew_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating crew: {str(e)}")

@router.put("/{crew_id}")
async def update_crew(crew_id: str, request: UpdateCrewRequest):
    """
    Atualiza uma crew existente
    """
    try:
        doc_ref = db.collection('crews').document(crew_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Crew not found")

        crew_data = doc.to_dict()

        # Verificar se pertence ao tenant
        if crew_data.get('tenantId') != request.tenantId:
            raise HTTPException(status_code=403, detail="Access denied")

        # Preparar dados para atualização
        update_data = {
            "updatedAt": datetime.utcnow().isoformat()
        }

        if request.name is not None:
            update_data["name"] = request.name

        if request.description is not None:
            update_data["description"] = request.description

        if request.agents is not None:
            update_data["agents"] = request.agents

        if request.config is not None:
            update_data["config"] = request.config

        if request.workflow is not None:
            update_data["workflow"] = request.workflow

        if request.status is not None:
            update_data["status"] = request.status

        if request.customTools is not None:
            update_data["customTools"] = request.customTools

        if request.training is not None:
            update_data["training"] = request.training

        # Atualizar no Firestore
        doc_ref.update(update_data)

        # Buscar dados atualizados
        updated_doc = doc_ref.get()
        result = updated_doc.to_dict()
        result['id'] = crew_id

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating crew: {str(e)}")

@router.delete("/{crew_id}")
async def delete_crew(crew_id: str, tenantId: str = Query(...)):
    """
    Deleta uma crew
    """
    try:
        doc_ref = db.collection('crews').document(crew_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Crew not found")

        crew_data = doc.to_dict()

        # Verificar se pertence ao tenant
        if crew_data.get('tenantId') != tenantId:
            raise HTTPException(status_code=403, detail="Access denied")

        # Deletar do Firestore
        doc_ref.delete()

        return {"message": "Crew deleted successfully", "id": crew_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting crew: {str(e)}")
