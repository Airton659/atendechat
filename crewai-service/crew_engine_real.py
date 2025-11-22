# crew_engine_real.py - Motor CrewAI COMPLETO com logging no backend e Knowledge Base

from typing import Dict, Any, List, Optional
import time
import os
import requests
import unicodedata
from datetime import datetime, timedelta
import json
from crewai import Agent, Task, Crew, Process
from langchain_google_vertexai import ChatVertexAI
from simple_knowledge_service import get_knowledge_service
# from claude_validator import ClaudeValidator  # DESABILITADO

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

class RealCrewEngine:
    """Motor CrewAI completo com suporte a sequential, hierarchical, manager, logging e Knowledge Base"""

    def __init__(self):
        print("🚀 Inicializando RealCrewEngine...")
        self.llm = None
        self.knowledge_service = get_knowledge_service()
        # self.claude_validator = None  # DESABILITADO
        self._initialize_llm()
        # self._initialize_claude_validator()  # DESABILITADO
        self.tools = {}  # Tools desabilitadas

    def _initialize_claude_validator(self):
        """DESABILITADO - Validator não será usado"""
        print("⚠️  VALIDAÇÃO CLAUDE DESABILITADA - Sistema não valida respostas")
        """DESABILITADO - Validator não será usado"""
        pass

    def _initialize_llm(self):
        """Inicializa o modelo Vertex AI padrão"""
        try:
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            
            self.llm = ChatVertexAI(
                model="gemini-2.0-flash-lite",
                project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                location=os.getenv("GOOGLE_CLOUD_LOCATION"),
                temperature=0.7,
                max_output_tokens=1024,
            )
            print("✅ Vertex AI (gemini-2.0-flash-lite) inicializado com sucesso!")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar Vertex AI: {e}")
            self.llm = None

    def _save_log_to_backend(self, log_data: Dict[str, Any]):
        """Salva log no backend"""
        try:
            response = requests.post(
                f"{BACKEND_URL}/agent-logs",
                json=log_data,
                timeout=5
            )
            if response.status_code == 201:
                print(f"✅ Log salvo no backend (ID: {response.json().get('log', {}).get('id')})")
            else:
                print(f"⚠️ Erro ao salvar log: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Erro ao conectar com backend para salvar log: {e}")

    def _get_llm_for_team(self, team_config: Dict[str, Any]) -> ChatVertexAI:
        """Cria LLM customizado baseado nas configurações da equipe"""
        temperature = team_config.get('temperature', 0.7)
        model = "gemini-2.0-flash-lite"
        
        if team_config.get('processType') == 'hierarchical' and team_config.get('managerLLM'):
            model = team_config['managerLLM']
        
        try:
            llm = ChatVertexAI(
                model=model,
                project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                location=os.getenv("GOOGLE_CLOUD_LOCATION"),
                temperature=temperature,
                max_output_tokens=1024,
            )
            print(f"✅ LLM customizado criado: {model}, temperature={temperature}")
            return llm
        except Exception as e:
            print(f"⚠️ Erro ao criar LLM customizado: {e}, usando padrão")
            return self.llm

    def _normalize_text(self, text: str) -> str:
        """Remove acentos e normaliza texto para comparação"""
        # Normaliza para NFD (separa caracteres base de acentos)
        nfd = unicodedata.normalize('NFD', text)
        # Remove acentos (categoria 'Mn' = Nonspacing Mark)
        return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn').lower()

    def _get_agent_files(self, agent_id: int) -> List[Dict[str, Any]]:
        """Busca arquivos disponíveis para o agente enviar via WhatsApp"""
        try:
            response = requests.get(
                f"{BACKEND_URL}/agent-files/agent/{agent_id}",
                timeout=3
            )

            if response.status_code == 200:
                files = response.json()
                print(f"📎 {len(files)} arquivos disponíveis para agente {agent_id}")
                return files
            else:
                print(f"⚠️ Erro ao buscar arquivos: {response.status_code}")
                return []
        except Exception as e:
            print(f"⚠️ Erro ao buscar arquivos do agente: {e}")
            return []

    def _get_relevant_training_examples(self, agent_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Busca exemplos de treinamento relevantes para few-shot learning"""
        try:
            response = requests.get(
                f"{BACKEND_URL}/agent-training-examples/relevant/{agent_id}",
                params={"limit": limit},
                timeout=3
            )

            if response.status_code == 200:
                examples = response.json().get('examples', [])
                print(f"✅ {len(examples)} exemplos de treinamento carregados para agente {agent_id}")
                return examples
            else:
                print(f"⚠️ Erro ao buscar exemplos: {response.status_code}")
                return []
        except Exception as e:
            print(f"⚠️ Erro ao buscar exemplos de treinamento: {e}")
            return []

    def _format_training_examples_for_prompt(self, examples: List[Dict[str, Any]]) -> str:
        """Formata exemplos de treinamento para o prompt (Few-Shot Learning)

        Sistema de Prioridades:
        - Prioridade 10: CRÍTICO - Copiar EXATAMENTE
        - Prioridade 8-9: MUITO IMPORTANTE - Seguir DE PERTO
        - Prioridade 5-7: IMPORTANTE - APRENDER padrão e ADAPTAR
        - Prioridade 0-4: REFERÊNCIA - Inspiração geral
        """
        if not examples:
            return ""

        prompt_parts = []
        prompt_parts.append("\n\n**📚 EXEMPLOS DE RESPOSTAS APROVADAS (Few-Shot Learning):**")
        prompt_parts.append("\nEstes são exemplos reais de como você deve (ou não deve) responder:\n")

        for idx, example in enumerate(examples, 1):
            feedback_type = example.get('feedbackType', 'approved')
            user_msg = example.get('userMessage', '')
            agent_resp = example.get('agentResponse', '')
            corrected_resp = example.get('correctedResponse')
            notes = example.get('feedbackNotes', '')
            priority = example.get('priority', 5)  # Default 5 se não tiver

            prompt_parts.append(f"\n**Exemplo {idx}:**")
            prompt_parts.append(f"Cliente: {user_msg}")

            if feedback_type == "corrected":
                # Mostrar resposta errada e correta
                prompt_parts.append(f"❌ Resposta ERRADA: {agent_resp}")
                prompt_parts.append(f"✅ Resposta CORRETA: {corrected_resp}")
                if notes:
                    prompt_parts.append(f"💡 Motivo da correção: {notes}")
            elif feedback_type == "approved":
                # Exemplo de resposta boa
                prompt_parts.append(f"✅ Resposta APROVADA: {agent_resp}")
                if notes:
                    prompt_parts.append(f"💡 Nota: {notes}")

            # ADICIONAR INSTRUÇÃO BASEADA NA PRIORIDADE
            if priority >= 10:
                prompt_parts.append("🔴 **PRIORIDADE CRÍTICA (10)**: Copie EXATAMENTE este formato, estrutura e tom. Este é um padrão obrigatório.")
            elif priority >= 8:
                prompt_parts.append("🟠 **PRIORIDADE MUITO ALTA (8-9)**: Siga este padrão MUITO DE PERTO. Se houver outros exemplos com esta prioridade, COMBINE as regras de todos.")
            elif priority >= 5:
                prompt_parts.append("🟡 **PRIORIDADE ALTA (5-7)**: APRENDA o padrão (tom, objetividade, nível de detalhe) e ADAPTE ao contexto atual. NÃO copie literalmente.")
            else:
                prompt_parts.append("🟢 **PRIORIDADE BAIXA (0-4)**: Use como inspiração geral. Você tem liberdade para adaptar.")

        # INSTRUÇÕES GERAIS SOBRE COMO USAR OS EXEMPLOS
        prompt_parts.append("\n⚠️ INSTRUÇÕES IMPORTANTES - COMO USAR ESTES EXEMPLOS:")
        prompt_parts.append("")
        prompt_parts.append("🔴 **PRIORIDADE 10 (CRÍTICO)**:")
        prompt_parts.append("   - Copie EXATAMENTE a estrutura, tom e formato mostrado")
        prompt_parts.append("   - Estes são padrões obrigatórios que NÃO devem ser alterados")
        prompt_parts.append("   - Use para: políticas fixas, avisos legais, procedimentos obrigatórios")
        prompt_parts.append("")
        prompt_parts.append("🟠 **PRIORIDADE 8-9 (MUITO IMPORTANTE)**:")
        prompt_parts.append("   - Siga MUITO DE PERTO o padrão mostrado")
        prompt_parts.append("   - Mantenha a estrutura e tom")
        prompt_parts.append("   - Se houver múltiplos exemplos desta prioridade, COMBINE os conhecimentos")
        prompt_parts.append("")
        prompt_parts.append("🟡 **PRIORIDADE 5-7 (IMPORTANTE)** ← PADRÃO MAIS COMUM:")
        prompt_parts.append("   - APRENDA o padrão: tom de voz, nível de detalhe, objetividade, estrutura")
        prompt_parts.append("   - ADAPTE ao contexto atual da conversa")
        prompt_parts.append("   - NÃO copie palavra por palavra - seja natural e contextual")
        prompt_parts.append("   - Mantenha o ESTILO aprendido mas ajuste o CONTEÚDO ao contexto")
        prompt_parts.append("")
        prompt_parts.append("🟢 **PRIORIDADE 0-4 (REFERÊNCIA)**:")
        prompt_parts.append("   - Use apenas como inspiração geral")
        prompt_parts.append("   - Você tem liberdade para adaptar como achar melhor")
        prompt_parts.append("")
        prompt_parts.append("⚠️ **REGRA GERAL**: Preste atenção nos exemplos marcados como ❌ ERRADOS - NUNCA faça igual a eles!")

        return "\n".join(prompt_parts)

    def _select_agent_by_keywords(self, message: str, agents: List[Dict[str, Any]], default_agent_id: Optional[int] = None, conversation_history: List[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Seleciona o agente mais apropriado baseado nas palavras-chave.
        MANTÉM o agente atual se já houver contexto de conversa em andamento.
        """
        # 🔄 NOVO: Verificar se há um agente já atendendo esta conversa
        # REGRA: Se há histórico com assistant reply, SEMPRE manter o mesmo agente
        # A MENOS QUE usuário explicitamente mencione outro agente por nome
        if conversation_history and len(conversation_history) >= 2:
            # Verificar se há resposta do assistant no histórico
            has_assistant_reply = any(msg.get('role') == 'assistant' for msg in conversation_history)

            if has_assistant_reply:
                # Encontrar qual agente tem maior score com a mensagem atual
                message_normalized = self._normalize_text(message)
                best_agent = None
                best_score = 0

                for agent in agents:
                    if not agent.get('isActive', True):
                        continue

                    keywords = agent.get('keywords', [])
                    if not keywords:
                        continue

                    score = 0
                    for keyword in keywords:
                        keyword_normalized = self._normalize_text(keyword)
                        if keyword_normalized in message_normalized:
                            score += 1

                    if score > best_score:
                        best_score = score
                        best_agent = agent

                # Se encontrou algum agente (mesmo com score 0), retorná-lo
                # Isso mantém o agente atual a menos que não haja nenhum ativo
                if best_agent:
                    print(f"🔄 Mantendo agente por contexto: '{best_agent['name']}' (score: {best_score})")
                    return best_agent

                # Se não encontrou nenhum agente com keywords, pegar o primeiro ativo
                for agent in agents:
                    if agent.get('isActive', True):
                        print(f"🔄 Mantendo primeiro agente ativo por contexto: '{agent['name']}'")
                        return agent

        # Se não há contexto ou precisa trocar, usar seleção normal por keywords
        message_normalized = self._normalize_text(message)

        print("\n" + "="*60)
        print("🔍 MATCHING DE KEYWORDS - DEBUG DETALHADO")
        print("="*60)
        print(f"📝 Mensagem original: '{message}'")
        print(f"📝 Mensagem normalizada: '{message_normalized}'")
        print("="*60)

        agent_scores = []

        for agent in agents:
            agent_name = agent.get('name', 'Unknown')

            if not agent.get('isActive', True):
                print(f"⏭️  Agente '{agent_name}' está INATIVO, pulando...")
                continue

            score = 0
            keywords = agent.get('keywords', [])
            matched_keywords = []

            print(f"\n🤖 Testando agente: {agent_name}")
            print(f"   Keywords configuradas: {keywords}")

            if keywords:
                for keyword in keywords:
                    keyword_normalized = self._normalize_text(keyword)
                    print(f"   🔑 Keyword '{keyword}' → normalizada: '{keyword_normalized}'")

                    if keyword_normalized in message_normalized:
                        score += 1
                        matched_keywords.append(keyword)
                        print(f"      ✅ MATCH! '{keyword_normalized}' encontrado em '{message_normalized}'")
                    else:
                        print(f"      ❌ Não encontrado")
            else:
                print(f"   ⚠️  Agente sem keywords configuradas")

            if score > 0:
                agent_scores.append((agent, score))
                print(f"   📊 Score final: {score} (keywords matched: {matched_keywords})")
            else:
                print(f"   📊 Score final: 0 (nenhuma keyword matched)")

        print("\n" + "="*60)
        print("📊 RESULTADO DO MATCHING")
        print("="*60)

        if agent_scores:
            agent_scores.sort(key=lambda x: x[1], reverse=True)
            selected = agent_scores[0][0]
            print(f"✅ AGENTE SELECIONADO: {selected.get('name')} (score: {agent_scores[0][1]})")
            print(f"   Total de agentes com match: {len(agent_scores)}")
            if len(agent_scores) > 1:
                print(f"   Outros candidatos:")
                for agent, score in agent_scores[1:]:
                    print(f"      - {agent.get('name')}: score {score}")
            print("="*60 + "\n")
            return selected

        print("⚠️  NENHUMA KEYWORD MATCHED - Usando agente padrão")
        for agent in agents:
            if agent.get('isActive', True):
                print(f"✅ AGENTE PADRÃO SELECIONADO: {agent.get('name')}")
                print("="*60 + "\n")
                return agent

        print("❌ NENHUM AGENTE ATIVO ENCONTRADO")
        print("="*60 + "\n")
        return None

    def _build_full_prompt(self, message: str, agent_data: Dict[str, Any], conversation_history: List[Dict[str, Any]], knowledge_context: Optional[str] = None) -> tuple[str, List[Dict[str, Any]]]:
        """Constrói o prompt completo com TODAS as configurações do agente + Knowledge Base + Tool Context

        Returns:
            tuple: (prompt_completo, training_examples_usados)
        """

        name = agent_data.get('name', 'Agente')
        role = agent_data.get('function', 'Assistente de atendimento')
        objective = agent_data.get('objetivo', 'Ajudar o cliente')
        backstory = agent_data.get('backstory', '')
        custom_instructions = agent_data.get('customInstructions', '')
        persona = agent_data.get('persona', '')
        do_list = agent_data.get('doList', [])
        dont_list = agent_data.get('dontList', [])

        print("\n" + "="*60)
        print("📋 CONFIGURAÇÃO DO AGENTE:")
        print("="*60)
        print(f"👤 Nome: {name}")
        print(f"💼 Função: {role}")
        print(f"🎯 Objetivo: {objective}")
        print(f"✅ DO List ({len(do_list)} itens): {do_list}")
        print(f"❌ DONT List ({len(dont_list)} itens): {dont_list}")
        if knowledge_context:
            print(f"📚 Knowledge Base: SIM ({len(knowledge_context)} chars)")
        print("="*60 + "\n")

        # Buscar exemplos de treinamento (Few-Shot Learning)
        training_examples = []
        agent_id = agent_data.get('id')
        if agent_id:
            training_examples = self._get_relevant_training_examples(agent_id, limit=5)
            if training_examples:
                print(f"🎓 {len(training_examples)} exemplos de treinamento serão usados para Few-Shot Learning")
                for idx, ex in enumerate(training_examples, 1):
                    print(f"   Exemplo {idx}: {ex.get('feedbackType')} - Priority {ex.get('priority')}")

        prompt_parts = []
        prompt_parts.append(f"Você é {name}, {role}.")
        prompt_parts.append(f"\nSeu objetivo é: {objective}")

        # ADICIONAR HISTÓRICO LOGO APÓS OBJETIVO (ANTES DAS INSTRUÇÕES)
        # Isso garante que o LLM veja o contexto da conversa ANTES das regras
        if conversation_history:
            print(f"\n💬 HISTÓRICO DA CONVERSA: {len(conversation_history)} mensagens")
            for idx, msg in enumerate(conversation_history, 1):
                role_label = msg.get('role', 'Cliente')
                body = msg.get('body', '')
                print(f"   [{idx}] {role_label}: {body[:80]}{'...' if len(body) > 80 else ''}")

            prompt_parts.append("\n\n**📜 HISTÓRICO DA CONVERSA ATÉ AGORA:**")
            for msg in conversation_history:
                role_label = msg.get('role', 'Cliente')
                prompt_parts.append(f"{role_label}: {msg.get('body', '')}")
            prompt_parts.append("\n---\n")

        if backstory:
            prompt_parts.append(f"\n\n**SUA HISTÓRIA E CONTEXTO:**\n{backstory}")

        if persona:
            prompt_parts.append(f"\n\n**SUA PERSONA:**\n{persona}")

        if custom_instructions:
            prompt_parts.append(f"\n\n**INSTRUÇÕES ESPECIAIS:**\n{custom_instructions}")

        # ADICIONAR KNOWLEDGE BASE LOGO APÓS INSTRUÇÕES
        if knowledge_context:
            prompt_parts.append(f"\n\n**📚 BASE DE CONHECIMENTO - INFORMAÇÕES OFICIAIS:**")
            prompt_parts.append(knowledge_context)
            prompt_parts.append("\n🔥 REGRA CRÍTICA - PRIORIDADE DA BASE DE CONHECIMENTO:")
            prompt_parts.append("1. SE a pergunta do cliente puder ser respondida com informações da Base de Conhecimento acima, você DEVE usar essas informações")
            prompt_parts.append("2. NÃO fale sobre você mesmo (suas funções/responsabilidades como agente) se a pergunta for sobre algo que está na Base de Conhecimento")
            prompt_parts.append("3. A Base de Conhecimento contém informações OFICIAIS e AUTORITATIVAS - sempre priorize-a")
            prompt_parts.append("4. NÃO invente, NÃO assuma, NÃO adicione informações que não estejam explicitamente na base")
            prompt_parts.append("5. Se NÃO houver informação relevante na base, aí sim responda normalmente com base na sua função")
            prompt_parts.append("6. NUNCA mencione recursos ou funcionalidades que você NÃO possui (ex: enviar imagens, fotos, vídeos, links)")
            prompt_parts.append("7. Você APENAS pode enviar arquivos usando [SEND_FILE:id] se o arquivo estiver listado na seção 'ARQUIVOS DISPONÍVEIS'")
            prompt_parts.append("8. NÃO use tags ou códigos falsos como [SEND_IMAGE:...], [SEND_PHOTO:...] - eles NÃO funcionam")
            prompt_parts.append("")
            prompt_parts.append("🎯 REGRA CRÍTICA - CONTEXTO CONVERSACIONAL E PRONOMES:")
            prompt_parts.append("6. MANTENHA O CONTEXTO: Se o cliente perguntou sobre uma pessoa/entidade específica (ex: 'Dr. Ricardo', 'produto X', 'serviço Y'), guarde essa informação")
            prompt_parts.append("7. RESOLVA PRONOMES: Quando o cliente usar pronomes como 'ele', 'ela', 'isso', 'esse', 'essa', 'aquele', refira-se à ÚLTIMA entidade mencionada na conversa")
            prompt_parts.append("8. FILTRE INFORMAÇÕES: Se o cliente perguntar 'quais exames ELE realiza?' e estava falando do Dr. Ricardo, responda APENAS sobre o Dr. Ricardo, NÃO liste todos os médicos")
            prompt_parts.append("9. SEJA CONTEXTUAL: Analise o histórico da conversa para entender sobre QUEM/O QUE o cliente está perguntando")
            prompt_parts.append("10. EXEMPLO PRÁTICO:")
            prompt_parts.append("    Cliente: 'Que dia o Dr. Ricardo atende?'")
            prompt_parts.append("    Você: 'Dr. Ricardo atende terças-feiras'")
            prompt_parts.append("    Cliente: 'Quais exames ele realiza?' ← 'ele' = Dr. Ricardo")
            prompt_parts.append("    Você: 'Dr. Ricardo realiza EEG e Ressonância Magnética' ← APENAS Dr. Ricardo, NÃO todos os médicos!\n")

        # ADICIONAR EXEMPLOS DE TREINAMENTO (Few-Shot Learning)
        if training_examples:
            examples_formatted = self._format_training_examples_for_prompt(training_examples)
            prompt_parts.append(examples_formatted)

        # ADICIONAR ARQUIVOS DISPONÍVEIS PARA ENVIO
        if agent_id:
            agent_files = self._get_agent_files(agent_id)
            if agent_files:
                prompt_parts.append("\n\n**📎 ARQUIVOS DISPONÍVEIS PARA ENVIO:**")
                prompt_parts.append("Você tem os seguintes arquivos que pode enviar ao cliente quando solicitado:")
                for file in agent_files:
                    file_desc = file.get('description') or file.get('originalName', 'Arquivo')
                    file_type = file.get('fileType', 'arquivo').upper()
                    prompt_parts.append(f"- [SEND_FILE:{file.get('id')}] {file_desc} ({file_type})")
                prompt_parts.append("\n**COMO ENVIAR ARQUIVOS:**")
                prompt_parts.append("- Quando o cliente pedir um arquivo (cardápio, tabela de preços, documento, etc), inclua o código [SEND_FILE:id] na sua resposta")
                prompt_parts.append("- Exemplo: 'Claro! Vou te enviar o cardápio agora. [SEND_FILE:1]'")
                prompt_parts.append("- O arquivo será enviado automaticamente pelo sistema")
                prompt_parts.append("- SEMPRE responda com uma frase natural ANTES do código [SEND_FILE:id]")
                prompt_parts.append("- Você pode enviar múltiplos arquivos se necessário: [SEND_FILE:1] [SEND_FILE:2]")

        if do_list:
            prompt_parts.append("\n\n**VOCÊ DEVE:**")
            for item in do_list:
                prompt_parts.append(f"- {item}")

        if dont_list:
            prompt_parts.append("\n\n**⛔ VOCÊ NÃO DEVE (PROIBIDO - NUNCA FAÇA ISSO):**")
            for item in dont_list:
                prompt_parts.append(f"❌ {item}")
            prompt_parts.append("\n⚠️ ATENÇÃO: As regras acima são OBRIGATÓRIAS e DEVEM ser seguidas em TODAS as respostas, sem exceção.")

        prompt_parts.append(f"\n\n**MENSAGEM ATUAL DO CLIENTE:**\n{message}")

        prompt_parts.append("\n\n**SUA RESPOSTA:**")

        full_prompt = "\n".join(prompt_parts)

        print("PROMPT COMPLETO:")
        print(full_prompt[:2000])

        return full_prompt, training_examples

    def _validate_response_against_config(self, response: str, agent_data: Dict[str, Any], llm: ChatVertexAI, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Validacao 100% generica usando Claude Haiku (primário) ou Gemini Free (fallback)
        Claude: 95%+ acurácia, $0.0002-0.0006 por validação
        Fallback: Gemini Free se Claude indisponível ou limite diário atingido
        """
        if conversation_history is None:
            conversation_history = []

        # Tentar usar Claude Validator primeiro
        if self.claude_validator:
            try:
                result = self.claude_validator.validate_response(response, agent_data, conversation_history)

                # Se usou Claude com sucesso
                if result["method"] == "claude":
                    return result["corrected_response"]

                # Se caiu em fallback (limite diário, erro, etc), usar Gemini abaixo
                print(f"⚠️  Claude fallback: {result['reason']}")
                print("⚠️  Usando validação Gemini Free...")

            except Exception as e:
                print(f"❌ Erro ao usar Claude Validator: {e}")
                print("⚠️  Usando validação Gemini Free (fallback)...")

        # Fallback: Validação com Gemini Free (método original)
        dont_list = agent_data.get("dontList", [])
        do_list = agent_data.get("doList", [])
        persona = agent_data.get("persona", "")
        custom_instructions = agent_data.get("customInstructions", "")

        # Se nao tem nenhuma regra, nao precisa validar
        if not dont_list and not do_list and not persona and not custom_instructions:
            return response

        print("\n" + "="*60)
        print("VALIDACAO GEMINI FREE (FALLBACK)")
        print("="*60 + "\n")

        # Construir prompt de validacao
        validation_parts = []
        validation_parts.append("Voce e um validador. Analise se a resposta respeita as regras:\n\n")
        validation_parts.append(f"RESPOSTA:\n{response}\n\n")
        validation_parts.append("REGRAS:\n")

        if do_list:
            validation_parts.append("DO List: " + ", ".join(do_list) + "\n")
        if dont_list:
            validation_parts.append("DONT List: " + ", ".join(dont_list) + "\n")
        if persona:
            validation_parts.append(f"Persona: {persona}\n")
        if custom_instructions:
            validation_parts.append(f"Instrucoes: {custom_instructions}\n")

        validation_parts.append("\nRESPONDA: OK ou VIOLACAO: [explicacao]")
        validation_prompt = "".join(validation_parts)

        try:
            from langchain_core.messages import HumanMessage
            validation_response = llm.invoke([HumanMessage(content=validation_prompt)])
            validation_text = validation_response.content.strip()

            print(f"Resultado: {validation_text}\n")

            if "VIOLACAO" in validation_text.upper():
                print("Violacao detectada! Pedindo reescrita...\n")

                rewrite_parts = []
                rewrite_parts.append(f"A resposta abaixo violou regras: {validation_text}\n\n")
                rewrite_parts.append(f"RESPOSTA ORIGINAL:\n{response}\n\n")
                rewrite_parts.append("REESCREVA respeitando:\n")

                if do_list:
                    rewrite_parts.append("DO: " + ", ".join(do_list) + "\n")
                if dont_list:
                    rewrite_parts.append("DONT: " + ", ".join(dont_list) + "\n")
                if persona:
                    rewrite_parts.append(f"Persona: {persona}\n")
                if custom_instructions:
                    rewrite_parts.append(f"Instrucoes: {custom_instructions}\n")

                rewrite_parts.append("\nResposta corrigida:")
                rewrite_prompt = "".join(rewrite_parts)
                rewrite_response = llm.invoke([HumanMessage(content=rewrite_prompt)])
                corrected = rewrite_response.content.strip()

                print(f"Resposta corrigida:\n{corrected}\n" + "="*60 + "\n")
                return corrected
            else:
                print("OK - regras respeitadas\n" + "="*60 + "\n")
                return response

        except Exception as e:
            print(f"Erro na validacao Gemini: {e}")
            return response


    def _create_crewai_agent(self, agent_data: Dict[str, Any], llm: ChatVertexAI, is_manager: bool = False) -> Agent:
        """
        Converte configuração de agente para objeto CrewAI Agent
        
        Args:
            agent_data: Dados do agente (name, function, objective, backstory, etc)
            llm: Modelo LLM a ser usado (Vertex AI)
            is_manager: Se True, adiciona capacidade de delegação
        """
        # Construir objetivo completo com instruções customizadas
        full_goal = agent_data.get('objective', '')
        
        if agent_data.get('customInstructions'):
            full_goal += f"\n\nInstruções especiais: {agent_data['customInstructions']}"
        
        # Adicionar DO List e DON'T List ao backstory
        backstory = agent_data.get('backstory', '')
        
        do_list = agent_data.get('doList', [])
        if do_list:
            backstory += "\n\nCoisas que VOCÊ DEVE fazer:"
            for item in do_list:
                if item.strip():
                    backstory += f"\n- {item}"
        
        dont_list = agent_data.get('dontList', [])
        if dont_list:
            backstory += "\n\nCoisas que você NÃO DEVE fazer (PROIBIDO):"
            for item in dont_list:
                if item.strip():
                    backstory += f"\n- {item}"
        
        if agent_data.get('persona'):
            backstory += f"\n\nPersona: {agent_data['persona']}"
        
        # IMPORTANTE: Remover OPENAI_API_KEY para forçar uso do Vertex AI
        import os
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        # Criar agente CrewAI com LLM Vertex AI explícito
        # IMPORTANTE: memory=False para evitar uso de OpenAI embeddings
        agent = Agent(
            role=agent_data.get('function', 'Assistente'),
            goal=full_goal,
            backstory=backstory,
            llm=llm,  # Vertex AI (Gemini) passado explicitamente
            verbose=True,
            allow_delegation=is_manager,  # Apenas manager pode delegar
            memory=False,  # Desabilita memória interna do CrewAI (usamos nosso próprio histórico)
            embedder=None  # Não usar embedder (evita OpenAI)
        )
        
        # Armazenar metadados adicionais
        agent._original_data = agent_data
        
        print(f"   ✅ Agente criado com LLM: {llm.model_name if hasattr(llm, 'model_name') else 'Vertex AI'}")
        
        return agent

    def _run_manual_hierarchical_delegation(
        self,
        message: str,
        manager_agent_data: Dict[str, Any],
        specialist_agents_data: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]],
        llm: ChatVertexAI,
        knowledge_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delegação hierárquica MANUAL usando apenas Vertex AI (sem CrewAI framework)
        
        Fluxo:
        1. Manager analisa mensagem e decide qual especialista usar
        2. Especialista selecionado processa a mensagem
        3. Retorna resposta do especialista
        
        Args:
            message: Mensagem do cliente
            manager_agent_data: Dados do Manager Agent
            specialist_agents_data: Lista de especialistas disponíveis
            conversation_history: Histórico da conversa
            llm: Modelo LLM Vertex AI
            knowledge_context: Contexto da KB (se houver)
        
        Returns:
            Dict com success, response, agent_used, delegation_info
        """
        try:
            print("\n" + "="*60)
            print("🎯 DELEGAÇÃO HIERÁRQUICA MANUAL - Vertex AI Only")
            print("="*60)
            print(f"Manager: {manager_agent_data.get('name')}")
            print(f"Especialistas disponíveis: {len(specialist_agents_data)}")
            
            # 1. Preparar contexto dos especialistas para o Manager
            specialists_info = []
            for idx, spec in enumerate(specialist_agents_data, 1):
                spec_name = spec.get('name', 'Unknown')
                spec_function = spec.get('function', 'Unknown')
                spec_keywords = spec.get('keywords', [])
                spec_objective = spec.get('objective', '')[:150]
                
                specialists_info.append(
                    f"{idx}. {spec_name} ({spec_function})\n"
                    f"   Especialidades: {', '.join(spec_keywords)}\n"
                    f"   Objetivo: {spec_objective}..."
                )
                print(f"   {idx}. {spec_name} - Keywords: {spec_keywords}")
            
            specialists_context = "\n".join(specialists_info)
            
            # 2. Manager decide qual especialista usar (via Vertex AI)
            print("\n🤔 Manager analisando mensagem para decidir delegação...")
            
            delegation_prompt = f"""Você é {manager_agent_data.get('name')}, {manager_agent_data.get('function')}.

ESPECIALISTAS DISPONÍVEIS:
{specialists_context}

MENSAGEM DO CLIENTE:
{message}

SUA TAREFA:
Analise a mensagem do cliente e decida qual especialista deve responder.

RESPONDA APENAS COM O NÚMERO do especialista (1, 2, 3, etc.) OU "0" se você mesmo deve responder.

🔥 REGRAS DE DELEGAÇÃO:

1. VOCÊ (Manager) SÓ responde (0) se for:
   - Saudação genérica SEM pedido específico: "oi", "olá", "bom dia", "boa tarde"

2. SEMPRE DELEGUE (1, 2, 3...) para o especialista apropriado quando o cliente:
   - Fizer uma pergunta específica
   - Pedir informações detalhadas
   - Solicitar algum serviço/ação
   - Mencionar palavras-chave que combinem com as especialidades dos especialistas

3. ANALISE O CONTEXTO DA PERGUNTA, NÃO OS NOMES:
   - ⚠️ IMPORTANTE: Se a mensagem mencionar o nome de um especialista (ex: "Ricardo", "Carlos"),
     NÃO delegue automaticamente para ele só por causa do nome
   - Analise o ASSUNTO/CONTEXTO da pergunta
   - Compare o ASSUNTO com as especialidades (palavras-chave) de cada especialista
   - Escolha o especialista cujas ESPECIALIDADES mais combinam com o ASSUNTO da pergunta
   - Exemplo: "Qual especialidade do Ricardo?" → assunto é "especialidade/informação" → delegar para especialista de SUPORTE/DÚVIDAS, NÃO para Ricardo

4. PRIORIDADE DAS PALAVRAS-CHAVE:
   - Identifique o assunto principal da pergunta
   - Compare com as especialidades listadas acima
   - Se houver dúvida entre 2 especialistas, escolha o mais específico

RESPONDA APENAS O NÚMERO (0, 1, 2, 3...), NADA MAIS."""

            from langchain_core.messages import HumanMessage
            delegation_response = llm.invoke([HumanMessage(content=delegation_prompt)])
            delegation_choice = delegation_response.content.strip()
            
            print(f"✅ Manager decidiu: '{delegation_choice}'")
            
            # 3. Selecionar agente baseado na decisão
            try:
                choice_num = int(delegation_choice)
                
                if choice_num == 0:
                    # Manager responde diretamente
                    selected_agent_data = manager_agent_data
                    print(f"✅ Manager vai responder diretamente")
                elif 1 <= choice_num <= len(specialist_agents_data):
                    # Delegar para especialista
                    selected_agent_data = specialist_agents_data[choice_num - 1]
                    print(f"✅ Delegando para: {selected_agent_data.get('name')}")
                else:
                    # Número inválido, usar Manager
                    print(f"⚠️  Número inválido ({choice_num}), Manager responde")
                    selected_agent_data = manager_agent_data
            except ValueError:
                # Resposta não foi um número, usar Manager
                print(f"⚠️  Resposta não numérica, Manager responde")
                selected_agent_data = manager_agent_data
            
            # 4. Especialista selecionado gera a resposta
            print(f"\n🚀 Gerando resposta com {selected_agent_data.get('name')}...")

            response_text, prompt_used, training_examples_used = self._create_simple_response(
                message,
                selected_agent_data,
                conversation_history,
                llm,
                knowledge_context
            )

            print(f"✅ Resposta gerada por {selected_agent_data.get('name')}")
            
            return {
                "success": True,
                "response": response_text,
                "agent_used": selected_agent_data.get('name'),
                "delegation_info": {
                    "manager": manager_agent_data.get('name'),
                    "manager_choice": delegation_choice,
                    "delegated_to": selected_agent_data.get('name'),
                    "specialists_available": len(specialist_agents_data),
                    "method": "manual_vertex_ai"
                }
            }
            
        except Exception as e:
            print(f"❌ Erro na delegação manual: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: Manager responde diretamente
            print("⚠️  Fallback: Manager responde diretamente...")
            fallback_response, _, _ = self._create_simple_response(
                message,
                manager_agent_data,
                conversation_history,
                llm,
                knowledge_context
            )
            
            return {
                "success": True,
                "response": fallback_response,
                "agent_used": manager_agent_data.get('name'),
                "delegation_info": {
                    "manager": manager_agent_data.get('name'),
                    "error": str(e),
                    "fallback": True
                }
            }


    def _create_simple_response(self, message: str, agent_data: Dict[str, Any], conversation_history: List[Dict[str, Any]], llm: ChatVertexAI, knowledge_context: Optional[str] = None) -> tuple[str, str, List[Dict[str, Any]]]:
        """Gera resposta usando Vertex AI diretamente

        Returns:
            tuple: (validated_response, prompt_completo, training_examples_usados)
        """
        try:
            prompt, training_examples = self._build_full_prompt(message, agent_data, conversation_history, knowledge_context)

            from langchain_core.messages import HumanMessage
            response = llm.invoke([HumanMessage(content=prompt)])

            print("\n" + "="*60)
            print("📥 RESPOSTA RECEBIDA:")
            print("="*60)
            print(response.content)
            print("="*60 + "\n")

            # TEMPORARIAMENTE DESABILITADO - DEBUGANDO
            # Aplicar validacao generica (100% baseada na config da equipe)
            # validated_response = self._validate_response_against_config(response.content, agent_data, llm, conversation_history)
            # return validated_response, prompt, training_examples

            print("⚠️ VALIDAÇÃO TEMPORARIAMENTE DESABILITADA - DEBUGANDO")
            return response.content, prompt, training_examples

        except Exception as e:
            print(f"❌ Erro ao gerar resposta: {e}")
            import traceback
            traceback.print_exc()
            return "Olá! Como posso ajudá-lo hoje?", "", []

    async def run_playground_crew(
        self,
        team_definition: Dict[str, Any],
        task: str,
        company_id: int,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executa uma Crew TEMPORÁRIA no modo Playground (não salva logs no banco).
        Usado para testar e refinar prompts antes de salvar alterações.

        Args:
            conversation_history: Lista de mensagens anteriores [{"role": "user"|"assistant", "content": "..."}]
        """
        if conversation_history is None:
            conversation_history = []
        print("\n" + "="*60)
        print("🧪 RUN PLAYGROUND CREW - Executando equipe temporária")
        print("="*60)

        # Capturar logs verbosos
        import io
        import sys
        log_capture = io.StringIO()
        original_stdout = sys.stdout

        success = False
        response_text = ""
        error_message = None
        agent_used = None
        execution_logs = ""

        try:
            # Extrair dados da definição temporária
            team_name = team_definition.get('name', 'Equipe Temporária')
            agents_data = team_definition.get('agents', [])
            process_type = team_definition.get('processType', 'sequential')
            temperature = team_definition.get('temperature', 0.7)

            print(f"Team: {team_name}")
            print(f"Process Type: {process_type}")
            print(f"Temperature: {temperature}")
            print(f"Agents: {len(agents_data)}")
            print(f"Task: {task}")
            print("="*60 + "\n")

            if not agents_data:
                raise ValueError("A equipe precisa ter pelo menos 1 agente")

            if not self.llm:
                raise ValueError("LLM não inicializado")

            # Criar LLM customizado
            custom_llm = self._get_llm_for_team({
                'temperature': temperature,
                'processType': process_type,
                'managerLLM': team_definition.get('managerLLM')
            })

            # Converter histórico para o formato esperado ANTES de usar
            # IMPORTANTE: Usar "role" (não "sender") para que _build_full_prompt pegue corretamente
            formatted_history = []
            if conversation_history:
                for msg in conversation_history:
                    if msg.get('role') == 'user':
                        formatted_history.append({"role": "Cliente", "body": msg.get('content', '')})
                    elif msg.get('role') == 'assistant':
                        formatted_history.append({"role": "Você", "body": msg.get('content', '')})

            # Redirecionar stdout para log_capture ANTES de processar
            sys.stdout = log_capture

            # DECISÃO: Hierarchical ou Sequential
            if process_type == 'hierarchical':
                # MODO HIERARCHICAL: Usar delegação manual
                manager_agent_id = team_definition.get('managerAgentId')
                
                print(f"🔍 DEBUG - team_definition keys: {team_definition.keys()}")
                print(f"🔍 DEBUG - managerAgentId value: {manager_agent_id}")
                print(f"🔍 DEBUG - managerAgentId type: {type(manager_agent_id)}")
                
                if not manager_agent_id:
                    print(f"❌ DEBUG - team_definition completo: {team_definition}")
                    raise ValueError("Modo hierarchical requer managerAgentId configurado")
                
                manager_agent_data = next((a for a in agents_data if a.get('id') == manager_agent_id), None)
                if not manager_agent_data:
                    raise ValueError(f"Manager Agent {manager_agent_id} não encontrado")

                specialist_agents_data = [a for a in agents_data if a.get('id') != manager_agent_id and a.get('isActive', True)]

                # BUSCAR KB ANTES da delegação (para todos os agentes que tem KB configurada)
                # Juntar todas as KBs de todos os agentes (manager + specialists)
                all_kb_ids = set()
                for agent in [manager_agent_data] + specialist_agents_data:
                    if agent.get('useKnowledgeBase'):
                        kb_ids = agent.get('knowledgeBaseIds', [])
                        all_kb_ids.update(kb_ids)

                knowledge_context = None
                if all_kb_ids:
                    print(f"📚 Buscando Knowledge Base ANTES da delegação...")
                    try:
                        team_id_for_kb = str(team_definition.get('id', 'playground'))
                        kb_chunks = self.knowledge_service.search_knowledge(
                            team_id=team_id_for_kb,
                            document_ids=list(all_kb_ids),
                            query=task,
                            top_k=20
                        )

                        if kb_chunks:
                            knowledge_context = "\n\n".join([
                                f"📄 {chunk['metadata'].get('filename', 'Documento')}: {chunk['content']}"
                                for chunk in kb_chunks
                            ])
                            print(f"✅ {len(kb_chunks)} chunks encontrados ANTES da delegação")
                    except Exception as e:
                        print(f"⚠️ Erro ao buscar KB: {e}")

                # Chamar delegação hierárquica manual COM knowledge_context
                delegation_result = self._run_manual_hierarchical_delegation(
                    message=task,
                    manager_agent_data=manager_agent_data,
                    specialist_agents_data=specialist_agents_data,
                    conversation_history=formatted_history,
                    llm=custom_llm,
                    knowledge_context=knowledge_context
                )

                response_text = delegation_result.get('response', '')
                agent_used = delegation_result.get('agent_used', 'Unknown')

                # Buscar o agente que realmente respondeu (pode ser o manager ou um especialista)
                delegated_agent_name = delegation_result.get('delegation_info', {}).get('delegated_to')
                selected_agent_data = next((a for a in agents_data if a.get('name') == delegated_agent_name), manager_agent_data)
            else:
                # MODO SEQUENTIAL: Usar keyword matching com manutenção de contexto
                selected_agent_data = self._select_agent_by_keywords(
                    task,
                    agents_data,
                    team_definition.get("defaultAgentId"),
                    conversation_history=formatted_history
                )
                if not selected_agent_data:
                    selected_agent_data = next((a for a in agents_data if a.get('isActive', True)), agents_data[0])

                agent_used = selected_agent_data.get('name', 'Agente')

            print(f"✅ Agente selecionado: {agent_used}")

            # Buscar Knowledge Base APENAS para modo SEQUENTIAL
            # (no modo hierarchical já foi buscado antes da delegação)
            if process_type != 'hierarchical':
                knowledge_context = None
                if selected_agent_data.get('useKnowledgeBase'):
                    kb_ids = selected_agent_data.get('knowledgeBaseIds', [])
                    if kb_ids:
                        print(f"📚 Buscando Knowledge Base...")
                        try:
                            # Usar teamId da definição se existir
                            team_id_for_kb = str(team_definition.get('id', 'playground'))
                            kb_chunks = self.knowledge_service.search_knowledge(
                                team_id=team_id_for_kb,
                                document_ids=kb_ids,
                                query=task,
                                top_k=20
                            )

                            if kb_chunks:
                                knowledge_context = "\n\n".join([
                                    f"📄 {chunk['metadata'].get('filename', 'Documento')}: {chunk['content']}"
                                    for chunk in kb_chunks
                                ])
                                print(f"✅ {len(kb_chunks)} chunks encontrados")
                        except Exception as e:
                            print(f"⚠️ Erro ao buscar KB (não crítico no playground): {e}")

            # Gerar resposta
            start_time = time.time()

            # Variáveis para prompt e exemplos
            prompt_used = ""
            training_examples_used = []

            # Só gerar resposta se NÃO for hierarchical (que já gerou)
            if process_type != 'hierarchical':
                response_text, prompt_used, training_examples_used = self._create_simple_response(
                    task,
                    selected_agent_data,
                    formatted_history,  # Histórico de conversação para contexto
                    custom_llm,
                    knowledge_context
                )
            elapsed_time = time.time() - start_time

            # Restaurar stdout
            sys.stdout = original_stdout
            execution_logs = log_capture.getvalue()

            success = True

            print(f"✅ Resposta gerada em {elapsed_time:.2f}s")
            print(f"📝 Logs capturados: {len(execution_logs)} caracteres")

            # Debug: verificar agent_id
            agent_id_value = selected_agent_data.get('id')
            print(f"🔍 DEBUG AGENT_ID - selected_agent_data.keys(): {selected_agent_data.keys()}")
            print(f"🔍 DEBUG AGENT_ID - agent_id value: {agent_id_value}")
            print(f"🔍 DEBUG AGENT_ID - agent_used: {agent_used}")

            return {
                "success": True,
                "final_output": response_text,
                "execution_logs": execution_logs,
                "agent_used": agent_used,
                "agent_id": agent_id_value,
                "config_used": {
                    "process_type": process_type,
                    "temperature": temperature,
                    "agent_name": agent_used
                },
                "processing_time": round(elapsed_time, 2),
                "prompt_used": prompt_used,
                "training_examples_used": training_examples_used,
                "training_examples_count": len(training_examples_used)
            }

        except Exception as e:
            # Restaurar stdout em caso de erro
            sys.stdout = original_stdout
            execution_logs = log_capture.getvalue()

            print(f"❌ Erro no playground: {e}")
            import traceback
            traceback.print_exc()

            error_message = str(e)

            return {
                "success": False,
                "final_output": f"Erro ao executar playground: {error_message}",
                "execution_logs": execution_logs + f"\n\nERRO: {error_message}",
                "error": error_message,
                "agent_used": agent_used,
                "processing_time": 0
            }

    async def process_message(
        self,
        tenant_id: str,
        crew_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        team_data: Optional[Dict[str, Any]] = None,
        agent_override: Optional[str] = None,
        remote_jid: Optional[str] = None,
        contact_id: Optional[int] = None,
        ticket_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Processa mensagem usando configurações avançadas da equipe"""
        
        print("\n" + "="*60)
        print("🎯 PROCESSANDO MENSAGEM - CrewAI Real Engine")
        print("="*60)
        print(f"Tenant ID: {tenant_id}")
        print(f"Crew ID: {crew_id}")
        print(f"Mensagem: {message}")
        print(f"Histórico recebido: {len(conversation_history) if conversation_history else 0} mensagens")
        if conversation_history:
            print(f"Exemplo do histórico: {conversation_history[0]}")
        print("="*60 + "\n")

        success = False
        response_text = ""
        error_message = None
        selected_agent_data = None
        prompt_used = ""

        try:
            if not self.llm:
                error_message = "LLM não inicializado"
                return {
                    "success": False,
                    "response": "Desculpe, o serviço de IA não está disponível no momento.",
                    "error": error_message
                }

            if not team_data:
                error_message = "No team data provided"
                return {
                    "success": False,
                    "response": "Desculpe, não foi possível processar sua mensagem. Equipe não configurada.",
                    "error": error_message
                }

            agents = team_data.get('agents', [])
            if not agents:
                error_message = "No agents in team"
                return {
                    "success": False,
                    "response": "Desculpe, não há agentes disponíveis nesta equipe.",
                    "error": error_message
                }

            process_type = team_data.get('processType', 'sequential')
            temperature = team_data.get('temperature', 0.7)
            verbose = team_data.get('verbose', True)

            print(f"\n⚙️ CONFIGURAÇÕES DA EQUIPE:")
            print(f"   Process Type: {process_type}")
            print(f"   Temperature: {temperature}")
            print(f"   Verbose: {verbose}")
            print(f"   Total de agentes: {len(agents)}\n")
            # DEBUG: Mostrar configuração de cada agente
            for idx, agent in enumerate(agents, 1):
                print(f"   Agente {idx}: {agent.get('name')}")
                print(f"      - useKnowledgeBase: {agent.get('useKnowledgeBase')}")
                if agent.get('knowledgeBaseIds'):
                    print(f"      - knowledgeBaseIds: {agent.get('knowledgeBaseIds')}")
            print()

            custom_llm = self._get_llm_for_team({
                'temperature': temperature,
                'processType': process_type,
                'managerLLM': team_data.get('managerLLM')
            })

            # MODO HIERARCHICAL: Delegação manual - EXIGE Manager Agent configurado
            if process_type == 'hierarchical':
                manager_agent_id = team_data.get('managerAgentId')
                
                # EXIGIR managerAgentId configurado no dropdown
                if not manager_agent_id:
                    print(f"❌ Modo hierarchical mas nenhum Manager Agent foi selecionado no dropdown")
                    return {
                        "success": False,
                        "response": "Desculpe, a equipe não está configurada corretamente. Por favor, selecione um Agente Coordenador (Manager) nas configurações da equipe.",
                        "error": "Manager Agent not selected in team settings"
                    }
                
                print(f"🎯 Modo HIERARCHICAL - Manager Agent ID: {manager_agent_id}")
                
                # Encontrar Manager Agent na lista
                manager_agent_data = next((a for a in agents if a.get('id') == manager_agent_id), None)
                
                if not manager_agent_data:
                    print(f"❌ Manager Agent ID {manager_agent_id} não encontrado na lista de agentes")
                    error_message = f"Manager Agent ID {manager_agent_id} not found"
                    return {
                        "success": False,
                        "response": "Desculpe, o agente coordenador não foi encontrado.",
                        "error": error_message
                    }
                
                print(f"✅ Manager Agent encontrado: {manager_agent_data.get('name')}")
                
                # Separar especialistas (todos os agentes exceto o manager)
                specialist_agents_data = [a for a in agents if a.get('id') != manager_agent_id and a.get('isActive', True)]
                print(f"📋 Especialistas disponíveis: {len(specialist_agents_data)}")
                for specialist in specialist_agents_data:
                    print(f"   - {specialist.get('name')} ({specialist.get('function')})")
                
                # Buscar Knowledge Base (pode ser usado por qualquer agente)
                knowledge_context = None
                kb_chunks = []
                kb_usage_info = None
                
                # Verificar se algum agente usa KB
                agents_with_kb = [a for a in agents if a.get('useKnowledgeBase')]
                if agents_with_kb:
                    all_kb_ids = []
                    for agent in agents_with_kb:
                        kb_ids = agent.get('knowledgeBaseIds', [])
                        all_kb_ids.extend(kb_ids)
                    
                    all_kb_ids = list(set(all_kb_ids))  # Remove duplicates
                    
                    if all_kb_ids:
                        print(f"📚 Buscando Knowledge Base: {len(all_kb_ids)} documentos")
                        try:
                            kb_chunks = self.knowledge_service.search_knowledge(
                                team_id=str(crew_id),
                                document_ids=all_kb_ids,
                                query=message,
                                top_k=20
                            )

                            if kb_chunks:
                                knowledge_context = "\n\n".join([
                                    f"📄 {chunk['metadata'].get('filename', 'Documento')}: {chunk['content']}"
                                    for chunk in kb_chunks
                                ])
                                print(f"✅ {len(kb_chunks)} chunks relevantes encontrados do KB")

                                kb_usage_info = {
                                    "used": True,
                                    "documentsSearched": len(all_kb_ids),
                                    "chunksFound": len(kb_chunks),
                                    "chunks": [
                                        {
                                            "filename": chunk['metadata'].get('filename', 'Documento'),
                                            "documentId": chunk.get('documentId'),
                                            "similarity": round(chunk.get('similarity', 0), 3),
                                            "contentPreview": chunk['content'][:100] + "..." if len(chunk['content']) > 100 else chunk['content']
                                        }
                                        for chunk in kb_chunks
                                    ]
                                }
                            else:
                                print("📭 Nenhum chunk relevante encontrado")
                                kb_usage_info = {
                                    "used": True,
                                    "documentsSearched": len(all_kb_ids),
                                    "chunksFound": 0,
                                    "chunks": []
                                }
                        except Exception as e:
                            print(f"⚠️ Erro ao buscar KB: {e}")
                            kb_usage_info = {
                                "used": True,
                                "documentsSearched": len(all_kb_ids),
                                "chunksFound": 0,
                                "error": str(e)
                            }
                
                # Converter histórico para o formato esperado
                formatted_history = []
                if conversation_history:
                    for msg in conversation_history:
                        if msg.get('role') == 'user':
                            formatted_history.append({"sender": "user", "body": msg.get('content', '')})
                        elif msg.get('role') == 'assistant':
                            formatted_history.append({"sender": "assistant", "body": msg.get('content', '')})
                
                # Usar delegação hierárquica com CrewAI Tasks
                print("🚀 Iniciando delegação hierárquica com CrewAI Tasks...")
                start_time = time.time()
                
                delegation_result = self._run_manual_hierarchical_delegation(
                    message=message,
                    manager_agent_data=manager_agent_data,
                    specialist_agents_data=specialist_agents_data,
                    conversation_history=formatted_history,
                    llm=custom_llm,
                    knowledge_context=knowledge_context
                )
                
                elapsed_time = time.time() - start_time
                
                if not delegation_result.get('success'):
                    return {
                        "success": False,
                        "response": delegation_result.get('response', 'Erro na delegação'),
                        "error": delegation_result.get('error', 'Unknown delegation error')
                    }
                
                response_text = delegation_result['response']
                selected_agent_data = manager_agent_data  # Para logs
                success = True
                prompt_used = f"[Hierarchical Delegation] Manager: {manager_agent_data.get('name')}, Specialists: {len(specialist_agents_data)}"
                
                print(f"✅ Delegação concluída em {elapsed_time:.2f}s")
                
            else:
                # MODO SEQUENTIAL: Usar keyword matching com manutenção de contexto
                selected_agent_data = self._select_agent_by_keywords(
                    message,
                    agents,
                    team_data.get("defaultAgentId"),
                    conversation_history=conversation_history
                )

                if not selected_agent_data:
                    error_message = "No appropriate agent found"
                    return {
                        "success": False,
                        "response": "Desculpe, não consegui encontrar um agente apropriado para sua solicitação.",
                        "error": error_message
                    }

                print(f"✅ Usando agente: {selected_agent_data.get('name')}")

                # Buscar Knowledge Base se o agente usar
                knowledge_context = None
                kb_chunks = []
                kb_usage_info = None

                if selected_agent_data.get('useKnowledgeBase'):
                    kb_ids = selected_agent_data.get('knowledgeBaseIds', [])
                    if kb_ids:
                        print(f"📚 Buscando Knowledge Base: {len(kb_ids)} documentos")
                        try:
                            kb_chunks = self.knowledge_service.search_knowledge(
                                team_id=str(crew_id),
                                document_ids=kb_ids,
                                query=message,
                                top_k=20
                            )

                            if kb_chunks:
                                knowledge_context = "\n\n".join([
                                    f"📄 {chunk['metadata'].get('filename', 'Documento')}: {chunk['content']}"
                                    for chunk in kb_chunks
                                ])
                                print(f"✅ {len(kb_chunks)} chunks relevantes encontrados do KB")

                                kb_usage_info = {
                                    "used": True,
                                    "documentsSearched": len(kb_ids),
                                    "chunksFound": len(kb_chunks),
                                    "chunks": [
                                        {
                                            "filename": chunk['metadata'].get('filename', 'Documento'),
                                            "documentId": chunk.get('documentId'),
                                            "similarity": round(chunk.get('similarity', 0), 3),
                                            "contentPreview": chunk['content'][:100] + "..." if len(chunk['content']) > 100 else chunk['content']
                                        }
                                        for chunk in kb_chunks
                                    ]
                                }
                            else:
                                print("📭 Nenhum chunk relevante encontrado")
                                kb_usage_info = {
                                    "used": True,
                                    "documentsSearched": len(kb_ids),
                                    "chunksFound": 0,
                                    "chunks": []
                                }
                        except Exception as e:
                            print(f"⚠️ Erro ao buscar KB: {e}")
                            kb_usage_info = {
                                "used": True,
                                "documentsSearched": len(kb_ids),
                                "chunksFound": 0,
                                "error": str(e)
                            }

                print("🚀 Gerando resposta com Vertex AI...")
                start_time = time.time()

                response_text, prompt_used, training_examples_used = self._create_simple_response(
                    message,
                    selected_agent_data,
                    conversation_history or [],
                    custom_llm,
                    knowledge_context
                )

                elapsed_time = time.time() - start_time
                success = True

            print(f"✅ Resposta gerada em {elapsed_time:.2f}s")

            # Salvar log no backend
            log_data = {
                "companyId": int(tenant_id),
                "teamId": int(crew_id),
                "agentId": selected_agent_data.get('id'),
                "message": message,
                "response": response_text,
                "agentConfig": {
                    "name": selected_agent_data.get('name'),
                    "function": selected_agent_data.get('function'),
                    "objective": selected_agent_data.get('objective'),
                    "keywords": selected_agent_data.get('keywords', []),
                    "useKnowledgeBase": selected_agent_data.get('useKnowledgeBase', False),
                    "trainingExamplesUsed": len(training_examples_used),
                    "trainingExamples": [
                        {
                            "feedbackType": ex.get('feedbackType'),
                            "priority": ex.get('priority'),
                            "userMessage": ex.get('userMessage', '')[:100],  # Preview
                            "hasCorrection": bool(ex.get('correctedResponse'))
                        }
                        for ex in training_examples_used
                    ]
                },
                "knowledgeBaseUsage": kb_usage_info,
                "teamConfig": {
                    "processType": process_type,
                    "temperature": temperature,
                    "verbose": verbose
                },
                "promptUsed": prompt_used,
                "processingTime": round(elapsed_time, 2),
                "success": True,
                "errorMessage": None
            }
            
            self._save_log_to_backend(log_data)

            return {
                "success": True,
                "response": response_text,
                "agent_used": selected_agent_data.get('name'),
                "processing_time": round(elapsed_time, 2),
                "config_used": {
                    "process_type": process_type,
                    "temperature": temperature,
                    "verbose": verbose
                }
            }

        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {e}")
            import traceback
            traceback.print_exc()
            error_message = str(e)
            
            # Salvar log de erro
            if selected_agent_data and team_data:
                log_data = {
                    "companyId": int(tenant_id),
                    "teamId": int(crew_id),
                    "agentId": selected_agent_data.get('id'),
                    "message": message,
                    "response": "Erro ao processar",
                    "agentConfig": {"name": selected_agent_data.get('name')},
                    "teamConfig": {"processType": team_data.get('processType', 'sequential')},
                    "promptUsed": prompt_used if prompt_used else None,
                    "processingTime": 0,
                    "success": False,
                    "errorMessage": error_message
                }
                self._save_log_to_backend(log_data)
            
            return {
                "success": False,
                "response": "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
                "error": error_message
            }
