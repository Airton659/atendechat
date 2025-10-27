"""
Motor CrewAI Real - Implementação com framework crewai
Mantém toda a lógica de guardrails, knowledge base, tools do SimpleEngine
mas usa Agent/Task/Crew real do framework para tool calling automático
"""

import os
import json
import time
import random
import asyncio
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from firebase_admin import firestore
from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool

# Importar implementações de ferramentas
from .tools import (
    create_knowledge_tool,
    _cadastrar_cliente_planilha_impl,
    _coletar_info_agendamento_impl,
    _buscar_cliente_planilha_impl,
    _enviar_imagem_impl,
    _schedule_appointment_impl,
    _check_schedules_impl,
    _cancel_schedule_impl,
    _update_schedule_impl,
    _list_files_impl,
    _send_file_impl
)


class RealCrewEngine:
    """Engine usando framework CrewAI real com tool calling automático"""

    def __init__(self):
        """Inicializa o motor com CrewAI real"""
        print("🚀 Inicializando RealCrewEngine com framework CrewAI...")

        try:
            self.db = firestore.client()
            print("✅ Firestore conectado")
        except Exception as e:
            print(f"❌ Erro ao conectar Firestore: {e}")
            self.db = None

        # Configurar LLM para usar Vertex AI (Gemini) ao invés de OpenAI
        # CrewAI suporta vertex_ai via modelo vertex_ai/gemini-...
        # Usar gemini-2.5-flash-lite (mesmo modelo do SimpleEngine que funciona)
        model_name = os.getenv("VERTEX_MODEL", "gemini-2.5-flash-lite")

        # Formato para CrewAI usar Vertex AI: vertex_ai/model-name
        self.llm = LLM(
            model=f"vertex_ai/{model_name}",
            temperature=0.2,  # Baixa temperatura para precisão
            max_tokens=2048
        )
        print(f"✅ LLM configurado: vertex_ai/{model_name} (temp=0.2)")

        # Controle de concorrência para requisições ao LLM
        # Limita número de requisições simultâneas ao Vertex AI
        max_concurrent = int(os.getenv("MAX_CONCURRENT_LLM_REQUESTS", "10"))
        self._llm_semaphore = asyncio.Semaphore(max_concurrent)
        print(f"✅ Controle de concorrência: máximo {max_concurrent} requests simultâneas")

        # Keyword search tool (não usa embeddings)
        self.knowledge_tool = self._create_keyword_search_tool()
        print("✅ Knowledge search tool criado")

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

                    print(f"🔍 Buscando conhecimento: '{query}' (crew: {crew_id})")
                    if forbidden_keywords:
                        print(f"   🔒 Filtrando palavras proibidas: {forbidden_keywords}")

                    total_docs = 0
                    forbidden_filtered = 0

                    for doc in vectors_ref.stream():
                        data = doc.to_dict()
                        total_docs += 1

                        # Filtrar por documentos específicos
                        if document_ids and data.get('documentId') not in document_ids:
                            continue

                        content = data.get('content', '').lower()

                        # PRÉ-FILTRO: Verificar palavras proibidas (guardrails)
                        is_forbidden = False
                        if forbidden_keywords:
                            for keyword in forbidden_keywords:
                                if keyword in content:
                                    is_forbidden = True
                                    forbidden_filtered += 1
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

                    print(f"   📊 Total chunks: {total_docs}, Filtrados: {forbidden_filtered}, Resultados: {len(results)}")

                    # Ordenar por score
                    results.sort(key=lambda x: x['similarity'], reverse=True)

                    if not results:
                        return "Não foram encontradas informações relevantes na base de conhecimento."

                    # Formatar resultados
                    formatted = []
                    for i, r in enumerate(results[:max_results], 1):
                        source = r.get('metadata', {}).get('source', 'documento')
                        formatted.append(f"{i}. [{source.upper()}] {r['content']}")

                    return "\n".join(formatted)

                except Exception as e:
                    print(f"❌ Erro ao buscar conhecimento: {e}")
                    return "Erro ao consultar base de conhecimento."

        return KeywordSearchTool(self.db) if self.db else None

    def _create_crewai_tools(self, agent_config: Dict[str, Any], tenant_id: str, crew_id: str, contact_id: int = None, ticket_id: int = None, agent_document_ids: List[str] = None) -> List:
        """Cria ferramentas do CrewAI (@tool decorated functions)"""
        tools = []
        agent_tools = agent_config.get('tools', [])
        tool_configs = agent_config.get('toolConfigs', {})

        print(f"🔧 Criando ferramentas CrewAI para agente: {agent_tools}")

        # 1. CONSULTAR BASE DE CONHECIMENTO
        if 'consultar_base_conhecimento' in agent_tools and self.knowledge_tool:
            # Extrair palavras proibidas dos guardrails
            agent_training = agent_config.get('training', {})
            guardrails = agent_training.get('guardrails', {})
            dont_rules = guardrails.get('dont', [])

            forbidden_keywords = []
            for rule in dont_rules:
                rule_lower = rule.lower()
                if 'compra' in rule_lower or 'comprar' in rule_lower:
                    forbidden_keywords.extend(['compra', 'comprar', 'venda'])
                if 'vend' in rule_lower:
                    forbidden_keywords.extend(['venda', 'vender'])

            # Criar tool com closure capturando variáveis
            knowledge_tool_instance = self.knowledge_tool
            _crew_id = crew_id
            _agent_document_ids = agent_document_ids
            _forbidden_keywords = forbidden_keywords

            @tool("consultar_base_conhecimento")
            def consultar_base_conhecimento(consulta: str, max_results: int = 3) -> str:
                """
                Busca informações na base de conhecimento da empresa.
                Use quando precisar de informações sobre produtos, serviços ou procedimentos.

                Args:
                    consulta: Texto da consulta para buscar
                    max_results: Número máximo de resultados (padrão: 3)

                Returns:
                    Informações relevantes encontradas na base de conhecimento
                """
                return knowledge_tool_instance._run(
                    query=consulta,
                    crew_id=_crew_id,
                    max_results=max_results,
                    document_ids=_agent_document_ids if _agent_document_ids else None,
                    forbidden_keywords=_forbidden_keywords if _forbidden_keywords else None
                )

            tools.append(consultar_base_conhecimento)
            print("   ✅ consultar_base_conhecimento adicionada")

        # 2. SCHEDULE_APPOINTMENT (AGENDAMENTO)
        if 'schedule_appointment' in agent_tools:
            _tenant_id = tenant_id
            _contact_id = contact_id

            @tool("schedule_appointment")
            def schedule_appointment(
                date_time: str,
                body: str,
                status: str = "pending_confirmation"
            ) -> str:
                """
                Agenda um compromisso/horário para o cliente.

                ⚠️ CRITÉRIOS OBRIGATÓRIOS PARA USO:
                SOMENTE use esta ferramenta quando TODAS as condições forem atendidas:
                1. Cliente EXPLICITAMENTE solicita um agendamento/horário/reserva
                2. Cliente fornece DATA e HORÁRIO específicos
                3. Cliente fornece MOTIVO/SERVIÇO do agendamento

                NÃO USE esta ferramenta para:
                - Cumprimentos ou despedidas
                - Agradecimentos
                - Confirmações genéricas sem data/hora/motivo
                - Perguntas sobre disponibilidade
                - Mensagens que não contêm os 3 elementos obrigatórios acima

                Use status='scheduled' se cliente confirmou explicitamente.
                Use status='pending_confirmation' se cliente apenas sugeriu horário.

                🚨 IMPORTANTE - AÇÃO OBRIGATÓRIA APÓS USAR ESTA FERRAMENTA:
                Depois de chamar esta ferramenta, você DEVE SEMPRE:
                1. Informar ao cliente que o agendamento foi registrado (use suas próprias palavras!)
                2. PERGUNTAR AO CLIENTE: "Prefere que EU confirme agora ou aguarda confirmação humana?"
                3. Aguardar a resposta do cliente antes de confirmar

                NUNCA finalize a conversa sem fazer essa pergunta!

                ⚠️ FORMATO DO RETORNO:
                Esta ferramenta retorna dados estruturados. Você DEVE interpretar e responder com suas próprias palavras:

                - "AGENDAMENTO_CRIADO|..." = Agendamento criado com sucesso (pendente)
                - "AGENDAMENTO_CONFIRMADO|..." = Agendamento confirmado com sucesso
                - "⚠️ CONFLITO DE HORÁRIO..." = Já existe agendamento neste horário - sugira outro
                - "ERRO_..." = Erro ao criar agendamento

                NÃO copie o retorno literal! Use suas palavras baseado na sua personalidade/role.

                Args:
                    date_time: Data e hora no formato ISO 8601 (ex: '2025-10-27T08:00:00')
                    body: Descrição completa do agendamento
                    status: 'scheduled' (confirmado) ou 'pending_confirmation' (pendente)

                Returns:
                    Dados estruturados sobre o resultado (você deve interpretar e responder naturalmente)
                """
                print(f"\n📅 EXECUTANDO schedule_appointment!")
                print(f"   tenant_id: {_tenant_id}")
                print(f"   contact_id: {_contact_id}")
                print(f"   date_time: {date_time}")
                print(f"   body: {body}")
                print(f"   status: {status}")

                result = _schedule_appointment_impl(
                    tenant_id=_tenant_id,
                    contact_id=_contact_id or 0,
                    user_id=None,  # Deixar null - será atribuído manualmente depois
                    date_time=date_time,
                    body=body,
                    status=status
                )

                print(f"   Resultado: {result}")
                return result

            tools.append(schedule_appointment)
            print("   ✅ schedule_appointment adicionada")

            # confirm_schedule - Auto-ativado com schedule_appointment
            @tool("confirm_schedule")
            def confirm_schedule(schedule_id: int) -> str:
                """
                Confirma um agendamento que está PENDENTE DE CONFIRMAÇÃO.

                Use esta ferramenta quando o cliente solicitar confirmação:
                - "Pode confirmar"
                - "Confirma agora"
                - "Eu confirmo"
                - "Confirme por favor"
                - Cliente responde que prefere que VOCÊ confirme (não humano)

                IMPORTANTE:
                1. Use check_schedules ANTES para ver agendamentos pendentes
                2. Confirme APENAS agendamentos com status PENDENTE
                3. Após confirmar, informe o cliente que foi confirmado

                Args:
                    schedule_id: ID do agendamento a ser confirmado (obtido via check_schedules)

                Returns:
                    Mensagem de sucesso ou erro
                """
                print(f"\n✅ EXECUTANDO confirm_schedule!")
                print(f"   tenant_id: {_tenant_id}")
                print(f"   schedule_id: {schedule_id}")

                result = _update_schedule_impl(
                    tenant_id=_tenant_id,
                    schedule_id=schedule_id,
                    new_status="scheduled"
                )

                print(f"   Resultado: {result}")
                return result

            tools.append(confirm_schedule)
            print("   ✅ confirm_schedule adicionada")

        # 2.1. CHECK_SCHEDULES (Consultar agendamentos)
        if 'check_schedules' in agent_tools or 'schedule_appointment' in agent_tools:
            _tenant_id = tenant_id
            _contact_id = contact_id

            @tool("check_schedules")
            def check_schedules() -> str:
                """
                Consulta todos os agendamentos existentes do cliente.

                Use esta ferramenta quando o cliente perguntar:
                - "Minha consulta foi confirmada?"
                - "Qual a data da minha consulta?"
                - "Tenho algum agendamento?"
                - "Quero ver meus agendamentos"

                Returns:
                    Lista de agendamentos com ID, data/hora, descrição e status
                """
                print(f"\n📋 EXECUTANDO check_schedules!")
                print(f"   tenant_id: {_tenant_id}")
                print(f"   contact_id: {_contact_id}")

                result = _check_schedules_impl(
                    tenant_id=_tenant_id,
                    contact_id=_contact_id or 0
                )

                print(f"   Resultado: {result}")
                return result

            tools.append(check_schedules)
            print("   ✅ check_schedules adicionada")

        # 2.2. CANCEL_SCHEDULE (Cancelar agendamento)
        if 'cancel_schedule' in agent_tools or 'schedule_appointment' in agent_tools:
            _tenant_id = tenant_id

            @tool("cancel_schedule")
            def cancel_schedule(schedule_id: int) -> str:
                """
                Cancela um agendamento existente.

                IMPORTANTE: Antes de cancelar, use check_schedules para mostrar os agendamentos
                e obter o ID correto.

                Use esta ferramenta quando o cliente solicitar:
                - "Quero cancelar minha consulta"
                - "Preciso desmarcar o agendamento"
                - "Não vou poder ir, cancela pra mim"

                Args:
                    schedule_id: ID do agendamento a ser cancelado (obtido via check_schedules)

                Returns:
                    Mensagem de sucesso ou erro do cancelamento
                """
                print(f"\n🗑️ EXECUTANDO cancel_schedule!")
                print(f"   tenant_id: {_tenant_id}")
                print(f"   schedule_id: {schedule_id}")

                result = _cancel_schedule_impl(
                    tenant_id=_tenant_id,
                    schedule_id=schedule_id
                )

                print(f"   Resultado: {result}")
                return result

            tools.append(cancel_schedule)
            print("   ✅ cancel_schedule adicionada")

        # 2.3. UPDATE_SCHEDULE (Atualizar agendamento)
        if 'update_schedule' in agent_tools or 'schedule_appointment' in agent_tools:
            _tenant_id = tenant_id

            @tool("update_schedule")
            def update_schedule(
                schedule_id: int,
                new_date_time: str = None,
                new_body: str = None,
                new_status: str = None
            ) -> str:
                """
                Atualiza data/hora, descrição ou status de um agendamento existente.

                IMPORTANTE: Antes de atualizar, use check_schedules para mostrar os agendamentos
                e obter o ID correto.

                Use esta ferramenta quando o cliente solicitar:
                - "Quero remarcar para outro dia"
                - "Pode mudar meu agendamento para às 15h?"
                - "Quero trocar de cardiologia para ortopedia"

                Args:
                    schedule_id: ID do agendamento a ser atualizado (obtido via check_schedules)
                    new_date_time: Nova data/hora em formato ISO 8601 (ex: '2025-10-28T15:00:00')
                    new_body: Nova descrição do agendamento
                    new_status: Novo status ('scheduled', 'pending_confirmation', 'cancelled')

                Returns:
                    Mensagem de sucesso mostrando as alterações realizadas
                """
                print(f"\n✏️ EXECUTANDO update_schedule!")
                print(f"   tenant_id: {_tenant_id}")
                print(f"   schedule_id: {schedule_id}")
                print(f"   new_date_time: {new_date_time}")
                print(f"   new_body: {new_body}")
                print(f"   new_status: {new_status}")

                result = _update_schedule_impl(
                    tenant_id=_tenant_id,
                    schedule_id=schedule_id,
                    new_date_time=new_date_time,
                    new_body=new_body,
                    new_status=new_status
                )

                print(f"   Resultado: {result}")
                return result

            tools.append(update_schedule)
            print("   ✅ update_schedule adicionada")

        # 2.4. LIST_FILES (Listar arquivos da File List)
        if 'list_files' in agent_tools or 'send_file' in agent_tools:
            _tenant_id = tenant_id

            @tool("list_files")
            def list_files() -> str:
                """
                Lista todos os arquivos disponíveis na File List (galeria de arquivos).

                Use esta ferramenta quando o cliente perguntar:
                - "Quais arquivos vocês têm?"
                - "Tem alguma foto/documento disponível?"
                - "Pode me mostrar o catálogo?"
                - "Que materiais vocês têm?"

                Returns:
                    Lista de arquivos com ID, nome e descrição
                """
                print(f"\n📁 EXECUTANDO list_files!")
                print(f"   tenant_id: {_tenant_id}")

                result = _list_files_impl(tenant_id=_tenant_id)

                print(f"   Resultado: {result[:200]}...")
                return result

            tools.append(list_files)
            print("   ✅ list_files adicionada")

        # 2.5. SEND_FILE (Enviar arquivo da File List)
        if 'send_file' in agent_tools:
            _tenant_id = tenant_id
            _ticket_id = ticket_id

            @tool("send_file")
            def send_file(file_id: int) -> str:
                """
                Envia um arquivo da File List (galeria de arquivos) para o cliente.

                ⚠️ IMPORTANTE:
                - Use a ferramenta list_files PRIMEIRO para saber quais arquivos existem
                - Só envie arquivos que o cliente solicitou explicitamente
                - Informe ao cliente qual arquivo você está enviando

                Args:
                    file_id: ID do arquivo (obtido com list_files)

                Returns:
                    Mensagem de sucesso ou erro do envio
                """
                print(f"\n📤 EXECUTANDO send_file!")
                print(f"   tenant_id: {_tenant_id}")
                print(f"   ticket_id: {_ticket_id}")
                print(f"   file_id: {file_id}")

                result = _send_file_impl(
                    tenant_id=_tenant_id,
                    ticket_id=_ticket_id or 0,
                    file_id=file_id
                )

                print(f"   Resultado: {result}")
                return result

            tools.append(send_file)
            print("   ✅ send_file adicionada")

        # 3. CADASTRAR CLIENTE EM PLANILHA (se configurado)
        if 'cadastrar_cliente_planilha' in agent_tools and 'googleSheets' in tool_configs:
            sheets_config = tool_configs['googleSheets']
            _spreadsheet_id = sheets_config.get('spreadsheetId', '')
            _range_name = sheets_config.get('rangeName', 'Clientes!A:E')
            _tenant_id = tenant_id

            if _spreadsheet_id:
                @tool("cadastrar_cliente")
                def cadastrar_cliente(nome: str, telefone: str = "", email: str = "", observacoes: str = "") -> str:
                    """
                    Cadastra um novo cliente na planilha Google Sheets.

                    Args:
                        nome: Nome completo do cliente
                        telefone: Telefone do cliente (opcional)
                        email: Email do cliente (opcional)
                        observacoes: Observações adicionais (opcional)

                    Returns:
                        Mensagem de sucesso ou erro do cadastro
                    """
                    return _cadastrar_cliente_planilha_impl(
                        spreadsheet_id=_spreadsheet_id,
                        range_name=_range_name,
                        nome=nome,
                        telefone=telefone,
                        email=email,
                        observacoes=observacoes,
                        tenant_id=_tenant_id
                    )

                tools.append(cadastrar_cliente)
                print("   ✅ cadastrar_cliente adicionada")

        print(f"✅ Total de {len(tools)} ferramentas criadas")
        return tools

    async def process_message(
        self,
        tenant_id: str,
        crew_id: str,
        message: str,
        conversation_history: List[Dict[str, Any]] = None,
        agent_override: str = None,
        remote_jid: str = None,
        contact_id: int = None,
        ticket_id: int = None
    ) -> Dict[str, Any]:
        """Processa mensagem usando CrewAI framework real"""

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

            # Selecionar agente (usa mesma lógica do SimpleEngine)
            selected_agent = self._select_agent(crew_data, message, agent_override)
            print(f"✅ Agente selecionado: {selected_agent.get('name')} (key: {selected_agent.get('key')})")

            # Verificar documentos específicos do agente
            agent_document_ids = selected_agent.get('knowledgeDocuments', [])

            # ============================================================================
            # VALIDAÇÕES PROGRAMÁTICAS (100% GENÉRICAS)
            # ============================================================================
            validation_message = ""
            validation_config = selected_agent.get('validation_config', {})

            if validation_config.get('enabled', False):
                print("🔍 Sistema de validação ATIVADO para este agente")

                try:
                    from .validation_hooks import GenericValidationHooks

                    # Wrapper para kb_search compatível com validation_hooks
                    async def kb_search_wrapper(query: str, crew_id: str, doc_ids: List[str]) -> List[Dict[str, Any]]:
                        """Wrapper para compatibilizar _search_knowledge com GenericValidationHooks"""
                        return await self._search_knowledge(
                            query=query,
                            crew_id=crew_id,
                            document_ids=doc_ids,
                            max_results=5
                        )

                    validator = GenericValidationHooks(kb_search_func=kb_search_wrapper)

                    # Executar cada regra de validação
                    rules = validation_config.get('rules', [])
                    print(f"   📋 {len(rules)} regra(s) de validação configurada(s)")

                    for rule in rules:
                        if not rule.get('enabled', True):
                            print(f"   ⏭️ Regra '{rule.get('name')}' desabilitada, pulando")
                            continue

                        print(f"   🎯 Executando regra: '{rule.get('name')}'")

                        validation_result = await validator.run_validation(
                            message=message,
                            crew_id=crew_id,
                            doc_ids=agent_document_ids if agent_document_ids else [],
                            rule_config=rule
                        )

                        if validation_result and not validation_result.get('valid', True):
                            # CONFLITO DETECTADO!
                            conflict = validation_result['conflict']
                            print(f"   ❌ CONFLITO: {conflict['correction_message'][:100]}...")

                            validation_message += f"\n\n⚠️ VALIDAÇÃO DETECTOU PROBLEMA:\n"
                            validation_message += f"{conflict['correction_message']}\n"
                            validation_message += f"\nEvidência da base de conhecimento:\n{conflict['kb_evidence'][:300]}...\n"

                except Exception as e:
                    print(f"⚠️ Erro ao executar validações: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("⏭️ Sistema de validação DESABILITADO para este agente")

            # Criar ferramentas do CrewAI
            crewai_tools = self._create_crewai_tools(
                agent_config=selected_agent,
                tenant_id=tenant_id,
                crew_id=crew_id,
                contact_id=contact_id,
                ticket_id=ticket_id,
                agent_document_ids=agent_document_ids if agent_document_ids else None
            )

            # Construir contexto (guardrails, persona, examples, suggestions)
            context = self._build_context(conversation_history, crew_data, selected_agent)

            # INJETAR VALIDAÇÕES no contexto se houver
            if validation_message:
                context += "\n\n" + "="*80 + "\n"
                context += validation_message
                context += "="*80 + "\n"
                print(f"✅ Mensagem de validação injetada no contexto ({len(validation_message)} caracteres)")

            print(f"📝 Tamanho do contexto: {len(context)} caracteres ({len(context.split())} palavras)")

            # Criar agente CrewAI
            agent_role = selected_agent.get('role', 'Atendente')
            agent_goal = selected_agent.get('goal', 'Ajudar o cliente')

            crew_agent = Agent(
                role=agent_role,
                goal=agent_goal,
                backstory=context,  # Todo o contexto vai aqui
                tools=crewai_tools,
                llm=self.llm,  # Usar Vertex AI (Gemini)
                verbose=False,  # Desabilita logs decorativos
                allow_delegation=False
            )

            # Criar task para processar a mensagem
            # IMPORTANTE: Não incluir texto que possa aparecer na resposta final
            scheduling_reminder = ""
            if 'schedule_appointment' in agent_tools:
                scheduling_reminder = """

            ⚠️ REGRA CRÍTICA DE AGENDAMENTO:
            1. Após usar schedule_appointment, SEMPRE perguntar: "Prefere que EU confirme agora ou aguarda confirmação humana?"
            2. Se cliente pedir confirmação ("confirma", "pode confirmar", "confirme"):
               - Use check_schedules para ver agendamentos pendentes
               - Use confirm_schedule(schedule_id) para confirmar
               - Informe ao cliente que foi CONFIRMADO com sucesso

            NUNCA diga que confirmou sem usar a ferramenta confirm_schedule!
            """

            task_description = f"""
            Mensagem do cliente: "{message}"

            {"Histórico da conversa:\n" + self._format_conversation_history(conversation_history) if conversation_history else ""}

            Instruções:
            1. Analisar a mensagem do cliente
            2. Usar suas ferramentas se necessário
            3. Responder de forma útil, clara e personalizada
            4. Manter o tom e personalidade do seu perfil
            5. SEGUIR RIGOROSAMENTE as regras de guardrails{scheduling_reminder}

            RESPONDA APENAS o que você diria ao cliente, SEM incluir estas instruções.
            """

            task = Task(
                description=task_description,
                expected_output="Resposta direta ao cliente",
                agent=crew_agent
            )

            # Criar e executar Crew
            crew = Crew(
                agents=[crew_agent],
                tasks=[task],
                verbose=False  # Desabilita logs decorativos do Crew
            )

            print("🚀 Executando CrewAI Crew...")
            print(f"   Agente: {crew_agent.role}")
            print(f"   Ferramentas disponíveis: {[str(t.name) if hasattr(t, 'name') else str(t) for t in crewai_tools]}")
            print(f"   Mensagem: {message}")

            # Executar com controle de concorrência e retry logic
            result = None
            max_retries = 3

            async with self._llm_semaphore:  # Controlar concorrência
                for attempt in range(max_retries):
                    try:
                        # Executar CrewAI (sincronamente dentro do contexto async)
                        result = await asyncio.to_thread(crew.kickoff)

                        print(f"✅ CrewAI executado com sucesso!")
                        print(f"   Tipo do resultado: {type(result)}")
                        print(f"   Resultado bruto: {result}")
                        break  # Sucesso, sair do loop

                    except Exception as e:
                        error_msg = str(e).lower()

                        # Verificar se é erro de rate limit
                        is_rate_limit = any(keyword in error_msg for keyword in [
                            "429", "rate", "quota", "resource exhausted", "too many requests"
                        ])

                        if is_rate_limit and attempt < max_retries - 1:
                            # Ainda tem tentativas, fazer backoff exponencial
                            wait_time = 2 ** attempt  # 1s, 2s, 4s
                            print(f"⚠️ Rate limit detectado (tentativa {attempt + 1}/{max_retries})")
                            print(f"   Aguardando {wait_time}s antes de tentar novamente...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # Não é rate limit OU última tentativa falhou
                            # Retornar mensagem amigável ao cliente
                            print(f"❌ Falha após {attempt + 1} tentativas: {e}")

                            return {
                                "response": self._create_friendly_error_message(selected_agent),
                                "agent_used": selected_agent.get("key", "geral"),
                                "agent_name": selected_agent.get("name", "Agente Geral"),
                                "tools_used": [],
                                "success": False,
                                "error": True,  # Flag para backend saber que houve erro
                                "processing_time": round(time.time() - start_time, 2),
                                "demo_mode": False
                            }

            # Se result ainda é None (não deveria acontecer), retornar erro amigável
            if result is None:
                return {
                    "response": self._create_friendly_error_message(selected_agent),
                    "agent_used": selected_agent.get("key", "geral"),
                    "agent_name": selected_agent.get("name", "Agente Geral"),
                    "tools_used": [],
                    "success": False,
                    "error": True,
                    "processing_time": round(time.time() - start_time, 2),
                    "demo_mode": False
                }

            # Processar resultado
            response_text = str(result).strip() if result else "Desculpe, não consegui processar sua solicitação."

            # Limpar resposta: remover texto da task description que pode vazar
            # Padrões a remover:
            cleanup_patterns = [
                "Você recebeu a seguinte mensagem de um cliente:",
                "Mensagem do cliente:",
                f'"{message}"',
                "Instruções:",
                "RESPONDA APENAS"
            ]

            for pattern in cleanup_patterns:
                if pattern in response_text:
                    # Remover o padrão e tudo antes dele
                    parts = response_text.split(pattern, 1)
                    if len(parts) > 1:
                        response_text = parts[1].strip()

            # Remover aspas duplas no início/fim se houver
            response_text = response_text.strip('"').strip()

            # Detectar quais ferramentas foram usadas (baseado no output do CrewAI)
            result_str = str(result).lower()
            if "consultar_base_conhecimento" in result_str or "base de conhecimento" in result_str:
                tools_used.append("consultar_base_conhecimento")
                print("   🔧 Ferramenta detectada: consultar_base_conhecimento")

            if "schedule_appointment" in result_str or "agendamento criado" in result_str or "agendado" in result_str:
                tools_used.append("schedule_appointment")
                print("   🔧 Ferramenta detectada: schedule_appointment")

            if "cadastrar_cliente" in result_str or "cadastrado" in result_str:
                tools_used.append("cadastrar_cliente")
                print("   🔧 Ferramenta detectada: cadastrar_cliente")

            print(f"   Total de ferramentas usadas: {len(tools_used)}")

            processing_time = time.time() - start_time

            return {
                "response": response_text,
                "agent_used": selected_agent.get("key", "geral"),
                "agent_name": selected_agent.get("name", "Agente Geral"),
                "tools_used": tools_used,
                "success": True,
                "processing_time": round(processing_time, 2),
                "demo_mode": False
            }

        except Exception as e:
            print(f"❌ Erro no RealCrewEngine: {e}")
            import traceback
            traceback.print_exc()

            # NUNCA retornar erro técnico ao cliente
            # Sempre retornar mensagem amigável
            return {
                "response": self._create_friendly_error_message({}),
                "agent_used": "error",
                "agent_name": "Sistema",
                "tools_used": [],
                "success": False,
                "error": True,
                "processing_time": round(time.time() - start_time, 2),
                "demo_mode": False
            }

    async def _load_crew_data(self, crew_id: str) -> Optional[Dict[str, Any]]:
        """Carrega dados da equipe do Firestore"""
        try:
            # Tentar primeiro em 'crews' (nova estrutura)
            doc_ref = self.db.collection('crews').document(crew_id)
            doc = doc_ref.get()

            # Se não encontrar, tentar em 'crew_blueprints'
            if not doc.exists:
                doc_ref = self.db.collection('crew_blueprints').document(crew_id)
                doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                print(f"✅ Equipe carregada: {data.get('name', 'Sem nome')}")
                return data
            else:
                print(f"❌ Equipe {crew_id} não encontrada")
                return None

        except Exception as e:
            print(f"❌ Erro ao carregar equipe: {e}")
            return None

    def _select_agent(self, crew_data: Dict[str, Any], message: str, agent_override: str = None) -> Dict[str, Any]:
        """Seleciona o agente apropriado (mesma lógica do SimpleEngine)"""

        agents = crew_data.get('agents', {})

        if not agents:
            print("❌ Nenhum agente encontrado - usando padrão")
            return {"key": "geral", "name": "Agente Geral", "role": "Atendente", "goal": "Ajudar o cliente"}

        # Se tem override, usar
        if agent_override and agent_override in agents:
            agent_data = agents[agent_override]
            agent_data["key"] = agent_override
            return agent_data

        message_lower = message.lower()

        print(f"\n🔍 SELEÇÃO DE AGENTE:")
        print(f"   Mensagem: '{message}'")
        print(f"   Total de agentes: {len(agents)}")

        # Roteamento baseado em palavras-chave
        best_match = None
        best_score = 0

        for agent_key, agent_data in agents.items():
            if not agent_data.get('isActive', True):
                print(f"   ⏭️ {agent_key} - INATIVO")
                continue

            score = 0
            role = agent_data.get('role', '').lower()
            goal = agent_data.get('goal', '').lower()
            agent_name = agent_data.get('name', agent_key)

            print(f"\n   🤖 Avaliando: {agent_name} ({agent_key})")

            # Palavras-chave do agente
            keywords = agent_data.get('keywords', [])
            print(f"      Keywords configuradas: {len(keywords)}")
            if keywords:
                print(f"      Keywords: {keywords[:3]}...")  # Mostrar primeiras 3

            matched_keywords = []
            for keyword in keywords:
                keyword_clean = keyword.strip()  # Remove espaços extras
                if keyword_clean.lower() in message_lower:
                    score += 3
                    matched_keywords.append(keyword_clean)

            if matched_keywords:
                print(f"      ✅ Keywords matched: {matched_keywords}")
                print(f"      Score de keywords: +{len(matched_keywords) * 3}")

            # Palavras do role/goal (ignorar palavras de 1-2 letras - vogais soltas)
            role_goal_words = [word for word in (role.split() + goal.split()) if len(word) > 2]
            matched_role_goal = [word for word in role_goal_words if word in message_lower]
            if matched_role_goal:
                score += 1
                print(f"      ✅ Role/Goal matched: {matched_role_goal}")
                print(f"      Score de role/goal: +1")

            print(f"      📊 Score total: {score}")

            if score > best_score:
                best_score = score
                best_match = agent_data
                best_match["key"] = agent_key
                print(f"      🏆 NOVO MELHOR! (score: {score})")

        print(f"\n   🎯 Melhor match: {best_match.get('name') if best_match else 'Nenhum'} (score: {best_score})")

        # Se encontrou com score bom, usar
        if best_match and best_score >= 2:
            print(f"   ✅ Score suficiente (>= 2), usando agente selecionado")
            return best_match

        print(f"   ⚠️ Score insuficiente (< 2), tentando fallback...")

        # Fallback: workflow entry point
        workflow = crew_data.get('workflow', {})
        entry_agent = workflow.get('entryPoint')
        if entry_agent and entry_agent in agents:
            agent_data = agents[entry_agent]
            agent_data["key"] = entry_agent
            return agent_data

        # Último recurso: primeiro agente ativo
        for agent_key, agent_data in agents.items():
            if agent_data.get('isActive', True):
                agent_data["key"] = agent_key
                return agent_data

        # Absolutamente último: primeiro da lista
        first_key = list(agents.keys())[0]
        first_agent = agents[first_key]
        first_agent["key"] = first_key
        return first_agent

    def _build_context(self, conversation_history: List[Dict[str, Any]], crew_data: Dict[str, Any], selected_agent: Dict[str, Any]) -> str:
        """Constrói contexto completo com guardrails, persona, examples (mesma lógica do SimpleEngine)"""

        context_parts = []

        # GUARDRAILS NO TOPO - PRIORIDADE MÁXIMA
        agent_training = selected_agent.get('training', {})
        guardrails = agent_training.get('guardrails', {})
        do_rules = guardrails.get('do', [])
        dont_rules = guardrails.get('dont', [])

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
            context_parts.append("="*70 + "\n")

        # Informações da empresa/equipe
        crew_name = crew_data.get('name', 'Equipe de Atendimento')
        crew_description = crew_data.get('description', '')

        context_parts.append(f"EMPRESA/EQUIPE: {crew_name}")
        if crew_description:
            context_parts.append(f"DESCRIÇÃO: {crew_description}")

        # Informações do agente
        agent_backstory = selected_agent.get('backstory', 'Sou um assistente especializado')
        context_parts.append(f"\nSUA HISTÓRIA: {agent_backstory}")

        # Personalidade
        personality = selected_agent.get('personality', {})
        if personality:
            tone = personality.get('tone', 'profissional')
            traits = personality.get('traits', [])
            context_parts.append(f"TOM DE VOZ: {tone}")
            if traits:
                context_parts.append(f"CARACTERÍSTICAS: {', '.join(traits)}")

            custom_instructions = personality.get('customInstructions', '').strip()
            if custom_instructions:
                context_parts.append(f"\n📋 INSTRUÇÕES PERSONALIZADAS:")
                context_parts.append(custom_instructions)

        # Persona do agente
        persona = agent_training.get('persona', '').strip()
        if persona:
            context_parts.append(f"\nSUA PERSONA:")
            context_parts.append(persona)

        # Exemplos de interação (few-shot learning)
        agent_examples = agent_training.get('examples', [])
        team_training = crew_data.get('training', {})
        team_examples = team_training.get('examples', []) if team_training else []
        all_examples = agent_examples + team_examples

        if all_examples:
            context_parts.append("\n" + "="*70)
            context_parts.append("🎯 EXEMPLOS DE RESPOSTAS CORRETAS - SIGA EXATAMENTE ESTE PADRÃO")
            context_parts.append("="*70)

            recent_examples = all_examples[-5:] if len(all_examples) > 5 else all_examples

            for i, example in enumerate(recent_examples, 1):
                scenario = example.get('scenario', '').strip()
                good = example.get('good', '').strip()
                bad = example.get('bad', '').strip()

                if scenario:
                    context_parts.append(f"\n📝 EXEMPLO {i}:")
                    context_parts.append(f"Cenário: {scenario}")
                    if good:
                        context_parts.append(f"✓ RESPOSTA CORRETA: {good}")
                    if bad:
                        context_parts.append(f"✗ RESPOSTA INCORRETA (NUNCA USE): {bad}")

            context_parts.append("\n" + "="*70)

        # SUGGESTIONS - REGRAS DE COMPORTAMENTO (IA)
        # Instruções comportamentais que o agente deve seguir (90-95% precisão)
        suggestions = agent_training.get('suggestions', [])
        if suggestions:
            # Separar por prioridade
            critical_suggestions = [s for s in suggestions if s.get('priority') == 'critical']
            high_suggestions = [s for s in suggestions if s.get('priority') == 'high']
            medium_suggestions = [s for s in suggestions if s.get('priority') == 'medium']

            # Incluir apenas critical e high no contexto (evitar sobrecarga)
            important_suggestions = critical_suggestions + high_suggestions

            if important_suggestions:
                context_parts.append("\n" + "="*70)
                context_parts.append("⚡ REGRAS DE COMPORTAMENTO CRÍTICAS")
                context_parts.append("="*70)
                context_parts.append("ATENÇÃO: Estas regras definem QUANDO e COMO você deve agir.")
                context_parts.append("Siga rigorosamente estas instruções em situações específicas:\n")

                for i, suggestion in enumerate(important_suggestions, 1):
                    trigger = suggestion.get('trigger', '')
                    behavior = suggestion.get('behavior', '')
                    priority_icon = "🔴" if suggestion.get('priority') == 'critical' else "🟠"

                    if trigger and behavior:
                        context_parts.append(f"{priority_icon} REGRA {i}:")
                        context_parts.append(f"   QUANDO: {trigger}")
                        context_parts.append(f"   VOCÊ DEVE: {behavior}\n")

                context_parts.append("="*70 + "\n")

                print(f"   📌 {len(important_suggestions)} sugestão(ões) de comportamento adicionadas ao contexto")

        return "\n".join(context_parts)

    def _format_conversation_history(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Formata histórico de conversa"""
        if not conversation_history:
            return ""

        formatted = []
        for msg in conversation_history[-5:]:  # Últimas 5 mensagens
            role = "Cliente" if msg.get('role') == 'user' else "Assistente"
            content = msg.get('content', '')
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def _create_demo_response(self, message: str, crew_id: str) -> Dict[str, Any]:
        """Resposta demo sem Firestore"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['olá', 'oi', 'bom dia']):
            response = "Olá! Como posso ajudá-lo hoje?"
            agent_used = "triagem"
        elif any(word in message_lower for word in ['agendar', 'marcar', 'consulta']):
            response = "Entendo que você deseja agendar. Pode me informar o dia e horário de sua preferência?"
            agent_used = "agendamento"
        else:
            response = f"Obrigado por sua mensagem. Como posso ajudá-lo?"
            agent_used = "geral"

        return {
            "response": response,
            "agent_used": agent_used,
            "agent_name": f"Agente {agent_used.title()}",
            "tools_used": [],
            "success": True,
            "demo_mode": True
        }

    def _create_friendly_error_message(self, agent: Dict[str, Any]) -> str:
        """
        Cria mensagem amigável ao cliente quando o sistema falha.
        NUNCA retorna erros técnicos - sempre mensagens claras e amigáveis.
        """
        agent_name = agent.get('name', 'Assistente') if agent else 'Assistente'

        # Lista de mensagens amigáveis (rotaciona para variar)
        messages = [
            f"Olá! Sou o {agent_name}. Estou com muitas conversas no momento 😅\n\n"
            "Por favor, envie sua mensagem novamente em 1-2 minutos.\n\n"
            "Obrigado pela compreensão!",

            f"Oi! Aqui é o {agent_name}. No momento estou atendendo vários clientes ao mesmo tempo.\n\n"
            "Aguarde 1-2 minutos e me envie sua mensagem novamente, por favor.\n\n"
            "Agradeço a paciência! 🙏",

            f"Desculpe! Estou com alto volume de atendimentos agora.\n\n"
            "Por gentileza, aguarde 1-2 minutos e tente novamente.\n\n"
            "Obrigado!",

            "Olá! Estou com muitas solicitações no momento.\n\n"
            "Por favor, aguarde 1-2 minutos e me envie sua mensagem novamente.\n\n"
            "Obrigado pela paciência! 😊"
        ]

        # Escolher mensagem aleatória para variar
        return random.choice(messages)

    async def get_available_agents(self, tenant_id: str, crew_id: str) -> List[Dict[str, Any]]:
        """Retorna lista de agentes disponíveis"""
        try:
            crew_data = await self._load_crew_data(crew_id)
            if not crew_data:
                return []

            agents = crew_data.get('agents', {})
            agent_list = []

            for agent_key, agent_config in agents.items():
                if agent_config.get('isActive', True):
                    agent_list.append({
                        'id': agent_key,
                        'name': agent_config.get('name', agent_key),
                        'role': agent_config.get('role', ''),
                        'goal': agent_config.get('goal', ''),
                        'tools': agent_config.get('tools', []),
                        'order': agent_config.get('order', 999)
                    })

            agent_list.sort(key=lambda x: x['order'])
            return agent_list

        except Exception as e:
            print(f"❌ Erro ao obter agentes: {e}")
            return []

    async def validate_crew_config(self, crew_blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """Valida configuração da equipe"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "agent_count": 0,
            "tools_count": 0
        }

        agents = crew_blueprint.get('agents', {})

        if not agents:
            validation["errors"].append("Nenhum agente definido")
            validation["valid"] = False
            return validation

        validation["agent_count"] = len(agents)

        # Validar cada agente
        for agent_key, agent_config in agents.items():
            required_fields = ['role', 'goal']
            for field in required_fields:
                if not agent_config.get(field):
                    validation["errors"].append(f"Agente '{agent_key}' sem campo '{field}'")

            tools = agent_config.get('tools', [])
            validation["tools_count"] += len(tools)

        validation["valid"] = len(validation["errors"]) == 0
        return validation
