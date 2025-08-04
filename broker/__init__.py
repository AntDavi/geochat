"""
Módulo do broker RabbitMQ para comunicação assíncrona
"""

from .rabbitmq_manager import ConfiguradorRabbitMQ, PublisherMensagem, ConsumerMensagem

__all__ = ['ConfiguradorRabbitMQ', 'PublisherMensagem', 'ConsumerMensagem']
