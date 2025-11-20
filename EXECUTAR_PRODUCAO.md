# 🚀 Guia de Execução em Produção

Este guia contém os passos exatos para executar as atualizações em produção.

---

## 📋 Passo 1: Conectar ao Servidor

```bash
ssh usuario@seu-servidor
```

---

## 📋 Passo 2: Navegar até o Diretório da Aplicação

```bash
cd /opt/contabil
```

---

## 📋 Passo 3: Ativar Ambiente Virtual

```bash
source venv/bin/activate
```

---

## 📋 Passo 4: Atualizar Código do Repositório

```bash
git fetch origin
git pull origin main
```

**Verificar commit:**
```bash
git log -1 --oneline
```

---

## 📋 Passo 5: Instalar/Atualizar Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 📋 Passo 6: Executar Migrações do Banco (se necessário)

```bash
# Verificar e executar migrações
bash scripts/run_migrations.sh
```

---

## 📋 Passo 7: Recriar Usuário Admin

**IMPORTANTE:** Execute este passo para garantir que o usuário admin tenha role 'admin' e senha 'admin123':

```bash
python3 scripts/recreate_admin_user.py
```

**Saída esperada:**
```
======================================================================
👤 RECRIAR/ATUALIZAR USUÁRIO ADMIN
======================================================================

✅ Arquivo .env carregado: /opt/contabil/.env
🔄 Verificando inicialização do banco de dados...
✅ Banco de dados inicializado

📋 Usuário admin encontrado. Atualizando...
   ID: 1
   Email atual: admin@contabil.com
   Role atual: admin

✅ Usuário admin atualizado com sucesso!

📋 Credenciais:
   Usuário: admin
   Senha: admin123
   Role: admin
   Email: admin@contabil.com

⚠️  IMPORTANTE: Altere a senha após o primeiro acesso!

======================================================================
✅ Operação concluída com sucesso!
======================================================================
```

---

## 📋 Passo 8: Reiniciar Serviço

```bash
sudo systemctl restart contabil.service
```

---

## 📋 Passo 9: Verificar Status do Serviço

```bash
sudo systemctl status contabil.service
```

**Verificar logs:**
```bash
sudo journalctl -u contabil.service -n 50 --no-pager
```

---

## 📋 Passo 10: Testar Aplicação

```bash
# Verificar se está respondendo
curl -I http://localhost:8501

# Ou acessar via navegador
# http://seu-servidor:8501
```

---

## 🔍 Verificação Final

1. **Acesse a aplicação** no navegador
2. **Faça login** com:
   - Usuário: `admin`
   - Senha: `admin123`
3. **Verifique** se consegue acessar todas as funcionalidades
4. **Teste o agente IA** - deve exibir apenas texto formatado, sem gráficos complexos

---

## ⚠️ Troubleshooting

### Erro ao executar recreate_admin_user.py

Se houver erro, verifique:

1. **Arquivo .env existe:**
   ```bash
   ls -la /opt/contabil/.env
   ```

2. **Variáveis de ambiente estão corretas:**
   ```bash
   cat /opt/contabil/.env | grep DATABASE_URL
   ```

3. **Conexão com banco funciona:**
   ```bash
   python3 scripts/verificar_env.py
   ```

### Serviço não inicia

```bash
# Ver logs detalhados
sudo journalctl -u contabil.service -n 100 --no-pager

# Verificar se porta está em uso
sudo netstat -tlnp | grep 8501
```

### Erro de permissões

```bash
# Verificar propriedade dos arquivos
ls -la /opt/contabil/

# Corrigir se necessário
sudo chown -R contabil:contabil /opt/contabil
```

---

## 📝 Comandos Rápidos (Copy & Paste)

```bash
# Sequência completa de deploy
cd /opt/contabil && \
source venv/bin/activate && \
git pull origin main && \
pip install -r requirements.txt && \
bash scripts/run_migrations.sh && \
python3 scripts/recreate_admin_user.py && \
sudo systemctl restart contabil.service && \
sudo systemctl status contabil.service
```

---

## ✅ Checklist de Deploy

- [ ] Código atualizado (git pull)
- [ ] Dependências instaladas
- [ ] Migrações executadas
- [ ] Usuário admin recriado/atualizado
- [ ] Serviço reiniciado
- [ ] Status do serviço verificado
- [ ] Aplicação respondendo
- [ ] Login funcionando
- [ ] Agente IA testado

---

**Pronto! Sistema atualizado em produção! 🎉**

