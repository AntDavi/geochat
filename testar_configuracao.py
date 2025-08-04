#!/usr/bin/env python3
"""
Script de teste para verificar configurações e dependências
"""

def testar_imports():
    """Testa se todos os imports estão funcionando"""
    print("🔍 Testando imports...")
    
    try:
        # Testa imports básicos
        from common.usuario import Usuario, StatusUsuario
        from common.config import config
        print("✅ Módulos common: OK")
        
        # Testa servidor
        from server.servidor_socket import ServidorSocket
        print("✅ Módulo servidor: OK")
        
        # Testa broker
        from broker.rabbitmq_manager import ConfiguradorRabbitMQ
        print("✅ Módulo broker: OK")
        
        # Testa GUI
        from gui.cliente_integrado import ClienteIntegrado
        from gui.interface_servidor import InterfaceServidor
        print("✅ Módulos GUI: OK")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return False

def testar_configuracoes():
    """Testa configurações"""
    print("\n🔧 Testando configurações...")
    
    try:
        from common.config import config
        config.print_config()
        return True
        
    except Exception as e:
        print(f"❌ Erro nas configurações: {e}")
        return False

def testar_usuario():
    """Testa classe Usuario"""
    print("\n👤 Testando classe Usuario...")
    
    try:
        from common.usuario import Usuario, StatusUsuario, calcular_distancia_haversine
        
        # Cria usuários de teste
        user1 = Usuario("TestUser1", -23.5505, -46.6333, 1000)
        user2 = Usuario("TestUser2", -23.5510, -46.6340, 1000)
        
        # Testa cálculo de distância
        distancia = user1.calcular_distancia(user2)
        print(f"   Distância entre usuários: {distancia:.2f}m")
        
        # Testa se estão no raio
        no_raio = user1.esta_no_raio(user2)
        print(f"   Usuários no raio: {no_raio}")
        
        # Testa comunicação síncrona
        user1.set_online()
        user2.set_online()
        pode_comunicar = user1.pode_comunicar_sincronamente(user2)
        print(f"   Pode comunicar sincronamente: {pode_comunicar}")
        
        print("✅ Classe Usuario: OK")
        return True
        
    except Exception as e:
        print(f"❌ Erro na classe Usuario: {e}")
        return False

def verificar_docker():
    """Verifica se Docker está disponível"""
    print("\n🐳 Verificando Docker...")
    
    import subprocess
    
    try:
        # Verifica se docker está instalado
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Docker instalado: {result.stdout.strip()}")
            
            # Verifica se docker-compose está disponível
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Docker Compose: {result.stdout.strip()}")
            else:
                print("⚠️  Docker Compose não encontrado")
            
            return True
        else:
            print("❌ Docker não está funcionando")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout ao verificar Docker")
        return False
    except FileNotFoundError:
        print("❌ Docker não está instalado")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar Docker: {e}")
        return False

def main():
    """Função principal do teste"""
    print("🚀 GeoChat - Teste de Configuração\n")
    
    testes = [
        testar_imports,
        testar_configuracoes,
        testar_usuario,
        verificar_docker
    ]
    
    sucessos = 0
    for teste in testes:
        try:
            if teste():
                sucessos += 1
        except Exception as e:
            print(f"❌ Erro inesperado em {teste.__name__}: {e}")
    
    print(f"\n📊 Resultado: {sucessos}/{len(testes)} testes passaram")
    
    if sucessos == len(testes):
        print("🎉 Tudo configurado corretamente!")
        print("\n💡 Próximos passos:")
        print("   1. Inicie o RabbitMQ: ./iniciar_rabbitmq.sh (Linux/Mac) ou iniciar_rabbitmq.bat (Windows)")
        print("   2. Inicie o servidor: python iniciar_servidor.py")
        print("   3. Inicie o(s) cliente(s): python iniciar_cliente.py")
    else:
        print("⚠️  Alguns problemas foram encontrados. Verifique as mensagens acima.")
    
    return sucessos == len(testes)

if __name__ == "__main__":
    main()
