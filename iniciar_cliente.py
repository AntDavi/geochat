#!/usr/bin/env python3
"""
Script para iniciar o cliente integrado (síncrono + assíncrono)
"""

if __name__ == "__main__":
    from gui.cliente_integrado import ClienteIntegrado
    
    print("Iniciando GeoChat Cliente Integrado...")
    cliente = ClienteIntegrado()
    cliente.executar()
