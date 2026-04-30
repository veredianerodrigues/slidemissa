# 🚀 COMECE AQUI - Guia Rápido

## ✨ Sua aplicação web está pronta!

Transformamos a app desktop **Slide Missa** para web com **FastAPI + React**.

---

## 🎯 OPÇÃO 1: Rodar com Docker (Recomendado)

### 1. Abra PowerShell / Terminal
```bash
cd slideMissa-web
```

### 2. Inicie tudo com um comando
```bash
docker-compose up
```

**Pronto!** Aguarde ~2-3 minutos na primeira execução.

### 3. Acesse no navegador
```
http://localhost:5173
```

**Parar:** Pressione `Ctrl+C`

---

## 🔧 OPÇÃO 2: Rodar Localmente (SEM Docker)

### Pré-requisitos
- Python 3.9+ instalado
- Node.js 16+ instalado

### Terminal 1: Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn main:app --reload
```
✅ Backend em: **http://localhost:8000**

### Terminal 2: Frontend
```bash
cd frontend
npm install
npm run dev
```
✅ Frontend em: **http://localhost:5173**

---

## 📝 Como Usar

### ABA 1: Gerar via TXT
1. Upload arquivo `.txt` com cantos
2. Upload arquivo `.pptx` (ritual base)
3. Clique "Gerar Apresentação"
4. Download automático
5. ✨ Cantos salvos no banco automaticamente

### ABA 2: Banco de Cantos
1. Filtrar por posição (ex: "CANTO DE ENTRADA")
2. Selecionar múltiplos cantos (Ctrl+clique)
3. Upload `.pptx`
4. Clique "Gerar com X selecionados"
5. Download automático

---

## 📚 Documentação

| Arquivo | Descrição |
|---------|-----------|
| `README.md` | Documentação completa |
| `COMO_EXECUTAR.md` | Instruções detalhadas |
| `ARQUITETURA.md` | Estrutura técnica |
| `backend/main.py` | API endpoints |

---

## 🔌 API Endpoints

Teste em: **http://localhost:8000/docs** (Swagger interativo)

```
POST   /api/gerar                  → Gera from TXT
GET    /api/banco/listar           → Lista cantos
GET    /api/banco/posicoes         → Posições disponíveis
POST   /api/gerar-do-banco         → Gera from banco
DELETE /api/banco/{id}             → Remove canto
GET    /api/health                 → Health check
```

---

## ✅ Estrutura Criada

```
slideMissa-web/
├── backend/                  ← FastAPI + Python
│   ├── main.py              ← API endpoints
│   ├── servicos/
│   │   ├── gerar_missa.py   ← (código original reutilizado)
│   │   └── banco.py         ← (código original reutilizado)
│   └── requirements.txt
│
├── frontend/                 ← React + Vite
│   ├── src/
│   │   ├── App.jsx          ← App principal
│   │   ├── components/
│   │   │   ├── Gerar.jsx    ← Aba Gerar
│   │   │   └── Banco.jsx    ← Aba Banco
│   │   └── api.js
│   └── package.json
│
├── docker-compose.yml        ← Orquestração
└── README.md
```

---

## 🛠️ Troubleshooting

### "Docker not found"
- Instale Docker Desktop: https://www.docker.com/products/docker-desktop

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
cd backend
pip install -r requirements.txt
```

### "npm not found"
- Instale Node.js: https://nodejs.org/

### Frontend não conecta ao backend
- Backend tem que estar rodando em http://localhost:8000
- Verificar logs: `docker-compose logs backend`

---

## 🎯 O que foi reutilizado?

✅ **100% da lógica Python**
- `gerar_missa.py` - Parse TXT + create slides
- `banco.py` - SQLite operations

✅ **Interface similar ao desktop**
- 2 abas (Gerar / Banco)
- Mesma funcionalidade
- Design moderno

---

## 📞 Próximos Passos

Quando estiver pronto:
- [ ] Adicionar autenticação (JWT)
- [ ] Integrar PostgreSQL (Fase 3)
- [ ] Deploy (Azure/Heroku)
- [ ] Converter DOCX para TXT
- [ ] Histórico de gerações

---

## 🎉 Pronto!

Agora é só:

```bash
cd slideMissa-web
docker-compose up
```

E acesse **http://localhost:5173** 🚀

Qualquer dúvida, consulte `COMO_EXECUTAR.md` ou `README.md`
