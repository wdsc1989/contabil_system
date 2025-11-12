# Guia de Instalação - Sistema Contábil

## Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Passo a Passo

### 1. Navegue até o diretório do projeto

```bash
cd C:\Users\DELL\Documents\Projetos\Contabil\contabil_system
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
```

### 3. Ative o ambiente virtual

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Inicialize o banco de dados

```bash
python init_db.py
```

### 6. Popule com dados de teste

```bash
python tests/seed_data.py --reset
```

Este comando irá:
- Criar usuários de teste
- Criar 3 clientes
- Gerar 2 anos de dados financeiros
- Criar grupos e subgrupos
- Gerar transações, contratos e contas

### 7. Execute a aplicação

```bash
streamlit run app.py
```

A aplicação estará disponível em: `http://localhost:8501`

## Credenciais de Acesso

Após o seed, use:

- **Admin**: `admin` / `admin123`
- **Gerente**: `gerente1` / `gerente123`
- **Visualizador**: `viewer1` / `viewer123`

## Estrutura de Diretórios

```
contabil_system/
├── app.py                      # Aplicação principal
├── init_db.py                  # Script de inicialização do BD
├── requirements.txt            # Dependências
├── README.md                   # Documentação
├── INSTALL.md                  # Este arquivo
├── config/                     # Configurações
│   ├── database.py
│   └── __init__.py
├── models/                     # Modelos de dados
│   ├── user.py
│   ├── client.py
│   ├── group.py
│   ├── transaction.py
│   ├── contract.py
│   ├── account.py
│   └── __init__.py
├── services/                   # Lógica de negócio
│   ├── auth_service.py
│   ├── import_service.py
│   ├── parser_service.py
│   ├── report_service.py
│   └── __init__.py
├── pages/                      # Páginas do Streamlit
│   ├── 1_Gestao_Clientes.py
│   ├── 2_Importacao_Dados.py
│   ├── 3_Contratos.py
│   ├── 4_Contas.py
│   ├── 5_DRE.py
│   ├── 6_DFC.py
│   ├── 7_Sazonalidade.py
│   ├── 8_Relatorios.py
│   └── 9_Admin.py
├── utils/                      # Utilitários
│   ├── validators.py
│   ├── formatters.py
│   ├── column_mapper.py
│   └── __init__.py
├── tests/                      # Testes e dados
│   ├── seed_data.py
│   ├── TESTING_GUIDE.md
│   └── sample_files/
└── data/                       # Banco de dados (criado automaticamente)
    └── contabil.db
```

## Solução de Problemas

### Erro: "No module named 'streamlit'"

**Solução:** Certifique-se de que o ambiente virtual está ativado e execute:
```bash
pip install -r requirements.txt
```

### Erro: "Unable to open database file"

**Solução:** Execute o script de inicialização:
```bash
python init_db.py
```

### Erro: "Import error" ou "Module not found"

**Solução:** Verifique se está no diretório correto:
```bash
cd C:\Users\DELL\Documents\Projetos\Contabil\contabil_system
```

### Aplicação não abre no navegador

**Solução:** Abra manualmente: `http://localhost:8501`

### Dados não aparecem

**Solução:** Execute o seed novamente:
```bash
python tests/seed_data.py --reset
```

## Comandos Úteis

### Limpar e recriar banco de dados
```bash
python tests/seed_data.py --reset
```

### Adicionar mais dados sem limpar
```bash
python tests/seed_data.py
```

### Atualizar dependências
```bash
pip install -r requirements.txt --upgrade
```

### Desativar ambiente virtual
```bash
deactivate
```

## Próximos Passos

1. Faça login com uma das credenciais fornecidas
2. Selecione um cliente na sidebar
3. Explore os dashboards e funcionalidades
4. Consulte o `tests/TESTING_GUIDE.md` para cenários de teste

## Suporte

Para mais informações:
- Consulte o `README.md`
- Veja o `tests/TESTING_GUIDE.md`
- Verifique o plano de desenvolvimento: `sistema-cont-bil-streamlit.plan.md`


