#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vista de configuración de la aplicación.
"""

import asyncio
import uuid
from async_utils import run_async  # Añadir esta importación
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, 
    QPushButton, QTabWidget, QWidget, QGroupBox, QFormLayout, QListWidget, 
    QListWidgetItem, QMessageBox, QScrollArea, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, pyqtSlot

from models.role import Role
from models.license import License
from services.business_central import BusinessCentralService
from services.microsoft_graph import MicrosoftGraphService


# Crear una clase personalizada de QPasswordLineEdit porque no existe por defecto
class QPasswordLineEdit(QLineEdit):
    """Campo de texto para contraseñas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEchoMode(QLineEdit.Password)


class ConfigurationView(QDialog):
    """Vista para la configuración de la aplicación."""
    
    def __init__(self, config_manager, logging_service, main_window):
        """
        Inicializar la vista de configuración.
        
        Args:
            config_manager: Gestor de configuración.
            logging_service: Servicio de logging.
            main_window: Ventana principal.
        """
        super().__init__(main_window)
        
        # Guardar referencias
        self.config_manager = config_manager
        self.logging_service = logging_service
        self.main_window = main_window
        
        # Crear servicios
        self.bc_service = BusinessCentralService(config_manager, logging_service)
        self.graph_service = MicrosoftGraphService(config_manager, logging_service)
        
        # Variables de estado
        self.roles = []
        self.licenses = []
        self.selected_role = None
        self.selected_license = None
        
        # Inicializar UI
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz de usuario."""
        # Configurar diálogo
        self.setWindowTitle("Configuración")
        self.setMinimumSize(800, 600)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        
        # Título
        self.title_label = QLabel("Configuración del Sistema")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 15px;")
        self.main_layout.addWidget(self.title_label)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab de Microsoft Graph
        self.graph_tab = QWidget()
        self.graph_tab_layout = QVBoxLayout(self.graph_tab)
        
        # Añadir elementos al tab de Microsoft Graph
        self.create_graph_tab()
        self.tabs.addTab(self.graph_tab, "Microsoft Graph")
        
        # Tab de Business Central
        self.bc_tab = QWidget()
        self.bc_tab_layout = QVBoxLayout(self.bc_tab)
        
        # Añadir elementos al tab de Business Central
        self.create_bc_tab()
        self.tabs.addTab(self.bc_tab, "Business Central")
        
        # Tab de configuración general
        self.general_tab = QWidget()
        self.general_tab_layout = QVBoxLayout(self.general_tab)
        
        # Añadir elementos al tab de configuración general
        self.create_general_tab()
        self.tabs.addTab(self.general_tab, "General")
        
        # Tab de roles y licencias
        self.roles_licenses_tab = QWidget()
        self.roles_licenses_tab_layout = QVBoxLayout(self.roles_licenses_tab)
        
        # Añadir elementos al tab de roles y licencias
        self.create_roles_licenses_tab()
        self.tabs.addTab(self.roles_licenses_tab, "Roles y Licencias")
        
        self.main_layout.addWidget(self.tabs)
        
        # Botones de acción
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        
        self.save_button = QPushButton("Guardar Configuración")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self.save_config)
        
        self.buttons_layout.addWidget(self.cancel_button)
        self.buttons_layout.addWidget(self.save_button)
        
        self.main_layout.addLayout(self.buttons_layout)
    
    def create_graph_tab(self):
        """Crear contenido del tab de Microsoft Graph."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)
        
        # Campos de texto
        self.ms_graph_tenant_id_edit = QLineEdit()
        self.ms_graph_client_id_edit = QLineEdit()
        self.ms_graph_client_secret_edit = QPasswordLineEdit()
        self.ms_graph_base_url_edit = QLineEdit()
        
        # Añadir campos al layout
        form_layout.addRow("ID del Tenant:", self.ms_graph_tenant_id_edit)
        form_layout.addRow("ID del Cliente:", self.ms_graph_client_id_edit)
        form_layout.addRow("Secreto del Cliente:", self.ms_graph_client_secret_edit)
        form_layout.addRow("URL Base de la API:", self.ms_graph_base_url_edit)
        
        # Botón de prueba de conexión
        self.test_graph_button = QPushButton("Probar Conexión")
        self.test_graph_button.clicked.connect(self.test_graph_connection)
        form_layout.addRow("", self.test_graph_button)
        
        scroll_area.setWidget(scroll_content)
        self.graph_tab_layout.addWidget(scroll_area)
    
    def create_bc_tab(self):
        """Crear contenido del tab de Business Central."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)
        
        # Campos de texto
        self.bc_tenant_id_edit = QLineEdit()
        self.bc_client_id_edit = QLineEdit()
        self.bc_client_secret_edit = QPasswordLineEdit()
        self.bc_base_url_edit = QLineEdit()
        self.bc_company_id_edit = QLineEdit()
        self.bc_api_version_edit = QLineEdit()
        
        # Añadir campos al layout
        form_layout.addRow("ID del Tenant:", self.bc_tenant_id_edit)
        form_layout.addRow("ID del Cliente:", self.bc_client_id_edit)
        form_layout.addRow("Secreto del Cliente:", self.bc_client_secret_edit)
        form_layout.addRow("URL Base de la API:", self.bc_base_url_edit)
        form_layout.addRow("ID de la Compañía:", self.bc_company_id_edit)
        form_layout.addRow("Versión de la API:", self.bc_api_version_edit)
        
        # Botón de prueba de conexión
        self.test_bc_button = QPushButton("Probar Conexión")
        self.test_bc_button.clicked.connect(self.test_bc_connection)
        form_layout.addRow("", self.test_bc_button)
        
        scroll_area.setWidget(scroll_content)
        self.bc_tab_layout.addWidget(scroll_area)
    
    def create_general_tab(self):
        """Crear contenido del tab de configuración general."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)
        
        # Campos de texto
        self.email_domain_edit = QLineEdit()
        self.default_password_edit = QPasswordLineEdit()
        
        # Casillas de verificación
        self.require_password_change_check = QCheckBox("Requerir cambio de contraseña en el próximo inicio de sesión")
        self.require_password_change_check.setChecked(True)
        
        # Clave de encriptación
        self.encryption_key_edit = QLineEdit()
        self.encryption_key_edit.setReadOnly(True)
        
        # Botón de generar clave
        self.generate_key_button = QPushButton("Generar Nueva Clave")
        self.generate_key_button.clicked.connect(self.generate_encryption_key)
        
        # Añadir campos al layout
        form_layout.addRow("Dominio de Correo Predeterminado:", self.email_domain_edit)
        form_layout.addRow("Contraseña Predeterminada:", self.default_password_edit)
        form_layout.addRow("", self.require_password_change_check)
        form_layout.addRow("Clave de Encriptación:", self.encryption_key_edit)
        form_layout.addRow("", self.generate_key_button)
        
        # Añadir nota de advertencia
        warning_label = QLabel(
            "Nota: Cambiar la clave de encriptación hará que las credenciales guardadas ya no sean válidas."
        )
        warning_label.setStyleSheet("color: #E81123; font-style: italic;")
        form_layout.addRow("", warning_label)
        
        scroll_area.setWidget(scroll_content)
        self.general_tab_layout.addWidget(scroll_area)
    
    def create_roles_licenses_tab(self):
        """Crear contenido del tab de roles y licencias."""
        # Layout de dos columnas
        split_layout = QHBoxLayout()
        
        # Columna izquierda - Roles
        roles_panel = QWidget()
        roles_layout = QVBoxLayout(roles_panel)
        
        roles_label = QLabel("Roles en Business Central")
        roles_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.roles_list = QListWidget()
        self.roles_list.currentItemChanged.connect(self.on_role_selected)
        
        roles_layout.addWidget(roles_label)
        roles_layout.addWidget(self.roles_list)
        
        # Grupo de edición de rol
        role_edit_group = QGroupBox("Editar Rol")
        role_edit_layout = QFormLayout()
        
        self.role_id_edit = QLineEdit()
        self.role_id_edit.setReadOnly(True)
        self.role_name_edit = QLineEdit()
        self.role_description_edit = QLineEdit()
        
        # Botones de rol
        role_buttons_layout = QHBoxLayout()
        self.new_role_button = QPushButton("Nuevo")
        self.new_role_button.clicked.connect(self.new_role)
        self.save_role_button = QPushButton("Guardar")
        self.save_role_button.setObjectName("PrimaryButton")
        self.save_role_button.clicked.connect(self.save_role)
        self.save_role_button.setEnabled(False)
        
        role_buttons_layout.addWidget(self.new_role_button)
        role_buttons_layout.addWidget(self.save_role_button)
        
        role_edit_layout.addRow("ID:", self.role_id_edit)
        role_edit_layout.addRow("Nombre:", self.role_name_edit)
        role_edit_layout.addRow("Descripción:", self.role_description_edit)
        role_edit_layout.addRow("", role_buttons_layout)
        
        role_edit_group.setLayout(role_edit_layout)
        roles_layout.addWidget(role_edit_group)
        
        # Columna derecha - Licencias
        licenses_panel = QWidget()
        licenses_layout = QVBoxLayout(licenses_panel)
        
        licenses_label = QLabel("Licencias de Microsoft 365")
        licenses_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.licenses_list = QListWidget()
        self.licenses_list.currentItemChanged.connect(self.on_license_selected)
        
        licenses_layout.addWidget(licenses_label)
        licenses_layout.addWidget(self.licenses_list)
        
        # Grupo de edición de licencia
        license_edit_group = QGroupBox("Editar Licencia")
        license_edit_layout = QFormLayout()
        
        self.license_id_edit = QLineEdit()
        self.license_id_edit.setReadOnly(True)
        self.license_name_edit = QLineEdit()
        self.license_sku_id_edit = QLineEdit()
        
        # Botones de licencia
        license_buttons_layout = QHBoxLayout()
        self.new_license_button = QPushButton("Nuevo")
        self.new_license_button.clicked.connect(self.new_license)
        self.save_license_button = QPushButton("Guardar")
        self.save_license_button.setObjectName("PrimaryButton")
        self.save_license_button.clicked.connect(self.save_license)
        self.save_license_button.setEnabled(False)
        
        license_buttons_layout.addWidget(self.new_license_button)
        license_buttons_layout.addWidget(self.save_license_button)
        
        license_edit_layout.addRow("ID:", self.license_id_edit)
        license_edit_layout.addRow("Nombre:", self.license_name_edit)
        license_edit_layout.addRow("SKU ID:", self.license_sku_id_edit)
        license_edit_layout.addRow("", license_buttons_layout)
        
        license_edit_group.setLayout(license_edit_layout)
        licenses_layout.addWidget(license_edit_group)
        
        # Añadir columnas al layout
        split_layout.addWidget(roles_panel)
        split_layout.addWidget(licenses_panel)
        
        self.roles_licenses_tab_layout.addLayout(split_layout)
    
    def load_config(self):
        """Cargar configuración actual."""
        try:
            config = self.config_manager.config
            
            # Microsoft Graph
            self.ms_graph_tenant_id_edit.setText(config["microsoft_graph"]["tenant_id"])
            self.ms_graph_client_id_edit.setText(config["microsoft_graph"]["client_id"])
            self.ms_graph_client_secret_edit.setText(config["microsoft_graph"]["client_secret"])
            self.ms_graph_base_url_edit.setText(config["microsoft_graph"]["base_url"])
            
            # Business Central
            self.bc_tenant_id_edit.setText(config["business_central"]["tenant_id"])
            self.bc_client_id_edit.setText(config["business_central"]["client_id"])
            self.bc_client_secret_edit.setText(config["business_central"]["client_secret"])
            self.bc_base_url_edit.setText(config["business_central"]["base_url"])
            self.bc_company_id_edit.setText(config["business_central"]["company_id"])
            self.bc_api_version_edit.setText(config["business_central"]["api_version"])
            
            # General
            self.email_domain_edit.setText(config["app"]["email_domain"])
            self.default_password_edit.setText(config["app"]["default_password"])
            self.require_password_change_check.setChecked(config["app"]["require_password_change"])
            self.encryption_key_edit.setText(config["app"]["encryption_key"])
            
            # Cargar roles y licencias
            run_async(self.load_roles_and_licenses())  # MODIFICADO
            
        except Exception as e:
            self.logging_service.log_error("Error al cargar configuración", e)
            self.main_window.show_error(f"Error al cargar configuración: {str(e)}")
    
    async def load_roles_and_licenses(self):
        """Cargar roles y licencias."""
        try:
            # Cargar roles
            self.roles = await self.config_manager.get_available_roles()
            self.update_roles_list()
            
            # Cargar licencias
            self.licenses = await self.config_manager.get_available_licenses()
            self.update_licenses_list()
            
        except Exception as e:
            self.logging_service.log_error("Error al cargar roles y licencias", e)
            self.main_window.show_error(f"Error al cargar roles y licencias: {str(e)}")
    
    def update_roles_list(self):
        """Actualizar lista de roles."""
        # Limpiar lista
        self.roles_list.clear()
        
        # Añadir roles
        for role in self.roles:
            item = QListWidgetItem(role.name)
            item.setData(Qt.UserRole, role)
            self.roles_list.addItem(item)
    
    def update_licenses_list(self):
        """Actualizar lista de licencias."""
        # Limpiar lista
        self.licenses_list.clear()
        
        # Añadir licencias
        for license_obj in self.licenses:
            item = QListWidgetItem(license_obj.name)
            item.setData(Qt.UserRole, license_obj)
            self.licenses_list.addItem(item)
    
    def on_role_selected(self, current, previous):
        """
        Manejar selección de rol.
        
        Args:
            current: Item actual seleccionado.
            previous: Item previamente seleccionado.
        """
        if current:
            role = current.data(Qt.UserRole)
            self.selected_role = role
            
            # Actualizar campos
            self.role_id_edit.setText(role.id)
            self.role_name_edit.setText(role.name)
            self.role_description_edit.setText(role.description)
            
            # Habilitar botón de guardar
            self.save_role_button.setEnabled(True)
        else:
            self.selected_role = None
            
            # Limpiar campos
            self.role_id_edit.setText("")
            self.role_name_edit.setText("")
            self.role_description_edit.setText("")
            
            # Deshabilitar botón de guardar
            self.save_role_button.setEnabled(False)
    
    def on_license_selected(self, current, previous):
        """
        Manejar selección de licencia.
        
        Args:
            current: Item actual seleccionado.
            previous: Item previamente seleccionado.
        """
        if current:
            license_obj = current.data(Qt.UserRole)
            self.selected_license = license_obj
            
            # Actualizar campos
            self.license_id_edit.setText(license_obj.id)
            self.license_name_edit.setText(license_obj.name)
            self.license_sku_id_edit.setText(license_obj.sku_id)
            
            # Habilitar botón de guardar
            self.save_license_button.setEnabled(True)
        else:
            self.selected_license = None
            
            # Limpiar campos
            self.license_id_edit.setText("")
            self.license_name_edit.setText("")
            self.license_sku_id_edit.setText("")
            
            # Deshabilitar botón de guardar
            self.save_license_button.setEnabled(False)
    
    def new_role(self):
        """Crear nuevo rol."""
        # Limpiar campos
        self.selected_role = None
        self.role_id_edit.setText("")
        self.role_name_edit.setText("Nuevo Rol")
        self.role_description_edit.setText("")
        
        # Habilitar botón de guardar
        self.save_role_button.setEnabled(True)
    
    def new_license(self):
        """Crear nueva licencia."""
        # Limpiar campos
        self.selected_license = None
        self.license_id_edit.setText("")
        self.license_name_edit.setText("Nueva Licencia")
        self.license_sku_id_edit.setText("")
        
        # Habilitar botón de guardar
        self.save_license_button.setEnabled(True)
    
    def save_role(self):
        """Guardar rol."""
        # Validar campos
        if not self.role_name_edit.text().strip():
            QMessageBox.warning(self, "Validación", "El nombre del rol es obligatorio.", QMessageBox.Ok)
            return
        
        # Crear o actualizar rol
        if self.selected_role:
            role = self.selected_role
            role.name = self.role_name_edit.text().strip()
            role.description = self.role_description_edit.text().strip()
        else:
            role = Role(
                id=str(uuid.uuid4()),
                name=self.role_name_edit.text().strip(),
                description=self.role_description_edit.text().strip()
            )
        
        # Guardar rol
        run_async(self.do_save_role(role))  # MODIFICADO
    
    def save_license(self):
        """Guardar licencia."""
        # Validar campos
        if not self.license_name_edit.text().strip():
            QMessageBox.warning(self, "Validación", "El nombre de la licencia es obligatorio.", QMessageBox.Ok)
            return
        
        if not self.license_sku_id_edit.text().strip():
            QMessageBox.warning(self, "Validación", "El SKU ID de la licencia es obligatorio.", QMessageBox.Ok)
            return
        
        # Crear o actualizar licencia
        if self.selected_license:
            license_obj = self.selected_license
            license_obj.name = self.license_name_edit.text().strip()
            license_obj.sku_id = self.license_sku_id_edit.text().strip()
        else:
            license_obj = License(
                id=str(uuid.uuid4()),
                name=self.license_name_edit.text().strip(),
                sku_id=self.license_sku_id_edit.text().strip()
            )
        
        # Guardar licencia
        run_async(self.do_save_license(license_obj))  # MODIFICADO
    
    async def do_save_role(self, role):
        """
        Guardar rol en la configuración.
        
        Args:
            role (Role): Rol a guardar.
        """
        try:
            await self.config_manager.save_role(role)
            
            # Recargar roles
            self.roles = await self.config_manager.get_available_roles()
            self.update_roles_list()
            
            # Mensaje de éxito
            QMessageBox.information(self, "Éxito", "Rol guardado correctamente.", QMessageBox.Ok)
            
        except Exception as e:
            self.logging_service.log_error(f"Error al guardar rol: {role.name}", e)
            QMessageBox.critical(self, "Error", f"Error al guardar rol: {str(e)}", QMessageBox.Ok)
    
    async def do_save_license(self, license_obj):
        """
        Guardar licencia en la configuración.
        
        Args:
            license_obj (License): Licencia a guardar.
        """
        try:
            await self.config_manager.save_license(license_obj)
            
            # Recargar licencias
            self.licenses = await self.config_manager.get_available_licenses()
            self.update_licenses_list()
            
            # Mensaje de éxito
            QMessageBox.information(self, "Éxito", "Licencia guardada correctamente.", QMessageBox.Ok)
            
        except Exception as e:
            self.logging_service.log_error(f"Error al guardar licencia: {license_obj.name}", e)
            QMessageBox.critical(self, "Error", f"Error al guardar licencia: {str(e)}", QMessageBox.Ok)
    
    def generate_encryption_key(self):
        """Generar nueva clave de encriptación."""
        # Pedir confirmación
        response = QMessageBox.warning(
            self,
            "Confirmación",
            "¿Está seguro de que desea generar una nueva clave de encriptación? "
            "Esto hará que las credenciales guardadas ya no sean válidas.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if response == QMessageBox.Yes:
            # Generar nueva clave
            new_key = self.config_manager.generate_encryption_key()
            self.encryption_key_edit.setText(new_key)
    
    @pyqtSlot()
    def test_graph_connection(self):
        """Probar conexión a Microsoft Graph."""
        # Actualizar configuración temporalmente
        config = self.config_manager.config.copy()
        config["microsoft_graph"]["tenant_id"] = self.ms_graph_tenant_id_edit.text()
        config["microsoft_graph"]["client_id"] = self.ms_graph_client_id_edit.text()
        config["microsoft_graph"]["client_secret"] = self.ms_graph_client_secret_edit.text()
        config["microsoft_graph"]["base_url"] = self.ms_graph_base_url_edit.text()
        
        # Crear servicio con la configuración temporal
        graph_service = MicrosoftGraphService(self.config_manager, self.logging_service)
        
        # Probar conexión
        run_async(self.do_test_graph_connection(graph_service))  # MODIFICADO
    
    @pyqtSlot()
    def test_bc_connection(self):
        """Probar conexión a Business Central."""
        # Actualizar configuración temporalmente
        config = self.config_manager.config.copy()
        config["business_central"]["tenant_id"] = self.bc_tenant_id_edit.text()
        config["business_central"]["client_id"] = self.bc_client_id_edit.text()
        config["business_central"]["client_secret"] = self.bc_client_secret_edit.text()
        config["business_central"]["base_url"] = self.bc_base_url_edit.text()
        config["business_central"]["company_id"] = self.bc_company_id_edit.text()
        config["business_central"]["api_version"] = self.bc_api_version_edit.text()
        
        # Crear servicio con la configuración temporal
        bc_service = BusinessCentralService(self.config_manager, self.logging_service)
        
        # Probar conexión
        run_async(self.do_test_bc_connection(bc_service))  # MODIFICADO
    
    async def do_test_graph_connection(self, graph_service):
        """
        Probar conexión a Microsoft Graph.
        
        Args:
            graph_service (MicrosoftGraphService): Servicio de Microsoft Graph.
        """
        try:
            # Deshabilitar botón durante la prueba
            self.test_graph_button.setEnabled(False)
            self.test_graph_button.setText("Probando...")
            
            # Probar conexión
            result = await graph_service.test_connection()
            
            # Mostrar resultado
            if result:
                QMessageBox.information(self, "Éxito", "Conexión a Microsoft Graph correcta.", QMessageBox.Ok)
            else:
                QMessageBox.warning(self, "Error", "No se pudo conectar a Microsoft Graph.", QMessageBox.Ok)
            
        except Exception as e:
            self.logging_service.log_error("Error al probar conexión a Microsoft Graph", e)
            QMessageBox.critical(self, "Error", f"Error al probar conexión: {str(e)}", QMessageBox.Ok)
            
        finally:
            # Restaurar botón
            self.test_graph_button.setEnabled(True)
            self.test_graph_button.setText("Probar Conexión")
    
    async def do_test_bc_connection(self, bc_service):
        """
        Probar conexión a Business Central.
        
        Args:
            bc_service (BusinessCentralService): Servicio de Business Central.
        """
        try:
            # Deshabilitar botón durante la prueba
            self.test_bc_button.setEnabled(False)
            self.test_bc_button.setText("Probando...")
            
            # Probar conexión
            result = await bc_service.test_connection()
            
            # Mostrar resultado
            if result:
                QMessageBox.information(self, "Éxito", "Conexión a Business Central correcta.", QMessageBox.Ok)
            else:
                QMessageBox.warning(self, "Error", "No se pudo conectar a Business Central.", QMessageBox.Ok)
            
        except Exception as e:
            self.logging_service.log_error("Error al probar conexión a Business Central", e)
            QMessageBox.critical(self, "Error", f"Error al probar conexión: {str(e)}", QMessageBox.Ok)
            
        finally:
            # Restaurar botón
            self.test_bc_button.setEnabled(True)
            self.test_bc_button.setText("Probar Conexión")
    
    @pyqtSlot()
    def save_config(self):
        """Guardar configuración."""
        try:
            # Obtener configuración actual
            config = self.config_manager.config
            
            # Actualizar valores
            # Microsoft Graph
            config["microsoft_graph"]["tenant_id"] = self.ms_graph_tenant_id_edit.text()
            config["microsoft_graph"]["client_id"] = self.ms_graph_client_id_edit.text()
            config["microsoft_graph"]["client_secret"] = self.ms_graph_client_secret_edit.text()
            config["microsoft_graph"]["base_url"] = self.ms_graph_base_url_edit.text()
            
            # Business Central
            config["business_central"]["tenant_id"] = self.bc_tenant_id_edit.text()
            config["business_central"]["client_id"] = self.bc_client_id_edit.text()
            config["business_central"]["client_secret"] = self.bc_client_secret_edit.text()
            config["business_central"]["base_url"] = self.bc_base_url_edit.text()
            config["business_central"]["company_id"] = self.bc_company_id_edit.text()
            config["business_central"]["api_version"] = self.bc_api_version_edit.text()
            
            # General
            config["app"]["email_domain"] = self.email_domain_edit.text()
            config["app"]["default_password"] = self.default_password_edit.text()
            config["app"]["require_password_change"] = self.require_password_change_check.isChecked()
            config["app"]["encryption_key"] = self.encryption_key_edit.text()
            
            # Guardar configuración
            self.config_manager.save_config()
            
            # Mensaje de éxito
            QMessageBox.information(self, "Éxito", "Configuración guardada correctamente.", QMessageBox.Ok)
            
            # Cerrar diálogo
            self.accept()
            
        except Exception as e:
            self.logging_service.log_error("Error al guardar configuración", e)
            QMessageBox.critical(self, "Error", f"Error al guardar configuración: {str(e)}", QMessageBox.Ok)