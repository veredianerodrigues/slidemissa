# Slide Missa Web - Estrutura de Projeto

## 📦 Arquitetura

```
slideMissa-web/
│
├── 📁 backend/                          # FastAPI Backend
│   ├── 📄 main.py                       # App principal + rotas
│   ├── 📄 requirements.txt              # Dependências Python
│   ├── 📄 Dockerfile                    # Docker build backend
│   ├── 📄 .dockerignore
│   │
│   └── 📁 servicos/                    # Lógica de negócio
│       ├── 📄 gerar_missa.py           # Parse TXT + create slides
│       ├── 📄 banco.py                 # SQLite operations
│       └── 📄 __init__.py
│
├── 📁 frontend/                        # React + Vite
│   ├── 📄 package.json                 # Dependências Node
│   ├── 📄 vite.config.js               # Configuração Vite
│   ├── 📄 index.html                   # Entry point HTML
│   ├── 📄 .gitignore
│   │
│   └── 📁 src/                         # Código React
│       ├── 📄 main.jsx                 # ReactDOM.render
│       ├── 📄 App.jsx                  # App principal + abas
│       ├── 📄 App.css                  # Estilos globais
│       ├── 📄 index.css
│       │
│       ├── 📄 api.js                   # Chamadas HTTP axios
│       │
│       ├── 📁 components/              # React components
│       │   ├── 📄 Gerar.jsx            # Aba "Gerar via TXT"
│       │   ├── 📄 Gerar.css
│       │   ├── 📄 Banco.jsx            # Aba "Banco de Cantos"
│       │   └── 📄 Banco.css
│       │
│       └── 📁 hooks/                   # Custom React hooks
│           └── 📄 useApi.js            # Hook para chamadas API
│
├── 📄 docker-compose.yml               # Orquestração containers
├── 📄 INICIAR.bat                      # Script start (Docker)
├── 📄 INICIAR_LOCAL.bat                # Script start (Local)
├── 📄 COMO_EXECUTAR.md                 # Instruções passo-a-passo
├── 📄 README.md                        # Documentação completa
└── 📄 .gitignore                       # Git ignore
```

---

## 🔄 Fluxo de Requisição

### Gerar via TXT

```
Usuario seleciona arquivos (TXT + PPTX)
        ↓
Form React → Gerar.jsx
        ↓
fetch POST /api/gerar (FormData)
        ↓
FastAPI main.py::gerar_apresentacao()
        ↓
gerar_missa.gerar(txt, pptx, output)
        ↓
banco.salvar_canto() [auto-salva]
        ↓
Return: pptx blob
        ↓
Frontend: downloadFile()
```

### Gerar via Banco

```
Usuario seleciona cantos do banco
        ↓
Banco.jsx → fetch GET /api/banco/listar
        ↓
FastAPI: retorna lista de cantos
        ↓
Usuario seleciona subset e clica "Gerar"
        ↓
fetch POST /api/gerar-do-banco
        ↓
FastAPI::gerar_do_banco()
        ↓
banco.carregar_blocos() x N chaves
        ↓
gerar_missa.gerar_do_banco()
        ↓
Return: pptx blob
        ↓
downloadFile()
```

---

## 🔌 Endpoints Principais

| Método | Path | Função |
|--------|------|--------|
| POST | `/api/gerar` | Gera PPTX from TXT |
| GET | `/api/banco/listar` | List cantos |
| GET | `/api/banco/posicoes` | Get posições filter |
| POST | `/api/gerar-do-banco` | Gera PPTX from banco |
| DELETE | `/api/banco/{id}` | Delete canto |
| GET | `/api/health` | Health check |

---

## 📊 Estado (State) no Frontend

### Componente: Gerar
```javascript
{
  txtFile: File | null,
  pptxFile: File | null,
  nomeSaida: "missa_pronta",
  log: ["msg1", "msg2"],
  loading: boolean,
  error: string | null
}
```

### Componente: Banco
```javascript
{
  posicoes: ["CANTO DE ENTRADA", ...],
  filtro: "Todas",
  cantos: [
    {
      id: 1,
      posicao: "CANTO DE ENTRADA",
      nome: "Eu venho",
      chave: "CANTO DE ENTRADA — Eu venho",
      criado_em: "2024-01-15 10:30:00"
    }, ...
  ],
  selecionados: Set(["chave1", "chave2"]),
  pptxFile: File | null,
  nomeSaida: "missa_pronta",
  log: [],
  loading: boolean,
  error: string | null
}
```

---

## 🗄️ Banco de Dados (SQLite)

```
cantos.db (backend/banco/)
│
└── TABLE cantos
    ├── id (INTEGER PRIMARY KEY)
    ├── posicao (TEXT) - "CANTO DE ENTRADA"
    ├── nome (TEXT) - "Eu venho"
    ├── chave (TEXT UNIQUE) - "CANTO DE ENTRADA — Eu venho"
    ├── blocos (TEXT JSON) - [{"lines": [...], "bold": bool}, ...]
    ├── criado_em (TEXT)
    └── atualizado_em (TEXT)

INDEX: idx_posicao on (posicao)
```

---

## 🚀 Ciclo de Build

### Docker Compose
```yaml
# backend service
├── Build: Dockerfile → python:3.11-slim
├── Install: requirements.txt
├── Port: 8000
├── Volume: ./backend → /app
└── CMD: uvicorn main:app --reload

# frontend service
├── Image: node:20-alpine
├── Install: npm install
├── Port: 5173
├── Volume: ./frontend → /app
└── CMD: npm run dev
```

### Frontend Build (Produção)
```bash
npm run build
# Output: frontend/dist/
# Static files ready for CDN/S3
```

---

## 🔒 Segurança (Local Dev)

- ✅ CORS permitido de `*` (apenas dev)
- ✅ Sem autenticação (MVP local)
- ⚠️ Mudar em produção:
  - [ ] CORS restrito
  - [ ] Auth (JWT/OAuth)
  - [ ] HTTPS
  - [ ] Validação de entrada

---

## 📈 Performance

### Frontend
- Vite: ~300ms dev
- React.StrictMode ativado
- Sem otimizações especiais (MVP)

### Backend
- FastAPI: ~50ms por requisição
- SQLite: OK para < 1000 cantos
- Sem cache (MVP)

---

## 🎯 Próximas Etapas

### Fase 3: Database
- [ ] Migrar para PostgreSQL
- [ ] Criar migrations (Alembic)
- [ ] Adicionar índices

### Fase 4: Deploy
- [ ] CI/CD (GitHub Actions)
- [ ] Docker Compose produção
- [ ] Deploy (Azure/Heroku)
- [ ] Monitoramento

### Features
- [ ] Autenticação
- [ ] Upload DOCX → TXT
- [ ] Histórico gerações
- [ ] Testes (pytest, Vitest)
- [ ] Dark mode

---

## 📝 Checklist de Desenvolvimento

- [x] Backend FastAPI
- [x] Frontend React
- [x] Docker Compose (dev)
- [x] Documentação
- [ ] Testes unitários
- [ ] Testes integração
- [ ] E2E tests
- [ ] Performance tunning

