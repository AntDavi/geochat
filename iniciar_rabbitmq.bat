@echo off
REM Script para iniciar o RabbitMQ via Docker no Windows

echo 🚀 Iniciando RabbitMQ via Docker...

REM Verifica se Docker está rodando
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Erro: Docker não está rodando. Por favor, inicie o Docker primeiro.
    pause
    exit /b 1
)

REM Inicia o RabbitMQ
docker-compose up -d rabbitmq

if %errorlevel% equ 0 (
    echo ✅ RabbitMQ iniciado com sucesso!
    echo.
    echo 📋 Informações de acesso:
    echo    - Porta AMQP: 5672
    echo    - Management UI: http://localhost:15672
    echo    - Usuário: geochat
    echo    - Senha: geochat123
    echo.
    echo 🔍 Para verificar logs: docker-compose logs -f rabbitmq
    echo 🛑 Para parar: docker-compose down
) else (
    echo ❌ Erro ao iniciar RabbitMQ
    pause
    exit /b 1
)

pause
