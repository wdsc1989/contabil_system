# 🚀 Deploy Rápido para Produção

> **Nota:** Para guia completo, veja `DEPLOY_PRODUCAO.md`

## 📋 Passos Rápidos (VPS Hostinger)

### 1. Conectar e Atualizar

```bash
ssh root@seu-ip-ou-dominio
cd /opt/contabil
git pull origin main
```

### 2. Deploy Automático (Recomendado)

```bash
# Executa tudo automaticamente
./deploy/deploy.sh
```

### 3. Ou Deploy Manual

```bash
# Instala dependências
source /opt/contabil/venv/bin/activate
pip install -r requirements.txt

# Verifica PyMuPDF
python -c "import fitz; print('OK')" || pip install PyMuPDF>=1.23.0

# Reinicia serviço
sudo systemctl restart contabil.service
```

### 4. Verificar

```bash
# Diagnóstico completo
bash deploy/check_service.sh

# Ou verificação rápida
systemctl status contabil.service
curl http://127.0.0.1:8501
```

## ✅ Checklist de Verificação

- [ ] Código atualizado (`git pull origin main`)
- [ ] PyMuPDF instalado e funcionando
- [ ] OpenAI instalado
- [ ] Serviço reiniciado e rodando
- [ ] Nginx configurado corretamente
- [ ] Aplicação responde na porta 8501
- [ ] Teste de upload funciona

## 🎯 O Que Foi Melhorado

### Interface de Importação:
- ✅ Interface mais limpa e direta
- ✅ Removidos passos intermediários desnecessários
- ✅ Barra de progresso durante processamento
- ✅ Métricas formatadas corretamente
- ✅ Tabela de edição melhorada
- ✅ Mensagens mais concisas
- ✅ Fluxo simplificado: Upload → IA → Revisão → Importação

### Experiência do Usuário:
- ✅ Menos cliques necessários
- ✅ Feedback visual em tempo real
- ✅ Informações mais claras
- ✅ Processo mais rápido

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
```

## 🐛 Se Algo Der Errado

1. **Serviço não inicia:**
   ```bash
   journalctl -u contabil.service -n 50
   ```

2. **Erro 502 Bad Gateway:**
   ```bash
   # Verifica se Streamlit está rodando
   systemctl status contabil.service
   curl http://127.0.0.1:8501
   
   # Verifica logs do nginx
   tail -50 /var/log/nginx/contabil_error.log
   ```

3. **Dependências faltando:**
   ```bash
   source /opt/contabil/venv/bin/activate
   pip install -r requirements.txt
   ```

## 🎉 Pronto!

Após executar os passos acima, a nova interface simplificada estará disponível em produção!

