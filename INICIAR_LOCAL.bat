@echo off
REM Script para iniciar sem Docker (localmente)
REM Requer: Python 3.9+, Node.js 16+

echo.
echo ========================================
echo  Slide Missa - Web (Local SEM Docker)
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não encontrado no PATH
    echo Instale Python 3.9+: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Node.js não encontrado no PATH
    echo Instale Node.js 16+: https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Python encontrado: 
python --version
echo [OK] Node.js encontrado:
node --version
echo.

REM Iniciar Backend em uma nova janela
echo Iniciando Backend (FastAPI)...
start "Slide Missa - Backend" cmd /k "cd backend && python -m venv venv && call venv\Scripts\activate.bat && pip install -r requirements.txt && uvicorn main:app --reload"

REM Aguardar um pouco para backend iniciar
timeout /t 3

REM Iniciar Frontend em outra janela
echo Iniciando Frontend (React)...
start "Slide Missa - Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo ========================================
echo Abra o navegador em: http://localhost:5173
echo Backend: http://localhost:8000
echo Docs: http://localhost:8000/docs
echo ========================================
echo.
pause
