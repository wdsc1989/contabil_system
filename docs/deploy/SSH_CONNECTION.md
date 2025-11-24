# 🔐 Como Conectar na VPS via SSH

Este guia explica como conectar na sua VPS da Hostinger usando SSH.

## 📋 Informações Necessárias

Antes de conectar, você precisa ter:

1. **IP da VPS** - Fornecido pela Hostinger (ex: `72.61.56.204`)
2. **Usuário** - Geralmente `root` para acesso administrativo
3. **Senha** - Fornecida pela Hostinger no email de boas-vindas
4. **Porta SSH** - Padrão é `22` (geralmente não precisa especificar)

---

## 🪟 Método 1: PowerShell (Windows)

### Conexão Básica

```powershell
# Conecta na VPS
ssh root@72.61.56.204
```

**O que acontece:**
- Na primeira conexão, você verá uma mensagem sobre autenticidade do host
- Digite `yes` para continuar
- Digite a senha quando solicitado (a senha não aparece enquanto você digita)
- Após autenticar, você estará conectado!

### Exemplo Completo

```powershell
PS C:\Users\DELL\Documents\Projetos> ssh root@72.61.56.204
The authenticity of host '72.61.56.204 (72.61.56.204)' can't be established.
ED25519 key fingerprint is SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '72.61.56.204' (ED25519) to the list of known hosts.
root@72.61.56.204's password: [digite sua senha aqui]
Welcome to Ubuntu 24.04 LTS (GNU/Linux 6.x.x-generic x86_64)
...
root@vps:~# 
```

**✅ Pronto! Você está conectado!**

---

## 🔑 Método 2: Usando Chave SSH (Recomendado)

Usar chave SSH é mais seguro e não requer senha a cada conexão.

### Gerar Chave SSH no Windows

```powershell
# Gera uma nova chave SSH
ssh-keygen -t ed25519 -C "seu_email@exemplo.com"

# Pressione Enter para aceitar o local padrão (C:\Users\DELL\.ssh\id_ed25519)
# Digite uma senha para proteger a chave (ou deixe em branco)
```

### Copiar Chave para VPS

```powershell
# Copia a chave pública para a VPS
ssh-copy-id root@72.61.56.204

# Ou manualmente:
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh root@72.61.56.204 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### Conectar com Chave

```powershell
# Agora você pode conectar sem senha
ssh root@72.61.56.204
```

---

## 🖥️ Método 3: PuTTY (Interface Gráfica)

Se preferir uma interface gráfica:

### Download e Instalação

1. Baixe o PuTTY: https://www.putty.org/
2. Instale o programa

### Configuração

1. Abra o PuTTY
2. Preencha:
   - **Host Name (or IP address):** `72.61.56.204`
   - **Port:** `22`
   - **Connection type:** `SSH`
3. Clique em **Open**
4. Digite o usuário: `root`
5. Digite a senha quando solicitado

### Salvar Configuração

1. Configure a conexão como acima
2. Em **Saved Sessions**, digite um nome (ex: "Hostinger VPS")
3. Clique em **Save**
4. Na próxima vez, selecione a sessão salva e clique em **Load**

---

## 📱 Método 4: Terminal do Windows (CMD)

```cmd
ssh root@72.61.56.204
```

Funciona igual ao PowerShell.

---

## 🔧 Método 5: VS Code (Remote SSH)

Se você usa VS Code:

1. Instale a extensão **Remote - SSH**
2. Pressione `F1` ou `Ctrl+Shift+P`
3. Digite: `Remote-SSH: Connect to Host`
4. Digite: `root@72.61.56.204`
5. Digite a senha quando solicitado

Agora você pode editar arquivos diretamente na VPS!

---

## 🚨 Solução de Problemas

### Erro: "Connection refused"

**Causa:** SSH não está rodando ou porta bloqueada

**Solução:**
```bash
# Na VPS (se conseguir acessar de outra forma)
sudo systemctl status ssh
sudo systemctl start ssh
```

### Erro: "Permission denied (publickey)"

**Causa:** Senha incorreta ou chave SSH não configurada

**Solução:**
- Verifique se digitou a senha correta
- Ou configure chave SSH (veja Método 2)

### Erro: "Host key verification failed"

**Causa:** Chave do host mudou (normal após reinstalação)

**Solução:**
```powershell
# Remove a chave antiga
ssh-keygen -R 72.61.56.204

# Tenta conectar novamente
ssh root@72.61.56.204
```

### Esqueci a Senha

**Solução:**
1. Acesse o painel da Hostinger (hPanel)
2. Vá em **VPS** → **Gerenciar**
3. Procure por **Reset Password** ou **Redefinir Senha**
4. Uma nova senha será enviada por email

---

## 📝 Comandos Úteis Após Conectar

```bash
# Ver informações do sistema
uname -a
df -h  # Espaço em disco
free -h  # Memória
uptime  # Tempo online

# Navegar diretórios
cd /opt/contabil/contabil_system
ls -la

# Ver logs
journalctl -u contabil.service -f

# Sair da conexão
exit
```

---

## 🔒 Segurança

### Boas Práticas

1. **Use chave SSH** ao invés de senha
2. **Desabilite login root** (crie usuário específico)
3. **Configure firewall** (UFW)
4. **Mude a porta SSH** (opcional, mas recomendado)
5. **Use senhas fortes**

### Desabilitar Login Root (Avançado)

```bash
# Na VPS, crie um novo usuário
adduser seu_usuario
usermod -aG sudo seu_usuario

# Configure chave SSH para o novo usuário
# Depois edite /etc/ssh/sshd_config:
# PermitRootLogin no

# Reinicie SSH
sudo systemctl restart sshd
```

---

## 📚 Referências

- [Documentação SSH da Hostinger](https://www.hostinger.com.br/tutoriais/como-conectar-vps-ssh)
- [Guia SSH do Ubuntu](https://help.ubuntu.com/community/SSH)

---

## ✅ Checklist de Conexão

- [ ] Tenho o IP da VPS
- [ ] Tenho a senha ou chave SSH
- [ ] Testei conexão via `ssh root@IP`
- [ ] Configurei chave SSH (recomendado)
- [ ] Salvei configuração no PuTTY (se usar)

---

**🎉 Pronto! Agora você pode conectar na sua VPS!**

Para mais informações sobre deploy, veja: [HOSTINGER_DEPLOY.md](./HOSTINGER_DEPLOY.md)









