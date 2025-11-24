# 🚀 Comandos Completos para Atualização em Produção

## 📋 Sequência Completa de Comandos

### 1. Conectar na VPS

```bash
ssh root@seu-ip-ou-dominio
```

### 2. Ir para o diretório da aplicação

```bash
cd /opt/contabil
```

### 3. Verificar status atual

```bash
# Ver status do Git
git status

# Ver último commit
git log --oneline -1

# Ver status do serviço
systemctl status contabil.service
```

### 4. Atualizar código do repositório

```bash
# Buscar atualizações
git fetch origin

# Ver mudanças antes de fazer pull
git log HEAD..origin/main --oneline

# Fazer pull das atualizações
git pull origin main
```

**Se houver conflitos:**

```bash
# Fazer stash de mudanças locais
git stash push -m "Mudanças locais antes do deploy $(date +%Y-%m-%d_%H:%M:%S)"

# Tentar pull novamente
git pull origin main

# Se ainda houver conflito, fazer reset (CUIDADO: perde mudanças locais)
git reset --hard origin/main
```

### 5. Garantir permissões dos scripts

```bash
chmod +x deploy/deploy.sh
chmod +x deploy/*.sh
```

### 6. Ativar ambiente virtual

```bash
source /opt/contabil/venv/bin/activate
```

### 7. Atualizar pip

```bash
pip install --upgrade pip
```

### 8. Instalar/Atualizar dependências Python

```bash
# Instalar todas as dependências
pip install -r requirements.txt

# Verificar instalação
pip list | grep -E "streamlit|pandas|pdfplumber|openai|PyMuPDF"
```

### 9. Verificar e instalar PyMuPDF (crítico)

```bash
# Verificar se está instalado
python -c "import fitz; print('✅ PyMuPDF OK:', fitz.__version__)"

# Se não estiver, instalar
pip install PyMuPDF>=1.23.0

# Verificar novamente
python -c "import fitz; print('✅ PyMuPDF instalado')"
```

### 10. Verificar dependências do sistema (poppler-utils)

```bash
# Verificar se poppler está instalado
pdftoppm -v

# Se não estiver, instalar
sudo apt-get update
sudo apt-get install -y poppler-utils

# Verificar instalação
pdftoppm -v
```

### 11. Verificar outras bibliotecas críticas

```bash
# Verificar OpenAI
python -c "import openai; print('✅ OpenAI OK:', openai.__version__)"

# Verificar pdfplumber
python -c "import pdfplumber; print('✅ pdfplumber OK')"

# Verificar pandas
python -c "import pandas; print('✅ pandas OK:', pandas.__version__)"

# Verificar streamlit
python -c "import streamlit; print('✅ streamlit OK:', streamlit.__version__)"
```

### 12. Executar migrações do banco (se necessário)

```bash
# Executar init_db.py
python3 /opt/contabil/init_db.py

# Se houver script de migrações
if [ -f "/opt/contabil/scripts/run_migrations.sh" ]; then
    bash /opt/contabil/scripts/run_migrations.sh
fi
```

### 13. Criar backup (opcional mas recomendado)

```bash
# Se houver script de backup
if [ -f "/opt/contabil/scripts/backup_postgres.sh" ]; then
    bash /opt/contabil/scripts/backup_postgres.sh daily
fi
```

### 14. Reiniciar serviço

```bash
# Recarregar configuração do systemd (se houver mudanças)
sudo systemctl daemon-reload

# Reiniciar serviço
sudo systemctl restart contabil.service

# Aguardar alguns segundos
sleep 3
```

### 15. Verificar status do serviço

```bash
# Ver status
systemctl status contabil.service

# Ver se está ativo
systemctl is-active contabil.service

# Ver logs recentes
journalctl -u contabil.service -n 50 --no-pager
```

### 16. Verificar se aplicação está respondendo

```bash
# Testar resposta HTTP
curl -I http://127.0.0.1:8501

# Ou testar com timeout
curl --max-time 5 http://127.0.0.1:8501 | head -20
```

### 17. Verificar Nginx (se configurado)

```bash
# Testar configuração do Nginx
sudo nginx -t

# Se OK, recarregar
sudo systemctl reload nginx

# Verificar status
systemctl status nginx
```

### 18. Verificar logs em tempo real (opcional)

```bash
# Ver logs do serviço
journalctl -u contabil.service -f

# Ver logs do Nginx (se houver erros)
tail -f /var/log/nginx/contabil_error.log
```

## 🔄 Script Automático (Alternativa Rápida)

Se preferir usar o script automático que faz tudo:

```bash
cd /opt/contabil
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

## 🔍 Diagnóstico Completo

Após a atualização, execute diagnóstico:

```bash
bash deploy/check_service.sh
```

## ⚠️ Troubleshooting

### Se o serviço não iniciar:

```bash
# Ver logs de erro detalhados
journalctl -u contabil.service -n 100 --no-pager

# Verificar erros específicos
journalctl -u contabil.service | grep -i error

# Tentar iniciar manualmente para ver erro
cd /opt/contabil
source venv/bin/activate
streamlit run app.py --server.port=8501
```

### Se PyMuPDF não funcionar:

```bash
source /opt/contabil/venv/bin/activate
pip uninstall PyMuPDF -y
pip install PyMuPDF>=1.23.0
python -c "import fitz; print('OK')"
```

### Se houver erro 502 no Nginx:

```bash
# Verificar se Streamlit está rodando
systemctl status contabil.service

# Verificar se responde na porta 8501
curl http://127.0.0.1:8501

# Ver logs do Nginx
tail -50 /var/log/nginx/contabil_error.log

# Reiniciar tudo
sudo systemctl restart contabil.service
sudo systemctl reload nginx
```

### Se houver problema de permissões:

```bash
# Corrigir permissões
sudo chown -R contabil:contabil /opt/contabil
chmod +x deploy/*.sh
```

### Se houver problema com Git:

```bash
# Corrigir propriedade do repositório
git config --global --add safe.directory /opt/contabil

# Limpar e resetar
git clean -fd
git reset --hard origin/main
```

## ✅ Checklist Final

Execute estes comandos para verificar:

```bash
# 1. Código atualizado
git log --oneline -1

# 2. Dependências instaladas
source /opt/contabil/venv/bin/activate
python -c "import fitz, openai, pdfplumber, pandas, streamlit; print('✅ Todas OK')"

# 3. Serviço rodando
systemctl is-active contabil.service && echo "✅ Serviço ativo" || echo "❌ Serviço inativo"

# 4. Aplicação respondendo
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8501 | grep -q "200\|302" && echo "✅ Aplicação OK" || echo "❌ Aplicação não responde"

# 5. Nginx OK (se configurado)
systemctl is-active nginx && echo "✅ Nginx OK" || echo "⚠️ Nginx não configurado"
```

## 📝 Comandos Úteis Pós-Deploy

```bash
# Ver logs em tempo real
journalctl -u contabil.service -f

# Ver uso de recursos
ps aux | grep streamlit
top -p $(pgrep -f streamlit)

# Ver portas abertas
netstat -tlnp | grep 8501

# Reiniciar serviço
sudo systemctl restart contabil.service

# Parar serviço
sudo systemctl stop contabil.service

# Iniciar serviço
sudo systemctl start contabil.service
```

## 🎯 Resumo Rápido (Copy & Paste)

```bash
# Sequência completa em um bloco
cd /opt/contabil && \
git fetch origin && \
git pull origin main && \
chmod +x deploy/deploy.sh && \
./deploy/deploy.sh && \
systemctl status contabil.service
```

---

**Nota:** O script `deploy/deploy.sh` executa a maioria desses comandos automaticamente. Use-o sempre que possível!

