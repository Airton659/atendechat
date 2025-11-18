# 🧪 Testando Agendamento no Playground

## Como Testar a Funcionalidade de Agendamento

O Playground agora suporta **execução de ferramentas (tools)** incluindo agendamentos!

### 1. Acessar o Playground

Acesse a interface web:
```
https://www.atendeaibr.com/teams-playground
```

ou localmente:
```
http://localhost:3000/teams-playground
```

### 2. Selecionar Equipe

Escolha a equipe que contém o agente "Assistente de Agendamentos"

### 3. Mensagens de Teste

#### Teste 1: Agendamento Completo

**Digite no campo de mensagem:**
```
Quero agendar uma consulta para amanhã às 14h
```

**Resultado Esperado:**
- ✅ System detecta keywords: "agendar", "consulta"
- ✅ Seleciona agente "Assistente de Agendamentos"
- ✅ Extrai: data (amanhã), hora (14h), descrição (consulta)
- ✅ Executa tool `schedule_appointment`
- ✅ Resposta: "✅ Agendamento criado com sucesso! Sua consulta foi agendada para [data] às 14:00!"

#### Teste 2: Informação Incompleta

**Digite:**
```
Quero marcar um horário
```

**Resultado Esperado:**
- ✅ Detecta intenção de agendamento
- ⚠️ Identifica falta de data/hora
- ✅ Resposta: "Claro! Para qual data e horário você gostaria de agendar?"

#### Teste 3: Múltiplas Datas

**Digite:**
```
Preciso agendar 2 consultas: segunda às 9h e quarta às 15h
```

**Resultado Esperado:**
- ✅ Detecta 2 agendamentos
- ✅ Confirma antes de criar
- ✅ Resposta solicitando confirmação

### 4. Verificar Tool Usage

No retorno do playground, você verá:

```json
{
  "success": true,
  "final_output": "✅ Agendamento criado com sucesso!...",
  "agent_used": "Assistente de Agendamentos",
  "tool_usage": {
    "tool_used": "schedule_appointment",
    "result": "✅ Agendamento criado com sucesso!\nID: 42\n...",
    "extracted_data": {
      "has_enough_info": true,
      "send_at": "2025-11-19T14:00:00",
      "message": "consulta"
    }
  },
  "execution_logs": "...",
  "processing_time": 2.34
}
```

### 5. Verificar Agendamento no Banco

**Via SQL:**
```sql
SELECT
  id,
  body,
  "sendAt",
  status,
  "contactId",
  "createdAt"
FROM "Schedules"
WHERE "contactId" = 1  -- Playground usa contactId = 1
ORDER BY "createdAt" DESC
LIMIT 5;
```

**Via API:**
```bash
curl -X GET "https://api.atendeaibr.com/schedules?contactId=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. Logs para Debug

**Verificar detecção de tool:**
```bash
ssh airton@46.62.147.212
pm2 logs crewai-api | grep -E "(TOOL DETECTION|schedule_appointment)"
```

**Deve mostrar:**
```
🔧 TOOL DETECTION: Intenção de agendamento detectada!
📊 Dados extraídos: {'has_enough_info': True, ...}
🔧 Tool executada: schedule_appointment
```

## Exemplos de Testes por Caso de Uso

### Clínica Médica

```
Mensagem: "Gostaria de agendar uma consulta com cardiologista para sexta às 10h"

Esperado:
- Agente: Assistente de Agendamentos
- Tool: schedule_appointment
- Data: próxima sexta-feira, 10:00
- Descrição: "consulta com cardiologista"
```

### Salão de Beleza

```
Mensagem: "Preciso marcar corte e coloração para terça 15h"

Esperado:
- Agente: Assistente de Agendamentos
- Tool: schedule_appointment
- Data: próxima terça-feira, 15:00
- Descrição: "corte e coloração"
```

### Escritório/Reuniões

```
Mensagem: "Agendar reunião de alinhamento para 20/11 às 14h30"

Esperado:
- Agente: Assistente de Agendamentos
- Tool: schedule_appointment
- Data: 2025-11-20T14:30:00
- Descrição: "reunião de alinhamento"
```

## Troubleshooting

### Tool não é executada

**Problema:** Mensagem processada mas tool não executa

**Verificar:**
1. Keywords do agente incluem termos de agendamento?
```sql
SELECT name, keywords FROM "Agents" WHERE id = 8;
```

2. Logs mostram detecção?
```bash
pm2 logs crewai-api --lines 100 | grep "TOOL DETECTION"
```

3. SERVICE_TOKEN configurado?
```bash
ssh airton@46.62.147.212 "cat /home/airton/crewai-service-new/.env | grep SERVICE_TOKEN"
```

### Data extraída incorretamente

**Problema:** LLM extrai data errada

**Solução:** Adicionar exemplos no `customInstructions` do agente:
```
Exemplos de interpretação:
- "amanhã" → dia seguinte a hoje
- "segunda" → próxima segunda-feira
- "daqui a 3 dias" → hoje + 3 dias
```

### Agendamento não aparece no banco

**Verificar:**
1. Tool retornou sucesso?
2. Backend está rodando?
```bash
pm2 list | grep atendechat-backend
```

3. PostgreSQL está acessível?
```bash
sudo -u postgres psql atendechat -c "SELECT COUNT(*) FROM \"Schedules\";"
```

## Comparação: Playground vs Produção

| Aspecto | Playground | Produção |
|---------|------------|----------|
| **contactId** | Fixo: 1 | Real do WhatsApp |
| **Histórico** | Vazio | Últimas 10 mensagens |
| **Logs** | Salvos localmente | Salvos no AgentLogs |
| **Persistência** | Sim (tabela Schedules) | Sim (tabela Schedules) |
| **Envio WhatsApp** | ✅ Sim (se sendAt futuro) | ✅ Sim |

**IMPORTANTE:** Agendamentos criados no playground **SÃO REAIS** e **SERÃO ENVIADOS** no horário programado!

Se quiser testar sem enviar, use datas muito distantes:
```
"Agendar teste para 31/12/2099 às 23h59"
```

## Métricas de Sucesso

Um teste bem-sucedido deve mostrar:

✅ Agente correto selecionado
✅ Tool detectada e executada
✅ Dados extraídos corretamente
✅ Agendamento criado no banco
✅ Resposta clara e confirmando agendamento
✅ Logs sem erros

## Próximos Passos

Após validar no Playground:
1. Testar via WhatsApp real
2. Monitorar logs de produção
3. Ajustar prompts se necessário
4. Coletar feedback de usuários

---

**Dica:** Use o Playground para iterar rapidamente nos prompts do agente antes de testar em produção!
