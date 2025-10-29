# COMO ACESSAR A VM E VER LOGS

## CREDENCIAIS
As credenciais SSH e SUDO estão no arquivo: `~/.ssh-atendechat-password`

Formato do arquivo:
```bash
export SSH_PASSWORD="123456"
export SUDO_PASSWORD="123456"
```

## COMANDOS ESSENCIAIS

### 1. VER LOGS DO SERVIÇO CREWAI
```bash
source ~/.ssh-atendechat-password && sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no airton@46.62.147.212 "journalctl -u crewai.service -n 200 --no-pager | tail -100"
```

### 2. VER LOGS COM FILTRO
```bash
source ~/.ssh-atendechat-password && sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no airton@46.62.147.212 "journalctl -u crewai.service -n 200 --no-pager | grep -E 'PATTERN' -A 5 -B 2"
```

### 3. FAZER DEPLOY (atualizar código e reiniciar)
```bash
source ~/.ssh-atendechat-password && sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no airton@46.62.147.212 "cd /home/airton/atendechat && git fetch origin main && git reset --hard origin/main && cd codatendechat-main/crewai-service && find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null && find . -type f -name '*.pyc' -delete 2>/dev/null && echo '$SUDO_PASSWORD' | sudo -S systemctl restart crewai.service && sleep 8 && echo '$SUDO_PASSWORD' | sudo -S systemctl status crewai.service --no-pager | head -10"
```

### 4. REINICIAR SERVIÇO SEM DEPLOY
```bash
source ~/.ssh-atendechat-password && sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no airton@46.62.147.212 "echo '$SUDO_PASSWORD' | sudo -S systemctl restart crewai.service && sleep 5 && lsof -i:8000"
```

### 5. MATAR PROCESSOS NA PORTA 8000
```bash
source ~/.ssh-atendechat-password && sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no airton@46.62.147.212 "echo '$SUDO_PASSWORD' | sudo -S systemctl stop crewai.service && echo '$SUDO_PASSWORD' | sudo -S killall -9 python python3 uvicorn 2>/dev/null; echo '$SUDO_PASSWORD' | sudo -S lsof -ti:8000 | xargs -r sudo kill -9 2>/dev/null; sleep 3"
```

## INFORMAÇÕES DA VM
- **IP**: 46.62.147.212
- **Usuário SSH**: airton
- **Porta SSH**: 22
- **Porta serviço**: 8000
- **Path do código**: /home/airton/atendechat/codatendechat-main/crewai-service
- **Serviço systemd**: crewai.service

## FLUXO DE TRABALHO PADRÃO

1. **Fazer alteração no código local**
2. **Commit e push**:
   ```bash
   git add .
   git commit -m "mensagem"
   git push origin main
   ```
3. **Fazer deploy** (usar comando #3 acima)
4. **Verificar logs** (usar comando #1 ou #2 acima)

## TROUBLESHOOTING

### Problema: Porta 8000 ocupada
Solução: Usar comando #5 para matar todos processos

### Problema: Código antigo rodando
Solução:
1. Verificar se push foi feito
2. Fazer deploy completo (comando #3)
3. Limpar __pycache__ está incluído no deploy

### Problema: Não consigo ver logs
Solução: O usuário airton precisa estar no grupo systemd-journal.
Use `sudo` ou peça para rodar com permissões adequadas.
