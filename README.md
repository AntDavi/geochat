# GeoChat - Sistema de Comunicação Baseado em Localização

Um sistema de comunicação em Python que combina comunicação síncrona (sockets) e assíncrona (RabbitMQ) baseada na localização geográfica dos usuários.

## 📋 Características

- **Comunicação Síncrona**: Via sockets TCP para usuários online e dentro do raio
- **Comunicação Assíncrona**: Via RabbitMQ para usuários offline ou fora do raio  
- **Interface Gráfica**: Tkinter para cliente e servidor
- **Localização Geográfica**: Cálculo de distância usando fórmula Haversine
- **Gerenciamento de Raio**: Configuração dinâmica do alcance de comunicação

## 🏗️ Arquitetura

```
geochat/
├── broker/              # Lógica RabbitMQ (consumidores e produtores)
│   ├── __init__.py
│   └── rabbitmq_manager.py
├── common/              # Classes e funções compartilhadas
│   ├── __init__.py
│   ├── usuario.py
│   └── config.py
├── gui/                 # Interfaces Tkinter
│   ├── __init__.py
│   ├── cliente_integrado.py   # Cliente síncrono + assíncrono
│   └── interface_servidor.py  # Interface administrativa
├── server/              # Servidor de sockets (sem UI)
│   ├── __init__.py
│   └── servidor_socket.py
├── docker-compose.yml   # Configuração Docker para RabbitMQ
├── .env                # Variáveis de ambiente
├── iniciar_rabbitmq.sh # Script Linux/Mac para RabbitMQ
├── iniciar_rabbitmq.bat # Script Windows para RabbitMQ
├── iniciar_servidor.py # Script do servidor
├── iniciar_cliente.py  # Script cliente integrado
├── inicio_rapido.sh    # Script de inicialização rápida
├── testar_configuracao.py # Script de testes
├── apresentacao.md     # Roteiro de apresentação
├── requirements.txt    # Dependências
└── README.md
```

## 🚀 Instalação

### Pré-requisitos

1. **Python 3.11+**
2. **Docker e Docker Compose** - Para RabbitMQ

#### Instalação do Docker

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER  # Reinicie o terminal após este comando
```

**Windows:**
- Baixe e instale: [Docker Desktop](https://docs.docker.com/desktop/windows/install/)

**macOS:**
```bash
brew install docker docker-compose
# Ou instale Docker Desktop: https://docs.docker.com/desktop/mac/install/
```

### Instalação das Dependências

```bash
cd geochat
pip install -r requirements.txt
```

## � Início Rápido

Para configurar e executar rapidamente (Linux/macOS):

```bash
./inicio_rapido.sh
```

Este script irá:
- Verificar dependências
- Criar ambiente virtual Python
- Instalar dependências
- Testar configuração
- Iniciar RabbitMQ via Docker

## �📖 Como Usar (Manual)

### 1. Iniciando o RabbitMQ (Docker)

#### Linux/macOS:
```bash
./iniciar_rabbitmq.sh
```

#### Windows:
```cmd
iniciar_rabbitmq.bat
```

#### Manualmente:
```bash
docker-compose up -d rabbitmq
```

**Acesso ao Management UI:**
- URL: http://localhost:15672
- Usuário: `geochat`
- Senha: `geochat123`

### 2. Iniciando o Servidor

```bash
python3 iniciar_servidor.py
```

### 3. Iniciando Cliente(s)

#### Cliente Integrado (Síncrono + Assíncrono)
```bash
python3 iniciar_cliente.py
```

### 4. Configuração Inicial

1. **No Servidor**: Configure host e porta, clique em "Iniciar Servidor"
2. **No Cliente**: 
   - Insira seu nome e localização (latitude, longitude)
   - Configure o raio de comunicação em metros
   - Conecte ao servidor socket
   - (Opcional) Conecte ao RabbitMQ para mensagens assíncronas
   - Use as credenciais: usuário `geochat`, senha `geochat123`

## 🎯 Funcionalidades

### Comunicação Síncrona
- Mensagens instantâneas entre usuários online
- Funciona apenas se ambos estiverem dentro do raio configurado
- Interface em tempo real com lista de contatos

### Comunicação Assíncrona  
- Mensagens persistentes via RabbitMQ
- Entregues quando o destinatário ficar online
- Funciona para usuários offline ou fora do raio

### Gerenciamento de Localização
- Atualização dinâmica de coordenadas
- Cálculo automático de distâncias (Haversine)
- Detecção de usuários no raio de comunicação

### Interface do Servidor
- Monitoramento de usuários conectados
- Estatísticas em tempo real
- Logs detalhados de atividades
- Controle completo do servidor

## � Docker

### RabbitMQ via Docker Compose

O projeto usa Docker para executar o RabbitMQ, proporcionando:
- **Isolamento**: Container dedicado para o broker
- **Simplicidade**: Configuração automática
- **Persistência**: Dados mantidos entre reinicializações
- **Management UI**: Interface web para monitoramento

### Comandos Docker Úteis

```bash
# Iniciar RabbitMQ
docker-compose up -d rabbitmq

# Ver logs do RabbitMQ
docker-compose logs -f rabbitmq

# Parar RabbitMQ
docker-compose down

# Reiniciar RabbitMQ
docker-compose restart rabbitmq

docker-compose ps

# Remover volumes (apaga dados persistidos)
docker-compose down -v
```

## 🔧 Configuração
```

### Containerizar a Aplicação (Opcional)

Para executar toda a aplicação em containers:

```bash
# Build da imagem
docker build -t geochat .

# Executar apenas o servidor
docker run -d -p 8888:8888 --name geochat-server geochat

# Executar com RabbitMQ
docker-compose up -d
```

## �🔧 Configuração

### Localização Padrão
- **São Paulo**: Latitude -23.5505, Longitude -46.6333
- **Raio Padrão**: 1000 metros

### Servidores Padrão
- **Socket**: localhost:8888
- **RabbitMQ**: localhost:5672
- **RabbitMQ Management**: localhost:15672
- **Credenciais RabbitMQ**: geochat / geochat123

## 📊 Exemplo de Uso

1. **Usuário A** se conecta em São Paulo (-23.5505, -46.6333)
2. **Usuário B** se conecta próximo (-23.5510, -46.6340) 
3. **Comunicação Síncrona**: Ambos online e no raio → mensagens instantâneas
4. **Usuário B** sai do raio ou fica offline
5. **Comunicação Assíncrona**: Mensagens via RabbitMQ são armazenadas
6. **Usuário B** retorna → recebe mensagens pendentes

## 🔍 Tipos de Comunicação

| Cenário | Tipo | Transporte |
|---------|------|------------|
| Ambos online + no raio | Síncrona | Socket TCP |
| Destinatário offline | Assíncrona | RabbitMQ |
| Destinatário fora do raio | Assíncrona | RabbitMQ |
| Modo forçado | Configurável | Conforme seleção |

## 🧪 Testes

### Teste de Configuração

Antes de usar o sistema, execute o teste para verificar se tudo está correto:

```bash
python3 testar_configuracao.py
```

Este script verifica:
- Imports de todos os módulos
- Configurações de ambiente
- Funcionalidade da classe Usuario
- Disponibilidade do Docker

### Teste Local com Múltiplos Usuários

1. Inicie o servidor
2. Abra múltiplas instâncias do cliente  
3. Configure usuários com nomes diferentes
4. Teste diferentes localizações e raios
5. Experimente cenários online/offline

### Teste de Comunicação Assíncrona

1. Conecte usuário A ao socket + RabbitMQ
2. Conecte usuário B apenas ao socket  
3. Usuário A envia mensagem para B
4. Feche cliente B
5. Usuário A envia mais mensagens
6. Reabra cliente B e conecte ao RabbitMQ
7. Mensagens pendentes devem aparecer

## 📋 Stack Tecnológica

- **Linguagem**: Python 3.11+
- **Interface**: Tkinter (built-in)
- **Comunicação Síncrona**: Sockets TCP
- **Comunicação Assíncrona**: RabbitMQ + Pika
- **Localização**: Cálculo Haversine (math)
- **Concorrência**: Threading
- **Serialização**: JSON

## 🎓 Conceitos Demonstrados

- Programação com sockets TCP
- Message broker (RabbitMQ)  
- Interface gráfica com Tkinter
- Programação concorrente/threading
- Cálculos geográficos (Haversine)
- Arquitetura cliente-servidor
- Padrões pub/sub e point-to-point
- Tratamento de erros robusto

## 🤝 Contribuição

Este é um projeto educacional demonstrando integração de múltiplas tecnologias de comunicação em Python.

## 📄 Licença

Projeto educacional para demonstração de conceitos de programação distribuída.
