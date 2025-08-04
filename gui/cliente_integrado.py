import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import json
import threading
import time
from datetime import datetime
from typing import Optional, Dict, List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.usuario import Usuario, StatusUsuario
from common.config import config
from broker.rabbitmq_manager import ConfiguradorRabbitMQ, PublisherMensagem, ConsumerMensagem

class ClienteIntegrado:
    """Cliente integrado com comunicação síncrona (sockets) e assíncrona (RabbitMQ)"""
    
    def __init__(self):
        """Inicializa o cliente integrado"""
        # Socket connection
        self.socket_cliente = None
        self.conectado_socket = False
        self.usuario = None
        self.thread_recebimento_socket = None
        
        # RabbitMQ connection
        self.configurador_rabbitmq = None
        self.publisher = None
        self.consumer = None
        self.conectado_rabbitmq = False
        
        # Lista de usuários online e no raio
        self.usuarios_disponiveis: List[dict] = []
        
        # Configuração da interface
        self.root = tk.Tk()
        self.root.title("GeoChat - Cliente Integrado")
        self.root.geometry("900x700")
        self.root.protocol("WM_DELETE_WINDOW", self.fechar_aplicacao)
        
        self.criar_interface()
    
    def criar_interface(self):
        """Cria a interface gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuração da grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Seção de conexão
        self.criar_secao_conexao(main_frame)
        
        # Seção de localização
        self.criar_secao_localizacao(main_frame)
        
        # Seção de RabbitMQ
        self.criar_secao_rabbitmq(main_frame)
        
        # Seção de usuários disponíveis
        self.criar_secao_usuarios(main_frame)
        
        # Seção de chat
        self.criar_secao_chat(main_frame)
        
        # Status bar
        self.criar_status_bar(main_frame)
    
    def criar_secao_conexao(self, parent):
        """Cria seção de conexão ao servidor"""
        conn_frame = ttk.LabelFrame(parent, text="Conexão Socket", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        conn_frame.columnconfigure(1, weight=1)
        conn_frame.columnconfigure(3, weight=1)
        
        ttk.Label(conn_frame, text="Nome:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.entry_nome = ttk.Entry(conn_frame, width=20)
        self.entry_nome.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(conn_frame, text="Servidor:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.entry_servidor = ttk.Entry(conn_frame, width=20)
        self.entry_servidor.insert(0, f"{config.SOCKET_HOST}:{config.SOCKET_PORT}")
        self.entry_servidor.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.btn_conectar_socket = ttk.Button(conn_frame, text="Conectar Socket", 
                                            command=self.conectar_desconectar_socket)
        self.btn_conectar_socket.grid(row=0, column=4, padx=(10, 0))
    
    def criar_secao_localizacao(self, parent):
        """Cria seção de localização"""
        loc_frame = ttk.LabelFrame(parent, text="Localização e Raio", padding="5")
        loc_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        loc_frame.columnconfigure(1, weight=1)
        loc_frame.columnconfigure(3, weight=1)
        loc_frame.columnconfigure(5, weight=1)
        
        ttk.Label(loc_frame, text="Latitude:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.entry_latitude = ttk.Entry(loc_frame, width=15)
        self.entry_latitude.insert(0, "-23.5505")
        self.entry_latitude.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(loc_frame, text="Longitude:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.entry_longitude = ttk.Entry(loc_frame, width=15)
        self.entry_longitude.insert(0, "-46.6333")
        self.entry_longitude.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(loc_frame, text="Raio (m):").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.entry_raio = ttk.Entry(loc_frame, width=10)
        self.entry_raio.insert(0, "1000")
        self.entry_raio.grid(row=0, column=5, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.btn_atualizar_loc = ttk.Button(loc_frame, text="Atualizar", 
                                          command=self.atualizar_localizacao, state="disabled")
        self.btn_atualizar_loc.grid(row=0, column=6, padx=(10, 0))
    
    def criar_secao_rabbitmq(self, parent):
        """Cria seção de configuração do RabbitMQ"""
        rabbit_frame = ttk.LabelFrame(parent, text="RabbitMQ (Mensagens Assíncronas)", padding="5")
        rabbit_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        rabbit_frame.columnconfigure(1, weight=1)
        rabbit_frame.columnconfigure(3, weight=1)
        
        ttk.Label(rabbit_frame, text="Host RabbitMQ:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.entry_rabbit_host = ttk.Entry(rabbit_frame, width=15)
        self.entry_rabbit_host.insert(0, config.RABBITMQ_HOST)
        self.entry_rabbit_host.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(rabbit_frame, text="Porta:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.entry_rabbit_porta = ttk.Entry(rabbit_frame, width=10)
        self.entry_rabbit_porta.insert(0, str(config.RABBITMQ_PORT))
        self.entry_rabbit_porta.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.btn_conectar_rabbit = ttk.Button(rabbit_frame, text="Conectar RabbitMQ", 
                                            command=self.conectar_desconectar_rabbitmq, state="disabled")
        self.btn_conectar_rabbit.grid(row=0, column=4, padx=(10, 0))
    
    def criar_secao_usuarios(self, parent):
        """Cria seção de usuários disponíveis"""
        users_frame = ttk.LabelFrame(parent, text="Usuários Disponíveis", padding="5")
        users_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        users_frame.columnconfigure(0, weight=1)
        
        columns = ('nome', 'distancia', 'no_raio', 'status', 'comunicacao')
        self.tree_usuarios = ttk.Treeview(users_frame, columns=columns, show='headings', height=6)
        
        self.tree_usuarios.heading('nome', text='Nome')
        self.tree_usuarios.heading('distancia', text='Distância (m)')
        self.tree_usuarios.heading('no_raio', text='No Raio')
        self.tree_usuarios.heading('status', text='Status')
        self.tree_usuarios.heading('comunicacao', text='Tipo Comunicação')
        
        self.tree_usuarios.column('nome', width=120)
        self.tree_usuarios.column('distancia', width=100)
        self.tree_usuarios.column('no_raio', width=70)
        self.tree_usuarios.column('status', width=80)
        self.tree_usuarios.column('comunicacao', width=150)
        
        scrollbar_users = ttk.Scrollbar(users_frame, orient=tk.VERTICAL, command=self.tree_usuarios.yview)
        self.tree_usuarios.configure(yscrollcommand=scrollbar_users.set)
        
        self.tree_usuarios.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_users.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.btn_atualizar_usuarios = ttk.Button(users_frame, text="Atualizar Lista", 
                                               command=self.atualizar_lista_usuarios, state="disabled")
        self.btn_atualizar_usuarios.grid(row=1, column=0, columnspan=2, pady=(5, 0))
    
    def criar_secao_chat(self, parent):
        """Cria seção de chat"""
        chat_frame = ttk.LabelFrame(parent, text="Chat (Síncrono + Assíncrono)", padding="5")
        chat_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        self.text_mensagens = scrolledtext.ScrolledText(chat_frame, height=15, state='disabled')
        self.text_mensagens.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        envio_frame = ttk.Frame(chat_frame)
        envio_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E))
        envio_frame.columnconfigure(1, weight=1)
        envio_frame.columnconfigure(3, weight=1)
        
        ttk.Label(envio_frame, text="Para:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.combo_destinatario = ttk.Combobox(envio_frame, width=20, state="readonly")
        self.combo_destinatario.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(envio_frame, text="Tipo:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.combo_tipo_envio = ttk.Combobox(envio_frame, width=15, state="readonly")
        self.combo_tipo_envio['values'] = ['Auto', 'Síncrono', 'Assíncrono']
        self.combo_tipo_envio.set('Auto')
        self.combo_tipo_envio.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(envio_frame, text="Mensagem:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.entry_mensagem = ttk.Entry(envio_frame)
        self.entry_mensagem.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        self.entry_mensagem.bind('<Return>', self.enviar_mensagem_enter)
        
        self.btn_enviar = ttk.Button(envio_frame, text="Enviar", 
                                   command=self.enviar_mensagem, state="disabled")
        self.btn_enviar.grid(row=1, column=3, padx=(10, 0), pady=(5, 0))
    
    def criar_status_bar(self, parent):
        """Cria barra de status"""
        self.status_var = tk.StringVar()
        self.status_var.set("Desconectado")
        
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky=tk.W)
        self.label_status = ttk.Label(status_frame, textvariable=self.status_var)
        self.label_status.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
    
    def conectar_desconectar_socket(self):
        """Conecta ou desconecta do servidor socket"""
        if not self.conectado_socket:
            self.conectar_socket()
        else:
            self.desconectar_socket()
    
    def conectar_socket(self):
        """Conecta ao servidor socket"""
        try:
            nome = self.entry_nome.get().strip()
            if not nome:
                messagebox.showerror("Erro", "Nome é obrigatório")
                return
            
            servidor_info = self.entry_servidor.get().strip()
            if ':' not in servidor_info:
                messagebox.showerror("Erro", "Formato do servidor deve ser host:porta")
                return
            
            host, porta = servidor_info.split(':', 1)
            porta = int(porta)
            
            try:
                latitude = float(self.entry_latitude.get())
                longitude = float(self.entry_longitude.get())
                raio = float(self.entry_raio.get())
            except ValueError:
                messagebox.showerror("Erro", "Localização e raio devem ser números válidos")
                return
            
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((host, porta))
            
            self.usuario = Usuario(nome, latitude, longitude, raio, StatusUsuario.ONLINE)
            
            mensagem_conexao = {
                'tipo': 'conectar',
                'usuario': self.usuario.to_dict()
            }
            self._enviar_mensagem_socket(mensagem_conexao)
            
            resposta = self._receber_mensagem_socket()
            if resposta and resposta.get('tipo') == 'conexao_aceita':
                self.conectado_socket = True
                self._atualizar_interface_socket_conectado()
                self._iniciar_thread_recebimento_socket()
                self.adicionar_mensagem_sistema(f"Conectado ao servidor como {nome}")
                self.atualizar_lista_usuarios()
                
                # Habilita conexão RabbitMQ
                self.btn_conectar_rabbit.config(state="normal")
            else:
                erro = resposta.get('mensagem', 'Erro desconhecido') if resposta else 'Sem resposta do servidor'
                messagebox.showerror("Erro", f"Falha na conexão: {erro}")
                self.socket_cliente.close()
                self.socket_cliente = None
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao conectar: {str(e)}")
            if self.socket_cliente:
                try:
                    self.socket_cliente.close()
                except:
                    pass
                self.socket_cliente = None
    
    def desconectar_socket(self):
        """Desconecta do servidor socket"""
        try:
            self.conectado_socket = False
            
            if self.socket_cliente:
                self.socket_cliente.close()
                self.socket_cliente = None
            
            if self.thread_recebimento_socket and self.thread_recebimento_socket.is_alive():
                self.thread_recebimento_socket.join(timeout=1)
            
            self._atualizar_interface_socket_desconectado()
            self.adicionar_mensagem_sistema("Desconectado do servidor")
            
            # Desabilita RabbitMQ se conectado
            if self.conectado_rabbitmq:
                self.desconectar_rabbitmq()
            
        except Exception as e:
            print(f"Erro ao desconectar socket: {e}")
    
    def conectar_desconectar_rabbitmq(self):
        """Conecta ou desconecta do RabbitMQ"""
        if not self.conectado_rabbitmq:
            self.conectar_rabbitmq()
        else:
            self.desconectar_rabbitmq()
    
    def conectar_rabbitmq(self):
        """Conecta ao RabbitMQ"""
        try:
            if not self.usuario:
                messagebox.showerror("Erro", "Conecte-se ao servidor socket primeiro")
                return
            
            host = self.entry_rabbit_host.get().strip()
            porta = int(self.entry_rabbit_porta.get().strip())
            
            self.configurador_rabbitmq = ConfiguradorRabbitMQ(host, porta)
            
            if not self.configurador_rabbitmq.conectar():
                messagebox.showerror("Erro", "Falha ao conectar ao RabbitMQ")
                return
            
            if not self.configurador_rabbitmq.configurar_topologia():
                messagebox.showerror("Erro", "Falha ao configurar topologia RabbitMQ")
                return
            
            if not self.configurador_rabbitmq.criar_fila_usuario(self.usuario.nome):
                messagebox.showerror("Erro", "Falha ao criar filas do usuário")
                return
            
            # Configura publisher
            self.publisher = PublisherMensagem(self.configurador_rabbitmq)
            if not self.publisher.conectar():
                messagebox.showerror("Erro", "Falha ao conectar publisher")
                return
            
            # Configura consumer
            self.consumer = ConsumerMensagem(self.configurador_rabbitmq, self.usuario.nome)
            if not self.consumer.conectar():
                messagebox.showerror("Erro", "Falha ao conectar consumer")
                return
            
            # Define callbacks
            self.consumer.definir_callback_mensagem(self.on_mensagem_assincrona)
            self.consumer.definir_callback_localizacao(self.on_atualizacao_localizacao)
            
            if not self.consumer.iniciar_consumo():
                messagebox.showerror("Erro", "Falha ao iniciar consumo")
                return
            
            self.conectado_rabbitmq = True
            self._atualizar_interface_rabbitmq_conectado()
            self.adicionar_mensagem_sistema("Conectado ao RabbitMQ - mensagens assíncronas habilitadas")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao conectar RabbitMQ: {str(e)}")
    
    def desconectar_rabbitmq(self):
        """Desconecta do RabbitMQ"""
        try:
            self.conectado_rabbitmq = False
            
            if self.consumer:
                self.consumer.desconectar()
                self.consumer = None
            
            if self.publisher:
                self.publisher.desconectar()
                self.publisher = None
            
            if self.configurador_rabbitmq:
                self.configurador_rabbitmq.desconectar()
                self.configurador_rabbitmq = None
            
            self._atualizar_interface_rabbitmq_desconectado()
            self.adicionar_mensagem_sistema("Desconectado do RabbitMQ")
            
        except Exception as e:
            print(f"Erro ao desconectar RabbitMQ: {e}")
    
    def atualizar_localizacao(self):
        """Atualiza localização no servidor e RabbitMQ"""
        if not self.conectado_socket:
            return
        
        try:
            latitude = float(self.entry_latitude.get())
            longitude = float(self.entry_longitude.get())
            
            # Atualiza no servidor socket
            mensagem = {
                'tipo': 'atualizar_localizacao',
                'latitude': latitude,
                'longitude': longitude
            }
            self._enviar_mensagem_socket(mensagem)
            self.usuario.atualizar_localizacao(latitude, longitude)
            
            # Publica no RabbitMQ se conectado
            if self.conectado_rabbitmq and self.publisher:
                self.publisher.publicar_atualizacao_localizacao(self.usuario)
            
        except ValueError:
            messagebox.showerror("Erro", "Latitude e longitude devem ser números válidos")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar localização: {str(e)}")
    
    def atualizar_lista_usuarios(self):
        """Atualiza lista de usuários disponíveis"""
        if not self.conectado_socket:
            return
        
        try:
            mensagem = {'tipo': 'listar_usuarios'}
            self._enviar_mensagem_socket(mensagem)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar lista: {str(e)}")
    
    def enviar_mensagem(self):
        """Envia mensagem (síncrona ou assíncrona conforme configuração)"""
        destinatario = self.combo_destinatario.get()
        conteudo = self.entry_mensagem.get().strip()
        tipo_envio = self.combo_tipo_envio.get()
        
        if not destinatario or not conteudo:
            messagebox.showwarning("Aviso", "Selecione um destinatário e digite uma mensagem")
            return
        
        try:
            # Encontra informações do destinatário
            usuario_destinatario = None
            for usuario in self.usuarios_disponiveis:
                if usuario['nome'] == destinatario:
                    usuario_destinatario = usuario
                    break
            
            if not usuario_destinatario:
                messagebox.showerror("Erro", "Destinatário não encontrado")
                return
            
            # LÓGICA DE DECISÃO AUTOMÁTICA: Core do sistema híbrido
            # Determina automaticamente se usa comunicação síncrona ou assíncrona
            if tipo_envio == 'Auto':
                # CRITÉRIOS PARA SÍNCRONO: online + no raio + socket conectado
                if (usuario_destinatario['status'] == 'online' and 
                    usuario_destinatario['no_raio'] and 
                    self.conectado_socket):
                    self._enviar_mensagem_sincrona(destinatario, conteudo)
                
                # FALLBACK PARA ASSÍNCRONO: qualquer falha nos critérios acima
                elif self.conectado_rabbitmq:
                    # DECISÃO INTELIGENTE: determina motivo para debugging
                    motivo = "offline" if usuario_destinatario['status'] == 'offline' else "fora_do_raio"
                    self._enviar_mensagem_assincrona(destinatario, conteudo, motivo)
                else:
                    messagebox.showerror("Erro", "Não é possível enviar mensagem - destinatário offline/fora do raio e RabbitMQ não conectado")
                    return
            
            # MODO FORÇADO SÍNCRONO: usuário escolhe explicitamente
            elif tipo_envio == 'Síncrono':
                if self.conectado_socket:
                    self._enviar_mensagem_sincrona(destinatario, conteudo)
                else:
                    messagebox.showerror("Erro", "Conexão socket não disponível")
                    return
            
            # MODO FORÇADO ASSÍNCRONO: usuário escolhe explicitamente
            elif tipo_envio == 'Assíncrono':
                if self.conectado_rabbitmq:
                    self._enviar_mensagem_assincrona(destinatario, conteudo, "forcado")
                else:
                    messagebox.showerror("Erro", "Conexão RabbitMQ não disponível")
                    return
            
            self.entry_mensagem.delete(0, tk.END)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao enviar mensagem: {str(e)}")
    
    def _enviar_mensagem_sincrona(self, destinatario: str, conteudo: str):
        """Envia mensagem síncrona via socket"""
        mensagem = {
            'tipo': 'enviar_mensagem',
            'destinatario': destinatario,
            'conteudo': conteudo
        }
        self._enviar_mensagem_socket(mensagem)
        self.adicionar_mensagem_enviada(destinatario, conteudo, "Síncrona")
    
    def _enviar_mensagem_assincrona(self, destinatario: str, conteudo: str, motivo: str):
        """Envia mensagem assíncrona via RabbitMQ"""
        if self.publisher:
            if self.publisher.enviar_mensagem_assincrona(self.usuario.nome, destinatario, conteudo, motivo):
                self.adicionar_mensagem_enviada(destinatario, conteudo, f"Assíncrona ({motivo})")
            else:
                messagebox.showerror("Erro", "Falha ao enviar mensagem assíncrona")
    
    def enviar_mensagem_enter(self, event):
        """Envia mensagem quando Enter é pressionado"""
        self.enviar_mensagem()
    
    def on_mensagem_assincrona(self, dados: dict):
        """Callback para mensagem assíncrona recebida"""
        remetente = dados['remetente']
        conteudo = dados['conteudo']
        motivo = dados.get('motivo', 'desconhecido')
        
        self.root.after(0, lambda: self.adicionar_mensagem_recebida(remetente, conteudo, f"Assíncrona ({motivo})"))
    
    def on_atualizacao_localizacao(self, dados: dict):
        """Callback para atualização de localização recebida"""
        usuario_dados = dados['usuario']
        nome = usuario_dados['nome']
        
        self.root.after(0, lambda: self.adicionar_mensagem_sistema(f"Localização atualizada: {nome}"))
        self.root.after(0, self.atualizar_lista_usuarios)
    
    def adicionar_mensagem_sistema(self, mensagem: str):
        """Adiciona mensagem do sistema na área de chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        texto = f"[{timestamp}] SISTEMA: {mensagem}\n"
        
        self.text_mensagens.config(state='normal')
        self.text_mensagens.insert(tk.END, texto)
        self.text_mensagens.config(state='disabled')
        self.text_mensagens.see(tk.END)
    
    def adicionar_mensagem_enviada(self, destinatario: str, conteudo: str, tipo: str):
        """Adiciona mensagem enviada na área de chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        texto = f"[{timestamp}] Você -> {destinatario} ({tipo}): {conteudo}\n"
        
        self.text_mensagens.config(state='normal')
        self.text_mensagens.insert(tk.END, texto)
        self.text_mensagens.config(state='disabled')
        self.text_mensagens.see(tk.END)
    
    def adicionar_mensagem_recebida(self, remetente: str, conteudo: str, tipo: str):
        """Adiciona mensagem recebida na área de chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        texto = f"[{timestamp}] {remetente} ({tipo}): {conteudo}\n"
        
        self.text_mensagens.config(state='normal')
        self.text_mensagens.insert(tk.END, texto)
        self.text_mensagens.config(state='disabled')
        self.text_mensagens.see(tk.END)
    
    def _atualizar_interface_socket_conectado(self):
        """Atualiza interface quando socket conectado"""
        self.btn_conectar_socket.config(text="Desconectar Socket")
        self.btn_atualizar_loc.config(state="normal")
        self.btn_atualizar_usuarios.config(state="normal")
        self.btn_enviar.config(state="normal")
        
        self.entry_nome.config(state="disabled")
        self.entry_servidor.config(state="disabled")
        
        self._atualizar_status()
    
    def _atualizar_interface_socket_desconectado(self):
        """Atualiza interface quando socket desconectado"""
        self.btn_conectar_socket.config(text="Conectar Socket")
        self.btn_atualizar_loc.config(state="disabled")
        self.btn_atualizar_usuarios.config(state="disabled")
        self.btn_enviar.config(state="disabled")
        self.btn_conectar_rabbit.config(state="disabled")
        
        self.entry_nome.config(state="normal")
        self.entry_servidor.config(state="normal")
        
        self.tree_usuarios.delete(*self.tree_usuarios.get_children())
        self.combo_destinatario.set('')
        self.combo_destinatario['values'] = []
        
        self._atualizar_status()
    
    def _atualizar_interface_rabbitmq_conectado(self):
        """Atualiza interface quando RabbitMQ conectado"""
        self.btn_conectar_rabbit.config(text="Desconectar RabbitMQ")
        self.entry_rabbit_host.config(state="disabled")
        self.entry_rabbit_porta.config(state="disabled")
        self._atualizar_status()
    
    def _atualizar_interface_rabbitmq_desconectado(self):
        """Atualiza interface quando RabbitMQ desconectado"""
        self.btn_conectar_rabbit.config(text="Conectar RabbitMQ")
        self.entry_rabbit_host.config(state="normal")
        self.entry_rabbit_porta.config(state="normal")
        self._atualizar_status()
    
    def _atualizar_status(self):
        """Atualiza barra de status"""
        status_parts = []
        
        if self.conectado_socket:
            status_parts.append(f"Socket: {self.usuario.nome}")
        else:
            status_parts.append("Socket: Desconectado")
        
        if self.conectado_rabbitmq:
            status_parts.append("RabbitMQ: Conectado")
        else:
            status_parts.append("RabbitMQ: Desconectado")
        
        self.status_var.set(" | ".join(status_parts))
    
    def _iniciar_thread_recebimento_socket(self):
        """Inicia thread para receber mensagens do socket"""
        self.thread_recebimento_socket = threading.Thread(target=self._receber_mensagens_socket_loop, daemon=True)
        self.thread_recebimento_socket.start()
    
    def _receber_mensagens_socket_loop(self):
        """Loop para receber mensagens do socket"""
        while self.conectado_socket:
            try:
                mensagem = self._receber_mensagem_socket()
                if mensagem:
                    self._processar_mensagem_socket_recebida(mensagem)
                else:
                    break
            except Exception as e:
                if self.conectado_socket:
                    print(f"Erro ao receber mensagem socket: {e}")
                break
        
        if self.conectado_socket:
            self.root.after(0, self._conexao_socket_perdida)
    
    def _processar_mensagem_socket_recebida(self, mensagem: dict):
        """Processa mensagem recebida do socket"""
        tipo = mensagem.get('tipo')
        
        if tipo == 'mensagem_recebida':
            remetente = mensagem['remetente']
            conteudo = mensagem['conteudo']
            self.root.after(0, lambda: self.adicionar_mensagem_recebida(remetente, conteudo, "Síncrona"))
        
        elif tipo == 'lista_usuarios':
            usuarios = mensagem['usuarios']
            self.root.after(0, lambda: self._atualizar_lista_usuarios_gui(usuarios))
        
        elif tipo == 'erro':
            erro = mensagem['mensagem']
            self.root.after(0, lambda: messagebox.showerror("Erro do Servidor", erro))
    
    def _atualizar_lista_usuarios_gui(self, usuarios: List[dict]):
        """
        Atualiza GUI com lista de usuários
        
        INTERFACE INTELIGENTE: Calcula automaticamente que tipos de comunicação
        estão disponíveis para cada usuário baseado em:
        1. Status online/offline
        2. Distância dentro/fora do raio
        3. Conexões disponíveis (socket/RabbitMQ)
        
        FEEDBACK VISUAL: TreeView mostra claramente as opções para cada usuário
        """
        self.tree_usuarios.delete(*self.tree_usuarios.get_children())
        self.usuarios_disponiveis = usuarios
        
        usuarios_para_combo = []
        
        for usuario in usuarios:
            nome = usuario['nome']
            distancia = f"{usuario['distancia']:.1f}"
            no_raio = "Sim" if usuario['no_raio'] else "Não"
            status = usuario['status']
            
            # LÓGICA DE DISPONIBILIDADE: Determina que comunicação é possível
            if status == 'online' and usuario['no_raio']:
                # Usuário online + no raio: síncrona sempre disponível
                if self.conectado_rabbitmq:
                    tipo_com = "Síncrona + Assíncrona"  # Ambas opções
                else:
                    tipo_com = "Síncrona"  # Só síncrona
            elif self.conectado_rabbitmq:
                # Usuário offline ou fora do raio: só assíncrona se RabbitMQ conectado
                tipo_com = "Assíncrona"
            else:
                # Sem opções de comunicação
                tipo_com = "Indisponível"
            
            self.tree_usuarios.insert('', 'end', values=(nome, distancia, no_raio, status, tipo_com))
            
            # Adiciona ao combobox apenas usuários com comunicação disponível
            if tipo_com != "Indisponível":
                usuarios_para_combo.append(nome)
        
        # Atualiza combobox de destinatários
        self.combo_destinatario['values'] = usuarios_para_combo
        if usuarios_para_combo and not self.combo_destinatario.get():
            self.combo_destinatario.set(usuarios_para_combo[0])
    
    def _conexao_socket_perdida(self):
        """Chamado quando conexão socket é perdida"""
        messagebox.showerror("Erro", "Conexão com o servidor foi perdida")
        self.desconectar_socket()
    
    def _enviar_mensagem_socket(self, mensagem: dict):
        """Envia mensagem para o servidor socket"""
        if self.socket_cliente:
            dados = json.dumps(mensagem).encode('utf-8')
            self.socket_cliente.send(dados)
    
    def _receber_mensagem_socket(self) -> Optional[dict]:
        """Recebe mensagem do servidor socket"""
        try:
            dados = self.socket_cliente.recv(4096)
            if dados:
                return json.loads(dados.decode('utf-8'))
        except:
            pass
        return None
    
    def fechar_aplicacao(self):
        """
        Fecha a aplicação graciosamente
        
        CLEANUP RESPONSÁVEL: Garante que todas as conexões sejam fechadas
        adequadamente antes de terminar a aplicação. Importante para:
        1. Liberar recursos de rede
        2. Notificar servidor sobre desconexão
        3. Fechar threads de recebimento
        4. Evitar conexões órfãs no RabbitMQ
        """
        if self.conectado_rabbitmq:
            self.desconectar_rabbitmq()
        if self.conectado_socket:
            self.desconectar_socket()
        self.root.destroy()
    
    def executar(self):
        """Executa a aplicação"""
        self.root.mainloop()

if __name__ == "__main__":
    cliente = ClienteIntegrado()
    cliente.executar()
