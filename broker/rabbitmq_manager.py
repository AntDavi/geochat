import pika
import json
import threading
import time
from typing import Dict, Callable, Optional
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.usuario import Usuario

class ConfiguradorRabbitMQ:
    """
    Classe para configurar e gerenciar a topologia do RabbitMQ
    
    TOPOLOGIA DO RABBITMQ: O sistema usa dois exchanges:
    1. 'geochat_messages' (DIRECT): Para mensagens diretas usuário-a-usuário
    2. 'geochat_location' (FANOUT): Para broadcast de atualizações de localização
    
    PADRÃO PUBLISHER-CONSUMER: Implementa tanto publisher quanto consumer
    de forma thread-safe para comunicação assíncrona.
    
    CONFIGURAÇÃO DOCKER: Usa credenciais padrão do Docker Compose
    """
    
    def __init__(self, host: str = 'localhost', porta: int = 5672, 
                 usuario: str = 'geochat', senha: str = 'geochat123'):
        """
        Inicializa o configurador do RabbitMQ
        
        Args:
            host: Host do RabbitMQ
            porta: Porta do RabbitMQ
            usuario: Usuário do RabbitMQ (padrão para Docker: geochat)
            senha: Senha do RabbitMQ (padrão para Docker: geochat123)
        """
        self.host = host
        self.porta = porta
        self.usuario = usuario
        self.senha = senha
        
        # Nomes dos exchanges e filas
        self.exchange_mensagens = 'geochat_messages'
        self.exchange_localizacao = 'geochat_location'
        
        self.connection = None
        self.channel = None
    
    def conectar(self) -> bool:
        """
        Conecta ao RabbitMQ
        
        Returns:
            True se conectado com sucesso, False caso contrário
        """
        try:
            credentials = pika.PlainCredentials(self.usuario, self.senha)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.porta,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            return True
            
        except Exception as e:
            print(f"Erro ao conectar ao RabbitMQ: {e}")
            return False
    
    def desconectar(self):
        """Desconecta do RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            print(f"Erro ao desconectar do RabbitMQ: {e}")
    
    def configurar_topologia(self) -> bool:
        """
        Configura a topologia do RabbitMQ (exchanges, filas, bindings)
        
        ARQUITETURA DE MESSAGING: Dois exchanges com propósitos distintos:
        
        1. DIRECT EXCHANGE (geochat_messages):
           - Mensagens diretas entre usuários específicos
           - Routing key = nome do destinatário
           - Cada usuário tem sua fila pessoal
           - Padrão Point-to-Point
        
        2. FANOUT EXCHANGE (geochat_location):
           - Broadcast de atualizações de localização
           - Todos os usuários conectados recebem
           - Padrão Publish-Subscribe
        
        DURABILIDADE: Exchanges são duráveis (sobrevivem a reinicializações)
        
        Returns:
            True se configurado com sucesso, False caso contrário
        """
        try:
            if not self.channel:
                print("Canal não está conectado")
                return False
            
            # Exchange para mensagens diretas (direct)
            # DECISÃO: Direct permite roteamento específico por nome de usuário
            self.channel.exchange_declare(
                exchange=self.exchange_mensagens,
                exchange_type='direct',  # Roteamento por routing key
                durable=True  # Sobrevive a restart do RabbitMQ
            )
            
            # Exchange para atualizações de localização (fanout)
            # DECISÃO: Fanout permite broadcast para todos os usuários
            self.channel.exchange_declare(
                exchange=self.exchange_localizacao,
                exchange_type='fanout',  # Broadcast para todas as filas ligadas
                durable=True
            )
            
            print("Topologia do RabbitMQ configurada com sucesso")
            return True
            
        except Exception as e:
            print(f"Erro ao configurar topologia: {e}")
            return False
    
    def criar_fila_usuario(self, nome_usuario: str) -> bool:
        """
        Cria fila específica para um usuário
        
        Args:
            nome_usuario: Nome do usuário
            
        Returns:
            True se criada com sucesso, False caso contrário
        """
        try:
            if not self.channel:
                print("Canal não está conectado")
                return False
            
            # Fila para mensagens do usuário
            fila_mensagens = f"user_{nome_usuario}_messages"
            self.channel.queue_declare(queue=fila_mensagens, durable=True)
            
            # Bind da fila ao exchange de mensagens
            self.channel.queue_bind(
                exchange=self.exchange_mensagens,
                queue=fila_mensagens,
                routing_key=nome_usuario
            )
            
            # Fila para atualizações de localização do usuário
            fila_localizacao = f"user_{nome_usuario}_location"
            self.channel.queue_declare(queue=fila_localizacao, durable=True)
            
            # Bind da fila ao exchange de localização
            self.channel.queue_bind(
                exchange=self.exchange_localizacao,
                queue=fila_localizacao
            )
            
            print(f"Filas criadas para usuário: {nome_usuario}")
            return True
            
        except Exception as e:
            print(f"Erro ao criar fila para usuário {nome_usuario}: {e}")
            return False
    
    def deletar_fila_usuario(self, nome_usuario: str) -> bool:
        """
        Deleta filas de um usuário
        
        Args:
            nome_usuario: Nome do usuário
            
        Returns:
            True se deletadas com sucesso, False caso contrário
        """
        try:
            if not self.channel:
                print("Canal não está conectado")
                return False
            
            fila_mensagens = f"user_{nome_usuario}_messages"
            fila_localizacao = f"user_{nome_usuario}_location"
            
            self.channel.queue_delete(queue=fila_mensagens)
            self.channel.queue_delete(queue=fila_localizacao)
            
            print(f"Filas deletadas para usuário: {nome_usuario}")
            return True
            
        except Exception as e:
            print(f"Erro ao deletar filas do usuário {nome_usuario}: {e}")
            return False
    
    def listar_filas(self) -> list:
        """
        Lista todas as filas do RabbitMQ
        
        Returns:
            Lista de nomes das filas
        """
        try:
            # Esta funcionalidade requer a API de Management do RabbitMQ
            # Por simplicidade, retornamos lista vazia aqui
            # Em produção, usaríamos requests para chamar a API Management
            return []
            
        except Exception as e:
            print(f"Erro ao listar filas: {e}")
            return []

class PublisherMensagem:
    """
    Publisher para enviar mensagens assíncronas
    
    PADRÃO PUBLISHER: Responsável exclusivamente por publicar mensagens.
    Separado do Consumer para seguir Single Responsibility Principle.
    
    USO: Quando comunicação síncrona não é possível:
    1. Usuário destinatário offline
    2. Usuário destinatário fora do raio
    3. Modo assíncrono forçado pelo usuário
    """
    
    def __init__(self, configurador: ConfiguradorRabbitMQ):
        """
        Inicializa o publisher
        
        Args:
            configurador: Instância do configurador RabbitMQ
        """
        self.configurador = configurador
        self.connection = None
        self.channel = None
    
    def conectar(self) -> bool:
        """Conecta ao RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                self.configurador.usuario, 
                self.configurador.senha
            )
            parameters = pika.ConnectionParameters(
                host=self.configurador.host,
                port=self.configurador.porta,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            return True
            
        except Exception as e:
            print(f"Erro ao conectar publisher: {e}")
            return False
    
    def desconectar(self):
        """Desconecta do RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            print(f"Erro ao desconectar publisher: {e}")
    
    def enviar_mensagem_assincrona(self, remetente: str, destinatario: str, 
                                 conteudo: str, motivo: str = "offline") -> bool:
        """
        Envia mensagem assíncrona para um usuário
        
        DECISÃO DE PERSISTÊNCIA: Mensagens são marcadas como persistent (delivery_mode=2)
        garantindo que sobrevivem a restart do RabbitMQ.
        
        ROTEAMENTO: Usa exchange 'direct' com routing_key = nome_destinatario
        Isso garante que a mensagem vai para a fila específica do usuário.
        
        METADADOS: Inclui timestamp e motivo (offline/fora_do_raio/forcado)
        para debugging e possível auditoria.
        
        Args:
            remetente: Nome do remetente
            destinatario: Nome do destinatário
            conteudo: Conteúdo da mensagem
            motivo: Motivo da mensagem assíncrona (offline, fora_do_raio, forcado)
            
        Returns:
            True se enviada com sucesso, False caso contrário
        """
        try:
            if not self.channel:
                print("Publisher não está conectado")
                return False
            
            # Estrutura da mensagem com metadados
            mensagem = {
                'tipo': 'mensagem_assincrona',
                'remetente': remetente,
                'destinatario': destinatario,
                'conteudo': conteudo,
                'motivo': motivo,  # Para tracking: por que foi assíncrona?
                'timestamp': datetime.now().isoformat()
            }
            
            # Publica no exchange direct com routing key = destinatario
            # ROTEAMENTO: Exchange direct roteia para fila específica do usuário
            self.channel.basic_publish(
                exchange=self.configurador.exchange_mensagens,
                routing_key=destinatario,  # Fila do destinatário
                body=json.dumps(mensagem),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # PERSISTÊNCIA: Mensagem sobrevive a restart
                )
            )
            
            print(f"Mensagem assíncrona enviada: {remetente} -> {destinatario} (motivo: {motivo})")
            return True
            
        except Exception as e:
            print(f"Erro ao enviar mensagem assíncrona: {e}")
            return False
    
    def publicar_atualizacao_localizacao(self, usuario: Usuario) -> bool:
        """
        Publica atualização de localização de um usuário
        
        Args:
            usuario: Usuário que atualizou a localização
            
        Returns:
            True se publicada com sucesso, False caso contrário
        """
        try:
            if not self.channel:
                print("Publisher não está conectado")
                return False
            
            # Dados da atualização
            atualizacao = {
                'tipo': 'atualizacao_localizacao',
                'usuario': usuario.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Publica no exchange de localização (fanout)
            self.channel.basic_publish(
                exchange=self.configurador.exchange_localizacao,
                routing_key='',  # Fanout ignora routing key
                body=json.dumps(atualizacao),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            
            print(f"Atualização de localização publicada para: {usuario.nome}")
            return True
            
        except Exception as e:
            print(f"Erro ao publicar atualização de localização: {e}")
            return False

class ConsumerMensagem:
    """Consumer para receber mensagens assíncronas"""
    
    def __init__(self, configurador: ConfiguradorRabbitMQ, nome_usuario: str):
        """
        Inicializa o consumer
        
        Args:
            configurador: Instância do configurador RabbitMQ
            nome_usuario: Nome do usuário que irá consumir mensagens
        """
        self.configurador = configurador
        self.nome_usuario = nome_usuario
        self.connection = None
        self.channel = None
        
        # Callbacks para diferentes tipos de mensagem
        self.callback_mensagem = None
        self.callback_localizacao = None
        
        # Controle do consumer
        self.consumindo = False
        self.thread_consumer = None
    
    def conectar(self) -> bool:
        """Conecta ao RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                self.configurador.usuario, 
                self.configurador.senha
            )
            parameters = pika.ConnectionParameters(
                host=self.configurador.host,
                port=self.configurador.porta,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            return True
            
        except Exception as e:
            print(f"Erro ao conectar consumer: {e}")
            return False
    
    def desconectar(self):
        """Desconecta do RabbitMQ"""
        try:
            self.parar_consumo()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            print(f"Erro ao desconectar consumer: {e}")
    
    def definir_callback_mensagem(self, callback: Callable[[dict], None]):
        """
        Define callback para mensagens recebidas
        
        Args:
            callback: Função que será chamada quando mensagem for recebida
        """
        self.callback_mensagem = callback
    
    def definir_callback_localizacao(self, callback: Callable[[dict], None]):
        """
        Define callback para atualizações de localização
        
        Args:
            callback: Função que será chamada quando atualização for recebida
        """
        self.callback_localizacao = callback
    
    def iniciar_consumo(self) -> bool:
        """
        Inicia o consumo de mensagens
        
        PADRÃO CONSUMER: Registra callbacks para duas filas diferentes:
        1. Fila de mensagens diretas (user_X_messages)
        2. Fila de atualizações de localização (user_X_location)
        
        THREADING: Consumer roda em thread separada para não bloquear a UI.
        Thread é daemon (morre com main thread).
        
        ACK MANUAL: auto_ack=False garante que mensagens só são removidas
        da fila após confirmação explícita (reliability).
        
        Returns:
            True se iniciado com sucesso, False caso contrário
        """
        try:
            if not self.channel:
                print("Consumer não está conectado")
                return False
            
            self.consumindo = True
            
            # Configura consumo da fila de mensagens pessoais
            fila_mensagens = f"user_{self.nome_usuario}_messages"
            self.channel.basic_consume(
                queue=fila_mensagens,
                on_message_callback=self._processar_mensagem,
                auto_ack=False  # ACK manual para confiabilidade
            )
            
            # Configura consumo da fila de localização (broadcast)
            fila_localizacao = f"user_{self.nome_usuario}_location"
            self.channel.basic_consume(
                queue=fila_localizacao,
                on_message_callback=self._processar_localizacao,
                auto_ack=False
            )
            
            # THREAD DEDICADA: Consumer não pode bloquear UI principal
            self.thread_consumer = threading.Thread(target=self._loop_consumo, daemon=True)
            self.thread_consumer.start()
            
            print(f"Consumo iniciado para usuário: {self.nome_usuario}")
            return True
            
        except Exception as e:
            print(f"Erro ao iniciar consumo: {e}")
            return False
    
    def parar_consumo(self):
        """Para o consumo de mensagens"""
        try:
            self.consumindo = False
            
            if self.channel:
                self.channel.stop_consuming()
            
            if self.thread_consumer and self.thread_consumer.is_alive():
                self.thread_consumer.join(timeout=2)
            
            print(f"Consumo parado para usuário: {self.nome_usuario}")
            
        except Exception as e:
            print(f"Erro ao parar consumo: {e}")
    
    def _loop_consumo(self):
        """Loop principal de consumo"""
        try:
            while self.consumindo:
                self.channel.start_consuming()
        except Exception as e:
            if self.consumindo:
                print(f"Erro no loop de consumo: {e}")
    
    def _processar_mensagem(self, channel, method, properties, body):
        """
        Processa mensagem recebida da fila pessoal
        
        CALLBACK PATTERN: Delega processamento para callback registrado
        pela aplicação. Isso mantém baixo acoplamento entre broker e UI.
        
        ACK/NACK: Confirma recebimento ou rejeita mensagem em caso de erro.
        Mensagens rejeitadas voltam para a fila (requeue=True).
        """
        try:
            dados = json.loads(body.decode('utf-8'))
            
            # PADRÃO CALLBACK: Notifica aplicação sobre nova mensagem
            if self.callback_mensagem:
                self.callback_mensagem(dados)
            
            # CONFIRMAÇÃO: Remove mensagem da fila após processamento
            channel.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
            # TRATAMENTO DE ERRO: Rejeita e recoloca na fila
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _processar_localizacao(self, channel, method, properties, body):
        """Processa atualização de localização"""
        try:
            dados = json.loads(body.decode('utf-8'))
            
            # Ignora suas próprias atualizações
            if dados.get('usuario', {}).get('nome') != self.nome_usuario:
                # Chama callback se definido
                if self.callback_localizacao:
                    self.callback_localizacao(dados)
            
            # Confirma recebimento
            channel.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Erro ao processar atualização de localização: {e}")
            # Rejeita mensagem em caso de erro
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

if __name__ == "__main__":
    # Teste básico do RabbitMQ
    configurador = ConfiguradorRabbitMQ()
    
    if configurador.conectar():
        print("Conectado ao RabbitMQ")
        
        if configurador.configurar_topologia():
            print("Topologia configurada")
            
            # Cria filas para usuários de teste
            configurador.criar_fila_usuario("usuario1")
            configurador.criar_fila_usuario("usuario2")
        
        configurador.desconectar()
    else:
        print("Falha ao conectar ao RabbitMQ")
