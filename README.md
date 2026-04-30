# Slide Missa - Versão Web

Transformação da aplicação desktop (Tkinter) para web com **FastAPI + React + Docker**.

## 🚀 Estrutura do Projeto

```
slideMissa-web/
├── backend/                    # FastAPI (Python)
│   ├── main.py                # App principal
│   ├── servicos/
│   │   ├── gerar_missa.py     # Lógica de geração (reutilizada)
│   │   └── banco.py           # Banco de cantos (reutilizado)
│   ├── banco/                 # Pasta de dados (SQLite)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # React + Vite
│   ├── src/
│   │   ├── App.jsx            # App principal
│   │   ├── components/
│   │   │   ├── Gerar.jsx      # Abas de geração
│   │   │   └── Banco.jsx      # Abas de banco
│   │   ├── hooks/
│   │   │   └── useApi.js      # Custom hook para API
│   │   ├── api.js             # Funções da API
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── docker-compose.yml         # Orquestração local
└── README.md
```

---

## ⚡ Quick Start (Com Docker)

### Pré-requisitos
- **Docker** e **Docker Compose** instalados
- Windows 10+, macOS ou Linux

### 1. Clone/prepare o projeto
```bash
cd slideMissa-web
```

### 2. Inicie com Docker Compose
```bash
docker-compose up
```

Isso vai:
- ✅ Instalar dependências Python (FastAPI, python-pptx)
- ✅ Instalar dependências Node (React, Vite)
- ✅ Iniciar backend em http://localhost:8000
- ✅ Iniciar frontend em http://localhost:5173

### 3. Acesse no navegador
```
http://localhost:5173
```

### Parar os containers
```bash
docker-compose down
```

---

## 📝 Setup Local (Sem Docker)

### Backend (FastAPI)

**Pré-requisitos**: Python 3.9+, pip

```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Rodar servidor
uvicorn main:app --reload
```

Backend roda em **http://localhost:8000**

API docs: **http://localhost:8000/docs** (Swagger)

---

### Frontend (React + Vite)

**Pré-requisitos**: Node.js 16+, npm

```bash
cd frontend

# Instalar dependências
npm install

# Rodar dev server
npm run dev
```

Frontend roda em **http://localhost:5173**

---

## 🔌 Endpoints da API

### Gerar Apresentação (TXT + PPTX)
```
POST /api/gerar
Body: form-data
  - txt: arquivo .txt
  - pptx: arquivo .pptx
  - nome_saida: string (ex: "missa_pronta")
Response: blob (arquivo .pptx)
```

### Listar Cantos do Banco
```
GET /api/banco/listar?posicao=CANTO%20DE%20ENTRADA
Response: { cantos: [...] }
```

### Obter Posições Disponíveis
```
GET /api/banco/posicoes
Response: { posicoes: ["CANTO DE ENTRADA", ...] }
```

### Gerar do Banco
```
POST /api/gerar-do-banco
Body: form-data
  - pptx: arquivo .pptx
  - chaves[]: lista de chaves de cantos (ex: ["CANTO DE ENTRADA — Eu venho"])
  - nome_saida: string
Response: blob (arquivo .pptx)
```

### Deletar Canto
```
DELETE /api/banco/{canto_id}
Response: { message: "Canto deletado com sucesso" }
```

### Health Check
```
GET /api/health
Response: { status: "ok" }
```

---

## 🛠️ Mudanças da Desktop para Web

| Aspecto | Desktop | Web |
|--------|---------|-----|
| **Interface** | Tkinter | React (SPA) |
| **Upload** | filedialog | Drag-and-drop / input |
| **Download** | Salva local | HTTP blob response |
| **Database** | SQLite local | SQLite server + backend |
| **Backend** | N/A | FastAPI |
| **Lógica PPTX** | ✓ Reutilizada | ✓ Reutilizada |
| **Lógica Banco** | ✓ Reutilizada | ✓ Reutilizada |

---

## 📂 Fluxo de Dados

### Geração via TXT

```
Frontend (React)
    ↓ (upload txt + pptx)
Backend (FastAPI)
    ↓ (recebe, salva em temp)
gerar_missa.parse_txt()
    ↓
Presentation(pptx).slides
    ↓ (cria novos slides com cantos)
banco.salvar_canto() (auto-salva)
    ↓
output.pptx
    ↓ (retorna como blob)
Frontend (download)
```

### Geração via Banco

```
Frontend (React)
    ↓ (seleciona cantos + pptx)
Backend (/gerar-do-banco)
    ↓
banco.carregar_blocos() x N
    ↓
gerar_missa.gerar_do_banco()
    ↓
output.pptx
    ↓ (retorna como blob)
Frontend (download)
```

---

## 🔧 Troubleshooting

### Backend não conecta
```bash
# Verificar se FastAPI está rodando
curl http://localhost:8000/api/health

# Verificar logs do container
docker-compose logs backend
```

### Frontend não conecta ao backend
- Confirmar que backend está em `http://localhost:8000`
- Verificar CORS em `backend/main.py`
- Limpar cache do navegador

### Banco de dados (cantos.db) não foi criado
- Backend cria automaticamente em `backend/banco/cantos.db`
- Verificar permissões de escrita na pasta

---

## 📦 Build para Produção

### Frontend
```bash
cd frontend
npm run build
# Gera dist/ pronto para deploy
```

### Docker (Production)
```bash
docker-compose -f docker-compose.prod.yml up
```

---

## 🚀 Deploy

### Opções:
1. **Azure App Service** - Recomendado
2. **Heroku** - Simples
3. **DigitalOcean** - Barato
4. **AWS ECS** - Escala

Vide `DEPLOY.md` (a ser criado).

---

## 📝 Próximas Fases

- [ ] Fase 3: Integração com PostgreSQL
- [ ] Fase 4: Deploy + CI/CD
- [ ] Autenticação de usuários
- [ ] Upload de DOCX para TXT
- [ ] Histórico de gerações
- [ ] Testes automatizados

---

## 📄 Licença

Reutiliza a lógica da aplicação desktop original.

---

## 👤 Suporte

Para dúvidas, abra uma issue no repositório.
