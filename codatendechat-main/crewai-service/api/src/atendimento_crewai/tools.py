# api/src/atendimento_crewai/tools.py - Ferramentas para agentes CrewAI

from typing import Optional, List, Dict, Any
from google.cloud import firestore
import numpy as np
from datetime import datetime
from crewai.tools import tool
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os


class ConsultarBaseConhecimentoTool:
    """
    Ferramenta para consultar a base de conhecimento do tenant.

    Permite que agentes busquem informações em documentos previamente
    carregados e processados na base de conhecimento.
    """

    def __init__(self, embedding_model=None):
        """
        Inicializa a ferramenta com modelo de embeddings opcional

        Args:
            embedding_model: Modelo para gerar embeddings (TextEmbeddingModel)
        """
        self.embedding_model = embedding_model
        self.db = firestore.Client()
        self.name = "consultar_base_conhecimento"
        self.description = (
            "Consulta a base de conhecimento do cliente para encontrar informações relevantes. "
            "Use esta ferramenta quando precisar de informações específicas sobre produtos, "
            "serviços, políticas ou qualquer conteúdo dos documentos do cliente. "
            "Exemplo: 'Qual o horário de atendimento?' ou 'Quais produtos estão disponíveis?'"
        )

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade de cosseno entre dois vetores"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _keyword_search(self, query: str, crew_id: str, max_results: int, document_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        Busca por palavra-chave quando embeddings não estão disponíveis

        Args:
            query: Texto da consulta
            crew_id: ID da crew
            max_results: Número máximo de resultados
            document_ids: Lista opcional de IDs de documentos para filtrar busca
        """
        print(f"🔍 Busca por palavra-chave: '{query}' (crew: {crew_id})")
        if document_ids:
            print(f"   Filtrando por {len(document_ids)} documento(s) específico(s)")

        # Buscar todos os chunks da crew
        vectors_ref = self.db.collection('vectors').where('crewId', '==', crew_id)

        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        total_docs = 0
        filtered_docs = 0

        for doc in vectors_ref.stream():
            data = doc.to_dict()
            total_docs += 1

            # Filtrar por documentos específicos se fornecido
            if document_ids and data.get('documentId') not in document_ids:
                print(f"   ⏭️ Pulando chunk (documentId {data.get('documentId')} não está em {document_ids})")
                continue

            filtered_docs += 1

            content = data.get('content', '').lower()

            # Calcular score baseado em palavras encontradas
            score = 0
            for word in query_words:
                if word in content:
                    score += content.count(word)

            if score > 0:
                results.append({
                    'content': data.get('content'),
                    'metadata': data.get('metadata', {}),
                    'score': score,
                    'documentId': data.get('documentId'),
                    'chunkIndex': data.get('chunkIndex', 0)
                })

        print(f"   📊 Total de chunks encontrados na crew: {total_docs}")
        print(f"   📊 Chunks após filtrar por documentId: {filtered_docs}")
        print(f"   📊 Chunks com score > 0: {len(results)}")

        # Ordenar por score e retornar top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]

    def _semantic_search(self, query: str, crew_id: str, max_results: int, document_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        Busca semântica usando embeddings

        Args:
            query: Texto da consulta
            crew_id: ID da crew
            max_results: Número máximo de resultados
            document_ids: Lista opcional de IDs de documentos para filtrar busca
        """
        print(f"🧠 Busca semântica: '{query}' (crew: {crew_id})")
        if document_ids:
            print(f"   Filtrando por {len(document_ids)} documento(s) específico(s)")

        # Gerar embedding da query
        try:
            query_embeddings = self.embedding_model.get_embeddings([query])
            query_embedding = query_embeddings[0].values
        except Exception as e:
            print(f"⚠️ Erro ao gerar embedding da query: {e}")
            return self._keyword_search(query, crew_id, max_results, document_ids)

        # Buscar vetores da crew
        vectors_ref = self.db.collection('vectors').where('crewId', '==', crew_id)

        results = []
        for doc in vectors_ref.stream():
            data = doc.to_dict()

            # Pular chunks sem embedding
            if not data.get('hasEmbedding') or 'embedding' not in data:
                continue

            # Filtrar por documentos específicos se fornecido
            if document_ids and data.get('documentId') not in document_ids:
                continue

            # Calcular similaridade
            similarity = self._cosine_similarity(query_embedding, data['embedding'])

            results.append({
                'content': data.get('content'),
                'metadata': data.get('metadata', {}),
                'score': similarity,
                'documentId': data.get('documentId'),
                'chunkIndex': data.get('chunkIndex', 0)
            })

        # Ordenar por similaridade
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]

    def _run(self, query: str, crew_id: str, max_results: int = 3, document_ids: List[str] = None) -> str:
        """
        Executa a busca na base de conhecimento

        Args:
            query: Texto da consulta
            crew_id: ID da crew
            max_results: Número máximo de resultados
            document_ids: Lista opcional de IDs de documentos para filtrar busca

        Returns:
            String formatada com os resultados encontrados
        """
        try:
            print(f"📚 Consultando base de conhecimento...")
            print(f"   Query: {query}")
            print(f"   Crew: {crew_id}")
            print(f"   Max results: {max_results}")
            if document_ids:
                print(f"   Documentos específicos: {document_ids}")

            # Escolher método de busca
            if self.embedding_model:
                results = self._semantic_search(query, crew_id, max_results, document_ids)
            else:
                results = self._keyword_search(query, crew_id, max_results, document_ids)

            if not results:
                return "Não foram encontradas informações relevantes na base de conhecimento para esta consulta."

            # Formatar resultados
            output = f"Encontrei {len(results)} resultado(s) relevante(s):\n\n"

            for i, result in enumerate(results, 1):
                content = result['content']
                metadata = result['metadata']
                score = result['score']

                output += f"--- Resultado {i} ---\n"
                output += f"{content}\n"

                # Adicionar metadados úteis
                if metadata.get('filename'):
                    output += f"Fonte: {metadata['filename']}\n"
                if metadata.get('page'):
                    output += f"Página: {metadata['page']}\n"

                output += f"Relevância: {score:.2f}\n\n"

            print(f"✅ Retornando {len(results)} resultados")
            return output.strip()

        except Exception as e:
            error_msg = f"Erro ao consultar base de conhecimento: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg


def create_knowledge_tool(embedding_model=None) -> ConsultarBaseConhecimentoTool:
    """
    Factory function para criar a ferramenta de conhecimento

    Args:
        embedding_model: Modelo opcional de embeddings

    Returns:
        Instância configurada da ferramenta
    """
    return ConsultarBaseConhecimentoTool(embedding_model=embedding_model)


def _cadastrar_cliente_planilha_impl(
    spreadsheet_id: str,
    range_name: str,
    nome: str,
    telefone: str = "",
    email: str = "",
    observacoes: str = "",
    tenant_id: str = ""
) -> str:
    """
    Grava dados de clientes (nome, telefone, email, observações, tenant_id) em uma planilha do Google Sheets em tempo real.

    Args:
        spreadsheet_id: ID da planilha do Google Sheets. É a parte longa da URL.
        range_name: O nome da aba e o intervalo de colunas. Exemplo: Clientes!A:F
        nome: Nome completo do cliente a ser cadastrado.
        telefone: Telefone do cliente a ser cadastrado
        email: Email do cliente a ser cadastrado
        observacoes: Observações sobre o cliente.
        tenant_id: ID do tenant/cliente que fez o cadastro

    Returns:
        str: Uma mensagem confirmando que o cliente foi cadastrado com sucesso.
    """
    print(f"🔧 FERRAMENTA GOOGLE SHEETS CHAMADA!")
    print(f"   📊 Parâmetros recebidos:")
    print(f"      - spreadsheet_id: {spreadsheet_id}")
    print(f"      - range_name: {range_name}")
    print(f"      - nome: {nome}")
    print(f"      - telefone: {telefone}")
    print(f"      - email: {email}")
    print(f"      - tenant_id: {tenant_id}")

    try:
        # 1. Autenticar no Google Sheets
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        # Tentar diferentes caminhos para as credenciais
        possible_paths = [
            'google-credentials.json',
            os.path.join(os.path.dirname(__file__), 'google-credentials.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'google-credentials.json'),
        ]

        credentials_path = None
        for path in possible_paths:
            if os.path.exists(path):
                credentials_path = path
                break

        if not credentials_path:
            return "❌ Erro: Arquivo de credenciais google-credentials.json não encontrado"

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=SCOPES
        )
        sheets_service = build('sheets', 'v4', credentials=credentials)

        # 2. Validar dados obrigatórios
        if not nome or not nome.strip():
            return "❌ Erro: Nome do cliente é obrigatório"

        if not spreadsheet_id or not spreadsheet_id.strip():
            return "❌ Erro: ID da planilha é obrigatório"

        if not range_name or not range_name.strip():
            return "❌ Erro: Range da planilha é obrigatório (ex: Clientes!A:E)"

        # 3. Construir dados para inserir
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        values = [
            [timestamp, nome.strip(), telefone.strip(), email.strip(), observacoes.strip(), tenant_id.strip()]
        ]

        body = {'values': values}

        # 4. Inserir na planilha
        result = sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()

        updated_range = result.get('updates', {}).get('updatedRange', '')

        return (
            f"✅ Cliente cadastrado com sucesso na planilha!\n"
            f"Nome: {nome}\n"
            f"Telefone: {telefone or 'Não informado'}\n"
            f"Email: {email or 'Não informado'}\n"
            f"Localização: {updated_range}"
        )

    except Exception as e:
        error_msg = f"❌ Erro ao cadastrar cliente: {str(e)}"
        print(f"ERRO GOOGLE SHEETS: {error_msg}")
        return error_msg


# Criar versão decorada para CrewAI
@tool("cadastrar_cliente_planilha")
def cadastrar_cliente_planilha(
    spreadsheet_id: str,
    range_name: str,
    nome: str,
    telefone: str = "",
    email: str = "",
    observacoes: str = "",
    tenant_id: str = ""
) -> str:
    """
    Grava dados de clientes (nome, telefone, email, observações, tenant_id) em uma planilha do Google Sheets em tempo real.

    Args:
        spreadsheet_id: ID da planilha do Google Sheets. É a parte longa da URL.
        range_name: O nome da aba e o intervalo de colunas. Exemplo: Clientes!A:F
        nome: Nome completo do cliente a ser cadastrado.
        telefone: Telefone do cliente a ser cadastrado
        email: Email do cliente a ser cadastrado
        observacoes: Observações sobre o cliente.
        tenant_id: ID do tenant/cliente que fez o cadastro

    Returns:
        str: Uma mensagem confirmando que o cliente foi cadastrado com sucesso.
    """
    return _cadastrar_cliente_planilha_impl(spreadsheet_id, range_name, nome, telefone, email, observacoes, tenant_id)


def _coletar_info_agendamento_impl(
    nome_cliente: str,
    tipo_servico: str,
    data_desejada: str = "",
    horario_preferencia: str = "",
    telefone: str = "",
    observacoes: str = ""
) -> str:
    """
    Coleta e organiza informações para agendamento de consulta ou exame.
    Use quando cliente desejar agendar um horário.

    Args:
        nome_cliente: Nome do cliente
        tipo_servico: Tipo de exame/consulta (ex: "Cardiologia", "Raio-X")
        data_desejada: Data desejada (ex: "próxima segunda", "15/10/2025")
        horario_preferencia: Horário preferido (ex: "manhã", "14h")
        telefone: Telefone de contato
        observacoes: Observações adicionais

    Returns:
        str: Resumo estruturado do agendamento
    """
    if not nome_cliente or not nome_cliente.strip():
        return "❌ Erro: Nome do cliente é obrigatório"

    if not tipo_servico or not tipo_servico.strip():
        return "❌ Erro: Tipo de serviço é obrigatório"

    try:
        # Estruturar informações
        resumo = f"""📅 SOLICITAÇÃO DE AGENDAMENTO

👤 Cliente: {nome_cliente.strip()}
📞 Telefone: {telefone.strip() if telefone else 'Não informado'}

🏥 Serviço: {tipo_servico.strip()}
📆 Data desejada: {data_desejada.strip() if data_desejada else 'Flexível'}
🕒 Horário: {horario_preferencia.strip() if horario_preferencia else 'Flexível'}

📝 Observações: {observacoes.strip() if observacoes else 'Nenhuma'}

⚠️ IMPORTANTE: Esta solicitação foi registrada e será processada por um atendente humano que entrará em contato para confirmar horário disponível."""

        # TODO: Futura integração - Salvar em Firestore para dashboard do atendente
        # TODO: Futura integração - Enviar notificação para equipe
        # TODO: Futura integração - Integrar com Google Calendar

        print(f"📅 Agendamento coletado: {nome_cliente} - {tipo_servico}")

        return resumo.strip()

    except Exception as e:
        error_msg = f"❌ Erro ao coletar informações: {str(e)}"
        print(f"ERRO AGENDAMENTO: {error_msg}")
        return error_msg


# Criar versão decorada para CrewAI
@tool("coletar_info_agendamento")
def coletar_info_agendamento(
    nome_cliente: str,
    servico_desejado: str,
    data_preferencial: str = "",
    horario_preferencial: str = "",
    observacoes: str = ""
) -> str:
    """
    Coleta e organiza informações para agendamento de consulta ou exame.
    Use quando cliente desejar agendar um horário.

    Args:
        nome_cliente: Nome do cliente
        servico_desejado: Tipo de exame/consulta (ex: "Cardiologia", "Raio-X")
        data_preferencial: Data desejada (ex: "próxima segunda", "15/10/2025")
        horario_preferencial: Horário preferido (ex: "manhã", "14h")
        observacoes: Observações adicionais

    Returns:
        str: Resumo estruturado do agendamento
    """
    return _coletar_info_agendamento_impl(
        nome_cliente=nome_cliente,
        tipo_servico=servico_desejado,
        data_desejada=data_preferencial,
        horario_preferencia=horario_preferencial,
        telefone="",
        observacoes=observacoes
    )


def _buscar_cliente_planilha_impl(
    spreadsheet_id: str,
    range_name: str,
    telefone: str,
    tenant_id: str = ""
) -> str:
    """
    Busca informações de um cliente na planilha Google Sheets usando o telefone.

    Args:
        spreadsheet_id: ID da planilha do Google Sheets
        range_name: O nome da aba e o intervalo de colunas. Exemplo: Clientes!A:F
        telefone: Telefone do cliente para buscar (com ou sem formatação)
        tenant_id: ID do tenant (opcional, para filtrar apenas clientes do tenant)

    Returns:
        str: Dados do cliente encontrado ou mensagem de não encontrado
    """
    print(f"🔍 FERRAMENTA BUSCAR CLIENTE CHAMADA!")
    print(f"   📊 Parâmetros recebidos:")
    print(f"      - spreadsheet_id: {spreadsheet_id}")
    print(f"      - range_name: {range_name}")
    print(f"      - telefone: {telefone}")
    print(f"      - tenant_id: {tenant_id}")

    try:
        # 1. Autenticar no Google Sheets
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

        # Tentar diferentes caminhos para as credenciais
        possible_paths = [
            'google-credentials.json',
            os.path.join(os.path.dirname(__file__), 'google-credentials.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'google-credentials.json'),
        ]

        credentials_path = None
        for path in possible_paths:
            if os.path.exists(path):
                credentials_path = path
                break

        if not credentials_path:
            return "❌ Erro: Arquivo de credenciais google-credentials.json não encontrado"

        print(f"   🔐 Usando credenciais em: {credentials_path}")

        # 2. Criar serviço Google Sheets
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )
        sheets_service = build('sheets', 'v4', credentials=credentials)

        # Validações
        if not spreadsheet_id or not spreadsheet_id.strip():
            return "❌ Erro: ID da planilha é obrigatório"

        if not range_name or not range_name.strip():
            return "❌ Erro: Range da planilha é obrigatório (ex: Clientes!A:F)"

        if not telefone or not telefone.strip():
            return "❌ Erro: Telefone é obrigatório para buscar cliente"

        # 3. Ler todos os dados da planilha
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])

        if not values:
            return "❌ Planilha vazia ou sem dados"

        # Limpar telefone da busca (remover espaços, hífens, parênteses)
        import re
        telefone_limpo = re.sub(r'[^\d]', '', telefone.strip())

        print(f"   🔎 Buscando telefone: {telefone_limpo}")
        print(f"   📋 Total de linhas na planilha: {len(values)}")

        # 4. Procurar cliente (pulando cabeçalho na linha 0)
        for i, row in enumerate(values[1:], start=2):  # Começar da linha 2 (pular cabeçalho)
            if len(row) < 3:  # Precisa ter pelo menos Data, Nome, Telefone
                continue

            # Formato esperado: [Data, Nome, Telefone, Email, Observacoes, TenantId]
            row_telefone = row[2] if len(row) > 2 else ""
            row_telefone_limpo = re.sub(r'[^\d]', '', row_telefone.strip())

            # Verificar se telefone bate
            if row_telefone_limpo == telefone_limpo:
                # Se tenant_id foi fornecido, verificar se bate
                if tenant_id:
                    row_tenant = row[5] if len(row) > 5 else ""
                    if row_tenant.strip() != tenant_id.strip():
                        print(f"   ⚠️ Cliente encontrado mas tenant diferente (linha {i})")
                        continue

                # Cliente encontrado!
                data_cadastro = row[0] if len(row) > 0 else ""
                nome = row[1] if len(row) > 1 else ""
                telefone_cadastrado = row[2] if len(row) > 2 else ""
                email = row[3] if len(row) > 3 else ""
                observacoes = row[4] if len(row) > 4 else ""
                tenant = row[5] if len(row) > 5 else ""

                print(f"   ✅ Cliente encontrado na linha {i}: {nome}")

                resultado = f"""✅ Cliente encontrado na base de dados!

📋 **Dados do Cliente:**
- **Nome:** {nome}
- **Telefone:** {telefone_cadastrado}
- **Email:** {email if email else 'Não informado'}
- **Cadastrado em:** {data_cadastro}
- **Observações:** {observacoes if observacoes else 'Nenhuma'}
"""
                if tenant_id:
                    resultado += f"- **Tenant ID:** {tenant}\n"

                return resultado.strip()

        # Cliente não encontrado
        print(f"   ❌ Cliente não encontrado com telefone: {telefone_limpo}")
        return f"❌ Cliente não encontrado na base de dados com o telefone {telefone}"

    except Exception as e:
        error_msg = f"❌ Erro ao buscar cliente: {str(e)}"
        print(f"ERRO BUSCAR CLIENTE: {error_msg}")
        return error_msg


# Criar versão decorada para CrewAI
@tool("buscar_cliente_planilha")
def buscar_cliente_planilha(
    spreadsheet_id: str,
    range_name: str,
    telefone: str,
    tenant_id: str = ""
) -> str:
    """
    Busca informações de um cliente na planilha Google Sheets usando o telefone.
    Use quando precisar identificar quem está mandando mensagem ou buscar dados de um cliente.

    Args:
        spreadsheet_id: ID da planilha do Google Sheets
        range_name: O nome da aba e o intervalo de colunas. Exemplo: Clientes!A:F
        telefone: Telefone do cliente para buscar
        tenant_id: ID do tenant (opcional)

    Returns:
        str: Dados do cliente encontrado ou mensagem de não encontrado
    """
    return _buscar_cliente_planilha_impl(spreadsheet_id, range_name, telefone, tenant_id)


def _enviar_imagem_impl(
    categoria: str,
    tenant_id: str,
    filtros: list = None,
    quantidade: int = 1
) -> dict:
    """
    Busca imagens no catálogo do tenant baseado em categoria e filtros.

    Args:
        categoria: Categoria da imagem (ex: "imoveis/vendas/casas")
        tenant_id: ID do tenant
        filtros: Lista de tags para filtrar (ex: ["3 quartos", "piscina"])
        quantidade: Número de imagens a retornar (1-5)

    Returns:
        dict: {"images": [{"url": "...", "description": "..."}], "count": N}
    """
    if filtros is None:
        filtros = []

    # Limitar quantidade
    quantidade = min(max(1, quantidade), 5)

    try:
        db = firestore.Client()

        # Buscar imagens da categoria no tenant
        images_ref = db.collection('media_library').where('tenantId', '==', tenant_id)

        # Filtrar por categoria (usa startswith para suportar subcategorias)
        images_query = images_ref.where('category', '>=', categoria).where('category', '<', categoria + '\uf8ff')

        imagens_encontradas = []

        for doc in images_query.stream():
            data = doc.to_dict()

            # Se há filtros, verificar se a imagem tem as tags
            if filtros:
                tags_imagem = [tag.lower() for tag in data.get('tags', [])]
                # Verificar se todos os filtros estão nas tags
                filtros_lower = [f.lower() for f in filtros]
                if not all(any(filtro in tag for tag in tags_imagem) for filtro in filtros_lower):
                    continue

            imagens_encontradas.append({
                'url': data.get('url'),
                'description': data.get('description', ''),
                'category': data.get('category', ''),
                'tags': data.get('tags', [])
            })

        # Limitar quantidade
        imagens_selecionadas = imagens_encontradas[:quantidade]

        if not imagens_selecionadas:
            return {
                "images": [],
                "count": 0,
                "message": f"❌ Nenhuma imagem encontrada para categoria '{categoria}'" + (f" com filtros {filtros}" if filtros else "")
            }

        return {
            "images": imagens_selecionadas,
            "count": len(imagens_selecionadas),
            "message": f"✅ {len(imagens_selecionadas)} imagem(ns) encontrada(s)"
        }

    except Exception as e:
        print(f"❌ Erro ao buscar imagens: {e}")
        return {
            "images": [],
            "count": 0,
            "message": f"❌ Erro ao buscar imagens: {str(e)}"
        }


@tool("enviar_imagem")
def enviar_imagem(
    categoria: str,
    tenant_id: str,
    filtros: str = "",
    quantidade: int = 1
) -> str:
    """
    Busca e prepara imagens do catálogo para envio ao cliente.
    Use quando o cliente pedir para ver fotos, imagens ou exemplos visuais.

    Args:
        categoria: Categoria da imagem (ex: "imoveis/vendas/casas", "produtos/eletronicos")
        tenant_id: ID do tenant
        filtros: Tags separadas por vírgula (ex: "3 quartos,piscina" ou "azul,grande")
        quantidade: Número de imagens (1-5)

    Returns:
        str: Resultado da busca em formato legível
    """
    # Converter string de filtros em lista
    filtros_list = [f.strip() for f in filtros.split(',')] if filtros else []

    result = _enviar_imagem_impl(categoria, tenant_id, filtros_list, quantidade)

    # Retornar em formato de string para o agente
    if result['count'] == 0:
        return result['message']

    return f"{result['message']}\n\nIMPORTANTE: As imagens serão enviadas automaticamente ao cliente."
