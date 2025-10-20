# CrewAI Service - Atendechat

Serviço standalone de CrewAI para atendimento inteligente com IA.

## Requisitos

- Python 3.10+
- Google Cloud Project com Vertex AI habilitado
- Firebase/Firestore configurado

## Instalação Local

```bash
cd crewai-service

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env com suas credenciais

# Rodar
cd api/src
python main.py
```

## Deploy na VM

```bash
# Copiar serviço para VM
scp -r crewai-service airton@46.62.147.212:/home/airton/atendechat/codatendechat-main/

# Na VM:
cd /home/airton/atendechat/codatendechat-main/crewai-service

# Instalar dependências
pip3 install -r requirements.txt

# Copiar arquivo de serviço
sudo cp crewai-service.service /etc/systemd/system/

# Habilitar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable crewai-service
sudo systemctl start crewai-service

# Ver logs
sudo journalctl -u crewai-service -f
```

## Endpoints

- `GET /` - Info do serviço
- `GET /health` - Health check
- `GET /docs` - Documentação Swagger
- `POST /api/v2/architect/generate-team` - Gerar equipe IA
- `POST /api/v2/crews` - Criar/editar equipe
- `GET /api/v2/crews` - Listar equipes
- `POST /api/v2/training/generate-response` - Treinar equipe

## Configuração Nginx

Adicionar ao nginx:

```nginx
location /api/crewai/ {
    proxy_pass http://localhost:8000/api/v2/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```
