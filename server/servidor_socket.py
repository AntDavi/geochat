import socket
import threading
import json
import time
from typing import Dict, List, Optional
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.usuario import Usuario, StatusUsuario

class ServidorSocket:
    """
    Servidor de socket para gerenciar conexões síncronas entre usuários
    
    ARQUITETURA MULTI-THREADED: O servidor usa uma arquitetura onde:
    1. Thread principal aceita novas conexões
    2. Uma thread dedicada para cada cliente conectado
    3. Locks garantem thread safety para dados compartilhados
    4. Callbacks notificam a interface sobre eventos
    
    PADRÃO OBSERVER: Usa callbacks para desacoplar lógica de servidor da interface
    """
    
    def __init__(self, host: str = 'localhost', porta: int = 8888):
        """
        Inicializa o servidor
        
        Args:
            host: Endereço do servidor
            porta: Porta do servidor
        """
        self.host = host
        self.porta = porta
        self.socket_servidor = None
        self.rodando = False
        
        # Dicionário de usuários conectados: {nome_usuario: Usuario}
        self.usuarios_conectados: Dict[str, Usuario] = {}
        
        # Dicionário de conexões: {nome_usuario: socket_connection}
        self.conexoes: Dict[str, socket.socket] = {}
        
        # THREAD SAFETY: Lock para proteger acesso concorrente aos dicionários
        # Múltiplas threads (uma por cliente) acessam estes dados simultaneamente
        self.lock = threading.Lock()
        
        # PADRÃO OBSERVER: Lista de callbacks para eventos do servidor
        # Permite que a interface gráfica reaja a eventos sem acoplamento direto
        self.callbacks_usuario_conectado = []
        self.callbacks_usuario_desconectado = []
        self.callbacks_mensagem_recebida = []
    
    def adicionar_callback_usuario_conectado(self, callback):
        """Adiciona callback para quando usuário se conecta"""
        self.callbacks_usuario_conectado.append(callback)
    
    def adicionar_callback_usuario_desconectado(self, callback):
        """Adiciona callback para quando usuário se desconecta"""
        self.callbacks_usuario_desconectado.append(callback)
    
    def adicionar_callback_mensagem_recebida(self, callback):
        """Adiciona callback para quando mensagem é recebida"""
        self.callbacks_mensagem_recebida.append(callback)
    
    def iniciar_servidor(self) -> bool:
        """
        Inicia o servidor
        
        Returns:
            True se iniciado com sucesso, False caso contrário
        """
        try:
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_servidor.bind((self.host, self.porta))
            self.socket_servidor.listen(10)
            
            self.rodando = True
            
            # Thread para aceitar conexões
            thread_aceitar = threading.Thread(target=self._aceitar_conexoes, daemon=True)
            thread_aceitar.start()
            
            print(f"Servidor iniciado em {self.host}:{self.porta}")
            return True
            
        except Exception as e:
            print(f"Erro ao iniciar servidor: {e}")
            return False
    
    def parar_servidor(self):
        """Para o servidor"""
        self.rodando = False
        
        # Desconecta todos os usuários
        with self.lock:
            for nome_usuario in list(self.usuarios_conectados.keys()):
                self._desconectar_usuario(nome_usuario)
        
        # Fecha socket do servidor
        if self.socket_servidor:
            try:
                self.socket_servidor.close()
            except:
                pass
        
        print("Servidor parado")
    
    def _aceitar_conexoes(self):
        """
        Thread que aceita novas conexões
        
        PADRÃO THREAD-PER-CLIENT: Para cada cliente que se conecta,
        criamos uma thread dedicada. Isso permite:
        1. Múltiplos clientes simultâneos
        2. Cada cliente tem seu próprio loop de comunicação
        3. Isolamento de falhas (um cliente com problema não afeta outros)
        """
        while self.rodando:
            try:
                # Accept é bloqueante - aguarda nova conexão
                conn, endereco = self.socket_servidor.accept()
                print(f"Nova conexão de {endereco}")
                
                # Cria thread dedicada para este cliente
                # daemon=True: thread morre quando main thread termina
                thread_cliente = threading.Thread(
                    target=self._lidar_com_cliente, 
                    args=(conn, endereco),
                    daemon=True
                )
                thread_cliente.start()
                
            except Exception as e:
                if self.rodando:
                    print(f"Erro ao aceitar conexão: {e}")
    
    def _lidar_com_cliente(self, conn: socket.socket, endereco):
        """Lida com um cliente específico"""
        nome_usuario = None
        
        try:
            while self.rodando:
                # Recebe dados do cliente
                dados = conn.recv(4096)
                if not dados:
                    break
                
                try:
                    mensagem = json.loads(dados.decode('utf-8'))
                    self._processar_mensagem(conn, endereco, mensagem)
                    
                except json.JSONDecodeError:
                    self._enviar_erro(conn, "Formato de mensagem inválido")
                except Exception as e:
                    print(f"Erro ao processar mensagem: {e}")
                    self._enviar_erro(conn, f"Erro interno: {str(e)}")
        
        except Exception as e:
            print(f"Erro na conexão com {endereco}: {e}")
        
        finally:
            # Remove usuário se estava conectado
            if nome_usuario:
                self._desconectar_usuario(nome_usuario)
            
            try:
                conn.close()
            except:
                pass
    
    def _processar_mensagem(self, conn: socket.socket, endereco, mensagem: dict):
        """Processa mensagem recebida do cliente"""
        tipo = mensagem.get('tipo')
        
        if tipo == 'conectar':
            self._processar_conexao(conn, endereco, mensagem)
        elif tipo == 'atualizar_localizacao':
            self._processar_atualizacao_localizacao(conn, mensagem)
        elif tipo == 'enviar_mensagem':
            self._processar_envio_mensagem(conn, mensagem)
        elif tipo == 'listar_usuarios':
            self._processar_listagem_usuarios(conn)
        else:
            self._enviar_erro(conn, f"Tipo de mensagem desconhecido: {tipo}")
    
    def _processar_conexao(self, conn: socket.socket, endereco, mensagem: dict):
        """Processa conexão de usuário"""
        try:
            dados_usuario = mensagem['usuario']
            usuario = Usuario.from_dict(dados_usuario)
            usuario.set_online(conn)
            
            with self.lock:
                # Verifica se usuário já está conectado
                if usuario.nome in self.usuarios_conectados:
                    self._enviar_erro(conn, "Usuário já está conectado")
                    return
                
                # Adiciona usuário
                self.usuarios_conectados[usuario.nome] = usuario
                self.conexoes[usuario.nome] = conn
            
            # Resposta de sucesso
            resposta = {
                'tipo': 'conexao_aceita',
                'mensagem': 'Conectado com sucesso',
                'timestamp': datetime.now().isoformat()
            }
            self._enviar_mensagem(conn, resposta)
            
            # Notifica callbacks
            for callback in self.callbacks_usuario_conectado:
                try:
                    callback(usuario)
                except Exception as e:
                    print(f"Erro em callback de conexão: {e}")
            
            print(f"Usuário {usuario.nome} conectado de {endereco}")
            
        except KeyError as e:
            self._enviar_erro(conn, f"Campo obrigatório ausente: {e}")
        except Exception as e:
            self._enviar_erro(conn, f"Erro ao processar conexão: {e}")
    
    def _processar_atualizacao_localizacao(self, conn: socket.socket, mensagem: dict):
        """Processa atualização de localização do usuário"""
        try:
            nome_usuario = self._encontrar_usuario_por_conexao(conn)
            if not nome_usuario:
                self._enviar_erro(conn, "Usuário não encontrado")
                return
            
            nova_lat = mensagem['latitude']
            nova_lon = mensagem['longitude']
            
            with self.lock:
                usuario = self.usuarios_conectados[nome_usuario]
                usuario.atualizar_localizacao(nova_lat, nova_lon)
            
            # Resposta de sucesso
            resposta = {
                'tipo': 'localizacao_atualizada',
                'mensagem': 'Localização atualizada com sucesso',
                'timestamp': datetime.now().isoformat()
            }
            self._enviar_mensagem(conn, resposta)
            
        except KeyError as e:
            self._enviar_erro(conn, f"Campo obrigatório ausente: {e}")
        except Exception as e:
            self._enviar_erro(conn, f"Erro ao atualizar localização: {e}")
    
    def _processar_envio_mensagem(self, conn: socket.socket, mensagem: dict):
        """
        Processa envio de mensagem entre usuários
        
        LÓGICA CENTRAL DE DECISÃO: Esta função implementa a regra de negócio
        fundamental do sistema - quando permitir comunicação síncrona.
        
        Critérios verificados:
        1. Remetente está autenticado
        2. Destinatário está online
        3. Ambos estão no raio de comunicação (método pode_comunicar_sincronamente)
        
        Se qualquer critério falhar, mensagem é rejeitada.
        Cliente deve usar RabbitMQ para comunicação assíncrona.
        """
        try:
            remetente = self._encontrar_usuario_por_conexao(conn)
            if not remetente:
                self._enviar_erro(conn, "Usuário remetente não encontrado")
                return
            
            destinatario = mensagem['destinatario']
            conteudo = mensagem['conteudo']
            
            # SEÇÃO CRÍTICA: Acesso thread-safe aos dados compartilhados
            with self.lock:
                usuario_remetente = self.usuarios_conectados[remetente]
                
                # Verifica se destinatário está conectado
                if destinatario not in self.usuarios_conectados:
                    self._enviar_erro(conn, "Destinatário não está online")
                    return
                
                usuario_destinatario = self.usuarios_conectados[destinatario]
                
                # DECISÃO ARQUITETURAL: Verifica critérios para comunicação síncrona
                # Esta é a linha que define quando usar socket vs RabbitMQ
                if not usuario_remetente.pode_comunicar_sincronamente(usuario_destinatario):
                    self._enviar_erro(conn, "Usuários não estão no raio de comunicação")
                    return
                
                # Envia mensagem para o destinatário via socket TCP
                conn_destinatario = self.conexoes[destinatario]
                mensagem_destinatario = {
                    'tipo': 'mensagem_recebida',
                    'remetente': remetente,
                    'conteudo': conteudo,
                    'timestamp': datetime.now().isoformat()
                }
                self._enviar_mensagem(conn_destinatario, mensagem_destinatario)
            
            # Confirmação para o remetente
            resposta = {
                'tipo': 'mensagem_enviada',
                'mensagem': 'Mensagem enviada com sucesso',
                'timestamp': datetime.now().isoformat()
            }
            self._enviar_mensagem(conn, resposta)
            
            # Notifica callbacks
            for callback in self.callbacks_mensagem_recebida:
                try:
                    callback(remetente, destinatario, conteudo)
                except Exception as e:
                    print(f"Erro em callback de mensagem: {e}")
            
        except KeyError as e:
            self._enviar_erro(conn, f"Campo obrigatório ausente: {e}")
        except Exception as e:
            self._enviar_erro(conn, f"Erro ao enviar mensagem: {e}")
    
    def _processar_listagem_usuarios(self, conn: socket.socket):
        """Processa solicitação de listagem de usuários"""
        try:
            nome_solicitante = self._encontrar_usuario_por_conexao(conn)
            if not nome_solicitante:
                self._enviar_erro(conn, "Usuário solicitante não encontrado")
                return
            
            with self.lock:
                usuario_solicitante = self.usuarios_conectados[nome_solicitante]
                usuarios_no_raio = []
                
                for nome, usuario in self.usuarios_conectados.items():
                    if nome != nome_solicitante:
                        distancia = usuario_solicitante.calcular_distancia(usuario)
                        no_raio = usuario_solicitante.esta_no_raio(usuario)
                        
                        usuario_info = {
                            'nome': usuario.nome,
                            'latitude': usuario.latitude,
                            'longitude': usuario.longitude,
                            'status': usuario.status.value,
                            'distancia': round(distancia, 2),
                            'no_raio': no_raio
                        }
                        usuarios_no_raio.append(usuario_info)
            
            resposta = {
                'tipo': 'lista_usuarios',
                'usuarios': usuarios_no_raio,
                'timestamp': datetime.now().isoformat()
            }
            self._enviar_mensagem(conn, resposta)
            
        except Exception as e:
            self._enviar_erro(conn, f"Erro ao listar usuários: {e}")
    
    def _encontrar_usuario_por_conexao(self, conn: socket.socket) -> Optional[str]:
        """Encontra nome do usuário pela conexão"""
        with self.lock:
            for nome, conexao in self.conexoes.items():
                if conexao == conn:
                    return nome
        return None
    
    def _desconectar_usuario(self, nome_usuario: str):
        """Desconecta usuário"""
        with self.lock:
            if nome_usuario in self.usuarios_conectados:
                usuario = self.usuarios_conectados[nome_usuario]
                usuario.set_offline()
                
                del self.usuarios_conectados[nome_usuario]
                del self.conexoes[nome_usuario]
                
                # Notifica callbacks
                for callback in self.callbacks_usuario_desconectado:
                    try:
                        callback(usuario)
                    except Exception as e:
                        print(f"Erro em callback de desconexão: {e}")
                
                print(f"Usuário {nome_usuario} desconectado")
    
    def _enviar_mensagem(self, conn: socket.socket, mensagem: dict):
        """Envia mensagem para conexão"""
        try:
            dados = json.dumps(mensagem).encode('utf-8')
            conn.send(dados)
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
    
    def _enviar_erro(self, conn: socket.socket, erro: str):
        """Envia mensagem de erro para conexão"""
        mensagem = {
            'tipo': 'erro',
            'mensagem': erro,
            'timestamp': datetime.now().isoformat()
        }
        self._enviar_mensagem(conn, mensagem)
    
    def obter_usuarios_conectados(self) -> List[Usuario]:
        """Retorna lista de usuários conectados"""
        with self.lock:
            return list(self.usuarios_conectados.values())
    
    def obter_estatisticas(self) -> dict:
        """Retorna estatísticas do servidor"""
        with self.lock:
            return {
                'usuarios_conectados': len(self.usuarios_conectados),
                'servidor_rodando': self.rodando,
                'host': self.host,
                'porta': self.porta
            }

if __name__ == "__main__":
    # Teste básico do servidor
    servidor = ServidorSocket()
    
    def callback_conexao(usuario):
        print(f"[CALLBACK] Usuário conectado: {usuario.nome}")
    
    def callback_desconexao(usuario):
        print(f"[CALLBACK] Usuário desconectado: {usuario.nome}")
    
    servidor.adicionar_callback_usuario_conectado(callback_conexao)
    servidor.adicionar_callback_usuario_desconectado(callback_desconexao)
    
    if servidor.iniciar_servidor():
        print("Servidor rodando... Pressione Ctrl+C para parar")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nParando servidor...")
            servidor.parar_servidor()
    else:
        print("Falha ao iniciar servidor")
