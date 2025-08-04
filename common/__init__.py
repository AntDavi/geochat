"""
Módulo comum com classes e funções compartilhadas entre cliente e servidor
"""

from .usuario import Usuario, StatusUsuario, calcular_distancia_haversine
from .config import Config, config

__all__ = ['Usuario', 'StatusUsuario', 'calcular_distancia_haversine', 'Config', 'config']
