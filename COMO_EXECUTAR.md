# Guia de Execução - Slide Missa Web

## ✅ Opção 1: Com Docker (RECOMENDADO)

### Pré-requisitos
- Docker Desktop instalado e rodando
- Windows 10+, macOS ou Linux

### Passos
1. Abra PowerShell / Terminal na pasta `slideMissa-web`
2. Execute:
   ```bash
   docker-compose up
   ```
3. Aguarde (vai instalar tudo na primeira vez ~ 2-3 minutos)
4. Acesse: **http://localhost:5173**
5. Backend Swagger docs: **http://localhost:8000/docs**

**Parar:** Pressione `Ctrl+C` no terminal

**Limpar containers:** 
```bash
docker-compose down
```

---

## 🔧 Opção 2: Local (SEM Docker)

### Pré-requisitos
- Python 3.9+ instalado
- Node.js 16+ instalado
- Git (opcional)

### Backend (FastAPI)

```bash
# 1. Entrar na pasta backend
cd backend

# 2. Criar ambiente virtual
python -m venv venv

# 3. Ativar ambiente virtual
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (CMD):
venv\Scripts\activate.bat

# Mac/Linux:
source venv/bin/activate

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Rodar servidor
uvicorn main:app --reload
```

✅ Backend rodando em **http://localhost:8000**

Teste a API: **http://localhost:8000/docs** (Swagger interativo)

---

### Frontend (React + Vite)

**Em OUTRO terminal/PowerShell:**

```bash
# 1. Entrar na pasta frontend
cd frontend

# 2. Instalar dependências
npm install

# 3. Rodar dev server
npm run dev
```

✅ Frontend rodando em **http://localhost:5173**

---

## 🚀 Acessar a Aplicação

### Via Docker
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **Docs da API**: http://localhost:8000/docs

### Via Local
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000/api
- **Docs da API**: http://localhost:8000/docs

---

## 📝 Como Usar

### Aba: Gerar via TXT

1. **Selecione arquivo de cantos** (.txt)
   - Formato: `[TITULO DO CANTO]` seguido de linhas com `*` (negrito)
   
2. **Selecione ritual** (.pptx)
   - Deve conter placeholders com títulos

3. **Informe nome de saída**
   - Ex: `missa_pronta`

4. **Clique em "Gerar Apresentação"**
   - Download automático do PPTX gerado
   - Cantos são salvos automaticamente no banco

### Aba: Banco de Cantos

1. **Filtrar por posição** (opcional)
   - Ex: "CANTO DE ENTRADA"

2. **Selecionar cantos** (múltiplos com Ctrl+clique)

3. **Selecionar ritual** (.pptx)

4. **Clicar em "Gerar com X selecionados"**
   - Download automático

---

## 🛠️ Troubleshooting

### Docker não inicia
```bash
# Verificar se Docker está rodando
docker ps

# Se não funcionar, reinicie Docker Desktop
```

### Backend: "Address already in use"
- Porta 8000 já está em uso
- Mudar em `main.py`: `uvicorn.run(app, host="0.0.0.0", port=8001)`

### Frontend: "Cannot find module 'react'"
```bash
cd frontend
npm install
```

### Banco de dados não foi criado
- Criar primeiro arquivo via TXT (auto-cria)
- Pasta `backend/banco/` deve existir
- Verificar permissões de escrita

---

## 📂 Estrutura de Arquivos

```
slideMissa-web/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── servicos/
│   │   ├── gerar_missa.py      # (reutilizado)
│   │   └── banco.py            # (reutilizado)
│   ├── banco/                  # SQLite (criado automaticamente)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   ├── hooks/
│   │   └── api.js
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── docker-compose.yml
├── README.md
└── INICIAR.bat (Windows)
```

---

## 🔌 Endpoints da API

### `POST /api/gerar`
- Upload TXT + PPTX
- Retorna PPTX gerado

### `GET /api/banco/listar`
- Lista cantos do banco
- Parâmetro: `?posicao=...` (opcional)

### `GET /api/banco/posicoes`
- Retorna posições disponíveis

### `POST /api/gerar-do-banco`
- Gera usando cantos do banco

### `DELETE /api/banco/{id}`
- Remove um canto

---

## 📞 Suporte

Se encontrar problemas:
1. Verificar logs do container: `docker-compose logs backend`
2. Testar API: `curl http://localhost:8000/api/health`
3. Limpar cache do navegador (F12 → Storage → Clear)
