#!/bin/bash
# Script de início rápido para o GeoChat

echo "🚀 GeoChat - Início Rápido"
echo ""

# Verifica se está no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Execute este script no diretório raiz do GeoChat"
    exit 1
fi

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verifica dependências
echo "🔍 Verificando dependências..."

if ! command_exists python3; then
    echo "❌ Python3 não encontrado. Instale o Python 3.11+"
    exit 1
fi

if ! command_exists docker; then
    echo "❌ Docker não encontrado. Instale o Docker"
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose não encontrado. Instale o Docker Compose"
    exit 1
fi

echo "✅ Dependências encontradas"

# Instala dependências Python se necessário
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

echo "📦 Ativando ambiente virtual e instalando dependências..."
source venv/bin/activate
pip install -r requirements.txt

# Testa configuração
echo "🧪 Testando configuração..."
python3 testar_configuracao.py

if [ $? -ne 0 ]; then
    echo "❌ Problemas na configuração detectados"
    exit 1
fi

# Inicia RabbitMQ
echo ""
echo "🐰 Iniciando RabbitMQ..."
./iniciar_rabbitmq.sh

if [ $? -ne 0 ]; then
    echo "❌ Falha ao iniciar RabbitMQ"
    exit 1
fi

echo ""
echo "🎉 Sistema pronto para uso!"
echo ""
echo "💡 Próximos passos:"
echo "   1. Em um terminal: python3 iniciar_servidor.py"
echo "   2. Em outro terminal: python3 iniciar_cliente.py"
echo "   3. Para mais clientes: python3 iniciar_cliente.py (em terminais separados)"
echo ""
echo "🌐 URLs úteis:"
echo "   - RabbitMQ Management: http://localhost:15672 (geochat/geochat123)"
echo ""
echo "🛑 Para parar tudo: docker-compose down"
