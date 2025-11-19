# 📁 Organização do Projeto Sistema Contábil

Este documento descreve a organização e estrutura do projeto após a reorganização.

## ✅ Arquivos na Raiz (Apenas Essenciais)

A raiz do projeto contém **apenas** os arquivos necessários para o funcionamento:

- `app.py` - Aplicação principal do Streamlit
- `init_db.py` - Script de inicialização do banco de dados
- `run.bat` - Script de execução (Windows)
- `install.bat` - Instalador automático
- `reset_data.bat` - Resetar dados de teste
- `build_exe.bat` - Criar executável
- `requirements.txt` - Dependências do projeto
- `README.md` - Documentação principal do projeto
- `.gitignore` - Configuração do Git

## 📚 Documentação Organizada em `docs/`

Toda a documentação adicional foi organizada em subpastas dentro de `docs/`:

### 📘 Tutoriais (`docs/tutoriais/`)
- Tutoriais completos do sistema
- Tutoriais com imagens
- Versões PDF dos tutoriais

### 📗 Guias (`docs/guias/`)
- Guias de instalação (fácil, completa, visual)
- Guia de início rápido (QUICKSTART)
- Guias de uso específicos

### 🔧 Desenvolvimento (`docs/desenvolvimento/`)
- Status do projeto
- Resumos de implementação
- Documentação técnica
- Melhorias e atualizações

### 📦 Distribuição (`docs/distribuicao/`)
- Guia de distribuição
- Documentação para versão executável

### 📸 Screenshots (`docs/screenshots/`)
- Imagens das telas do sistema
- Documentação dos screenshots

## 🔧 Scripts Organizados em `scripts/`

Scripts auxiliares foram movidos para `scripts/`:

- `scripts/build_exe_spec.py` - Especificação para build
- `scripts/SistemaContabil.spec` - Configuração PyInstaller
- `scripts/auxiliares/` - Scripts de desenvolvimento
  - `capture_screenshots.py` - Captura de screenshots
  - `generate_pdf_tutorial*.py` - Geração de PDFs

## 🗂️ Estrutura Completa

```
contabil_system/
├── 📄 Arquivos Essenciais (Raiz)
│   ├── app.py
│   ├── init_db.py
│   ├── run.bat
│   ├── install.bat
│   ├── reset_data.bat
│   ├── build_exe.bat
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
│
├── 📁 Código Fonte
│   ├── config/          # Configurações
│   ├── models/          # Modelos de dados
│   ├── services/        # Serviços de negócio
│   ├── pages/           # Páginas do Streamlit
│   └── utils/           # Utilitários
│
├── 📚 Documentação
│   └── docs/            # Toda documentação organizada
│       ├── README.md    # Índice
│       ├── tutoriais/
│       ├── guias/
│       ├── desenvolvimento/
│       ├── distribuicao/
│       └── screenshots/
│
├── 🔧 Scripts
│   └── scripts/         # Scripts auxiliares
│       └── auxiliares/
│
├── 🧪 Testes
│   └── tests/           # Testes e dados de exemplo
│
└── 📦 Dados e Build
    ├── data/            # Banco de dados
    ├── build/           # Arquivos de build
    └── dist/            # Executável gerado
```

## 🎯 Benefícios da Organização

1. **Raiz Limpa**: Apenas arquivos essenciais na raiz, facilitando navegação
2. **Documentação Centralizada**: Toda documentação organizada por categoria
3. **Fácil Manutenção**: Estrutura clara e lógica
4. **Melhor Versionamento**: Arquivos de documentação separados do código
5. **Profissional**: Estrutura padrão de projetos Python/Streamlit
6. **Escalável**: Fácil adicionar nova documentação nas categorias apropriadas

## 📝 Notas

- Os arquivos de dados (`data/`, `build/`, `dist/`) são ignorados pelo Git (via `.gitignore`)
- Arquivos de exemplo estão em `tests/sample_files/` para referência
- A documentação principal (`README.md`) permanece na raiz para visibilidade no GitHub
- Scripts de uso comum (run.bat, install.bat) permanecem na raiz para fácil acesso

## 🔄 Próximos Passos

Ao adicionar nova documentação:
- Coloque em `docs/` na subpasta apropriada
- Atualize `docs/README.md` com o novo documento
- Mantenha apenas `README.md` na raiz

Ao adicionar novos scripts:
- Scripts de uso comum: mantenha na raiz
- Scripts auxiliares: coloque em `scripts/auxiliares/`
- Scripts de build: coloque em `scripts/`

---

**Data da Organização**: 2025-01-XX
**Versão**: 1.0






