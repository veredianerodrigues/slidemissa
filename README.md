# slideMissa-web

Gerador de slides para missa católica. Converte cantos em formato TXT ou DOCX para apresentações PPTX.

## Stack

- **Backend:** Python + FastAPI
- **Frontend:** React + Vite
- **Banco:** SQLite

## Executar localmente

**Backend**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Acesse: `http://localhost:5173`

## Executar com Docker

```bash
docker-compose up
```

## Funcionalidades

| Aba | Descrição |
|---|---|
| Gerar via TXT | Gera PPTX a partir de um arquivo `.txt` + ritual `.pptx` |
| Converter DOCX | Converte `.docx` para `.txt` com mapeamento automático de seções litúrgicas |
| Banco de Cantos | Armazena cantos reutilizáveis; gera PPTX direto do banco |
