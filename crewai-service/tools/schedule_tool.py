"""
Tool para agendamento de compromissos/mensagens
"""

import requests
from typing import Dict, Any, Optional
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# URL do backend Node.js
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN", "")


class ScheduleAppointmentTool:
    """
    Tool para agendar compromissos/mensagens para serem enviadas em uma data/hora específica.

    Esta ferramenta permite que agentes CrewAI criem agendamentos no sistema de calendário,
    que serão processados automaticamente pelo sistema de filas no horário especificado.
    """

    name = "schedule_appointment"
    description = """
    Agenda um compromisso ou mensagem para ser enviada em uma data/hora específica.

    Use esta ferramenta quando o usuário solicitar:
    - Agendar uma consulta
    - Marcar um horário
    - Criar um lembrete para data futura
    - Programar envio de mensagem

    Parâmetros necessários:
    - contact_id (int): ID do contato no sistema
    - message (str): Mensagem a ser enviada no agendamento
    - send_at (str): Data e hora no formato ISO 8601 (YYYY-MM-DDTHH:mm:ss)
    - company_id (int): ID da empresa

    Exemplo de uso:
    contact_id=123, message="Lembrete: Sua consulta é amanhã às 14h",
    send_at="2025-11-18T14:00:00", company_id=1

    Retorna um dicionário com o resultado da operação.
    """

    def _run(
        self,
        contact_id: int,
        message: str,
        send_at: str,
        company_id: int,
        user_id: Optional[int] = None,
        dry_run: bool = False
    ) -> str:
        """
        Executa o agendamento chamando o backend Node.js

        Args:
            contact_id: ID do contato
            message: Mensagem a ser enviada
            send_at: Data/hora no formato ISO (YYYY-MM-DDTHH:mm:ss)
            company_id: ID da empresa
            user_id: ID do usuário (opcional)
            dry_run: Se True, apenas simula (não cria de verdade)

        Returns:
            String com resultado da operação (formato para LLM processar)
        """
        try:
            # Modo dry-run (simulação) - usado no Playground
            if dry_run:
                logger.info(f"[DRY-RUN] Simulando agendamento: {send_at} - {message}")
                return (
                    f"✅ [SIMULAÇÃO] Agendamento seria criado:\n"
                    f"Data/Hora: {send_at}\n"
                    f"Mensagem: {message}\n"
                    f"Company: {company_id}\n"
                    f"\n⚠️ Este é um modo de teste. Nenhum agendamento real foi criado."
                )

            # Modo real (produção)
            # Validar formato da data
            try:
                datetime.fromisoformat(send_at.replace('Z', '+00:00'))
            except ValueError as e:
                error_msg = f"Formato de data inválido: {send_at}. Use YYYY-MM-DDTHH:mm:ss"
                logger.error(error_msg)
                return f"ERRO: {error_msg}"

            # Validar que a data está no futuro
            send_datetime = datetime.fromisoformat(send_at.replace('Z', '+00:00'))
            if send_datetime <= datetime.now():
                error_msg = "A data/hora do agendamento deve ser no futuro"
                logger.error(error_msg)
                return f"ERRO: {error_msg}"

            # Preparar payload
            payload = {
                "body": message,
                "sendAt": send_at,
                "contactId": contact_id,
                "companyId": company_id
            }

            if user_id:
                payload["userId"] = user_id

            # Preparar headers de autenticação
            headers = {
                "Content-Type": "application/json"
            }

            if SERVICE_TOKEN:
                headers["Authorization"] = f"Bearer {SERVICE_TOKEN}"

            # Fazer request para o backend (endpoint interno sem autenticação)
            logger.info(f"Criando agendamento para contactId={contact_id}, sendAt={send_at}")

            response = requests.post(
                f"{BACKEND_URL}/schedules/internal",
                json=payload,
                headers=headers,
                timeout=10
            )

            # Processar resposta
            if response.status_code in [200, 201]:
                data = response.json()
                schedule_id = data.get("id")

                success_msg = (
                    f"✅ Agendamento criado com sucesso!\n"
                    f"ID: {schedule_id}\n"
                    f"Data/Hora: {send_at}\n"
                    f"Mensagem: {message[:50]}{'...' if len(message) > 50 else ''}"
                )

                logger.info(f"Agendamento {schedule_id} criado com sucesso")
                return success_msg

            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get('error', f'HTTP {response.status_code}')

                logger.error(f"Erro ao criar agendamento: {error_msg}")
                return f"❌ Erro ao criar agendamento: {error_msg}"

        except requests.exceptions.Timeout:
            error_msg = "Timeout ao conectar com o servidor. Tente novamente."
            logger.error(error_msg)
            return f"❌ {error_msg}"

        except requests.exceptions.ConnectionError:
            error_msg = "Não foi possível conectar ao servidor de agendamentos."
            logger.error(error_msg)
            return f"❌ {error_msg}"

        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            logger.error(f"Erro ao executar schedule_appointment: {e}", exc_info=True)
            return f"❌ {error_msg}"

    def _arun(self, *args, **kwargs):
        """Versão assíncrona (não implementada)"""
        raise NotImplementedError("ScheduleAppointmentTool não suporta execução assíncrona")
