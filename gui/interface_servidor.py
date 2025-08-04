import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
from typing import List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.servidor_socket import ServidorSocket
from common.usuario import Usuario

class InterfaceServidor:
    """Interface Tkinter para administração do servidor"""
    
    def __init__(self):
        """Inicializa a interface do servidor"""
        self.servidor = None
        self.servidor_rodando = False
        self.thread_atualizacao = None
        
        # Configuração da interface
        self.root = tk.Tk()
        self.root.title("GeoChat - Servidor")
        self.root.geometry("900x700")
        self.root.protocol("WM_DELETE_WINDOW", self.fechar_aplicacao)
        
        self.criar_interface()
        self.configurar_servidor()
    
    def criar_interface(self):
        """Cria a interface gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuração da grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Seção de controle do servidor
        self.criar_secao_controle(main_frame)
        
        # Seção de estatísticas
        self.criar_secao_estatisticas(main_frame)
        
        # Seção de usuários conectados
        self.criar_secao_usuarios(main_frame)
        
        # Seção de logs
        self.criar_secao_logs(main_frame)
        
        # Barra de status
        self.criar_status_bar(main_frame)
    
    def criar_secao_controle(self, parent):
        """Cria seção de controle do servidor"""
        controle_frame = ttk.LabelFrame(parent, text="Controle do Servidor", padding="10")
        controle_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        controle_frame.columnconfigure(1, weight=1)
        controle_frame.columnconfigure(3, weight=1)
        
        # Configurações do servidor
        ttk.Label(controle_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.entry_host = ttk.Entry(controle_frame, width=15)
        self.entry_host.insert(0, "localhost")
        self.entry_host.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(controle_frame, text="Porta:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.entry_porta = ttk.Entry(controle_frame, width=10)
        self.entry_porta.insert(0, "8888")
        self.entry_porta.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Botões de controle
        self.btn_iniciar = ttk.Button(controle_frame, text="Iniciar Servidor", 
                                     command=self.iniciar_servidor)
        self.btn_iniciar.grid(row=0, column=4, padx=(10, 0))
        
        self.btn_parar = ttk.Button(controle_frame, text="Parar Servidor", 
                                   command=self.parar_servidor, state="disabled")
        self.btn_parar.grid(row=0, column=5, padx=(10, 0))
    
    def criar_secao_estatisticas(self, parent):
        """Cria seção de estatísticas"""
        stats_frame = ttk.LabelFrame(parent, text="Estatísticas", padding="10")
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Labels para estatísticas
        self.label_usuarios_conectados = ttk.Label(stats_frame, text="Usuários Conectados: 0")
        self.label_usuarios_conectados.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        self.label_tempo_funcionamento = ttk.Label(stats_frame, text="Tempo de Funcionamento: 00:00:00")
        self.label_tempo_funcionamento.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.label_mensagens_enviadas = ttk.Label(stats_frame, text="Mensagens Enviadas: 0")
        self.label_mensagens_enviadas.grid(row=0, column=2, sticky=tk.W)
        
        # Botão de atualização manual
        self.btn_atualizar_stats = ttk.Button(stats_frame, text="Atualizar", 
                                             command=self.atualizar_estatisticas)
        self.btn_atualizar_stats.grid(row=0, column=3, padx=(20, 0))
        
        # Variáveis para estatísticas
        self.tempo_inicio = None
        self.contador_mensagens = 0
    
    def criar_secao_usuarios(self, parent):
        """Cria seção de usuários conectados"""
        usuarios_frame = ttk.LabelFrame(parent, text="Usuários Conectados", padding="10")
        usuarios_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        usuarios_frame.columnconfigure(0, weight=1)
        usuarios_frame.rowconfigure(0, weight=1)
        
        # Treeview para listar usuários
        columns = ('nome', 'latitude', 'longitude', 'raio', 'status', 'conexao_tempo')
        self.tree_usuarios = ttk.Treeview(usuarios_frame, columns=columns, show='headings')
        
        self.tree_usuarios.heading('nome', text='Nome')
        self.tree_usuarios.heading('latitude', text='Latitude')
        self.tree_usuarios.heading('longitude', text='Longitude')
        self.tree_usuarios.heading('raio', text='Raio (m)')
        self.tree_usuarios.heading('status', text='Status')
        self.tree_usuarios.heading('conexao_tempo', text='Conectado em')
        
        self.tree_usuarios.column('nome', width=120)
        self.tree_usuarios.column('latitude', width=100)
        self.tree_usuarios.column('longitude', width=100)
        self.tree_usuarios.column('raio', width=80)
        self.tree_usuarios.column('status', width=80)
        self.tree_usuarios.column('conexao_tempo', width=150)
        
        # Scrollbars
        scrollbar_v = ttk.Scrollbar(usuarios_frame, orient=tk.VERTICAL, command=self.tree_usuarios.yview)
        scrollbar_h = ttk.Scrollbar(usuarios_frame, orient=tk.HORIZONTAL, command=self.tree_usuarios.xview)
        
        self.tree_usuarios.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        self.tree_usuarios.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Frame para ações com usuários
        acoes_frame = ttk.Frame(usuarios_frame)
        acoes_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.btn_desconectar_usuario = ttk.Button(acoes_frame, text="Desconectar Usuário Selecionado", 
                                                 command=self.desconectar_usuario_selecionado, 
                                                 state="disabled")
        self.btn_desconectar_usuario.grid(row=0, column=0, padx=(0, 10))
        
        self.btn_atualizar_usuarios = ttk.Button(acoes_frame, text="Atualizar Lista", 
                                                command=self.atualizar_lista_usuarios)
        self.btn_atualizar_usuarios.grid(row=0, column=1)
        
        # Dicionário para armazenar tempos de conexão
        self.tempos_conexao = {}
    
    def criar_secao_logs(self, parent):
        """Cria seção de logs"""
        logs_frame = ttk.LabelFrame(parent, text="Logs do Servidor", padding="10")
        logs_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        # Área de logs
        self.text_logs = scrolledtext.ScrolledText(logs_frame, height=12, state='disabled')
        self.text_logs.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame para controles de log
        log_controles = ttk.Frame(logs_frame)
        log_controles.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.btn_limpar_logs = ttk.Button(log_controles, text="Limpar Logs", 
                                         command=self.limpar_logs)
        self.btn_limpar_logs.grid(row=0, column=0)
        
        # Checkbox para auto-scroll
        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.check_auto_scroll = ttk.Checkbutton(log_controles, text="Auto-scroll", 
                                                variable=self.auto_scroll_var)
        self.check_auto_scroll.grid(row=0, column=1, padx=(20, 0))
    
    def criar_status_bar(self, parent):
        """Cria barra de status"""
        self.status_var = tk.StringVar()
        self.status_var.set("Servidor parado")
        
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky=tk.W)
        self.label_status = ttk.Label(status_frame, textvariable=self.status_var)
        self.label_status.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
    
    def configurar_servidor(self):
        """Configura o servidor com callbacks"""
        self.servidor = ServidorSocket()
        
        # Configura callbacks
        self.servidor.adicionar_callback_usuario_conectado(self.on_usuario_conectado)
        self.servidor.adicionar_callback_usuario_desconectado(self.on_usuario_desconectado)
        self.servidor.adicionar_callback_mensagem_recebida(self.on_mensagem_recebida)
    
    def iniciar_servidor(self):
        """Inicia o servidor"""
        try:
            host = self.entry_host.get().strip()
            porta = int(self.entry_porta.get().strip())
            
            if not host:
                messagebox.showerror("Erro", "Host é obrigatório")
                return
            
            # Reconfigura servidor com novos parâmetros
            self.servidor = ServidorSocket(host, porta)
            self.servidor.adicionar_callback_usuario_conectado(self.on_usuario_conectado)
            self.servidor.adicionar_callback_usuario_desconectado(self.on_usuario_desconectado)
            self.servidor.adicionar_callback_mensagem_recebida(self.on_mensagem_recebida)
            
            if self.servidor.iniciar_servidor():
                self.servidor_rodando = True
                self.tempo_inicio = datetime.now()
                self.contador_mensagens = 0
                
                self._atualizar_interface_iniciado()
                self._iniciar_thread_atualizacao()
                self.adicionar_log(f"Servidor iniciado em {host}:{porta}")
                
            else:
                messagebox.showerror("Erro", "Falha ao iniciar servidor")
        
        except ValueError:
            messagebox.showerror("Erro", "Porta deve ser um número válido")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar servidor: {str(e)}")
    
    def parar_servidor(self):
        """Para o servidor"""
        try:
            if self.servidor and self.servidor_rodando:
                self.servidor.parar_servidor()
                self.servidor_rodando = False
                
                self._atualizar_interface_parado()
                self.adicionar_log("Servidor parado")
                
                # Para thread de atualização
                if self.thread_atualizacao and self.thread_atualizacao.is_alive():
                    self.thread_atualizacao.join(timeout=1)
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao parar servidor: {str(e)}")
    
    def desconectar_usuario_selecionado(self):
        """Desconecta usuário selecionado"""
        selecao = self.tree_usuarios.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um usuário para desconectar")
            return
        
        item = self.tree_usuarios.item(selecao[0])
        nome_usuario = item['values'][0]
        
        resultado = messagebox.askyesno("Confirmar", 
                                       f"Desconectar usuário '{nome_usuario}'?")
        if resultado:
            try:
                # Implementação seria adicionar método no servidor para desconectar usuário específico
                self.adicionar_log(f"Solicitada desconexão do usuário: {nome_usuario}")
                messagebox.showinfo("Info", "Funcionalidade será implementada")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao desconectar usuário: {str(e)}")
    
    def atualizar_lista_usuarios(self):
        """Atualiza lista de usuários conectados"""
        if not self.servidor_rodando:
            return
        
        try:
            # Limpa lista atual
            self.tree_usuarios.delete(*self.tree_usuarios.get_children())
            
            # Obtém usuários conectados
            usuarios = self.servidor.obter_usuarios_conectados()
            
            for usuario in usuarios:
                tempo_conexao = self.tempos_conexao.get(usuario.nome, "N/A")
                valores = (
                    usuario.nome,
                    f"{usuario.latitude:.6f}",
                    f"{usuario.longitude:.6f}",
                    f"{usuario.raio_comunicacao:.0f}",
                    usuario.status.value,
                    tempo_conexao
                )
                
                self.tree_usuarios.insert('', 'end', values=valores)
            
            # Atualiza botão de desconexão
            if usuarios:
                self.btn_desconectar_usuario.config(state="normal")
            else:
                self.btn_desconectar_usuario.config(state="disabled")
        
        except Exception as e:
            self.adicionar_log(f"Erro ao atualizar lista de usuários: {e}")
    
    def atualizar_estatisticas(self):
        """Atualiza estatísticas do servidor"""
        if not self.servidor_rodando:
            return
        
        try:
            stats = self.servidor.obter_estatisticas()
            
            # Atualiza labels
            self.label_usuarios_conectados.config(text=f"Usuários Conectados: {stats['usuarios_conectados']}")
            
            if self.tempo_inicio:
                tempo_funcionamento = datetime.now() - self.tempo_inicio
                horas, resto = divmod(tempo_funcionamento.total_seconds(), 3600)
                minutos, segundos = divmod(resto, 60)
                tempo_str = f"{int(horas):02d}:{int(minutos):02d}:{int(segundos):02d}"
                self.label_tempo_funcionamento.config(text=f"Tempo de Funcionamento: {tempo_str}")
            
            self.label_mensagens_enviadas.config(text=f"Mensagens Enviadas: {self.contador_mensagens}")
        
        except Exception as e:
            self.adicionar_log(f"Erro ao atualizar estatísticas: {e}")
    
    def _atualizar_interface_iniciado(self):
        """Atualiza interface quando servidor é iniciado"""
        self.btn_iniciar.config(state="disabled")
        self.btn_parar.config(state="normal")
        self.entry_host.config(state="disabled")
        self.entry_porta.config(state="disabled")
        self.status_var.set(f"Servidor rodando em {self.entry_host.get()}:{self.entry_porta.get()}")
    
    def _atualizar_interface_parado(self):
        """Atualiza interface quando servidor é parado"""
        self.btn_iniciar.config(state="normal")
        self.btn_parar.config(state="disabled")
        self.entry_host.config(state="normal")
        self.entry_porta.config(state="normal")
        self.status_var.set("Servidor parado")
        
        # Limpa listas
        self.tree_usuarios.delete(*self.tree_usuarios.get_children())
        self.btn_desconectar_usuario.config(state="disabled")
        self.tempos_conexao.clear()
    
    def _iniciar_thread_atualizacao(self):
        """Inicia thread para atualização automática"""
        self.thread_atualizacao = threading.Thread(target=self._loop_atualizacao, daemon=True)
        self.thread_atualizacao.start()
    
    def _loop_atualizacao(self):
        """Loop de atualização automática"""
        while self.servidor_rodando:
            try:
                self.root.after(0, self.atualizar_estatisticas)
                self.root.after(0, self.atualizar_lista_usuarios)
                time.sleep(2)  # Atualiza a cada 2 segundos
            except Exception as e:
                print(f"Erro no loop de atualização: {e}")
                break
    
    def on_usuario_conectado(self, usuario: Usuario):
        """Callback chamado quando usuário se conecta"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.tempos_conexao[usuario.nome] = timestamp
        self.root.after(0, lambda: self.adicionar_log(f"Usuário conectado: {usuario.nome} ({usuario.latitude}, {usuario.longitude})"))
    
    def on_usuario_desconectado(self, usuario: Usuario):
        """Callback chamado quando usuário se desconecta"""
        if usuario.nome in self.tempos_conexao:
            del self.tempos_conexao[usuario.nome]
        self.root.after(0, lambda: self.adicionar_log(f"Usuário desconectado: {usuario.nome}"))
    
    def on_mensagem_recebida(self, remetente: str, destinatario: str, conteudo: str):
        """Callback chamado quando mensagem é recebida"""
        self.contador_mensagens += 1
        mensagem_log = f"Mensagem: {remetente} -> {destinatario}: {conteudo[:50]}{'...' if len(conteudo) > 50 else ''}"
        self.root.after(0, lambda: self.adicionar_log(mensagem_log))
    
    def adicionar_log(self, mensagem: str):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        texto = f"[{timestamp}] {mensagem}\n"
        
        self.text_logs.config(state='normal')
        self.text_logs.insert(tk.END, texto)
        self.text_logs.config(state='disabled')
        
        if self.auto_scroll_var.get():
            self.text_logs.see(tk.END)
    
    def limpar_logs(self):
        """Limpa área de logs"""
        self.text_logs.config(state='normal')
        self.text_logs.delete(1.0, tk.END)
        self.text_logs.config(state='disabled')
    
    def fechar_aplicacao(self):
        """Fecha a aplicação"""
        if self.servidor_rodando:
            self.parar_servidor()
        
        # Aguarda um pouco para finalizar operações
        self.root.after(100, self.root.destroy)
    
    def executar(self):
        """Executa a aplicação"""
        self.root.mainloop()

if __name__ == "__main__":
    interface = InterfaceServidor()
    interface.executar()
