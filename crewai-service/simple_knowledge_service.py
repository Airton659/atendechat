# simple_knowledge_service.py - Knowledge Base com TF-IDF (sem PyTorch, GRATUITO)

import os
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.cloud import firestore
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import PyPDF2
import docx
import pandas as pd
import io

class SimpleKnowledgeService:
    """
    Serviço de Knowledge Base simples e GRATUITO usando TF-IDF

    Features:
    - Sem PyTorch (economia de disk space)
    - TF-IDF para busca (entende relevância de termos)
    - Suporta PDF, DOCX, TXT, XLSX
    - Armazena no Firestore
    - 100% gratuito
    """

    def __init__(self):
        print("🚀 Inicializando SimpleKnowledgeService (TF-IDF)...")

        # Firestore
        credentials_path = os.path.join(os.path.dirname(__file__), 'atendechat-credentials.json')
        self.db = firestore.Client.from_service_account_json(credentials_path)

        # TF-IDF Vectorizer (leve e rápido)
        self.vectorizer = TfidfVectorizer(
            max_features=1000,  # Top 1000 palavras
            ngram_range=(1, 2),  # Uni e bigramas
            stop_words=None,  # Vamos manter stopwords em português
            max_df=0.85,
            min_df=2
        )

        print("✅ SimpleKnowledgeService inicializado!")

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extrai texto de PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"❌ Erro ao extrair PDF: {e}")
            return ""

    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extrai texto de DOCX"""
        try:
            doc = docx.Document(io.BytesIO(file_content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            print(f"❌ Erro ao extrair DOCX: {e}")
            return ""

    def extract_text_from_txt(self, file_content: bytes) -> str:
        """Extrai texto de TXT"""
        try:
            return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"❌ Erro ao extrair TXT: {e}")
            return ""

    def extract_text_from_xlsx(self, file_content: bytes) -> str:
        """
        Extrai texto de XLSX preservando estrutura tabular

        Processa todas as sheets do arquivo e preserva formato de tabela
        para facilitar compreensão dos agentes.
        """
        try:
            # Ler arquivo Excel
            excel_file = pd.ExcelFile(io.BytesIO(file_content))
            text_parts = []

            print(f"📊 XLSX contém {len(excel_file.sheet_names)} sheet(s): {excel_file.sheet_names}")

            # Processar cada sheet
            for sheet_name in excel_file.sheet_names:
                # Ler sheet como DataFrame
                df = pd.read_excel(excel_file, sheet_name=sheet_name)

                # Pular sheets vazias
                if df.empty:
                    print(f"⚠️ Sheet '{sheet_name}' está vazia, pulando...")
                    continue

                # Adicionar cabeçalho da sheet
                text_parts.append(f"\n{'='*60}")
                text_parts.append(f"PLANILHA: {sheet_name}")
                text_parts.append(f"{'='*60}\n")

                # Converter DataFrame para string preservando estrutura tabular
                # to_string() mantém colunas alinhadas, melhor para agentes entenderem
                table_text = df.to_string(index=False, na_rep='')
                text_parts.append(table_text)
                text_parts.append("\n")

                print(f"✅ Sheet '{sheet_name}': {len(df)} linhas, {len(df.columns)} colunas")

            result = "\n".join(text_parts)
            print(f"📄 XLSX processado: {len(result)} caracteres")

            return result

        except Exception as e:
            print(f"❌ Erro ao extrair XLSX: {e}")
            import traceback
            traceback.print_exc()
            return ""

    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extrai texto baseado na extensão"""
        extension = filename.lower().split('.')[-1]

        if extension == 'pdf':
            return self.extract_text_from_pdf(file_content)
        elif extension in ['docx', 'doc']:
            return self.extract_text_from_docx(file_content)
        elif extension == 'txt':
            return self.extract_text_from_txt(file_content)
        elif extension in ['xlsx', 'xls']:
            return self.extract_text_from_xlsx(file_content)
        else:
            print(f"⚠️ Tipo de arquivo não suportado: {extension}")
            return ""

    def create_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Divide texto em chunks com overlap"""
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]

            # Tentar quebrar no final de frase
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > chunk_size * 0.7:  # Pelo menos 70% do chunk
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return [c for c in chunks if len(c) > 50]  # Mínimo 50 chars

    def generate_document_id(self, team_id: str, filename: str) -> str:
        """Gera ID único para o documento"""
        hash_input = f"{team_id}_{filename}_{datetime.now().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    async def process_document(
        self,
        team_id: str,
        file_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Processa documento e salva no Firestore

        Returns:
            {
                'success': True,
                'documentId': 'abc123',
                'chunks': 15,
                'wordCount': 1234
            }
        """
        try:
            print(f"📄 Processando documento: {filename}")

            # 1. Extrair texto
            text = self.extract_text(file_content, filename)
            if not text:
                return {'success': False, 'error': 'Não foi possível extrair texto'}

            word_count = len(text.split())
            print(f"📊 Texto extraído: {len(text)} chars, {word_count} palavras")

            # 2. Criar chunks
            chunks = self.create_chunks(text)
            print(f"✂️ {len(chunks)} chunks criados")

            # 3. Gerar document ID
            doc_id = self.generate_document_id(team_id, filename)

            # 4. Salvar metadados do documento
            doc_ref = self.db.collection('knowledge_documents').document(doc_id)
            doc_ref.set({
                'documentId': doc_id,
                'teamId': team_id,
                'filename': filename,
                'fileType': filename.split('.')[-1],
                'fileSize': len(file_content),
                'chunksCount': len(chunks),
                'wordCount': word_count,
                'status': 'processed',
                'uploadedAt': firestore.SERVER_TIMESTAMP,
                'processedAt': firestore.SERVER_TIMESTAMP
            })

            # 5. Salvar chunks no Firestore
            batch = self.db.batch()
            for i, chunk_content in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_ref = self.db.collection('knowledge_chunks').document(chunk_id)

                batch.set(chunk_ref, {
                    'chunkId': chunk_id,
                    'teamId': team_id,
                    'documentId': doc_id,
                    'chunkIndex': i,
                    'content': chunk_content,
                    'wordCount': len(chunk_content.split()),
                    'metadata': {
                        'filename': filename,
                        'totalChunks': len(chunks)
                    },
                    'createdAt': firestore.SERVER_TIMESTAMP
                })

            batch.commit()
            print(f"✅ Documento processado: {doc_id}")

            return {
                'success': True,
                'documentId': doc_id,
                'filename': filename,
                'chunksCount': len(chunks),
                'wordCount': word_count
            }

        except Exception as e:
            print(f"❌ Erro ao processar documento: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def search_knowledge(
        self,
        team_id: str,
        document_ids: Optional[List[str]],
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Busca chunks relevantes usando TF-IDF

        Args:
            team_id: ID da equipe
            document_ids: IDs dos documentos para buscar (None = todos)
            query: Query de busca
            top_k: Número de resultados

        Returns:
            Lista de chunks relevantes com score
        """
        try:
            print(f"🔍 Buscando knowledge: team={team_id}, docs={document_ids}, query='{query[:50]}'")

            # 1. Buscar chunks no Firestore
            chunks_query = self.db.collection('knowledge_chunks').where('teamId', '==', team_id)

            if document_ids:
                chunks_query = chunks_query.where('documentId', 'in', document_ids)

            chunks = list(chunks_query.stream())

            if not chunks:
                print("📭 Nenhum chunk encontrado")
                return []

            print(f"📦 {len(chunks)} chunks encontrados")

            # 2. Extrair conteúdo dos chunks
            chunk_contents = []
            chunk_data = []

            for doc in chunks:
                data = doc.to_dict()
                chunk_contents.append(data['content'])
                chunk_data.append({
                    'chunkId': data['chunkId'],
                    'documentId': data['documentId'],
                    'content': data['content'],
                    'metadata': data.get('metadata', {})
                })

            # 3. TF-IDF: Criar matriz de features
            try:
                # Fit vectorizer nos chunks + query
                tfidf_matrix = self.vectorizer.fit_transform(chunk_contents + [query])

                # Separar query vector
                query_vector = tfidf_matrix[-1]
                chunk_vectors = tfidf_matrix[:-1]

                # Calcular similaridade coseno
                similarities = cosine_similarity(query_vector, chunk_vectors)[0]

            except Exception as e:
                print(f"⚠️ Erro no TF-IDF, usando busca keyword: {e}")
                # Fallback: busca keyword simples
                query_words = set(query.lower().split())
                similarities = []
                for content in chunk_contents:
                    content_words = set(content.lower().split())
                    # Jaccard similarity
                    intersection = len(query_words & content_words)
                    union = len(query_words | content_words)
                    sim = intersection / union if union > 0 else 0
                    similarities.append(sim)
                similarities = np.array(similarities)

            # 4. Ordenar por similaridade
            top_indices = np.argsort(similarities)[::-1][:top_k]

            # 5. Preparar resultados
            results = []
            for idx in top_indices:
                if True:  # Sempre incluir, ordenado por relevância
                    results.append({
                        'content': chunk_data[idx]['content'],
                        'similarity': float(similarities[idx]),
                        'metadata': chunk_data[idx]['metadata'],
                        'documentId': chunk_data[idx]['documentId'],
                        'chunkId': chunk_data[idx]['chunkId']
                    })

            print(f"✅ {len(results)} chunks relevantes encontrados")
            for i, r in enumerate(results[:3]):
                print(f"  [{i+1}] Score: {r['similarity']:.3f} - {r['content'][:80]}...")

            return results

        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def delete_document(self, document_id: str) -> bool:
        """Deleta documento e todos seus chunks"""
        try:
            # Deletar documento
            self.db.collection('knowledge_documents').document(document_id).delete()

            # Deletar chunks
            chunks = self.db.collection('knowledge_chunks')\
                .where('documentId', '==', document_id)\
                .stream()

            batch = self.db.batch()
            for chunk in chunks:
                batch.delete(chunk.reference)
            batch.commit()

            print(f"🗑️ Documento {document_id} deletado")
            return True

        except Exception as e:
            print(f"❌ Erro ao deletar: {e}")
            return False


# Singleton
_knowledge_service = None

def get_knowledge_service() -> SimpleKnowledgeService:
    """Get or create singleton instance"""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = SimpleKnowledgeService()
    return _knowledge_service
