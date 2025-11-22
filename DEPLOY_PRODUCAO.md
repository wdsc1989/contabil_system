# 🚀 Deploy para Produção - Guia Completo

## 📋 Passos para Executar na VPS (Hostinger)

### 1. Conectar na VPS via SSH

```bash
ssh root@seu-ip-ou-dominio
```

### 2. Ir para o Diretório da Aplicação

```bash
cd /opt/contabil
```

### 3. Atualizar Código do Repositório

```bash
# Atualiza código
git fetch origin
git checkout main
git pull origin main
```

### 4. Opção A: Deploy Automático (Recomendado)

```bash
# Usa o script de deploy completo (faz tudo automaticamente)
./deploy/deploy.sh
```

O script `deploy.sh` faz automaticamente:
- ✅ Atualiza código
- ✅ Instala/atualiza dependências Python
- ✅ Verifica e instala PyMuPDF se necessário
- ✅ Verifica e instala poppler-utils se necessário
- ✅ Executa migrações do banco
- ✅ Reinicia serviço systemd
- ✅ Verifica se está funcionando

### 4. Opção B: Deploy Manual (Se necessário)

Se preferir fazer manualmente ou se o script automático falhar:

```bash
# 4.1. Corrigir permissões
chmod +x deploy/deploy.sh deploy/*.sh

# 4.2. Ativar ambiente virtual e instalar dependências
source /opt/contabil/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4.3. Verificar PyMuPDF (crítico para Vision API)
python -c "import fitz; print('✅ PyMuPDF OK')" || pip install PyMuPDF>=1.23.0

# 4.4. Verificar OpenAI
python -c "import openai; print('✅ OpenAI OK')" || pip install openai>=1.0.0

# 4.5. Verificar poppler-utils (fallback para PDFs)
pdftoppm -v || sudo apt-get update && sudo apt-get install -y poppler-utils
```

### 5. Atualizar Configurações (se necessário)

```bash
# 5.1. Nginx
sudo cp deploy/nginx/contabil.conf /etc/nginx/sites-available/contabil
sudo nginx -t && sudo systemctl reload nginx

# 5.2. Systemd
sudo cp deploy/systemd/contabil.service /etc/systemd/system/contabil.service
sudo systemctl daemon-reload
```

### 6. Reiniciar Serviço

```bash
sudo systemctl restart contabil.service
```

### 7. Verificar se Está Funcionando

```bash
# 7.1. Status do serviço
systemctl status contabil.service

# 7.2. Testa se Streamlit responde
curl http://127.0.0.1:8501

# 7.3. Diagnóstico completo (recomendado)
bash deploy/check_service.sh

# 7.4. Verifica logs recentes
journalctl -u contabil.service -n 30
```

### 8. Verificar Dependências Críticas

```bash
source /opt/contabil/venv/bin/activate

# PyMuPDF (principal para PDFs)
python -c "import fitz; print('✅ PyMuPDF:', fitz.__version__)"

# OpenAI (obrigatório para Vision API)
python -c "import openai; print('✅ OpenAI:', openai.__version__)"

# poppler-utils (fallback)
pdftoppm -v
```

## ✅ Checklist de Verificação

Marque cada item após executar:

- [ ] Código atualizado (`git pull origin main`)
- [ ] Dependências Python instaladas (`pip install -r requirements.txt`)
- [ ] PyMuPDF instalado e funcionando
- [ ] OpenAI instalado
- [ ] poppler-utils instalado (opcional, mas recomendado)
- [ ] Nginx configurado e recarregado
- [ ] Serviço systemd atualizado e reiniciado
- [ ] Serviço está rodando (`systemctl status contabil.service`)
- [ ] Streamlit responde na porta 8501 (`curl http://127.0.0.1:8501`)
- [ ] Nginx não mostra erros 502
- [ ] Teste de upload funciona no sistema

## 🔍 Troubleshooting

### Problema: Serviço não inicia

```bash
# Ver logs de erro
journalctl -u contabil.service -n 50

# Verifica erros específicos
journalctl -u contabil.service | grep -i error

# Verifica se há problemas de importação
journalctl -u contabil.service | grep -i "import\|module"
```

### Problema: Erro 502 Bad Gateway

```bash
# 1. Verifica se Streamlit está rodando
systemctl status contabil.service

# 2. Verifica se responde na porta 8501
curl http://127.0.0.1:8501

# 3. Verifica logs do nginx
tail -50 /var/log/nginx/contabil_error.log

# 4. Reinicia tudo
sudo systemctl restart contabil.service
sudo systemctl reload nginx

# 5. Verifica timeouts no nginx (devem ser 900s)
grep -i timeout /etc/nginx/sites-available/contabil
```

### Problema: PyMuPDF não funciona

```bash
source /opt/contabil/venv/bin/activate

# Reinstala PyMuPDF
pip uninstall PyMuPDF
pip install PyMuPDF>=1.23.0

# Verifica
python -c "import fitz; print('OK')"
```

### Problema: Dependências faltando

```bash
source /opt/contabil/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Problema: Permissões negadas

```bash
# Corrige permissões dos scripts
chmod +x deploy/deploy.sh
chmod +x deploy/*.sh
chmod +x scripts/*.sh 2>/dev/null || true
```

## 📝 Comandos Úteis

```bash
# Ver logs em tempo real
journalctl -u contabil.service -f

# Reiniciar serviço
sudo systemctl restart contabil.service

# Recarregar Nginx (sem downtime)
sudo systemctl reload nginx

# Ver status completo do serviço
systemctl status contabil.service

# Ver uso de memória e CPU
ps aux | grep streamlit

# Verificar portas em uso
netstat -tlnp | grep 8501

# Executar diagnóstico completo
bash deploy/check_service.sh
```

## 🎯 O Que Foi Implementado

### Vision API (GPT-4o):
- ✅ Processamento automático de CSV, Excel, PDF, Imagens
- ✅ Detecção automática do tipo de dado
- ✅ Classificação automática por grupos/subgrupos
- ✅ Extração e estruturação completa de dados

### Interface Simplificada:
- ✅ Fluxo direto: Upload → Processamento IA → Revisão → Importação
- ✅ Barra de progresso durante processamento
- ✅ Métricas formatadas corretamente
- ✅ Tabela de edição melhorada
- ✅ Mensagens mais claras e concisas

### Configurações de Produção:
- ✅ Nginx com timeouts aumentados (900s)
- ✅ Upload máximo de 100M
- ✅ Systemd com mais memória (4G)
- ✅ Scripts de deploy e diagnóstico

## 🧪 Testes Após Deploy

1. **Teste básico:**
   - Acesse a aplicação no navegador
   - Verifique se a página carrega

2. **Teste de upload:**
   - Faça upload de um CSV pequeno
   - Verifique se processa corretamente
   - Teste importação

3. **Teste com PDF:**
   - Faça upload de um PDF
   - Verifique se converte e processa
   - Teste importação

4. **Teste com imagem:**
   - Faça upload de uma imagem (JPG/PNG)
   - Verifique se processa com Vision API
   - Teste importação

## 📞 Suporte

Se encontrar problemas:

1. Execute o diagnóstico: `bash deploy/check_service.sh`
2. Verifique os logs: `journalctl -u contabil.service -n 50`
3. Verifique logs do nginx: `tail -50 /var/log/nginx/contabil_error.log`

## 🎉 Pronto!

Após executar os passos acima e verificar o checklist, o sistema estará atualizado e funcionando em produção!

