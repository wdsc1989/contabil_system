# 🚀 Próximos Passos para Produção - Vision API

## ✅ Commit e Push Realizados

Todas as mudanças foram commitadas e enviadas para o repositório.

## 📋 Passos para Executar na VPS (Hostinger)

### 1. Conectar na VPS via SSH

```bash
ssh root@seu-ip-ou-dominio
```

### 2. Ir para o diretório da aplicação

```bash
cd /opt/contabil
```

### 3. Atualizar código do repositório

```bash
git fetch origin
git checkout main
git pull origin main
```

### 4. Corrigir permissões e instalar dependências

```bash
# Opção A: Usar script automático (recomendado)
bash deploy/fix_production.sh

# Opção B: Manual
chmod +x deploy/deploy.sh
chmod +x deploy/*.sh
source /opt/contabil/venv/bin/activate
pip install --upgrade pip
pip install PyMuPDF>=1.23.0
pip install -r requirements.txt
```

### 5. Atualizar configuração do Nginx

```bash
# Copia nova configuração
sudo cp deploy/nginx/contabil.conf /etc/nginx/sites-available/contabil

# Testa configuração
sudo nginx -t

# Se OK, recarrega
sudo systemctl reload nginx
```

### 6. Atualizar serviço systemd

```bash
# Copia nova configuração
sudo cp deploy/systemd/contabil.service /etc/systemd/system/contabil.service

# Recarrega systemd
sudo systemctl daemon-reload

# Reinicia serviço
sudo systemctl restart contabil.service
```

### 7. Verificar se tudo está funcionando

```bash
# Verifica status do serviço
systemctl status contabil.service

# Executa diagnóstico completo
bash deploy/check_service.sh

# Verifica se Streamlit responde
curl http://127.0.0.1:8501

# Verifica logs em tempo real (se necessário)
journalctl -u contabil.service -f
```

### 8. Verificar instalação das dependências

```bash
source /opt/contabil/venv/bin/activate

# Verifica PyMuPDF
python -c "import fitz; print('✅ PyMuPDF OK:', fitz.__version__)"

# Verifica OpenAI
python -c "import openai; print('✅ OpenAI OK:', openai.__version__)"

# Verifica poppler (fallback)
pdftoppm -v
```

## 🔍 Troubleshooting

### Se o serviço não iniciar:

```bash
# Ver logs de erro
journalctl -u contabil.service -n 50

# Verifica se há erros de importação
journalctl -u contabil.service | grep -i error
```

### Se PyMuPDF não funcionar:

```bash
source /opt/contabil/venv/bin/activate
pip uninstall PyMuPDF
pip install PyMuPDF>=1.23.0
python -c "import fitz; print('OK')"
```

### Se ainda der erro 502:

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
```

### Se precisar reinstalar tudo:

```bash
# Usa o script de deploy completo
./deploy/deploy.sh
```

## ✅ Checklist Final

- [ ] Código atualizado (`git pull`)
- [ ] PyMuPDF instalado e funcionando
- [ ] OpenAI instalado
- [ ] Nginx configurado e recarregado
- [ ] Serviço systemd atualizado e reiniciado
- [ ] Serviço está rodando (`systemctl status contabil.service`)
- [ ] Streamlit responde na porta 8501
- [ ] Nginx não mostra erros 502
- [ ] Teste de upload de imagem funciona

## 📝 Comandos Úteis

```bash
# Ver logs em tempo real
journalctl -u contabil.service -f

# Reiniciar serviço
sudo systemctl restart contabil.service

# Recarregar Nginx
sudo systemctl reload nginx

# Ver status completo
systemctl status contabil.service

# Ver uso de memória
ps aux | grep streamlit

# Verificar portas
netstat -tlnp | grep 8501
```

## 🎯 Após Concluir

1. Teste o upload de uma imagem pequena primeiro
2. Se funcionar, teste com PDF
3. Se tudo OK, teste com arquivos maiores
4. Monitore os logs durante os testes

## 📞 Se Precisar de Ajuda

Execute o diagnóstico completo:
```bash
bash deploy/check_service.sh
```

E compartilhe a saída para análise.

