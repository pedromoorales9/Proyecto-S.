#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Punto de entrada principal para la aplicación de Provisión de Usuarios.
Esta aplicación permite gestionar la creación de usuarios en Business Central 
y asignar licencias de Microsoft 365.
"""

import sys
import os
import logging
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Asegurar que podemos importar desde cualquier ubicación
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Importar componentes de la aplicación
from ui.main_window import MainWindow
from config.config_manager import ConfigManager
from services.logging_service import LoggingService


def setup_logging():
    """Configurar el sistema de logging."""
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/app.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def main():
    """Función principal que inicia la aplicación."""
    # Configurar logging
    logger = setup_logging()
    logger.info("Iniciando aplicación de Provisión de Usuarios")
    
    # Inicializar servicios
    logging_service = LoggingService()
    config_manager = ConfigManager(logging_service)
    
    # Cargar configuración
    config_manager.load_config()
    
    # Inicializar aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Herramienta de Provisión de Usuarios")
    
    # Configurar estilo
    style_path = os.path.join("resources", "styles", "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as style_file:
            app.setStyleSheet(style_file.read())
    
    # Icono de la aplicación
    icon_path = os.path.join("resources", "icons", "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Crear y mostrar la ventana principal
    main_window = MainWindow(config_manager, logging_service)
    main_window.show()
    
    # Ejecutar el bucle de eventos de la aplicación
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()