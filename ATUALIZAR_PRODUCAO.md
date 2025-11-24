# 🚀 Atualizar em Produção - Guia Rápido

> **📖 Para comandos detalhados, veja:** `COMANDOS_ATUALIZACAO.md`

## 📋 Passos para Atualizar na VPS

### 1. Conectar na VPS via SSH

```bash
ssh root@seu-ip-ou-dominio
```

### 2. Ir para o diretório da aplicação

```bash
cd /opt/contabil
```

### 3. Executar Script de Deploy Automático (RECOMENDADO)

```bash
# Garante que o script tem permissão de execução
chmod +x deploy/deploy.sh

# Executa o deploy
./deploy/deploy.sh
```

O script irá:
- ✅ Fazer `git pull` das atualizações
- ✅ Instalar/atualizar dependências Python
- ✅ Verificar e instalar PyMuPDF
- ✅ Verificar poppler-utils (para pdf2image)
- ✅ Executar migrações do banco
- ✅ Reiniciar o serviço
- ✅ Verificar se tudo está funcionando

### 4. Verificar se a Atualização Funcionou

```bash
# Ver status do serviço
systemctl status contabil.service

# Ver logs recentes
journalctl -u contabil.service -n 50

# Verificar se está respondendo
curl -I http://127.0.0.1:8501
```

### 5. Se Houver Problemas

#### Problema: Erro de permissão no script
```bash
chmod +x deploy/deploy.sh
chmod +x deploy/*.sh
```

#### Problema: Conflito no Git
```bash
# O script já faz stash automático, mas se precisar:
git stash
git pull origin main
```

#### Problema: PyMuPDF não instalado
```bash
source /opt/contabil/venv/bin/activate
pip install PyMuPDF>=1.23.0
python -c "import fitz; print('OK')"
```

#### Problema: Serviço não inicia
```bash
# Ver logs detalhados
journalctl -u contabil.service -n 100

# Reiniciar manualmente
systemctl restart contabil.service
```

## 🔍 Verificação Pós-Deploy

Execute o diagnóstico completo:

```bash
bash deploy/check_service.sh
```

## 📝 Comandos Úteis

```bash
# Ver logs em tempo real
journalctl -u contabil.service -f

# Reiniciar serviço
systemctl restart contabil.service

# Verificar dependências
source /opt/contabil/venv/bin/activate
python -c "import fitz, openai, pdfplumber; print('✅ Todas OK')"
```

## ✅ Checklist

- [ ] Código atualizado (`git pull` executado)
- [ ] Dependências instaladas
- [ ] PyMuPDF funcionando
- [ ] Serviço rodando (`systemctl status contabil.service`)
- [ ] Aplicação respondendo (teste no navegador)
- [ ] Sem erros nos logs

## 🎯 Próximos Passos

Após o deploy, teste:
1. Acessar a aplicação no navegador
2. Fazer login
3. Testar importação de um arquivo pequeno (CSV/Excel)
4. Testar importação de PDF
5. Verificar se a classificação com IA está funcionando

---

**Nota:** O script `deploy.sh` já trata a maioria dos problemas automaticamente. Use-o sempre que possível!

