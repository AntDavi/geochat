#!/bin/bash
"""
Script para iniciar o RabbitMQ via Docker
"""

echo "🚀 Iniciando RabbitMQ via Docker..."

# Verifica se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Erro: Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# Inicia o RabbitMQ
docker-compose up -d rabbitmq

# Verifica se o container foi iniciado
if [ $? -eq 0 ]; then
    echo "✅ RabbitMQ iniciado com sucesso!"
    echo ""
    echo "📋 Informações de acesso:"
    echo "   - Porta AMQP: 5672"
    echo "   - Management UI: http://localhost:15672"
    echo "   - Usuário: geochat"
    echo "   - Senha: geochat123"
    echo ""
    echo "🔍 Para verificar logs: docker-compose logs -f rabbitmq"
    echo "🛑 Para parar: docker-compose down"
else
    echo "❌ Erro ao iniciar RabbitMQ"
    exit 1
fi
