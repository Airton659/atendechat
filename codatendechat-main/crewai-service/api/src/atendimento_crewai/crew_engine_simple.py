"""
Motor de CrewAI Simplificado - Versão Funcional
Implementação direta usando Gemini sem dependências complexas
"""

import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel
from firebase_admin import firestore
from typing import Dict, Any, List, Optional
import time

# Importar ferramentas
from .tools import (
    create_knowledge_tool,
    _cadastrar_cliente_planilha_impl,
    _coletar_info_agendamento_impl,
    _buscar_cliente_planilha_impl,
    _enviar_imagem_impl,
    schedule_appointment
)


class SimpleCrewEngine:
    def __init__(self):
        """Inicializa o motor simplificado"""

        # Location configurado em main.py: southamerica-east1 (São Paulo)
        # Suporta tanto Gemini quanto Embeddings

        try:
            # Modelo Gemini que funcionava antes em location=global
            self.model = GenerativeModel("gemini-2.5-flash-lite")
            print("✅ Modelo Gemini 2.5 Flash Lite carregado")
        except Exception as e:
            print(f"❌ Erro ao carregar Gemini 2.5 Flash Lite: {e}")
            try:
                self.model = GenerativeModel("gemini-1.5-flash")
                print("✅ Modelo Gemini 1.5 Flash carregado")
            except Exception as e2:
                print(f"❌ Erro ao carregar modelos Gemini: {e2}")
                self.model = None

        try:
            self.db = firestore.client()
            print("✅ Firestore conectado no SimpleCrewEngine")
        except Exception as e:
            print(f"❌ Erro ao conectar Firestore no SimpleCrewEngine: {e}")
            self.db = None

        # Usar busca por palavra-chave ao invés de embeddings
        # Embeddings não funcionam com location=global, Gemini não funciona com southamerica-east1
        print("ℹ️ Usando busca por palavra-chave na base de conhecimento")
        self.embedding_model = None
        self.knowledge_tool = self._create_keyword_search_tool()

    def _create_keyword_search_tool(self):
        """Cria ferramenta de busca por palavra-chave na base de conhecimento"""
        class KeywordSearchTool:
            def __init__(self, db):
                self.db = db

            def _run(self, query: str, crew_id: str, max_results: int = 3, document_ids: List[str] = None, forbidden_keywords: List[str] = None) -> str:
                """Busca por palavra-chave nos vetores com filtro de guardrails"""
                try:
                    results = []
                    vectors_ref = self.db.collection('vectors').where('crewId', '==', crew_id)

                    query_lower = query.lower()
                    query_words = set(query_lower.split())

                    print(f"🔍 Buscando por palavra-chave: '{query}' (crew: {crew_id})")
                    if document_ids:
                        print(f"   Filtrando por {len(document_ids)} documento(s) específico(s): {document_ids}")
                    if forbidden_keywords:
                        print(f"   🔍 Palavras-chave proibidas: {forbidden_keywords}")

                    total_docs = 0
                    filtered_docs = 0
                    forbidden_filtered = 0

                    for doc in vectors_ref.stream():
                        data = doc.to_dict()
                        total_docs += 1

                        # Filtrar por documentos específicos se fornecido
                        if document_ids and data.get('documentId') not in document_ids:
                            if total_docs <= 3:  # Só mostrar os primeiros 3 para não poluir o log
                                print(f"   ⏭️ Pulando chunk (documentId '{data.get('documentId')}' não está em {document_ids})")
                            continue

                        filtered_docs += 1

                        content = data.get('content', '').lower()

                        # PRÉ-FILTRO: Verificar se contém palavras proibidas
                        is_forbidden = False
                        if forbidden_keywords:
                            for keyword in forbidden_keywords:
                                if keyword in content:
                                    is_forbidden = True
                                    forbidden_filtered += 1
                                    if forbidden_filtered <= 3:  # Só mostrar os primeiros 3
                                        print(f"   ⛔ Filtrado por guardrail: contém '{keyword}'")
                                    break

                        if is_forbidden:
                            continue

                        # Calcular score baseado em palavras encontradas
                        score = 0
                        for word in query_words:
                            if word in content:
                                score += content.count(word)

                        if score > 0:
                            results.append({
                                'content': data.get('content'),
                                'metadata': data.get('metadata', {}),
                                'similarity': score
                            })

                    print(f"   📊 Total de chunks encontrados na crew: {total_docs}")
                    print(f"   📊 Chunks após filtrar por documentId: {filtered_docs}")
                    if forbidden_keywords:
                        print(f"   📊 Chunks filtrados por guardrails: {forbidden_filtered}")
                    print(f"   📊 Chunks com score > 0: {len(results)}")

                    # Ordenar por score
                    results.sort(key=lambda x: x['similarity'], reverse=True)

                    print(f"✅ Encontrados {len(results)} resultados por palavra-chave")

                    if not results:
                        return "Não foram encontradas informações relevantes na base de conhecimento."

                    # Formatar resultados
                    formatted = []
                    for i, r in enumerate(results[:max_results], 1):
                        source = r.get('metadata', {}).get('source', 'documento')
                        formatted.append(f"{i}. [{source.upper()}] {r['content']}")

                    return "\n".join(formatted)

                except Exception as e:
                    print(f"Erro ao buscar conhecimento: {e}")
                    return "Erro ao consultar base de conhecimento."

        return KeywordSearchTool(self.db) if self.db else None

    async def process_message(
        self,
        tenant_id: str,
        crew_id: str,
        message: str,
        conversation_history: List[Dict[str, Any]] = None,
        agent_override: str = None,
        remote_jid: str = None
    ) -> Dict[str, Any]:
        """Processa mensagem de forma simples e funcional"""

        start_time = time.time()
        tools_used = []

        try:
            # Se não tem DB, retorna demo
            if not self.db:
                return self._create_demo_response(message, crew_id)

            # Carregar dados da equipe
            crew_data = await self._load_crew_data(crew_id)
            if not crew_data:
                return self._create_demo_response(message, crew_id)

            # Selecionar agente baseado na mensagem ou override
            print(f"🔍 INICIANDO SELEÇÃO DE AGENTE - Mensagem: '{message}', Override: {agent_override}")
            selected_agent = self._select_agent(crew_data, message, agent_override)
            print(f"✅ AGENTE SELECIONADO: {selected_agent.get('name')} (key: {selected_agent.get('key')})")

            # Verificar se agente pode usar ferramentas
            agent_tools = selected_agent.get('tools', [])
            tool_configs = selected_agent.get('toolConfigs', {})
            knowledge_context = ""
            tools_context = ""
            cliente_nome = None  # Nome do cliente identificado

            # BUSCA AUTOMÁTICA DE CLIENTE PELO NÚMERO DO WHATSAPP (remoteJid)
            if remote_jid and 'buscar_cliente_planilha' in agent_tools and 'buscarCliente' in tool_configs:
                import re
                # Extrair apenas os dígitos do remoteJid (ex: 5531994042943@s.whatsapp.net -> 5531994042943)
                telefone_match = re.search(r'(\d{10,13})', remote_jid)

                if telefone_match:
                    telefone_cliente = telefone_match.group(1)
                    # Remover código do país se tiver (ex: 5531994042943 -> 31994042943)
                    if len(telefone_cliente) > 11:
                        telefone_cliente = telefone_cliente[-11:]

                    buscar_config = tool_configs['buscarCliente']
                    spreadsheet_id = buscar_config.get('spreadsheetId', '')
                    range_name = buscar_config.get('rangeName', 'Clientes!A:F')

                    if spreadsheet_id:
                        print(f"📞 Buscando cliente automaticamente pelo número: {telefone_cliente}")

                        try:
                            busca_result = _buscar_cliente_planilha_impl(
                                spreadsheet_id=spreadsheet_id,
                                range_name=range_name,
                                telefone=telefone_cliente,
                                tenant_id=tenant_id
                            )

                            if "✅ Cliente encontrado" in busca_result:
                                # Extrair nome do cliente do resultado
                                nome_match = re.search(r'Nome:\s*([^\n]+)', busca_result)
                                if nome_match:
                                    cliente_nome = nome_match.group(1).strip()
                                    print(f"✅ Cliente identificado: {cliente_nome}")

                                tools_context += f"\n\n🔍 CLIENTE IDENTIFICADO:\n{busca_result}\n"
                                tools_context += f"IMPORTANTE: Este cliente já está cadastrado. Trate-o pelo nome ({cliente_nome}).\n"
                                tools_used.append("buscar_cliente_planilha")
                            else:
                                print(f"ℹ️ Cliente {telefone_cliente} não encontrado na base")
                        except Exception as e:
                            print(f"⚠️ Erro ao buscar cliente automaticamente: {e}")

            # Se agente pode consultar base de conhecimento, fazer busca prévia
            if 'consultar_base_conhecimento' in agent_tools and self.knowledge_tool:
                try:
                    print(f"🔍 Agente '{selected_agent.get('name')}' consultando base de conhecimento...")

                    # PILAR 1: Obter documentos específicos do agente
                    agent_document_ids = selected_agent.get('knowledgeDocuments', [])

                    if agent_document_ids:
                        print(f"   Agente tem {len(agent_document_ids)} documento(s) específico(s)")
                    else:
                        print(f"   Agente usará toda a base de conhecimento do tenant")

                    # Extrair palavras-chave proibidas dos guardrails para pré-filtrar conhecimento
                    agent_training = selected_agent.get('training', {})
                    guardrails = agent_training.get('guardrails', {})
                    dont_rules = guardrails.get('dont', [])

                    forbidden_keywords = []
                    for rule in dont_rules:
                        rule_lower = rule.lower()
                        if 'compra' in rule_lower or 'comprar' in rule_lower:
                            forbidden_keywords.extend(['compra', 'comprar', 'venda'])
                        if 'vend' in rule_lower:
                            forbidden_keywords.extend(['venda', 'vender'])

                    knowledge_result = self.knowledge_tool._run(
                        query=message,
                        crew_id=crew_id,
                        max_results=3,
                        document_ids=agent_document_ids if agent_document_ids else None,
                        forbidden_keywords=forbidden_keywords if forbidden_keywords else None
                    )
                    if knowledge_result and "Não foram encontradas" not in knowledge_result:
                        knowledge_context = f"\n\nINFORMAÇÕES DA BASE DE CONHECIMENTO:\n{knowledge_result}"
                        tools_used.append("consultar_base_conhecimento")
                        print(f"✅ Base de conhecimento consultada com sucesso")
                except Exception as e:
                    print(f"⚠️ Erro ao consultar base de conhecimento: {e}")

            # DETECTAR E EXECUTAR FERRAMENTAS DE GOOGLE SHEETS E AGENDAMENTO
            message_lower = message.lower()

            # 0. FERRAMENTA DE BUSCAR CLIENTE (executar primeiro se houver número de telefone)
            # Isso permite personalizar o atendimento se reconhecer o cliente
            if 'buscar_cliente_planilha' in agent_tools and 'buscarCliente' in tool_configs:
                print(f"\n🔍 Agente tem ferramenta de busca de cliente configurada")

                # Tentar extrair telefone da mensagem ou do contexto da conversa
                import re
                telefone_match = re.search(r'(\d{10,11})', message)

                # Se não achou na mensagem, tentar no histórico
                if not telefone_match and conversation_history:
                    for msg in reversed(conversation_history[-5:]):  # Últimas 5 mensagens
                        content = msg.get('content', '')
                        telefone_match = re.search(r'(\d{10,11})', content)
                        if telefone_match:
                            break

                if telefone_match:
                    telefone_busca = telefone_match.group(1)
                    buscar_config = tool_configs['buscarCliente']
                    spreadsheet_id = buscar_config.get('spreadsheetId', '')
                    range_name = buscar_config.get('rangeName', 'Clientes!A:F')

                    if spreadsheet_id:
                        print(f"   🔎 Buscando cliente com telefone: {telefone_busca}")

                        try:
                            busca_result = _buscar_cliente_planilha_impl(
                                spreadsheet_id=spreadsheet_id,
                                range_name=range_name,
                                telefone=telefone_busca,
                                tenant_id=tenant_id
                            )

                            # Se encontrou o cliente, adicionar ao contexto
                            if "✅ Cliente encontrado" in busca_result:
                                tools_context += f"\n\nINFORMAÇÕES DO CLIENTE:\n{busca_result}\n"
                                tools_used.append("buscar_cliente_planilha")
                                print(f"   ✅ Cliente encontrado e adicionado ao contexto")
                            else:
                                print(f"   ℹ️ Cliente não encontrado na base")

                        except Exception as e:
                            print(f"   ⚠️ Erro ao buscar cliente: {e}")

            # 1. FERRAMENTA DE CADASTRO EM GOOGLE SHEETS
            if 'cadastrar_cliente_planilha' in agent_tools:
                print(f"\n📊 Agente tem ferramenta de Google Sheets configurada")
                print(f"   Tool configs: {tool_configs}")

                # Palavras que indicam cadastro/registro
                cadastro_keywords = [
                    'cadastr', 'registr', 'anot', 'salv', 'inclui',
                    'adicionar', 'guardar', 'anotar', 'nome', 'telefone',
                    'email', 'dados', 'informaç'
                ]

                # Verificar se mensagem parece ser um cadastro
                is_cadastro = any(keyword in message_lower for keyword in cadastro_keywords)

                if is_cadastro and 'googleSheets' in tool_configs:
                    print(f"   🎯 Mensagem detectada como cadastro!")

                    sheets_config = tool_configs['googleSheets']
                    spreadsheet_id = sheets_config.get('spreadsheetId', '')
                    range_name = sheets_config.get('rangeName', 'Clientes!A:E')

                    if spreadsheet_id:
                        print(f"   Tentando cadastrar em planilha: {spreadsheet_id}")

                        try:
                            import re
                            from datetime import datetime

                            # Extrair informações da mensagem usando regex
                            # Extrair nome (procurar por "nome é/:" seguido de texto)
                            nome_match = re.search(r'(?:nome\s+(?:é|e)\s+|me\s+chamo\s+|sou\s+o?\s*)([A-Za-zÀ-ÿ\s]+?)(?:\s*,|\s+meu|\s+telefone|\s+email|\s+e-mail|$)', message, re.IGNORECASE)
                            nome = nome_match.group(1).strip() if nome_match else ""

                            # Extrair telefone (procurar por números com 10-11 dígitos)
                            telefone_match = re.search(r'(?:telefone|fone|cel|celular|whats|whatsapp)?\s*:?\s*(\d{10,11})', message, re.IGNORECASE)
                            telefone = telefone_match.group(1) if telefone_match else ""

                            # Extrair email
                            email_match = re.search(r'(?:email|e-mail|mail)?\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', message, re.IGNORECASE)
                            email = email_match.group(1) if email_match else ""

                            # Data/hora atual
                            data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            # Se não extraiu nome, usar mensagem completa
                            if not nome:
                                nome = message

                            print(f"   📝 Dados extraídos:")
                            print(f"      Nome: {nome}")
                            print(f"      Telefone: {telefone}")
                            print(f"      Email: {email}")
                            print(f"      Data: {data_cadastro}")

                            tool_result = _cadastrar_cliente_planilha_impl(
                                spreadsheet_id=spreadsheet_id,
                                range_name=range_name,
                                nome=nome,
                                telefone=telefone,
                                email=email,
                                observacoes=f"Cadastrado via chat - {crew_data.get('name', 'Equipe')} em {data_cadastro}",
                                tenant_id=tenant_id
                            )

                            tools_context += f"\n\nRESULTADO DO CADASTRO:\n{tool_result}"
                            tools_used.append("cadastrar_cliente_planilha")
                            print(f"   ✅ Cadastro executado com sucesso")

                        except Exception as e:
                            error_msg = f"Erro ao cadastrar: {str(e)}"
                            tools_context += f"\n\nERRO NO CADASTRO:\n{error_msg}"
                            print(f"   ❌ Erro ao executar cadastro: {e}")
                    else:
                        print(f"   ⚠️ spreadsheet_id não configurado")

            # 2. FERRAMENTA DE AGENDAMENTO
            if 'coletar_info_agendamento' in agent_tools:
                print(f"\n📅 Agente tem ferramenta de agendamento configurada")

                # Palavras que indicam agendamento
                agendamento_keywords = [
                    'agendar', 'marcar', 'horário', 'hora', 'dia',
                    'consulta', 'reunião', 'encontro', 'atendimento',
                    'disponível', 'disponibilidade'
                ]

                is_agendamento = any(keyword in message_lower for keyword in agendamento_keywords)

                if is_agendamento:
                    print(f"   🎯 Mensagem detectada como agendamento!")

                    try:
                        # Coletar informações da mensagem
                        tool_result = _coletar_info_agendamento_impl(
                            nome_cliente="Cliente",  # TODO: Extrair do contexto
                            tipo_servico=message,
                            data_desejada="",    # TODO: Extrair da mensagem
                            horario_preferencia="", # TODO: Extrair da mensagem
                            telefone="",
                            observacoes=f"Solicitado via chat"
                        )

                        tools_context += f"\n\nINFORMAÇÕES DE AGENDAMENTO COLETADAS:\n{tool_result}"
                        tools_used.append("coletar_info_agendamento")
                        print(f"   ✅ Informações de agendamento coletadas")

                    except Exception as e:
                        error_msg = f"Erro ao coletar agendamento: {str(e)}"
                        tools_context += f"\n\nERRO NO AGENDAMENTO:\n{error_msg}"
                        print(f"   ❌ Erro ao coletar agendamento: {e}")

            # 3. FERRAMENTA DE ENVIO DE IMAGENS
            media_to_send = []
            if 'enviar_imagem' in agent_tools:
                print(f"\n📸 Agente tem ferramenta de envio de imagens configurada")

                # Palavras que indicam pedido de imagens
                image_keywords = [
                    'foto', 'imagem', 'imagens', 'fotos', 'ver', 'mostrar',
                    'quero ver', 'me mostra', 'tem foto', 'ver imagens'
                ]

                if any(keyword in message_lower for keyword in image_keywords):
                    print(f"   🔍 Mensagem parece solicitar imagens")

                    # Obter configurações de catálogo de mídia
                    tool_configs_media = tool_configs.get('enviadorImagem', {})
                    categoria_base = tool_configs_media.get('categoria', '')

                    if categoria_base:
                        # TODO: Melhorar extração de filtros da mensagem usando NLP
                        # Por enquanto, enviar imagens da categoria base
                        try:
                            result = _enviar_imagem_impl(
                                categoria=categoria_base,
                                tenant_id=tenant_id,
                                filtros=[],
                                quantidade=3
                            )

                            if result['count'] > 0:
                                media_to_send = result['images']
                                tools_context += f"\n\n📸 IMAGENS JÁ ENVIADAS AO CLIENTE:\n"
                                tools_context += f"- Você acabou de enviar {result['count']} foto(s) de imóveis da categoria '{categoria_base}'\n"
                                tools_context += f"IMPORTANTE: As imagens JÁ FORAM enviadas ao cliente ANTES desta mensagem.\n"
                                tools_context += f"Agora você deve comentar sobre as fotos enviadas e fazer perguntas ao cliente.\n"
                                tools_used.append("enviar_imagem")
                                print(f"   ✅ {result['count']} imagem(ns) selecionada(s) para envio")
                            else:
                                print(f"   ℹ️ Nenhuma imagem encontrada na categoria '{categoria_base}'")

                        except Exception as e:
                            print(f"   ❌ Erro ao buscar imagens: {e}")

            # Preparar contexto (com conhecimento e ferramentas se disponível)
            context = self._build_context(conversation_history, crew_data, selected_agent, knowledge_context, tools_context)

            # Gerar resposta usando Gemini
            response = await self._generate_response(message, context, selected_agent)

            processing_time = time.time() - start_time

            return {
                "response": response,
                "agent_used": selected_agent.get("key", "geral"),
                "agent_name": selected_agent.get("name", "Agente Geral"),
                "tools_used": tools_used,
                "success": True,
                "processing_time": round(processing_time, 2),
                "demo_mode": False,
                "customer_name": cliente_nome,  # Nome do cliente identificado
                "media": media_to_send  # Imagens para enviar
            }

        except Exception as e:
            print(f"❌ Erro no SimpleCrewEngine: {e}")
            return {
                "response": f"Desculpe, ocorreu um erro interno: {str(e)}",
                "agent_used": "error",
                "agent_name": "Sistema",
                "tools_used": [],
                "success": False,
                "processing_time": time.time() - start_time,
                "demo_mode": True
            }

    async def _load_crew_data(self, crew_id: str) -> Optional[Dict[str, Any]]:
        """Carrega dados da equipe do Firestore"""
        try:
            # Tentar primeiro em 'crews' (nova estrutura)
            doc_ref = self.db.collection('crews').document(crew_id)
            doc = doc_ref.get()

            # Se não encontrar, tentar em 'crew_blueprints' (estrutura antiga)
            if not doc.exists:
                doc_ref = self.db.collection('crew_blueprints').document(crew_id)
                doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                print(f"✅ Dados da equipe carregados: {data.get('name', 'Sem nome')}")
                return data
            else:
                print(f"❌ Equipe {crew_id} não encontrada em /crews nem /crew_blueprints")
                return None

        except Exception as e:
            print(f"❌ Erro ao carregar equipe: {e}")
            return None

    def _select_agent(self, crew_data: Dict[str, Any], message: str, agent_override: str = None) -> Dict[str, Any]:
        """Seleciona o agente apropriado baseado nos dados da equipe"""

        # CORREÇÃO: A estrutura mudou - agentes estão direto em crew_data['agents']
        # e não mais em crew_data['blueprint']['agents']
        agents = crew_data.get('agents', {})

        if not agents:
            print(f"   ❌ NENHUM AGENTE ENCONTRADO - Retornando agente geral padrão")
            return {"key": "geral", "name": "Agente Geral", "role": "Atendente", "goal": "Ajudar o cliente"}

        # Se tem override, usar ele
        if agent_override and agent_override in agents:
            agent_data = agents[agent_override]
            agent_data["key"] = agent_override
            return agent_data

        message_lower = message.lower()

        # 1. ROTEAMENTO BASEADO NAS PALAVRAS-CHAVE DOS AGENTES
        best_match = None
        best_score = 0

        print(f"\n🔍 SELEÇÃO DE AGENTE PARA MENSAGEM: '{message}'")
        print(f"   Agentes disponíveis: {list(agents.keys())}")

        for agent_key, agent_data in agents.items():
            # Pular agentes inativos
            if not agent_data.get('isActive', True):
                print(f"   ⏭️ Pulando agente inativo: {agent_key}")
                continue

            score = 0
            agent_name = agent_data.get('name', agent_key)
            print(f"\n   🤖 Analisando agente: {agent_name} ({agent_key})")

            # Verificar palavras-chave específicas do agente
            keywords = agent_data.get('keywords', [])
            print(f"      Keywords configuradas: {keywords}")
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    score += 10  # Peso alto para palavras-chave específicas
                    print(f"      ✅ Keyword '{keyword}' encontrada! +10 pontos")

            # Verificar role e goal do agente
            role = agent_data.get('role', '').lower()
            goal = agent_data.get('goal', '').lower()
            backstory = agent_data.get('backstory', '').lower()

            # Dividir em palavras para comparação mais inteligente
            agent_words = set()
            for text in [role, goal, backstory]:
                agent_words.update(text.split())

            # Comparar palavras da mensagem com palavras do agente
            message_words = set(message_lower.split())

            # Interseção de palavras (palavras em comum)
            common_words = message_words.intersection(agent_words)
            score += len(common_words) * 2

            # Verificar palavras relacionadas a funções comuns
            if any(word in message_lower for word in ['preço', 'valor', 'custo', 'comprar', 'vender', 'orçamento']):
                if any(word in role + goal for word in ['venda', 'comercial', 'vendedor', 'consultor']):
                    score += 5

            if any(word in message_lower for word in ['problema', 'erro', 'ajuda', 'suporte', 'dúvida']):
                if any(word in role + goal for word in ['suporte', 'técnico', 'ajuda', 'atendimento']):
                    score += 5

            if any(word in message_lower for word in ['agendar', 'marcar', 'horário', 'consulta', 'agendamento']):
                if any(word in role + goal for word in ['agenda', 'agendamento', 'marcação', 'horário']):
                    score += 5

            # Se encontrou uma correspondência melhor
            if score > best_score:
                best_score = score
                best_match = agent_data
                best_match["key"] = agent_key

            print(f"      Score final: {score}")

        print(f"\n   🏆 Melhor match: {best_match.get('name') if best_match else 'Nenhum'} (score: {best_score})")

        # Se encontrou um agente com boa correspondência, usar ele
        if best_match and best_score >= 2:
            print(f"   ✅ Agente selecionado: {best_match.get('name')}")
            return best_match

        print(f"   ⚠️ Score muito baixo ({best_score}), usando fallback...")

        # 2. FALLBACK: VERIFICAR WORKFLOW/HIERARQUIA
        workflow = crew_data.get('workflow', {})

        # Usar agente de entrada se definido
        entry_agent = workflow.get('entryPoint')
        if entry_agent and entry_agent in agents and agents[entry_agent].get('isActive', True):
            agent_data = agents[entry_agent]
            agent_data["key"] = entry_agent
            return agent_data

        # Procurar agente de triagem/atendimento/geral
        for agent_key, agent_data in agents.items():
            if not agent_data.get('isActive', True):
                continue

            role = agent_data.get('role', '').lower()
            if any(word in role for word in ['triagem', 'atendimento', 'geral', 'recepcao']):
                agent_data["key"] = agent_key
                return agent_data

        # 3. ÚLTIMO RECURSO: PRIMEIRO AGENTE ATIVO
        for agent_key, agent_data in agents.items():
            if agent_data.get('isActive', True):
                agent_data["key"] = agent_key
                return agent_data

        # Se nenhum agente ativo, usar o primeiro
        first_key = list(agents.keys())[0]
        first_agent = agents[first_key]
        first_agent["key"] = first_key
        return first_agent

    def _build_context(self, conversation_history: List[Dict[str, Any]], crew_data: Dict[str, Any], selected_agent: Dict[str, Any], knowledge_context: str = "", tools_context: str = "") -> str:
        """Constrói contexto para o agente"""

        context_parts = []

        # PILAR 2: TREINAMENTO DE COMPORTAMENTO (POR AGENTE)
        agent_training = selected_agent.get('training', {})
        agent_name = selected_agent.get('name', 'Agente')

        # Log de debug do treinamento
        print(f"\n🎭 TREINAMENTO DO AGENTE '{agent_name}':")
        print(f"   Training data: {agent_training}")

        # Guardrails (Regras de Comportamento) do Agente - PRIORIDADE MÁXIMA NO TOPO
        guardrails = agent_training.get('guardrails', {})
        do_rules = guardrails.get('do', [])
        dont_rules = guardrails.get('dont', [])

        print(f"   Guardrails DO: {do_rules}")
        print(f"   Guardrails DON'T: {dont_rules}")

        # ⚠️⚠️⚠️ GUARDRAILS NO TOPO - PRIORIDADE MÁXIMA ⚠️⚠️⚠️
        if do_rules or dont_rules:
            context_parts.append("⚠️⚠️⚠️ ATENÇÃO CRÍTICA - LEIA ISTO PRIMEIRO ⚠️⚠️⚠️")
            context_parts.append("="*70)
            context_parts.append("REGRAS CRÍTICAS (SIGA RIGOROSAMENTE):")
            context_parts.append("="*70)

            if dont_rules:
                context_parts.append("\n🚫 PROIBIDO - Você NÃO DEVE JAMAIS:")
                for rule in dont_rules:
                    if rule and rule.strip():
                        context_parts.append(f"  ✗ {rule}")

            if do_rules:
                context_parts.append("\n🔴 OBRIGATÓRIO - Você DEVE:")
                for rule in do_rules:
                    if rule and rule.strip():
                        context_parts.append(f"  ✓ {rule}")

            context_parts.append("\n" + "="*70)
            context_parts.append("🚨 ANTES DE RESPONDER, RELEIA AS REGRAS PROIBIDAS ACIMA 🚨")
            context_parts.append("QUALQUER VIOLAÇÃO DESSAS REGRAS RESULTARÁ EM RESPOSTA INCORRETA")
            context_parts.append("="*70 + "\n")

        # Informações da empresa/equipe
        crew_name = crew_data.get('name', 'Equipe de Atendimento')
        crew_description = crew_data.get('description', 'Equipe especializada em atendimento ao cliente')

        context_parts.append(f"EMPRESA/EQUIPE: {crew_name}")
        context_parts.append(f"DESCRIÇÃO: {crew_description}")

        # Informações do agente selecionado
        agent_role = selected_agent.get('role', 'Atendente')
        agent_goal = selected_agent.get('goal', 'Ajudar o cliente')
        agent_backstory = selected_agent.get('backstory', 'Sou um assistente especializado')

        context_parts.append(f"\nSEU PAPEL: {agent_role}")
        context_parts.append(f"SEU OBJETIVO: {agent_goal}")
        context_parts.append(f"SUA HISTÓRIA: {agent_backstory}")

        # Personalidade do agente
        personality = selected_agent.get('personality', {})
        if personality:
            tone = personality.get('tone', 'profissional')
            traits = personality.get('traits', [])
            context_parts.append(f"TOM DE VOZ: {tone}")
            if traits:
                context_parts.append(f"CARACTERÍSTICAS: {', '.join(traits)}")

            # Custom Instructions (instruções personalizadas)
            custom_instructions = personality.get('customInstructions', '').strip()
            if custom_instructions:
                context_parts.append(f"\n📋 INSTRUÇÕES PERSONALIZADAS:")
                context_parts.append(custom_instructions)

        # Persona do Agente (específica)
        persona = agent_training.get('persona', '').strip()
        if persona:
            print(f"   ✓ Persona encontrada: {persona[:100]}...")
            context_parts.append(f"\nSUA PERSONA:")
            context_parts.append(persona)
        else:
            print(f"   ⚠️ Nenhuma persona configurada")

        # Exemplos de Interação (Few-shot Learning)
        # Combinar exemplos do agente específico + exemplos gerais da equipe
        agent_examples = agent_training.get('examples', [])
        team_training = crew_data.get('training', {})
        team_examples = team_training.get('examples', []) if team_training else []

        # Prioridade: exemplos do agente primeiro, depois exemplos gerais
        all_examples = agent_examples + team_examples

        if all_examples:
            context_parts.append("\n" + "="*70)
            context_parts.append("🎯 EXEMPLOS DE RESPOSTAS CORRETAS - SIGA EXATAMENTE ESTE PADRÃO")
            context_parts.append("="*70)
            context_parts.append("\n⚠️  ATENÇÃO: Você DEVE replicar o estilo, formato e abordagem destes exemplos.")
            context_parts.append("Estas são as ÚNICAS respostas corretas e aprovadas para situações similares.\n")

            # Pegar os 5 mais recentes (ou todos se forem menos que 5)
            recent_examples = all_examples[-5:] if len(all_examples) > 5 else all_examples

            for i, example in enumerate(recent_examples, 1):
                scenario = example.get('scenario', '').strip()
                good = example.get('good', '').strip()
                bad = example.get('bad', '').strip()

                if scenario and good:
                    context_parts.append(f"━━━ EXEMPLO {i} ━━━")
                    context_parts.append(f"📋 SITUAÇÃO:\n{scenario}\n")
                    context_parts.append(f"✅ RESPOSTA OBRIGATÓRIA (copie este padrão):")
                    context_parts.append(f"「{good}」")
                    context_parts.append(f"\n⚠️  Para situações similares, você DEVE responder seguindo EXATAMENTE este modelo acima.")
                    context_parts.append("─"*70 + "\n")

            print(f"📚 {len(recent_examples)} exemplo(s) de treinamento carregado(s) ({len(agent_examples)} do agente, {len(team_examples)} da equipe)")

        # Adicionar contexto da base de conhecimento se disponível
        if knowledge_context:
            context_parts.append(knowledge_context)

        # Histórico da conversa
        if conversation_history:
            context_parts.append("\nHISTÓRICO DA CONVERSA:")
            context_parts.append("⚠️ IMPORTANTE: Se você ver '[Enviei X foto(s)]' no histórico, significa que você JÁ enviou as fotos.")
            context_parts.append("   NÃO invente ou descreva detalhes sobre as fotos. Apenas confirme que foram enviadas e pergunte se o cliente gostou.")
            for msg in conversation_history[-5:]:  # Últimas 5 mensagens
                role_name = "Cliente" if msg.get('role') == 'user' else "Você"
                content = msg.get('content', '')
                if msg.get('type') == 'correction':
                    context_parts.append(f"CORREÇÃO APLICADA: {content}")
                else:
                    context_parts.append(f"{role_name}: {content}")

        # AÇÕES EXECUTADAS AGORA (ferramentas)
        if tools_context:
            context_parts.append("\n" + "="*50)
            context_parts.append("⚡ AÇÕES QUE VOCÊ ACABOU DE EXECUTAR AGORA:")
            context_parts.append("="*50)
            context_parts.append(tools_context)

        # Instruções finais - REFORÇAR REGRAS COM CHECKLIST
        context_parts.append("\n" + "="*70)
        context_parts.append("🎯 INSTRUÇÕES CRÍTICAS - REVISE ANTES DE RESPONDER:")
        context_parts.append("="*70)

        if dont_rules or do_rules:
            context_parts.append("\n⚠️  PRIORIDADE MÁXIMA #1 - GUARDRAILS:")
            context_parts.append("   • RELEIA as regras PROIBIDAS no topo deste prompt")
            context_parts.append("   • Se sua resposta violar QUALQUER regra proibida, PARE e reformule")
            context_parts.append("   • NUNCA cite, mencione ou ofereça algo que esteja nas regras PROIBIDAS")
            context_parts.append("   • Mesmo que a base de conhecimento contenha, IGNORE se for proibido")

        context_parts.append("\n⚠️  PRIORIDADE MÁXIMA #2 - FILTRO DE CONHECIMENTO:")
        context_parts.append("   • A base de conhecimento acima pode conter informações PROIBIDAS")
        context_parts.append("   • Você DEVE FILTRAR e mostrar APENAS o que está permitido pelas regras")
        context_parts.append("   • Exemplo: Se a base tem 10 imóveis mas 5 são para COMPRA (proibido), mostre APENAS os 5 permitidos")
        context_parts.append("   • NUNCA mencione que existem opções filtradas ou proibidas")
        context_parts.append("   • Se TODOS os resultados forem proibidos, informe que não há opções disponíveis no momento")
        context_parts.append("   • Seja PRECISO: se o cliente pede 'casa em Curitiba', mostre apenas casas em Curitiba (não Londrina, não São Paulo)")

        if all_examples:
            context_parts.append("\n⚠️  PRIORIDADE MÁXIMA #3 - EXEMPLOS:")
            context_parts.append("   • Se há EXEMPLOS DE RESPOSTAS CORRETAS acima, você DEVE:")
            context_parts.append("   • Replicar EXATAMENTE o estilo, tom e formato mostrado nos exemplos")
            context_parts.append("   • Usar a mesma estrutura de resposta dos exemplos")
            context_parts.append("   • Os exemplos são OBRIGATÓRIOS - não são opcionais")

        context_parts.append("\n📋 CHECKLIST ANTES DE RESPONDER:")
        context_parts.append("1. ✅ Minha resposta viola alguma regra PROIBIDA? Se SIM, reformule!")
        context_parts.append("2. ✅ Filtrei TODOS os itens proibidos da base de conhecimento?")
        context_parts.append("3. ✅ Minha resposta é PRECISA (cidade, tipo, características corretas)?")
        context_parts.append("4. ✅ Estou seguindo os exemplos fornecidos?")
        context_parts.append("5. ✅ Estou mantendo o tom e personalidade definidos?")

        if knowledge_context:
            context_parts.append("\n📚 IMPORTANTE: Use APENAS as informações da base de conhecimento fornecida acima")
            context_parts.append("   Quando o cliente pedir cardápio/menu/produtos, mostre os itens da base de conhecimento")

        context_parts.append("\n✓ Responda como o agente descrito acima")
        context_parts.append("✓ Seja útil, preciso e mantenha o tom apropriado")
        context_parts.append("✓ Use o histórico da conversa para dar continuidade")
        context_parts.append("✓ NUNCA invente detalhes sobre fotos/imagens que você enviou - apenas confirme que foram enviadas")

        context_parts.append("\n⚠️  LEMBRE-SE: Se você mencionar algo PROIBIDO ou impreciso, sua resposta será REPROVADA.")

        final_context = "\n".join(context_parts)

        # Log do contexto completo para debug
        print("\n" + "="*80)
        print("CONTEXTO ENVIADO AO MODELO:")
        print("="*80)
        print(final_context)
        print("="*80 + "\n")

        return final_context

    async def _generate_response(self, message: str, context: str, selected_agent: Dict[str, Any]) -> str:
        """Gera resposta usando Gemini"""

        # Se não tem modelo disponível, usar resposta inteligente
        if not self.model:
            return self._create_smart_fallback_response(message, selected_agent)

        full_prompt = f"""{context}

MENSAGEM DO CLIENTE: {message}

RESPOSTA:"""

        try:
            # Configuração de geração: temperatura baixa para respostas mais precisas e determinísticas
            from vertexai.generative_models import GenerationConfig

            generation_config = GenerationConfig(
                temperature=0.2,  # Baixa temperatura = mais focado, menos criativo, mais determinístico
                top_p=0.8,       # Amostragem nucleus: considera tokens com probabilidade acumulada de 80%
                top_k=40,        # Considera os 40 tokens mais prováveis
                max_output_tokens=2048
            )

            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )

            if response and response.text:
                return response.text.strip()
            else:
                return self._create_smart_fallback_response(message, selected_agent)

        except Exception as e:
            print(f"❌ Erro ao gerar resposta com Gemini: {e}")
            return self._create_smart_fallback_response(message, selected_agent)

    def _create_smart_fallback_response(self, message: str, selected_agent: Dict[str, Any]) -> str:
        """Cria resposta inteligente baseada no agente quando Gemini falha"""

        agent_name = selected_agent.get('name', 'Assistente')
        agent_role = selected_agent.get('role', 'Atendente')
        agent_goal = selected_agent.get('goal', '')
        message_lower = message.lower()

        # Extrair palavras-chave do goal do agente para resposta personalizada
        goal_words = agent_goal.lower().split() if agent_goal else []

        # Identificar tipo de resposta baseado na mensagem e agente
        greeting_words = ['olá', 'oi', 'bom dia', 'boa tarde', 'boa noite', 'hello']
        price_words = ['preço', 'valor', 'custo', 'quanto', 'orçamento']
        help_words = ['ajuda', 'problema', 'dúvida', 'informação']
        schedule_words = ['agendar', 'marcar', 'horário', 'consulta', 'agendamento']

        # Saudação simples
        if any(word in message_lower for word in greeting_words):
            if agent_goal:
                return f"Olá! Sou {agent_name}, {agent_role}. {agent_goal}. Como posso ajudá-lo?"
            else:
                return f"Olá! Sou {agent_name}, {agent_role}. Como posso ajudá-lo hoje?"

        # Perguntas sobre preço/valor
        elif any(word in message_lower for word in price_words):
            if any(word in goal_words for word in ['venda', 'vendas', 'comercial', 'produto']):
                return f"Olá! Sou {agent_name}. Vou verificar as informações sobre preços para você. Pode me dar mais detalhes sobre o que está procurando?"
            else:
                return f"Olá! Sou {agent_name}. Vou ajudá-lo com sua consulta sobre valores. O que você gostaria de saber?"

        # Pedidos de ajuda
        elif any(word in message_lower for word in help_words):
            return f"Olá! Sou {agent_name}, {agent_role}. Estou aqui para ajudá-lo. Pode me explicar melhor sua dúvida?"

        # Agendamentos
        elif any(word in message_lower for word in schedule_words):
            if any(word in goal_words for word in ['agenda', 'agendamento', 'consulta', 'horário']):
                return f"Olá! Sou {agent_name}. Vou ajudá-lo com o agendamento. Que tipo de serviço você gostaria de agendar?"
            else:
                return f"Olá! Sou {agent_name}. Para agendamentos, posso direcioná-lo para a pessoa certa. O que você precisa agendar?"

        # Resposta genérica baseada no objetivo do agente
        else:
            if agent_goal:
                return f"Olá! Sou {agent_name}, {agent_role}. {agent_goal}. Como posso ajudá-lo com '{message}'?"
            else:
                return f"Olá! Sou {agent_name}, {agent_role}. Como posso ajudá-lo com sua solicitação?"

    def _create_demo_response(self, message: str, crew_id: str) -> Dict[str, Any]:
        """Cria resposta demo quando não há dados da equipe"""

        message_lower = message.lower()

        if any(word in message_lower for word in ['olá', 'oi', 'bom dia', 'boa tarde']):
            response = f"Olá! Sou da equipe {crew_id}. Como posso ajudá-lo hoje?"
            agent_used = "triagem"
        elif any(word in message_lower for word in ['preço', 'valor', 'quanto custa']):
            response = "Vou consultar nossos preços para você. Pode me dar mais detalhes sobre o que você está procurando?"
            agent_used = "vendas"
        elif any(word in message_lower for word in ['cardápio', 'menu', 'pratos']):
            response = "Nosso cardápio tem várias opções deliciosas! Que tipo de prato você está procurando?"
            agent_used = "cardapio"
        else:
            response = f"Obrigado por sua mensagem sobre '{message}'. Como posso ajudá-lo com isso?"
            agent_used = "geral"

        return {
            "response": response,
            "agent_used": agent_used,
            "agent_name": f"Agente {agent_used.title()}",
            "tools_used": False,
            "success": True,
            "processing_time": 0.5,
            "demo_mode": True
        }

    async def get_available_agents(self, tenant_id: str, crew_id: str) -> List[Dict[str, Any]]:
        """Retorna lista de agentes disponíveis na equipe"""
        try:
            crew_data = await self._load_crew_data(crew_id)
            if not crew_data:
                return []

            agents = crew_data.get('agents', {})
            agent_list = []

            for agent_key, agent_data in agents.items():
                agent_list.append({
                    'id': agent_key,
                    'name': agent_data.get('name', agent_key),
                    'role': agent_data.get('role', 'Agente'),
                    'goal': agent_data.get('goal', ''),
                    'isActive': agent_data.get('isActive', True),
                    'tools': agent_data.get('tools', [])
                })

            return agent_list

        except Exception as e:
            print(f"❌ Erro ao obter agentes: {e}")
            return []

    async def validate_crew_config(self, crew_blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """Valida configuração da equipe"""
        try:
            errors = []
            warnings = []

            # Validar estrutura básica
            if not crew_blueprint.get('name'):
                errors.append("Nome da equipe é obrigatório")

            agents = crew_blueprint.get('agents', {})
            if not agents:
                errors.append("Pelo menos um agente é obrigatório")

            # Validar agentes
            for agent_key, agent_data in agents.items():
                if not agent_data.get('name'):
                    errors.append(f"Nome do agente '{agent_key}' é obrigatório")

                if not agent_data.get('role'):
                    warnings.append(f"Agente '{agent_key}' não tem papel definido")

                if not agent_data.get('goal'):
                    warnings.append(f"Agente '{agent_key}' não tem objetivo definido")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "agent_count": len(agents)
            }

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Erro na validação: {str(e)}"],
                "warnings": [],
                "agent_count": 0
            }