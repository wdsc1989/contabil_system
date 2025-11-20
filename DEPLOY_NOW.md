# 🚀 Deploy Rápido - Executar Agora

## ✅ Status: Código commitado e enviado para o GitHub

O código foi commitado e enviado para o repositório. Agora você precisa executar o deploy na VPS.

---

## 📋 Passos para Deploy

### 1️⃣ Conectar na VPS

No PowerShell do Windows, execute:

```powershell
ssh root@72.61.56.204
```

Digite a senha quando solicitado.

---

### 2️⃣ Executar Script de Deploy

Após conectar na VPS, execute:

```bash
cd /opt/contabil/contabil_system
bash deploy/deploy.sh
```

O script irá:
- ✅ Fazer `git pull` para atualizar o código
- ✅ Instalar/atualizar dependências Python
- ✅ Executar migrações do banco de dados (criar nova tabela `client_report_configs`)
- ✅ Reiniciar o serviço Streamlit
- ✅ Verificar se está funcionando

---

### 3️⃣ Verificar se Funcionou

```bash
# Ver status do serviço
systemctl status contabil.service

# Ver logs em tempo real
journalctl -u contabil.service -f

# Verificar se a aplicação está respondendo
curl http://localhost:8501
```

---

### 4️⃣ Acessar a Aplicação

Abra no navegador:
- **HTTP:** `http://72.61.56.204`
- **HTTPS:** `https://72.61.56.204` (se SSL estiver configurado)

---

## 🔍 O que foi adicionado nesta versão

1. **Nova tabela:** `client_report_configs` - Configuração de relatórios por cliente
2. **Novas páginas:**
   - `13_Aplicacoes_Financeiras.py` - Gestão de aplicações financeiras
   - `14_Maquina_Cartao.py` - Gestão de extratos de máquina de cartão
   - `15_Estoque.py` - Gestão de controle de estoque
3. **Novo serviço:** `ReportConfigService` - Gerencia configurações de relatórios
4. **Atualizações:**
   - Página de Gestão de Clientes com configuração de relatórios
   - Páginas DRE, DFC e Sazonalidade agora respeitam configurações do cliente
   - Navegação atualizada com links para novas páginas

---

## ⚠️ Importante

- O script de deploy criará automaticamente a nova tabela no banco de dados
- Configurações padrão serão criadas para todos os clientes existentes (todos os tipos habilitados)
- Se houver erro, verifique os logs: `journalctl -u contabil.service -n 50`

---

## 🆘 Problemas?

Se algo der errado:

1. **Ver logs:**
   ```bash
   journalctl -u contabil.service -n 100
   ```

2. **Verificar banco de dados:**
   ```bash
   sudo -u postgres psql -d contabil_db -c "\dt" | grep client_report_configs
   ```

3. **Reiniciar serviço manualmente:**
   ```bash
   systemctl restart contabil.service
   ```

4. **Verificar se o código foi atualizado:**
   ```bash
   cd /opt/contabil/contabil_system
   git log -1
   ```

---

**✅ Pronto! Execute os comandos acima para fazer o deploy.**

