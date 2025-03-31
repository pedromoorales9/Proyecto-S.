#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para ejecutar la aplicación de Provisión de Usuarios.
Este script verifica los requisitos, configura el entorno y ejecuta la aplicación.
"""

import os
import sys
import subprocess
import importlib.util


def check_python_version():
    """
    Verificar versión de Python.
    
    Returns:
        bool: True si la versión es 3.8 o superior.
    """
    version_info = sys.version_info
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
        print(f"⚠️ Versión de Python no compatible: {sys.version}")
        print("Se requiere Python 3.8 o superior.")
        return False
    return True


def check_requirements():
    """
    Verificar si se cumplen los requisitos.
    
    Returns:
        bool: True si todos los requisitos están instalados.
    """
    required_packages = [
        'PyQt5',
        'requests',
        'msal',
        'pycryptodome',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print("⚠️ Paquetes requeridos no instalados:")
        for package in missing_packages:
            print(f"  - {package}")
        
        # Preguntar si desea instalar los paquetes faltantes
        response = input("¿Desea instalar los paquetes faltantes? (s/n): ")
        if response.lower() in ('s', 'si', 'y', 'yes'):
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
                print("✅ Paquetes instalados correctamente.")
                return True
            except subprocess.CalledProcessError:
                print("❌ Error al instalar paquetes. Intente manualmente con:")
                print(f"  {sys.executable} -m pip install -r requirements.txt")
                return False
        else:
            return False
    
    return True


def create_directory_structure():
    """
    Crear estructura de directorios si no existe.
    
    Returns:
        bool: True si se creó o ya existía la estructura.
    """
    directories = [
        'logs',
        'config',
        'resources/icons',
        'resources/styles'
    ]
    
    try:
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        return True
    except Exception as e:
        print(f"❌ Error al crear directorios: {str(e)}")
        return False


def main():
    """Función principal."""
    print("🚀 Inicializando aplicación de Provisión de Usuarios...")
    
    # Verificar versión de Python
    if not check_python_version():
        return
    
    # Verificar requisitos
    if not check_requirements():
        return
    
    # Crear estructura de directorios
    if not create_directory_structure():
        return
    
    # Configurar PYTHONPATH para incluir el directorio actual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Ejecutar aplicación
    try:
        print("✅ Iniciando aplicación...")
        from main import main as run_app
        run_app()
    except ImportError as e:
        print(f"❌ Error al importar la aplicación: {str(e)}")
        print("Asegúrese de que el archivo main.py existe y todos los módulos están instalados.")
    except Exception as e:
        print(f"❌ Error al ejecutar la aplicación: {str(e)}")


if __name__ == "__main__":
    main()