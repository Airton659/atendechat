# knowledge_service_router.py - Router para Knowledge Base

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from simple_knowledge_service import get_knowledge_service

router = APIRouter()

@router.post("/knowledge/upload")
async def upload_knowledge_document(
    file: UploadFile = File(...),
    team_id: str = Form(...),
    company_id: str = Form(...)
):
    """
    Upload e processamento de documento para knowledge base

    Args:
        file: Arquivo (PDF, DOCX, XLSX, TXT)
        team_id: ID da equipe
        company_id: ID da empresa

    Returns:
        {
            "document_id": str,
            "chunks_count": int,
            "word_count": int
        }
    """
    try:
        # Ler conteúdo do arquivo
        file_content = await file.read()

        # Obter extensão
        filename = file.filename
        extension = filename.split('.')[-1].lower() if filename else 'txt'

        # Validar tipo
        if extension not in ['pdf', 'docx', 'xlsx', 'xls', 'txt']:
            raise HTTPException(status_code=400, detail="Tipo de arquivo não suportado. Use PDF, DOCX, XLSX ou TXT.")

        # Processar documento
        knowledge_service = get_knowledge_service()
        result = await knowledge_service.process_document(
            team_id=team_id,
            file_content=file_content,
            filename=filename
        )

        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Erro ao processar documento'))

        return {
            "document_id": result['documentId'],
            "chunks_count": result['chunksCount'],
            "word_count": result['wordCount']
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao fazer upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge/documents/{document_id}")
async def delete_knowledge_document(document_id: str):
    """
    Deleta documento da knowledge base

    Args:
        document_id: ID do documento

    Returns:
        { "success": bool }
    """
    try:
        knowledge_service = get_knowledge_service()
        success = await knowledge_service.delete_document(document_id)

        if not success:
            raise HTTPException(status_code=404, detail="Documento não encontrado")

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao deletar: {e}")
        raise HTTPException(status_code=500, detail=str(e))
