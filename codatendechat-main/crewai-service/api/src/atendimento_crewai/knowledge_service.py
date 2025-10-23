# api/src/atendimento_crewai/knowledge_service.py - Serviço de Processamento de Conhecimento

from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import json
import tempfile
from datetime import datetime
import hashlib

# Imports para processamento de documentos
import PyPDF2
from docx import Document
import pandas as pd
from pathlib import Path

# Imports para embeddings e busca vetorial
import vertexai
from vertexai.language_models import TextEmbeddingModel
from firebase_admin import firestore

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

# Classes antigas removidas - não são mais usadas

class KnowledgeService:
    def __init__(self):
        # Configurar modelo de embeddings
        # IMPORTANTE: Location já foi configurado em vertexai.init() no main.py (southamerica-east1)
        # Não precisa passar location aqui

        try:
            # Modelos de embedding disponíveis (2025) para southamerica-east1
            # Fonte: https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings
            embedding_models = [
                "text-embedding-005",  # Especializado em inglês e código
                "text-multilingual-embedding-002",  # Multilíngue
                "text-embedding-004",
                "textembedding-gecko@003",
                "textembedding-gecko@latest",
                "textembedding-gecko"
            ]

            self.embedding_model = None
            for model_name in embedding_models:
                try:
                    print(f"   Tentando modelo de embedding: {model_name}")
                    self.embedding_model = TextEmbeddingModel.from_pretrained(model_name)
                    print(f"✅ Modelo de embeddings carregado: {model_name}")
                    break
                except Exception as e:
                    print(f"   ⚠️ {model_name} não disponível: {str(e)[:150]}")
                    continue

            if not self.embedding_model:
                raise Exception("Nenhum modelo de embedding disponível")

        except Exception as e:
            print(f"⚠️ Erro ao carregar modelos de embedding: {e}")
            print("📝 Continuando sem embeddings (busca por palavra-chave apenas)")
            self.embedding_model = None

        self.chunk_size = 1000  # Tamanho máximo dos chunks
        self.chunk_overlap = 200  # Sobreposição entre chunks

        # Bucket para armazenamento de arquivos
        self.bucket_name = "atende-saas-kb-files"

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extrai texto de arquivo PDF"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Erro ao extrair texto do PDF: {str(e)}")

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extrai texto de arquivo Word"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Erro ao extrair texto do Word: {str(e)}")

    def extract_text_from_txt(self, file_path: str) -> str:
        """Extrai texto de arquivo de texto"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            try:
                # Tentar com codificação latin-1 se UTF-8 falhar
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read().strip()
            except:
                raise Exception(f"Erro ao extrair texto do arquivo: {str(e)}")

    def extract_text_from_excel(self, file_path: str) -> str:
        """Extrai texto de planilha Excel/CSV"""
        try:
            # Detectar tipo de arquivo
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            # Converter para texto estruturado
            text = ""
            for index, row in df.iterrows():
                row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                text += row_text + "\n"

            return text.strip()
        except Exception as e:
            raise Exception(f"Erro ao extrair dados da planilha: {str(e)}")

    def extract_text_from_document(self, file_path: str, file_type: str) -> str:
        """Extrai texto baseado no tipo do documento"""
        extractors = {
            'pdf': self.extract_text_from_pdf,
            'text': self.extract_text_from_txt,
            'word': self.extract_text_from_docx,
            'excel': self.extract_text_from_excel,
            'powerpoint': self.extract_text_from_txt  # Fallback para PPT
        }

        extractor = extractors.get(file_type, self.extract_text_from_txt)
        return extractor(file_path)

    def create_chunks(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Divide o texto em chunks menores"""
        if not text or len(text.strip()) == 0:
            return []

        chunks = []
        text = text.strip()

        # Dividir por parágrafos primeiro
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        current_chunk = ""
        chunk_index = 0

        for paragraph in paragraphs:
            # Se o parágrafo sozinho é maior que o chunk_size, dividir por frases
            if len(paragraph) > self.chunk_size:
                sentences = [s.strip() for s in paragraph.split('.') if s.strip()]

                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                        if current_chunk:
                            chunks.append(self._create_chunk_object(current_chunk, chunk_index, metadata))
                            chunk_index += 1
                            # Manter sobreposição
                            overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                            current_chunk = overlap_text + " " + sentence
                        else:
                            current_chunk = sentence
                    else:
                        current_chunk += (". " if current_chunk else "") + sentence
            else:
                # Verificar se cabe no chunk atual
                if len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                    if current_chunk:
                        chunks.append(self._create_chunk_object(current_chunk, chunk_index, metadata))
                        chunk_index += 1
                        # Manter sobreposição
                        overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                        current_chunk = overlap_text + "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    current_chunk += ("\n\n" if current_chunk else "") + paragraph

        # Adicionar último chunk se houver conteúdo
        if current_chunk.strip():
            chunks.append(self._create_chunk_object(current_chunk, chunk_index, metadata))

        return chunks

    def _create_chunk_object(self, content: str, index: int, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Cria objeto de chunk padronizado"""
        chunk_metadata = metadata.copy() if metadata else {}
        chunk_metadata.update({
            'chunkIndex': index,
            'length': len(content),
            'wordCount': len(content.split())
        })

        return {
            'content': content.strip(),
            'metadata': chunk_metadata,
            'index': index
        }

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para lista de textos"""
        try:
            if not self.embedding_model:
                raise Exception("Modelo de embeddings não inicializado. Verifique a configuração do Vertex AI.")

            # Vertex AI Text Embedding
            embeddings = []

            # Processar em lotes para evitar limites de rate
            batch_size = 5
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self.embedding_model.get_embeddings(batch)
                embeddings.extend([emb.values for emb in batch_embeddings])

            return embeddings
        except Exception as e:
            raise Exception(f"Erro ao gerar embeddings: {str(e)}")

    async def store_vectors(self, crew_id: str, document_id: str, chunks: List[Dict[str, Any]]) -> int:
        """Armazena chunks no Firestore com embeddings (se disponível)"""
        try:
            db = firestore.client()
            vectors_collection = db.collection('vectors')

            # Tentar gerar embeddings se modelo estiver disponível
            embeddings = []
            has_embeddings = False

            if self.embedding_model:
                try:
                    chunk_contents = [chunk['content'] for chunk in chunks]
                    embeddings = await self.generate_embeddings(chunk_contents)
                    has_embeddings = True
                    print(f"✅ Embeddings gerados para {len(embeddings)} chunks")
                except Exception as e:
                    print(f"⚠️ Erro ao gerar embeddings: {e}")
                    print("   Continuando sem embeddings...")

            # Armazenar cada chunk
            stored_count = 0
            for i, chunk in enumerate(chunks):
                vector_doc = {
                    'crewId': crew_id,
                    'documentId': document_id,
                    'chunkId': f"{document_id}-chunk-{i}",
                    'content': chunk['content'],
                    'metadata': chunk['metadata'],
                    'createdAt': datetime.now(),
                    'chunkIndex': i,
                    'hasEmbedding': has_embeddings
                }

                # Adicionar embedding se disponível
                if has_embeddings and i < len(embeddings):
                    vector_doc['embedding'] = embeddings[i]

                # Usar chunkId como ID do documento
                vectors_collection.document(vector_doc['chunkId']).set(vector_doc)
                stored_count += 1

            mode = "com embeddings" if has_embeddings else "apenas texto"
            print(f"✅ Armazenados {stored_count} chunks ({mode})")
            return stored_count

        except Exception as e:
            raise Exception(f"Erro ao armazenar chunks: {str(e)}")

    async def search_vectors(self, crew_id: str, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Busca vetorial semântica"""
        try:
            # Gerar embedding da consulta
            query_embeddings = await self.generate_embeddings([query])
            query_embedding = query_embeddings[0]

            # Buscar vetores da crew no Firestore
            db = firestore.client()
            vectors_query = db.collection('vectors').where('crewId', '==', crew_id).get()

            results = []
            for doc in vectors_query:
                vector_data = doc.data()
                stored_embedding = vector_data.get('embedding', [])

                if stored_embedding:
                    # Calcular similaridade de cosseno
                    similarity = self._cosine_similarity(query_embedding, stored_embedding)

                    results.append({
                        'content': vector_data['content'],
                        'metadata': vector_data['metadata'],
                        'similarity': similarity,
                        'documentId': vector_data['documentId'],
                        'chunkId': vector_data['chunkId']
                    })

            # Ordenar por similaridade (maior primeiro)
            results.sort(key=lambda x: x['similarity'], reverse=True)

            # Retornar apenas os top resultados
            return results[:max_results]

        except Exception as e:
            raise Exception(f"Erro na busca vetorial: {str(e)}")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade de cosseno entre dois vetores"""
        try:
            import numpy as np

            vec1 = np.array(vec1)
            vec2 = np.array(vec2)

            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot_product / (norm1 * norm2))
        except:
            return 0.0

    async def delete_document_vectors(self, crew_id: str, document_id: str) -> int:
        """Remove todos os vetores de um documento"""
        try:
            db = firestore.client()

            # Buscar todos os chunks do documento
            vectors_query = db.collection('vectors').where('crewId', '==', crew_id).where('documentId', '==', document_id).get()

            deleted_count = 0
            for doc in vectors_query:
                doc.reference.delete()
                deleted_count += 1

            return deleted_count

        except Exception as e:
            raise Exception(f"Erro ao remover vetores: {str(e)}")

# Instância global do serviço
knowledge_service = KnowledgeService()

@router.get("/stats/{crew_id}")
async def get_knowledge_stats(crew_id: str):
    """
    Obtém estatísticas da base de conhecimento de uma crew
    """
    try:
        db = firestore.client()

        # Contar vetores
        vectors_query = db.collection('vectors').where('crewId', '==', crew_id).get()
        total_vectors = len(vectors_query.docs)

        # Contar documentos únicos
        unique_documents = set()
        for doc in vectors_query:
            unique_documents.add(doc.to_dict().get('documentId'))

        return {
            "totalVectors": total_vectors,
            "totalDocuments": len(unique_documents),
            "avgChunksPerDocument": total_vectors / len(unique_documents) if unique_documents else 0
        }

    except Exception as e:
        print(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    crewId: str = Form(...)
):
    """
    Upload de documento para a base de conhecimento

    Multipart form-data com:
    - file: arquivo a ser processado
    - crewId: ID da crew (obrigatório)
    """
    try:
        print(f"📥 Upload recebido na API Python")
        print(f"   Arquivo: {file.filename}")
        print(f"   Content-Type: {file.content_type}")
        print(f"   Crew: {crewId}")

        # Validar tipo de arquivo
        allowed_extensions = ['.pdf', '.docx', '.txt', '.csv', '.xlsx']
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de arquivo não suportado. Use: {', '.join(allowed_extensions)}"
            )

        # Gerar ID único para o documento
        document_id = hashlib.md5(f"{crewId}-{file.filename}-{datetime.now()}".encode()).hexdigest()

        # Criar diretório temporário se não existir
        upload_dir = Path(tempfile.gettempdir()) / "knowledge_uploads" / crewId
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Salvar arquivo
        file_path = upload_dir / f"{document_id}{file_ext}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Detectar tipo do arquivo
        file_type_map = {
            '.pdf': 'pdf',
            '.docx': 'word',
            '.txt': 'text',
            '.csv': 'excel',
            '.xlsx': 'excel'
        }
        file_type = file_type_map.get(file_ext, 'text')

        # Extrair texto
        text = knowledge_service.extract_text_from_document(str(file_path), file_type)

        if not text or len(text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Documento não contém texto suficiente")

        # Criar metadados
        doc_metadata = {
            'filename': file.filename,
            'documentId': document_id,
            'type': file_type,
            'uploadedAt': datetime.now().isoformat(),
            'fileSize': len(content)
        }

        # Criar chunks
        chunks = knowledge_service.create_chunks(text, doc_metadata)

        if not chunks:
            raise HTTPException(status_code=400, detail="Não foi possível criar chunks do documento")

        # Armazenar vetores
        stored_count = await knowledge_service.store_vectors(crewId, document_id, chunks)

        # Salvar metadados do documento no Firestore
        db = firestore.client()
        doc_ref = db.collection('knowledge_documents').document(document_id)
        doc_data = {
            'crewId': crewId,
            'documentId': document_id,
            'filename': file.filename,
            'fileType': file_type,
            'filePath': str(file_path),
            'fileSize': len(content),
            'uploadedAt': datetime.now(),
            'processedAt': datetime.now(),
            'chunksCount': stored_count,
            'wordCount': len(text.split()),
            'status': 'processed'
        }

        doc_ref.set(doc_data)

        return {
            "success": True,
            "documentId": document_id,
            "filename": file.filename,
            "chunks": stored_count,
            "wordCount": len(text.split()),
            "fileSize": len(content),
            "message": f"Documento processado com sucesso. {stored_count} chunks criados."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro no upload do documento: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/documents")
async def list_documents(crewId: str):
    """
    Lista todos os documentos de uma crew
    """
    try:
        db = firestore.client()
        query = db.collection('knowledge_documents').where('crewId', '==', crewId)
        docs_query = query.get()

        documents = []
        for doc in docs_query:
            doc_data = doc.to_dict()
            documents.append({
                'id': doc.id,
                'filename': doc_data.get('filename'),
                'fileType': doc_data.get('fileType'),
                'fileSize': doc_data.get('fileSize'),
                'chunksCount': doc_data.get('chunksCount'),
                'wordCount': doc_data.get('wordCount'),
                'uploadedAt': doc_data.get('uploadedAt'),
                'status': doc_data.get('status')
            })

        # Ordenar por data de upload (mais recente primeiro)
        documents.sort(key=lambda x: x.get('uploadedAt', ''), reverse=True)

        return {
            "documents": documents,
            "total": len(documents)
        }

    except Exception as e:
        print(f"Erro ao listar documentos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Remove um documento e todos os seus vetores
    """
    try:
        db = firestore.client()

        # Buscar documento
        doc_ref = db.collection('knowledge_documents').document(document_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Documento não encontrado")

        doc_data = doc.to_dict()

        # Pegar crewId do documento
        crewId = doc_data.get('crewId')

        # Remover vetores
        deleted_vectors = await knowledge_service.delete_document_vectors(crewId, document_id)

        # Remover arquivo físico se existir
        file_path = doc_data.get('filePath')
        if file_path and Path(file_path).exists():
            try:
                Path(file_path).unlink()
            except:
                pass

        # Remover documento do Firestore
        doc_ref.delete()

        return {
            "success": True,
            "documentId": document_id,
            "deletedVectors": deleted_vectors,
            "message": "Documento removido com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro ao remover documento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")