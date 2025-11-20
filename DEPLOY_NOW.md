# 🚀 Deploy em Produção - Guia Rápido

## ✅ Status Atual
- ✅ Código commitado e pushado no GitHub
- ✅ Branch: `main`
- ✅ Último commit: `99e9567`

## 📋 Passos para Deploy

### 1. Conectar na VPS via SSH

**No Windows PowerShell:**
```powershell
ssh root@72.61.56.204
```
*(Digite a senha quando solicitado)*

### 2. Executar Deploy Automatizado

**Na VPS (após conectar via SSH, copie e cole os comandos abaixo):**

```bash
cd /opt/contabil/contabil_system && bash deploy/deploy.sh main
```

**OU execute passo a passo:**

```bash
cd /opt/contabil/contabil_system
bash deploy/deploy.sh main
```

O script irá automaticamente:
- ✅ Puxar código atualizado do GitHub
- ✅ Instalar/atualizar dependências Python
- ✅ Executar migrações do banco (se necessário)
- ✅ Criar backup antes de atualizar
- ✅ Reiniciar o serviço
- ✅ Verificar se está funcionando

### 3. Verificar Deploy

**Na VPS:**
```bash
# Verifica status do serviço
systemctl status contabil.service

# Verifica logs (últimas 50 linhas)
journalctl -u contabil.service -n 50

# Verifica logs em tempo real
journalctl -u contabil.service -f

# Testa aplicação
curl http://localhost:8501
```

### 4. Verificar no Navegador

Acesse a aplicação no navegador:
- URL: `http://72.61.56.204` (ou seu domínio configurado)
- Verifique se a aplicação está funcionando corretamente

## 🔧 Troubleshooting

### Se o serviço não iniciar:
```bash
# Ver logs detalhados
journalctl -u contabil.service -n 100

# Reiniciar manualmente
systemctl restart contabil.service

# Verificar se há erros no código
cd /opt/contabil/contabil_system
source venv/bin/activate
python app.py
```

### Se houver erro de dependências:
```bash
cd /opt/contabil/contabil_system
source venv/bin/activate
pip install -r requirements.txt
```

### Se houver erro de banco de dados:
```bash
# Verificar conexão com PostgreSQL
cd /opt/contabil/contabil_system
source venv/bin/activate
python -c "from config.database import engine; print(engine.connect())"
```

## 📞 Suporte

Se encontrar problemas, verifique:
1. Logs do serviço: `journalctl -u contabil.service -n 100`
2. Logs do Nginx: `journalctl -u nginx -n 50`
3. Status do PostgreSQL: `systemctl status postgresql`
