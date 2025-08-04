"""
Módulo de configuração para carregar variáveis de ambiente
"""

import os
from typing import Optional

try:
    from dotenv import load_dotenv
    # Carrega variáveis do arquivo .env se existir
    load_dotenv()
except ImportError:
    # python-dotenv não instalado, usa apenas variáveis do sistema
    pass

class Config:
    """Classe para centralizar configurações da aplicação"""
    
    # RabbitMQ
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
    RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'geochat')
    RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'geochat123')
    RABBITMQ_MANAGEMENT_PORT = int(os.getenv('RABBITMQ_MANAGEMENT_PORT', '15672'))
    
    # Servidor Socket
    SOCKET_HOST = os.getenv('SOCKET_HOST', 'localhost')
    SOCKET_PORT = int(os.getenv('SOCKET_PORT', '8888'))
    
    # Localização padrão
    DEFAULT_LATITUDE = float(os.getenv('DEFAULT_LATITUDE', '-23.5505'))
    DEFAULT_LONGITUDE = float(os.getenv('DEFAULT_LONGITUDE', '-46.6333'))
    DEFAULT_RADIUS = float(os.getenv('DEFAULT_RADIUS', '1000'))
    
    @classmethod
    def get_rabbitmq_url(cls) -> str:
        """Retorna URL de conexão do RabbitMQ"""
        return f"amqp://{cls.RABBITMQ_USER}:{cls.RABBITMQ_PASS}@{cls.RABBITMQ_HOST}:{cls.RABBITMQ_PORT}/"
    
    @classmethod
    def get_rabbitmq_management_url(cls) -> str:
        """Retorna URL do Management UI do RabbitMQ"""
        return f"http://{cls.RABBITMQ_HOST}:{cls.RABBITMQ_MANAGEMENT_PORT}"
    
    @classmethod
    def get_socket_address(cls) -> tuple:
        """Retorna tupla (host, porta) para socket"""
        return (cls.SOCKET_HOST, cls.SOCKET_PORT)
    
    @classmethod
    def get_default_location(cls) -> tuple:
        """Retorna tupla (latitude, longitude) padrão"""
        return (cls.DEFAULT_LATITUDE, cls.DEFAULT_LONGITUDE)
    
    @classmethod
    def print_config(cls):
        """Imprime configurações atuais (sem senhas)"""
        print("🔧 Configurações atuais:")
        print(f"   Socket: {cls.SOCKET_HOST}:{cls.SOCKET_PORT}")
        print(f"   RabbitMQ: {cls.RABBITMQ_HOST}:{cls.RABBITMQ_PORT}")
        print(f"   RabbitMQ User: {cls.RABBITMQ_USER}")
        print(f"   Management UI: {cls.get_rabbitmq_management_url()}")
        print(f"   Localização padrão: {cls.DEFAULT_LATITUDE}, {cls.DEFAULT_LONGITUDE}")
        print(f"   Raio padrão: {cls.DEFAULT_RADIUS}m")

# Instância global para fácil acesso
config = Config()
