import math
from typing import Tuple, Optional
from enum import Enum

class StatusUsuario(Enum):
    """Enum para status do usuário"""
    ONLINE = "online"
    OFFLINE = "offline"

class Usuario:
    """Classe que representa um usuário do sistema de comunicação baseado em localização"""
    
    def __init__(self, nome: str, latitude: float, longitude: float, 
                 raio_comunicacao: float = 1000.0, status: StatusUsuario = StatusUsuario.OFFLINE):
        """
        Inicializa um usuário
        
        Args:
            nome: Nome do usuário
            latitude: Latitude da localização do usuário
            longitude: Longitude da localização do usuário
            raio_comunicacao: Raio de comunicação em metros (padrão: 1000m)
            status: Status do usuário (online/offline)
        """
        self.nome = nome
        self.latitude = latitude
        self.longitude = longitude
        self.raio_comunicacao = raio_comunicacao
        self.status = status
        self.socket_connection = None  # Para armazenar a conexão socket quando online
    
    def atualizar_localizacao(self, latitude: float, longitude: float) -> None:
        """Atualiza a localização do usuário"""
        self.latitude = latitude
        self.longitude = longitude
    
    def atualizar_raio(self, novo_raio: float) -> None:
        """Atualiza o raio de comunicação do usuário"""
        if novo_raio > 0:
            self.raio_comunicacao = novo_raio
        else:
            raise ValueError("Raio deve ser maior que zero")
    
    def atualizar_status(self, novo_status: StatusUsuario) -> None:
        """Atualiza o status do usuário"""
        self.status = novo_status
    
    def set_online(self, socket_connection=None) -> None:
        """Define o usuário como online"""
        self.status = StatusUsuario.ONLINE
        self.socket_connection = socket_connection
    
    def set_offline(self) -> None:
        """Define o usuário como offline"""
        self.status = StatusUsuario.OFFLINE
        self.socket_connection = None
    
    def esta_online(self) -> bool:
        """Verifica se o usuário está online"""
        return self.status == StatusUsuario.ONLINE
    
    def calcular_distancia(self, outro_usuario: 'Usuario') -> float:
        """
        Calcula a distância entre este usuário e outro usando a fórmula Haversine
        
        Args:
            outro_usuario: Outro usuário para calcular a distância
            
        Returns:
            Distância em metros
        """
        return calcular_distancia_haversine(
            self.latitude, self.longitude,
            outro_usuario.latitude, outro_usuario.longitude
        )
    
    def esta_no_raio(self, outro_usuario: 'Usuario') -> bool:
        """
        Verifica se outro usuário está dentro do raio de comunicação
        
        Args:
            outro_usuario: Outro usuário para verificar
            
        Returns:
            True se estiver dentro do raio, False caso contrário
        """
        distancia = self.calcular_distancia(outro_usuario)
        return distancia <= self.raio_comunicacao
    
    def pode_comunicar_sincronamente(self, outro_usuario: 'Usuario') -> bool:
        """
        Verifica se pode comunicar sincronamente com outro usuário
        (ambos online e dentro do raio)
        
        DECISÃO ARQUITETURAL: Esta é a lógica central que determina quando
        usar comunicação síncrona (socket TCP) vs assíncrona (RabbitMQ).
        Comunicação síncrona só acontece quando TODOS os critérios são atendidos:
        1. Ambos usuários estão online
        2. Ambos estão dentro do raio de comunicação
        
        Args:
            outro_usuario: Outro usuário para verificar
            
        Returns:
            True se pode comunicar sincronamente, False caso contrário
        """
        return (self.esta_online() and 
                outro_usuario.esta_online() and 
                self.esta_no_raio(outro_usuario))
    
    def to_dict(self) -> dict:
        """Converte o usuário para dicionário (útil para serialização)"""
        return {
            'nome': self.nome,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'raio_comunicacao': self.raio_comunicacao,
            'status': self.status.value
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Usuario':
        """Cria um usuário a partir de um dicionário"""
        return cls(
            nome=data['nome'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            raio_comunicacao=data.get('raio_comunicacao', 1000.0),
            status=StatusUsuario(data.get('status', 'offline'))
        )
    
    def __str__(self) -> str:
        """Representação string do usuário"""
        return f"Usuario(nome='{self.nome}', lat={self.latitude}, lon={self.longitude}, raio={self.raio_comunicacao}m, status={self.status.value})"
    
    def __repr__(self) -> str:
        """Representação para debug"""
        return self.__str__()


def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância entre dois pontos na Terra usando a fórmula Haversine
    
    IMPLEMENTAÇÃO GEOGRÁFICA: A fórmula Haversine é usada para calcular distâncias
    sobre a superfície esférica da Terra. É mais precisa que cálculos euclidanos
    simples para distâncias médias (até ~1000 km).
    
    Fórmula: a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
             c = 2 ⋅ atan2( √a, √(1−a) )
             d = R ⋅ c
    
    Args:
        lat1, lon1: Latitude e longitude do primeiro ponto
        lat2, lon2: Latitude e longitude do segundo ponto
    
    Returns:
        Distância em metros
        
    Exemplo:
        São Paulo (-23.5505, -46.6333) → Rio de Janeiro (-22.9068, -43.1729)
        Resultado: ~357.000 metros
    """
    # Raio da Terra em metros (valor médio)
    R = 6371000
    
    # Converte graus para radianos (necessário para funções trigonométricas)
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferenças angulares
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Aplicação da fórmula Haversine
    # sin²(Δφ/2): componente latitudinal
    # cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2): componente longitudinal ajustada pela latitude
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    
    # Cálculo do ângulo central entre os pontos
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Distância linear sobre a superfície da Terra
    distancia = R * c
    
    return distancia
