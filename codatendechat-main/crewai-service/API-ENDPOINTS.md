# CrewAI Service API - Documentação de Endpoints

## Base URL
`http://46.62.147.212:8000` (produção)
`http://localhost:8000` (local)

## Documentação Interativa
- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`

---

## Endpoints Existentes

### Health Check
- `GET /` - Info do serviço
- `GET /health` - Health check
- `GET /api/v2/health` - Health check v2

### Architect (Geração de Equipes)
- `POST /api/v2/architect/analyze-business` - Analisa descrição do negócio
- `POST /api/v2/architect/generate-team` - **Gera equipe automaticamente**
- `POST /api/v2/architect/suggest-improvements` - Sugere melhorias
- `POST /api/v2/architect/adapt-industry` - Adapta equipe para setor
- `GET /api/v2/architect/templates` - Templates por setor
- `POST /api/v2/architect/validate-blueprint` - Valida blueprint

### Knowledge Base
- `POST /api/v2/knowledge/upload` - Upload de documento (multipart/form-data)
- `POST /api/v2/knowledge/process-document` - Processa documento
- `POST /api/v2/knowledge/search` - Busca semântica
- `DELETE /api/v2/knowledge/delete-vectors` - Remove vetores
- `GET /api/v2/knowledge/stats/{tenant_id}` - Estatísticas
- `GET /api/v2/knowledge/documents/{tenant_id}` - Lista documentos
- `DELETE /api/v2/knowledge/documents/{document_id}` - Remove documento

### Training
- `POST /api/v2/training/generate-response` - Gera resposta da IA
- `POST /api/v2/training/analyze-conversation` - Analisa conversa
- `POST /api/v2/training/suggest-improvements` - Sugere melhorias
- `GET /api/v2/training/templates/{industry}` - Templates de treinamento
- `POST /api/v2/training/save-correction` - Salva correção

### Crews
- `GET /api/v2/crews/{tenant_id}/{crew_id}/agents` - Lista agentes da equipe
- `POST /api/v2/process-message` - Processa mensagem
- `POST /api/v2/validate-crew` - Valida configuração

### Stats & Admin
- `GET /api/v2/stats/{tenant_id}` - Estatísticas do tenant
- `GET /api/v2/capabilities` - Recursos disponíveis
- `POST /api/v2/migrate-from-autogen` - Migração do AutoGen
- `GET /api/v2/superadmin/tenants` - Lista todos tenants (superadmin)
- `GET /api/v2/superadmin/crews` - Lista todas crews (superadmin)

---

## Endpoints a CRIAR (CRUD de Crews)

### Listar Crews
```
GET /api/v2/crews?tenantId={tenant_id}
Response: [{ id, name, description, status, agents, ... }]
```

### Buscar Crew
```
GET /api/v2/crews/{crew_id}?tenantId={tenant_id}
Response: { id, name, description, agents, config, workflow, ... }
```

### Criar Crew
```
POST /api/v2/crews
Body: {
  tenantId: string,
  name: string,
  description: string,
  industry?: string,
  objective?: string,
  tone?: string,
  createdBy?: string
}
Response: { id, ... }
```

### Atualizar Crew
```
PUT /api/v2/crews/{crew_id}
Body: {
  tenantId: string,
  name?: string,
  description?: string,
  agents?: object,
  config?: object,
  workflow?: object,
  status?: string
}
Response: { id, ... }
```

### Deletar Crew
```
DELETE /api/v2/crews/{crew_id}?tenantId={tenant_id}
Response: { message: "deleted" }
```

---

## Estrutura de Dados

### Crew (Firestore)
```json
{
  "name": "Nome da Equipe",
  "description": "Descrição do negócio",
  "tenantId": "company_123",
  "createdBy": "user_id",
  "status": "active|draft",
  "version": "1.0",
  "createdAt": "2025-10-21T...",
  "updatedAt": "2025-10-21T...",

  "config": {
    "industry": "imobiliario",
    "objective": "...",
    "tone": "professional",
    "language": "pt-BR"
  },

  "agents": {
    "agent_id": {
      "name": "Nome do Agente",
      "role": "Função",
      "goal": "Objetivo",
      "backstory": "História",
      "order": 1,
      "isActive": true,
      "keywords": ["palavra1", "palavra2"],
      "personality": {
        "tone": "friendly",
        "traits": ["atencioso", "paciente"],
        "customInstructions": "..."
      },
      "tools": ["tool1", "tool2"],
      "toolConfigs": {
        "tool1": { config... }
      },
      "knowledgeDocuments": [],
      "training": {
        "guardrails": {
          "do": ["faça isso"],
          "dont": ["não faça isso"]
        },
        "persona": "...",
        "examples": []
      }
    }
  },

  "workflow": {
    "entryPoint": "agent_id",
    "fallbackAgent": "agent_id",
    "escalationRules": []
  },

  "customTools": [],
  "training": {
    "guardrails": { "do": [], "dont": [] },
    "persona": "...",
    "examples": []
  },

  "metrics": {
    "totalConversations": 0,
    "avgResponseTime": 0,
    "satisfactionRate": 0,
    "lastUsed": null
  }
}
```

### Agent Structure
```json
{
  "name": "string",
  "role": "string",
  "goal": "string",
  "backstory": "string",
  "order": "number",
  "isActive": "boolean",
  "keywords": ["string"],
  "personality": {
    "tone": "professional|friendly|empathetic|technical|sales",
    "traits": ["string"],
    "customInstructions": "string"
  },
  "tools": ["string"],
  "toolConfigs": {},
  "knowledgeDocuments": [],
  "training": {
    "guardrails": {
      "do": ["string"],
      "dont": ["string"]
    },
    "persona": "string",
    "examples": []
  }
}
```
