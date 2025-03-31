#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ventana principal de la aplicación de Provisión de Usuarios.
"""

import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QMessageBox, QStatusBar
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize

# Importar vistas
from ui.user_creation import UserCreationView
from ui.license_assignment import LicenseAssignmentView
from ui.configuration import ConfigurationView
from ui.logs import LogsView


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación."""
    
    def __init__(self, config_manager, logging_service):
        """
        Inicializar la ventana principal.
        
        Args:
            config_manager: Gestor de configuración.
            logging_service: Servicio de logging.
        """
        super().__init__()
        
        # Guardar referencias a los servicios
        self.config_manager = config_manager
        self.logging_service = logging_service
        
        # Inicializar UI
        self.init_ui()
        
        # Verificar configuración
        self.check_configuration()
    
    def init_ui(self):
        """Inicializar interfaz de usuario."""
        # Configurar ventana principal
        self.setWindowTitle("Herramienta de Provisión de Usuarios")
        self.setGeometry(100, 100, 1000, 700)
        
        # Widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Cabecera
        self.header_frame = QFrame()
        self.header_frame.setObjectName("HeaderFrame")
        self.header_layout = QHBoxLayout(self.header_frame)
        
        # Logo o ícono en la cabecera
        icon_path = os.path.join("resources", "icons", "app_icon.ico")
        if os.path.exists(icon_path):
            self.logo_label = QLabel()
            pixmap = QPixmap(icon_path)
            self.logo_label.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.header_layout.addWidget(self.logo_label)
        
        # Título en la cabecera
        self.title_label = QLabel("Herramienta de Provisión de Usuarios")
        self.title_label.setObjectName("HeaderLabel")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        # Botón de configuración en la cabecera
        self.config_button = QPushButton("⚙️")
        self.config_button.setToolTip("Configuración")
        self.config_button.setFixedSize(40, 40)
        self.config_button.clicked.connect(self.open_configuration)
        self.header_layout.addWidget(self.config_button)
        
        self.main_layout.addWidget(self.header_frame)
        
        # Contenido principal: navegación y contenido
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Panel de navegación
        self.nav_frame = QFrame()
        self.nav_frame.setObjectName("NavigationFrame")
        self.nav_frame.setFixedWidth(200)
        self.nav_layout = QVBoxLayout(self.nav_frame)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(0)
        
        # Botones de navegación
        self.create_user_btn = QPushButton("👤 Crear Usuario")
        self.create_user_btn.setObjectName("NavButton")
        self.create_user_btn.setCheckable(True)
        self.create_user_btn.clicked.connect(lambda: self.switch_view(0))
        self.nav_layout.addWidget(self.create_user_btn)
        
        self.assign_license_btn = QPushButton("🔑 Asignar Licencias")
        self.assign_license_btn.setObjectName("NavButton")
        self.assign_license_btn.setCheckable(True)
        self.assign_license_btn.clicked.connect(lambda: self.switch_view(1))
        self.nav_layout.addWidget(self.assign_license_btn)
        
        self.logs_btn = QPushButton("📋 Ver Logs")
        self.logs_btn.setObjectName("NavButton")
        self.logs_btn.setCheckable(True)
        self.logs_btn.clicked.connect(lambda: self.switch_view(2))
        self.nav_layout.addWidget(self.logs_btn)
        
        # Espacio en blanco en la navegación
        self.nav_layout.addStretch()
        
        # Contenedor de contenido
        self.content_stack = QStackedWidget()
        
        # Vistas
        self.user_creation_view = UserCreationView(self.config_manager, self.logging_service, self)
        self.license_assignment_view = LicenseAssignmentView(self.config_manager, self.logging_service, self)
        self.logs_view = LogsView(self.logging_service, self)
        self.config_view = ConfigurationView(self.config_manager, self.logging_service, self)
        
        # Añadir vistas al stack
        self.content_stack.addWidget(self.user_creation_view)
        self.content_stack.addWidget(self.license_assignment_view)
        self.content_stack.addWidget(self.logs_view)
        
        # No añadir la vista de configuración al stack ya que se mostrará como ventana emergente
        
        # Añadir navegación y contenido al layout
        self.content_layout.addWidget(self.nav_frame)
        self.content_layout.addWidget(self.content_stack)
        
        self.main_layout.addLayout(self.content_layout)
        
        # Barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo")
        
        # Seleccionar vista predeterminada
        self.switch_view(0)
    
    def switch_view(self, index):
        """
        Cambiar vista actual.
        
        Args:
            index (int): Índice de la vista.
        """
        # Desmarcar todos los botones y marcar el seleccionado
        for i, btn in enumerate([self.create_user_btn, self.assign_license_btn, self.logs_btn]):
            btn.setChecked(i == index)
        
        # Cambiar vista
        self.content_stack.setCurrentIndex(index)
    
    def open_configuration(self):
        """Abrir vista de configuración."""
        self.config_view.load_config()
        self.config_view.exec_()
    
    def check_configuration(self):
        """Verificar si la configuración está completa."""
        # Verificar si la configuración está completa
        if not self.config_manager.is_configuration_complete():
            QMessageBox.warning(
                self,
                "Configuración incompleta",
                "La configuración de la aplicación no está completa. "
                "Por favor, configure los parámetros de conexión.",
                QMessageBox.Ok
            )
            self.open_configuration()
    
    def update_status(self, message):
        """
        Actualizar el mensaje de la barra de estado.
        
        Args:
            message (str): Mensaje a mostrar.
        """
        self.status_bar.showMessage(message)
    
    def show_error(self, message):
        """
        Mostrar un mensaje de error.
        
        Args:
            message (str): Mensaje de error.
        """
        self.logging_service.log_error(message)
        QMessageBox.critical(self, "Error", message, QMessageBox.Ok)
    
    def show_warning(self, message):
        """
        Mostrar un mensaje de advertencia.
        
        Args:
            message (str): Mensaje de advertencia.
        """
        self.logging_service.log_warning(message)
        QMessageBox.warning(self, "Advertencia", message, QMessageBox.Ok)
    
    def show_info(self, message):
        """
        Mostrar un mensaje informativo.
        
        Args:
            message (str): Mensaje informativo.
        """
        self.logging_service.log_info(message)
        QMessageBox.information(self, "Información", message, QMessageBox.Ok)
    
    def show_success(self, message):
        """
        Mostrar un mensaje de éxito.
        
        Args:
            message (str): Mensaje de éxito.
        """
        self.logging_service.log_info(message)
        QMessageBox.information(self, "Éxito", message, QMessageBox.Ok)
    
    def confirm_action(self, title, message):
        """
        Solicitar confirmación para una acción.
        
        Args:
            title (str): Título del diálogo.
            message (str): Mensaje del diálogo.
            
        Returns:
            bool: True si se confirmó la acción.
        """
        response = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return response == QMessageBox.Yes