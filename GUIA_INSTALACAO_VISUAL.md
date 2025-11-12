# 📸 Guia Visual de Instalação

## 🎯 Instalação em 3 Passos Simples

---

## Passo 1️⃣: Verificar Python

### Abra o Prompt de Comando:

1. Pressione `Windows + R`
2. Digite: `cmd`
3. Pressione Enter

### Digite o comando:
```
python --version
```

### Resultado Esperado:
```
Python 3.x.x
```

### ❌ Se aparecer erro "Python não encontrado":

**Instale o Python:**

1. Acesse: https://www.python.org/downloads/
2. Clique em "Download Python 3.x.x"
3. Execute o instalador
4. **⚠️ IMPORTANTE:** Marque ☑️ **"Add Python to PATH"**
5. Clique em "Install Now"
6. Aguarde instalação
7. Feche e abra o CMD novamente
8. Teste: `python --version`

---

## Passo 2️⃣: Instalar o Sistema

### Localize a pasta do sistema:
```
📁 contabil_system
   ├── 📄 install.bat      ← Este arquivo!
   ├── 📄 run.bat
   ├── 📁 pages
   ├── 📁 models
   └── ...
```

### Execute a instalação:

1. **Clique duas vezes** em: `install.bat`

2. Uma janela preta abrirá:
```
============================================================
  INSTALAÇÃO DO SISTEMA CONTÁBIL
============================================================

✓ Python encontrado
Python 3.x.x

📦 Criando ambiente virtual...
✓ Ambiente virtual criado

📥 Instalando dependências...
[Aguarde 2-5 minutos]
✓ Dependências instaladas

🗄️ Inicializando banco de dados...
✓ Banco de dados criado

📊 Carregando dados de teste (2 anos)...
✓ 5.239 transações criadas
✓ 623 contratos criados
...

============================================================
  ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!
============================================================

📋 CREDENCIAIS DE ACESSO:
   Admin:        admin / admin123
   Gerente:      gerente1 / gerente123
   Visualizador: viewer1 / viewer123

🚀 Para executar o sistema, use: run.bat

Pressione qualquer tecla para continuar...
```

3. Pressione qualquer tecla para fechar

---

## Passo 3️⃣: Executar o Sistema

### Sempre que quiser usar:

1. **Clique duas vezes** em: `run.bat`

2. Uma janela preta abrirá:
```
============================================================
  SISTEMA CONTÁBIL - Iniciando...
============================================================

✓ Iniciando Sistema Contábil...

🌐 O sistema abrirá automaticamente no navegador
📍 URL: http://localhost:8501

📋 Credenciais:
   Admin: admin / admin123

⚠️ Para parar o sistema, feche esta janela ou pressione Ctrl+C
============================================================
```

3. O navegador abrirá automaticamente

4. **Tela de Login:**
```
┌─────────────────────────────┐
│   🔐 Sistema Contábil       │
├─────────────────────────────┤
│   Usuário: [admin        ]  │
│   Senha:   [••••••••••••]   │
│   [      Entrar      ]      │
└─────────────────────────────┘
```

5. Digite:
   - **Usuário:** `admin`
   - **Senha:** `admin123`

6. Clique em **"Entrar"**

7. **Pronto!** Sistema funcionando! 🎉

---

## 🎮 Usando o Sistema

### Primeira Tela:
```
┌─────────────────────────────────────────┐
│ 📊 Sistema Contábil                     │
│ Usuário: admin                          │
│ Perfil: Admin                           │
├─────────────────────────────────────────┤
│ 🏢 Cliente                              │
│ [Empresa de Eventos Ltda [Eventos] ▼]  │
│ 📋 12.345.678/0001-90                   │
├─────────────────────────────────────────┤
│ Menu                                    │
│ 🏠 Início                               │
│                                         │
│ Dados                                   │
│ 📥 Importação                           │
│ 💳 Transações                           │
│ 📝 Contratos                            │
│ 💰 Contas                               │
│                                         │
│ Dashboards                              │
│ 📊 DRE                                  │
│ 💵 DFC                                  │
│ 📈 Sazonalidade                         │
│ 📑 Relatórios                           │
└─────────────────────────────────────────┘
```

### Selecionar Cliente:
1. Clique na lista suspensa de clientes
2. **Digite** para buscar (ex: "eventos")
3. Selecione o cliente
4. Navegue pelas páginas

### Explorar Dashboards:
1. Clique em **📊 DRE**
2. Veja receitas e despesas
3. Expanda "Detalhamento Completo"
4. Explore categorias e transações

---

## 🔄 Operações Comuns

### Iniciar o Sistema:
```
Clique 2x em: run.bat
```

### Parar o Sistema:
```
Feche a janela preta (CMD)
ou
Pressione Ctrl+C na janela
```

### Resetar Dados de Teste:
```
Clique 2x em: reset_data.bat
Digite: S
Aguarde
```

### Fazer Backup:
```
Copie a pasta: data/
Cole em local seguro
```

### Restaurar Backup:
```
Substitua a pasta: data/
pela pasta do backup
```

---

## 📊 Dados Incluídos

Após instalação, o sistema já vem com:

- ✅ **3 usuários** (admin, gerente, visualizador)
- ✅ **5 clientes** (Eventos, Consultoria, Serviços, Comércio, Indústria)
- ✅ **2 anos de dados** (nov/2023 a nov/2025)
- ✅ **5.239 transações** financeiras
- ✅ **623 contratos** e eventos
- ✅ **1.888 contas** a pagar/receber
- ✅ **Sazonalidade** realista

**Tudo pronto para explorar!**

---

## 💡 Dicas

### Para Melhor Experiência:

1. **Use navegadores modernos:**
   - Google Chrome (recomendado)
   - Microsoft Edge
   - Firefox

2. **Mantenha a janela CMD aberta:**
   - Não feche enquanto usa o sistema
   - É normal ficar aberta

3. **Acesse pelo endereço:**
   - http://localhost:8501
   - Salve nos favoritos

4. **Múltiplos usuários:**
   - Cada um pode abrir em seu navegador
   - Use o endereço de rede mostrado

---

## 🆘 Resolução de Problemas

### Problema: "Python não encontrado"
**Solução:**
1. Instale o Python
2. Marque "Add Python to PATH"
3. Reinicie o computador
4. Execute `install.bat` novamente

### Problema: "Erro ao instalar dependências"
**Solução:**
1. Clique com botão direito em `install.bat`
2. Escolha "Executar como administrador"
3. Aguarde instalação

### Problema: "Sistema não abre no navegador"
**Solução:**
1. Abra o navegador manualmente
2. Digite: http://localhost:8501
3. Pressione Enter

### Problema: "Porta 8501 já em uso"
**Solução:**
1. Feche todas as janelas CMD abertas
2. Execute `run.bat` novamente
3. Se persistir, reinicie o computador

### Problema: "Dados não aparecem"
**Solução:**
1. Execute `reset_data.bat`
2. Digite S para confirmar
3. Aguarde
4. Execute `run.bat`

---

## 📱 Compartilhar com Outros

### Para instalar em outro computador:

1. **Copie a pasta completa** `contabil_system`
2. Cole no outro computador
3. Execute `install.bat`
4. Pronto!

### Para compartilhar apenas dados:

1. Copie a pasta `data/`
2. Envie para o outro usuário
3. Ele substitui a pasta `data/` dele
4. Dados sincronizados!

---

## 🎓 Próximos Passos

Após instalar:

1. ✅ Faça login
2. ✅ Explore os 5 clientes de teste
3. ✅ Veja os dashboards (DRE, DFC, Sazonalidade)
4. ✅ Teste importar um arquivo CSV
5. ✅ Crie uma transação manual
6. ✅ Gere um relatório
7. ✅ Exporte para Excel

### Quando estiver pronto:

1. Crie seus próprios clientes
2. Importe seus dados reais
3. Delete os dados de teste (se quiser)
4. Altere as senhas padrão
5. Configure permissões de usuários

---

## 🎉 Pronto!

**Instalação fácil em 3 cliques:**
1. `install.bat` (primeira vez)
2. `run.bat` (sempre)
3. Login no navegador

**Sistema profissional sem complicação!** 🚀


