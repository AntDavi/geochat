#!/usr/bin/env python3
"""
Script para iniciar o servidor com interface gráfica
"""

if __name__ == "__main__":
    from gui.interface_servidor import InterfaceServidor
    
    print("Iniciando GeoChat Servidor com Interface...")
    interface = InterfaceServidor()
    interface.executar()
