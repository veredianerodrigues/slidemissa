@echo off
REM Script para iniciar a aplicação web localmente
REM Requer: Docker Desktop instalado e rodando

echo.
echo ========================================
echo  Slide Missa - Web (Local)
echo ========================================
echo.

REM Verificar se Docker está instalado
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Docker não está instalado ou não está no PATH
    echo Instale o Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [OK] Docker encontrado
echo.
echo Iniciando containers...
echo.

REM Iniciar docker-compose
docker-compose up

REM Se chegou aqui, user pressionou Ctrl+C
echo.
echo ========================================
echo Containers parados.
pause
