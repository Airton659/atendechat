# api/src/atendimento_crewai/training_service.py - Serviço de Treinamento Interativo

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import time
from datetime import datetime

from firebase_admin import firestore

router = APIRouter(prefix="/training", tags=["Training"])

class GenerateResponseRequest(BaseModel):
    tenantId: str
    teamId: str
    agentId: Optional[str] = None
    message: str
    conversationHistory: List[Dict[str, Any]] = []

class TrainingService:
    def __init__(self):
        self.db = firestore.client()

    async def get_team_blueprint(self, tenant_id: str, team_id: str) -> Dict[str, Any]:
        """Obtém o blueprint da equipe"""
        try:
            # Tentar primeiro em 'crews' (nova estrutura)
            team_doc = self.db.collection('crews').document(team_id).get()

            # Se não encontrar, tentar em 'crew_blueprints' (estrutura antiga)
            if not team_doc.exists:
                team_doc = self.db.collection('crew_blueprints').document(team_id).get()

            if not team_doc.exists:
                raise Exception(f"Equipe {team_id} não encontrada")

            team_data = team_doc.to_dict()

            # Verificação de tenant - comentada pois pode não existir em todas as equipes
            # if team_data.get('tenantId') != tenant_id:
            #     raise Exception("Acesso negado à equipe")

            return team_data
        except Exception as e:
            raise Exception(f"Erro ao obter equipe: {str(e)}")

    async def get_knowledge_context(self, crew_id: str, query: str, max_results: int = 3, document_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Busca contexto relevante na base de conhecimento usando busca por palavra-chave"""
        try:
            results = []

            # Busca por palavra-chave nos vetores usando crewId (não tenantId!)
            vectors_ref = self.db.collection('vectors').where('crewId', '==', crew_id)

            query_lower = query.lower()
            query_words = set(query_lower.split())

            print(f"🔍 Buscando por palavra-chave: '{query}' (crew: {crew_id})")
            if document_ids:
                print(f"   Filtrando por {len(document_ids)} documento(s) específico(s): {document_ids}")

            all_chunks = list(vectors_ref.stream())
            total_chunks = len(all_chunks)
            print(f"   📊 Total de chunks encontrados na crew: {total_chunks}")

            chunks_after_filter = []
            chunks_with_score = []

            for doc in all_chunks:
                data = doc.to_dict()

                # Filtrar por documentos específicos se fornecido
                if document_ids and data.get('documentId') not in document_ids:
                    continue

                chunks_after_filter.append(data)
                content = data.get('content', '').lower()

                # Calcular score baseado em palavras encontradas
                score = 0
                for word in query_words:
                    if word in content:
                        score += content.count(word)

                if score > 0:
                    chunks_with_score.append(data)
                    results.append({
                        'content': data.get('content'),
                        'metadata': data.get('metadata', {}),
                        'similarity': score,
                        'documentId': data.get('documentId'),
                        'chunkIndex': data.get('chunkIndex', 0)
                    })

            print(f"   📊 Chunks após filtrar por documentId: {len(chunks_after_filter)}")
            print(f"   📊 Chunks com score > 0: {len(chunks_with_score)}")

            # Ordenar por score
            results.sort(key=lambda x: x['similarity'], reverse=True)

            print(f"✅ Encontrados {len(results)} resultados por palavra-chave")

            return results[:max_results]

        except Exception as e:
            print(f"Erro ao buscar contexto: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def generate_training_response(self, request: GenerateResponseRequest) -> Dict[str, Any]:
        """Gera resposta usando a equipe de IA para treinamento"""
        try:
            start_time = time.time()

            # Obter blueprint da equipe
            team_data = await self.get_team_blueprint(request.tenantId, request.teamId)

            # DEBUG: Log do agente solicitado
            print(f"\n📋 REQUEST DEBUG:")
            print(f"   agentId solicitado: '{request.agentId}'")
            print(f"   agentId type: {type(request.agentId)}")
            print(f"   agentId bool: {bool(request.agentId)}")
            print(f"   Agentes disponíveis: {list(team_data.get('agents', {}).keys())}")

            # Determinar qual agente usar
            agent_to_use = self._select_agent_for_training(team_data, request.agentId, request.message)
            print(f"   ✅ Agente selecionado: '{agent_to_use}'\n")

            # Construir prompt para o agente
            agent_config = team_data['agents'][agent_to_use]

            # Obter documentos específicos do agente
            agent_document_ids = agent_config.get('knowledgeDocuments', [])

            # Buscar contexto na base de conhecimento (filtrado por documentos do agente)
            knowledge_context = await self.get_knowledge_context(
                request.teamId,  # Usar teamId/crewId, NÃO tenantId!
                request.message,
                document_ids=agent_document_ids if agent_document_ids else None
            )

            # DEBUG: Log da configuração do agente
            print(f"\n🎭 DEBUG - Configuração do agente '{agent_to_use}':")
            print(f"   Nome: {agent_config.get('name')}")
            print(f"   Training: {agent_config.get('training')}")
            print(f"   Knowledge Docs: {agent_config.get('knowledgeDocuments')}")
            print(f"   Tools: {agent_config.get('tools')}\n")

            # EXECUTAR FERRAMENTAS SE NECESSÁRIO
            tools_context = ""
            agent_tools = agent_config.get('tools', [])
            tool_configs = agent_config.get('toolConfigs', {})
            message_lower = request.message.lower()

            # 0. FERRAMENTA DE BUSCAR CLIENTE (executar primeiro se houver número de telefone)
            if 'buscar_cliente_planilha' in agent_tools and 'buscarCliente' in tool_configs:
                print(f"\n🔍 Agente tem ferramenta de busca de cliente configurada")

                # Tentar extrair telefone da mensagem
                import re
                telefone_match = re.search(r'(\d{10,11})', request.message)

                if telefone_match:
                    telefone_busca = telefone_match.group(1)
                    buscar_config = tool_configs['buscarCliente']
                    spreadsheet_id = buscar_config.get('spreadsheetId', '')
                    range_name = buscar_config.get('rangeName', 'Clientes!A:F')

                    if spreadsheet_id:
                        print(f"   🔎 Buscando cliente com telefone: {telefone_busca}")

                        try:
                            from .tools import _buscar_cliente_planilha_impl

                            busca_result = _buscar_cliente_planilha_impl(
                                spreadsheet_id=spreadsheet_id,
                                range_name=range_name,
                                telefone=telefone_busca,
                                tenant_id=request.tenantId
                            )

                            # Se encontrou o cliente, adicionar ao contexto
                            if "✅ Cliente encontrado" in busca_result:
                                tools_context += f"\n\nINFORMAÇÕES DO CLIENTE:\n{busca_result}\n"
                                print(f"   ✅ Cliente encontrado e adicionado ao contexto")
                            else:
                                print(f"   ℹ️ Cliente não encontrado na base")

                        except Exception as e:
                            print(f"   ⚠️ Erro ao buscar cliente: {e}")

            # 1. FERRAMENTA DE CADASTRO EM GOOGLE SHEETS
            if 'cadastrar_cliente_planilha' in agent_tools:
                print(f"\n📊 Agente tem ferramenta de Google Sheets configurada")
                print(f"   Tool configs: {tool_configs}")

                # Palavras que indicam cadastro/registro (específicas!)
                cadastro_keywords = [
                    'quero me cadastr', 'fazer cadastro', 'cadastr',
                    'me registr', 'fazer registro', 'registr',
                    'meu nome é', 'me chamo'
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
                            from .tools import _cadastrar_cliente_planilha_impl
                            import re
                            from datetime import datetime

                            # Extrair informações da mensagem usando regex
                            message_text = request.message.lower()

                            # Extrair nome (procurar por "nome é/:" seguido de texto)
                            nome_match = re.search(r'(?:nome\s+(?:é|e)\s+|me\s+chamo\s+|sou\s+o?\s*)([A-Za-zÀ-ÿ\s]+?)(?:\s*,|\s+meu|\s+telefone|\s+email|\s+e-mail|$)', request.message, re.IGNORECASE)
                            nome = nome_match.group(1).strip() if nome_match else ""

                            # Extrair telefone (procurar por números com 10-11 dígitos)
                            telefone_match = re.search(r'(?:telefone|fone|cel|celular|whats|whatsapp)?\s*:?\s*(\d{10,11})', request.message, re.IGNORECASE)
                            telefone = telefone_match.group(1) if telefone_match else ""

                            # Extrair email
                            email_match = re.search(r'(?:email|e-mail|mail)?\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', request.message, re.IGNORECASE)
                            email = email_match.group(1) if email_match else ""

                            # Data/hora atual
                            data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            # Se não extraiu nome, usar mensagem completa
                            if not nome:
                                nome = request.message

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
                                observacoes=f"Cadastrado via treinamento - {team_data.get('name', 'Equipe')} em {data_cadastro}",
                                tenant_id=request.tenantId
                            )

                            tools_context += f"\n\nRESULTADO DO CADASTRO:\n{tool_result}\n"
                            print(f"   ✅ Cadastro executado com sucesso")

                        except Exception as e:
                            error_msg = f"Erro ao cadastrar: {str(e)}"
                            tools_context += f"\n\nERRO NO CADASTRO:\n{error_msg}\n"
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
                        from .tools import _coletar_info_agendamento_impl

                        # Coletar informações da mensagem
                        tool_result = _coletar_info_agendamento_impl(
                            nome_cliente="Cliente",  # TODO: Extrair do contexto
                            tipo_servico=request.message,
                            data_desejada="",    # TODO: Extrair da mensagem
                            horario_preferencia="", # TODO: Extrair da mensagem
                            telefone="",
                            observacoes=f"Solicitado via treinamento"
                        )

                        tools_context += f"\n\nINFORMAÇÕES DE AGENDAMENTO COLETADAS:\n{tool_result}\n"
                        print(f"   ✅ Informações de agendamento coletadas")

                    except Exception as e:
                        error_msg = f"Erro ao coletar agendamento: {str(e)}"
                        tools_context += f"\n\nERRO NO AGENDAMENTO:\n{error_msg}\n"
                        print(f"   ❌ Erro ao coletar agendamento: {e}")

            # Preparar contexto do conhecimento
            context_text = ""
            if knowledge_context:
                context_text = "Contexto relevante da base de conhecimento:\n"
                for i, ctx in enumerate(knowledge_context, 1):
                    source = ctx.get('metadata', {}).get('source', 'documento')
                    context_text += f"{i}. [{source.upper()}] {ctx['content']}\n"
                context_text += "\n"

            # Construir histórico da conversa
            conversation_context = ""
            if request.conversationHistory:
                conversation_context = "Histórico da conversa:\n"
                for msg in request.conversationHistory[-5:]:  # Últimas 5 mensagens
                    role = "Usuário" if msg['role'] == 'user' else "Assistente"
                    conversation_context += f"{role}: {msg['content']}\n"
                conversation_context += "\n"

            # PILAR 2: Obter treinamento do agente
            agent_training = agent_config.get('training', {})
            persona = agent_training.get('persona', '').strip()
            guardrails = agent_training.get('guardrails', {})
            do_rules = guardrails.get('do', [])
            dont_rules = guardrails.get('dont', [])

            # Construir seção de guardrails
            guardrails_text = ""
            if do_rules or dont_rules:
                guardrails_text = "\n" + "="*50 + "\n"
                guardrails_text += "REGRAS CRÍTICAS (SIGA RIGOROSAMENTE):\n"
                guardrails_text += "="*50 + "\n"

                if do_rules:
                    guardrails_text += "\n🔴 OBRIGATÓRIO - Você DEVE:\n"
                    for rule in do_rules:
                        if rule and rule.strip():
                            guardrails_text += f"  • {rule}\n"

                if dont_rules:
                    guardrails_text += "\n🚫 PROIBIDO - Você NÃO DEVE:\n"
                    for rule in dont_rules:
                        if rule and rule.strip():
                            guardrails_text += f"  • {rule}\n"

            # PILAR 2: Exemplos de Interação (Few-shot Learning)
            # Pegar exemplos específicos do agente primeiro, depois exemplos gerais da equipe
            agent_examples = agent_training.get('examples', [])
            team_examples = team_data.get('blueprint', {}).get('training', {}).get('examples', [])

            # Combinar exemplos: prioridade para exemplos do agente
            all_examples = agent_examples + team_examples

            examples_text = ""
            if all_examples:
                examples_text = "\n" + "="*50 + "\n"
                examples_text += "EXEMPLOS DE INTERAÇÕES (USE COMO REFERÊNCIA):\n"
                examples_text += "="*50 + "\n"
                examples_text += "\nEstes são exemplos de boas respostas que você deve seguir:\n\n"

                # Pegar os 5 exemplos mais recentes
                recent_examples = all_examples[-5:] if len(all_examples) > 5 else all_examples

                for i, example in enumerate(recent_examples, 1):
                    scenario = example.get('scenario', '')
                    good = example.get('good', '')
                    bad = example.get('bad', '')

                    if scenario and good:
                        examples_text += f"--- Exemplo {i} ---\n"
                        examples_text += f"Situação: {scenario}\n"

                        if bad:
                            examples_text += f"\n❌ RESPOSTA INADEQUADA (NÃO fazer assim):\n{bad}\n"

                        examples_text += f"\n✅ RESPOSTA IDEAL (fazer assim):\n{good}\n\n"

                print(f"📚 {len(recent_examples)} exemplo(s) de treinamento carregado(s) ({len(agent_examples)} específicos do agente, {len(team_examples)} gerais)")

            # Construir prompt específico para treinamento
            training_prompt = f"""
            Você está em uma sessão de TREINAMENTO INTERATIVO. O objetivo é fornecer a melhor resposta possível para que o usuário possa avaliar e melhorar sua performance.

            PAPEL: {agent_config['role']}
            OBJETIVO: {agent_config['goal']}
            CONTEXTO: {agent_config.get('backstory', '')}

            {"PERSONA:\n" + persona if persona else ""}

            PERSONALIDADE:
            - Tom: {agent_config.get('personality', {}).get('tone', 'friendly')}
            - Características: {', '.join(agent_config.get('personality', {}).get('traits', []))}
            - Instruções especiais: {agent_config.get('personality', {}).get('customInstructions', '')}
            {guardrails_text}
            {examples_text}
            {context_text}
            {tools_context}
            {conversation_context}

            MENSAGEM DO USUÁRIO: {request.message}

            INSTRUÇÕES IMPORTANTES:
            1. Responda como o agente especificado acima
            2. Use o contexto da base de conhecimento quando relevante
            3. Mantenha a personalidade e tom definidos
            4. SIGA RIGOROSAMENTE as regras de guardrails acima
            5. Se existirem exemplos acima, use-os como referência para o formato e estilo da resposta
            6. Se não souber algo, seja honesto mas útil
            7. Esta é uma sessão de treinamento - seja claro e didático
            8. Não mencione que está em treinamento para o usuário

            RESPOSTA:
            """

            # Log do prompt completo para debug
            print("\n" + "="*80)
            print("PROMPT DE TREINAMENTO ENVIADO AO MODELO:")
            print("="*80)
            print(training_prompt)
            print("="*80 + "\n")

            # Gerar resposta usando Vertex AI com retry para 429
            from vertexai.generative_models import GenerativeModel
            import os

            model_name = os.getenv("VERTEX_MODEL", "gemini-2.5-flash-lite")
            model = GenerativeModel(model_name)

            # Tentar até 3 vezes com backoff exponencial em caso de erro 429
            max_retries = 3
            retry_delay = 2  # segundos
            last_error = None

            for attempt in range(max_retries):
                try:
                    response = model.generate_content(training_prompt)
                    ai_response = response.text.strip()
                    break  # Sucesso, sair do loop
                except Exception as e:
                    error_msg = str(e)
                    last_error = e

                    # Se for erro 429 (rate limit), tentar novamente
                    if "429" in error_msg or "Resource exhausted" in error_msg or "quota" in error_msg.lower():
                        if attempt < max_retries - 1:  # Não é a última tentativa
                            wait_time = retry_delay * (2 ** attempt)  # Backoff exponencial: 2s, 4s, 8s
                            print(f"⚠️ Erro 429 (Rate Limit) - Aguardando {wait_time}s antes de tentar novamente (tentativa {attempt + 1}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"❌ Erro 429 persistiu após {max_retries} tentativas")
                            raise HTTPException(
                                status_code=429,
                                detail="Limite de requisições atingido. Por favor, aguarde alguns segundos e tente novamente."
                            )
                    else:
                        # Outro tipo de erro, não tentar novamente
                        raise e
            else:
                # Se chegou aqui, todas as tentativas falharam
                raise last_error if last_error else Exception("Falha ao gerar resposta")

            # Calcular tempo de resposta
            response_time = time.time() - start_time

            # Calcular score de confiança baseado na presença de contexto
            confidence_score = 0.8  # Base
            if knowledge_context:
                confidence_score += 0.1  # Boost por ter contexto
            if len(ai_response) > 50:
                confidence_score += 0.1  # Boost por resposta substantiva

            confidence_score = min(confidence_score, 1.0)

            return {
                "response": ai_response,
                "agentUsed": agent_to_use,
                "responseTime": round(response_time, 2),
                "confidenceScore": confidence_score,
                "knowledgeUsed": len(knowledge_context),
                "metadata": {
                    "agentConfig": {
                        "name": agent_config['name'],
                        "role": agent_config['role'],
                        "tone": agent_config.get('personality', {}).get('tone', 'friendly')
                    },
                    "contextSources": [ctx.get('metadata', {}).get('source', 'unknown') for ctx in knowledge_context]
                }
            }

        except Exception as e:
            print(f"Erro na geração de resposta para treinamento: {e}")
            raise Exception(f"Erro ao gerar resposta: {str(e)}")

    def _select_agent_for_training(self, team_data: Dict[str, Any], requested_agent: str = None, message: str = "") -> str:
        """Seleciona qual agente usar para o treinamento"""

        agents = team_data.get('agents', {})

        # Se agente específico foi solicitado, usar ele
        if requested_agent and requested_agent in agents:
            return requested_agent

        # Usar agente de entrada padrão se definido
        workflow = team_data.get('workflow', {})
        entry_point = workflow.get('entryPoint')

        if entry_point and entry_point in agents:
            return entry_point

        # Buscar agente de triagem
        for agent_key in agents.keys():
            if 'triagem' in agent_key.lower():
                return agent_key

        # Usar primeiro agente ativo
        for agent_key, agent_config in agents.items():
            if agent_config.get('isActive', True):
                return agent_key

        # Fallback: primeiro agente disponível
        return list(agents.keys())[0] if agents else 'geral'

    async def analyze_training_conversation(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analisa uma conversa de treinamento para insights"""
        try:
            analysis = {
                "totalMessages": len(conversation),
                "userMessages": 0,
                "aiMessages": 0,
                "corrections": 0,
                "avgMessageLength": 0,
                "topics": [],
                "sentiment": "neutral",
                "improvementAreas": []
            }

            total_length = 0
            user_messages = []
            ai_messages = []
            corrections = []

            for msg in conversation:
                total_length += len(msg.get('content', ''))

                if msg.get('role') == 'user':
                    analysis["userMessages"] += 1
                    if msg.get('type') != 'user_correction':
                        user_messages.append(msg['content'])
                elif msg.get('role') == 'assistant':
                    analysis["aiMessages"] += 1
                    ai_messages.append(msg['content'])
                elif msg.get('role') == 'correction':
                    analysis["corrections"] += 1
                    corrections.append(msg['content'])

            if len(conversation) > 0:
                analysis["avgMessageLength"] = total_length / len(conversation)

            # Análise de tópicos simples (palavras-chave frequentes)
            all_text = " ".join(user_messages + ai_messages).lower()
            words = all_text.split()
            word_freq = {}

            for word in words:
                if len(word) > 3:  # Ignorar palavras muito curtas
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Top 5 palavras mais frequentes como tópicos
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            analysis["topics"] = [word for word, freq in sorted_words[:5] if freq > 1]

            # Áreas de melhoria baseadas em correções
            if analysis["corrections"] > 0:
                correction_ratio = analysis["corrections"] / max(analysis["aiMessages"], 1)
                if correction_ratio > 0.3:
                    analysis["improvementAreas"].append("Alta taxa de correções - revisar treinamento")
                if analysis["avgMessageLength"] < 50:
                    analysis["improvementAreas"].append("Respostas muito curtas - incentivar mais detalhamento")

            return analysis

        except Exception as e:
            print(f"Erro na análise da conversa: {e}")
            return {"error": str(e)}

# Instância global do serviço
training_service = TrainingService()

@router.post("/generate-response")
async def generate_response(request: GenerateResponseRequest = Body(...)):
    """
    Gera resposta da IA para sessão de treinamento
    """
    try:
        if not request.message or len(request.message.strip()) < 1:
            raise HTTPException(status_code=400, detail="Mensagem é obrigatória")

        result = await training_service.generate_training_response(request)

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro ao gerar resposta de treinamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/analyze-conversation")
async def analyze_conversation(conversation: List[Dict[str, Any]] = Body(...)):
    """
    Analisa uma conversa de treinamento para insights
    """
    try:
        if not conversation:
            raise HTTPException(status_code=400, detail="Conversa é obrigatória")

        analysis = await training_service.analyze_training_conversation(conversation)

        return {
            "analysis": analysis,
            "insights": {
                "engagementLevel": "high" if analysis.get("totalMessages", 0) > 10 else "low",
                "trainingQuality": "good" if analysis.get("corrections", 0) < analysis.get("aiMessages", 0) * 0.2 else "needs_improvement",
                "conversationFlow": "natural" if analysis.get("avgMessageLength", 0) > 30 else "brief"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro ao analisar conversa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/suggest-improvements")
async def suggest_improvements(
    conversation: List[Dict[str, Any]] = Body(...),
    teamId: str = Body(...),
    tenantId: str = Body(...)
):
    """
    Sugere melhorias baseadas na sessão de treinamento
    """
    try:
        analysis = await training_service.analyze_training_conversation(conversation)

        suggestions = []

        # Sugestões baseadas na análise
        if analysis.get("corrections", 0) > analysis.get("aiMessages", 0) * 0.3:
            suggestions.append({
                "type": "training",
                "priority": "high",
                "title": "Alta taxa de correções",
                "description": "Considere adicionar mais contexto à base de conhecimento ou revisar as instruções dos agentes.",
                "action": "review_knowledge_base"
            })

        if analysis.get("avgMessageLength", 0) < 30:
            suggestions.append({
                "type": "agent_config",
                "priority": "medium",
                "title": "Respostas muito breves",
                "description": "Configure os agentes para fornecer respostas mais detalhadas e explicativas.",
                "action": "update_agent_instructions"
            })

        if len(analysis.get("topics", [])) < 2:
            suggestions.append({
                "type": "content",
                "priority": "low",
                "title": "Conversas pouco variadas",
                "description": "Teste diferentes tipos de perguntas para treinar a equipe em cenários diversos.",
                "action": "diversify_training"
            })

        # Sugestões específicas do domínio
        team_data = await training_service.get_team_blueprint(tenantId, teamId)
        industry = team_data.get('config', {}).get('industry', '')

        if industry == 'restaurante' and 'cardapio' not in ' '.join(analysis.get("topics", [])):
            suggestions.append({
                "type": "domain_specific",
                "priority": "medium",
                "title": "Treinamento específico para restaurante",
                "description": "Teste perguntas sobre cardápio, preços e pedidos para melhorar o atendimento.",
                "action": "test_menu_scenarios"
            })

        return {
            "suggestions": suggestions,
            "analysis": analysis,
            "nextSteps": [
                "Implemente as sugestões de alta prioridade primeiro",
                "Continue o treinamento com cenários variados",
                "Monitore as métricas de melhoria"
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro ao sugerir melhorias: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/templates/{industry}")
async def get_training_templates(industry: str):
    """
    Retorna templates de perguntas para treinamento por setor
    """
    try:
        templates = {
            "restaurante": [
                "Qual é o horário de funcionamento?",
                "Vocês fazem delivery?",
                "Qual é o prato mais pedido?",
                "Tem opções vegetarianas?",
                "Quanto custa o rodízio?",
                "Vocês aceitam reservas?",
                "Qual é a especialidade da casa?",
                "Tem estacionamento?"
            ],
            "imobiliaria": [
                "Quero alugar um apartamento de 2 quartos",
                "Qual é o preço do metro quadrado na região?",
                "Vocês fazem financiamento?",
                "Quero vender minha casa",
                "Tem imóveis com piscina?",
                "Qual é a documentação necessária?",
                "Posso agendar uma visita?",
                "Vocês trabalham com permuta?"
            ],
            "e-commerce": [
                "Qual é o prazo de entrega?",
                "Como faço para trocar um produto?",
                "Vocês aceitam cartão?",
                "Tem desconto para pagamento à vista?",
                "O produto tem garantia?",
                "Como acompanho meu pedido?",
                "Fazem entrega no mesmo dia?",
                "Qual é a política de devolução?"
            ],
            "saude": [
                "Quero agendar uma consulta",
                "Vocês atendem convênio?",
                "Qual é o horário de funcionamento?",
                "Tem médico de plantão?",
                "Preciso de exames urgentes",
                "Como remarco minha consulta?",
                "Vocês fazem teleconsulta?",
                "Qual é o valor da consulta particular?"
            ]
        }

        return {
            "templates": templates.get(industry, templates.get("geral", [])),
            "industry": industry,
            "total": len(templates.get(industry, []))
        }

    except Exception as e:
        print(f"Erro ao obter templates: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/save-correction")
async def save_correction(
    teamId: str = Body(...),
    tenantId: str = Body(...),
    scenario: str = Body(...),
    badResponse: str = Body(...),
    goodResponse: str = Body(...),
    agentId: str = Body(default=None)  # ID do agente específico (opcional)
):
    """
    Salva uma correção como exemplo de treinamento no agente específico ou na equipe
    """
    try:
        from firebase_admin import firestore
        db = firestore.client()

        # Buscar equipe
        team_ref = db.collection('crew_blueprints').document(teamId)
        team_doc = team_ref.get()

        if not team_doc.exists:
            raise HTTPException(status_code=404, detail="Equipe não encontrada")

        team_data = team_doc.to_dict()

        # Verificar se pertence ao tenant
        if team_data.get('tenantId') != tenantId:
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Adicionar novo exemplo
        new_example = {
            'scenario': scenario,
            'good': goodResponse,
            'bad': badResponse,
            'addedAt': datetime.now().isoformat(),
            'source': 'correction'  # Identificar que veio de correção
        }

        # Se um agente específico foi informado, salvar no agente
        if agentId and agentId in team_data.get('agents', {}):
            # Inicializar estrutura de treinamento do agente se não existir
            if 'agents' not in team_data:
                team_data['agents'] = {}
            if agentId not in team_data['agents']:
                team_data['agents'][agentId] = {}
            if 'training' not in team_data['agents'][agentId]:
                team_data['agents'][agentId]['training'] = {}
            if 'examples' not in team_data['agents'][agentId]['training']:
                team_data['agents'][agentId]['training']['examples'] = []

            team_data['agents'][agentId]['training']['examples'].append(new_example)

            # Atualizar agente no Firestore
            team_ref.update({
                f'agents.{agentId}.training.examples': team_data['agents'][agentId]['training']['examples']
            })

            print(f"✅ Correção salva como exemplo de treinamento no agente '{agentId}' da equipe {teamId}")

            return {
                "success": True,
                "message": f"Correção salva com sucesso no agente {team_data['agents'][agentId].get('name', agentId)}",
                "totalExamples": len(team_data['agents'][agentId]['training']['examples']),
                "agentId": agentId
            }

        # Caso contrário, salvar no nível da equipe (comportamento anterior)
        else:
            # Inicializar estrutura de treinamento da equipe se não existir
            if 'blueprint' not in team_data:
                team_data['blueprint'] = {}
            if 'training' not in team_data['blueprint']:
                team_data['blueprint']['training'] = {}
            if 'examples' not in team_data['blueprint']['training']:
                team_data['blueprint']['training']['examples'] = []

            team_data['blueprint']['training']['examples'].append(new_example)

            # Atualizar equipe no Firestore
            team_ref.update({
                'blueprint.training.examples': team_data['blueprint']['training']['examples']
            })

            print(f"✅ Correção salva como exemplo de treinamento geral na equipe {teamId}")

            return {
                "success": True,
                "message": "Correção salva com sucesso como exemplo de treinamento geral",
                "totalExamples": len(team_data['blueprint']['training']['examples'])
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro ao salvar correção: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")