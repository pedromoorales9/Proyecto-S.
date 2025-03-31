#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vista de creación de usuarios.
"""

import re
import asyncio
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, 
    QPushButton, QScrollArea, QGroupBox, QGridLayout, QFormLayout, 
    QMessageBox, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, pyqtSlot

from models.user import User
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


class UserCreationView(QWidget):
    """Vista para la creación de nuevos usuarios."""
    
    def __init__(self, config_manager, logging_service, main_window):
        """
        Inicializar la vista de creación de usuarios.
        
        Args:
            config_manager: Gestor de configuración.
            logging_service: Servicio de logging.
            main_window: Ventana principal.
        """
        super().__init__()
        
        # Guardar referencias
        self.config_manager = config_manager
        self.logging_service = logging_service
        self.main_window = main_window
        
        # Crear servicios
        self.bc_service = BusinessCentralService(config_manager, logging_service)
        self.graph_service = MicrosoftGraphService(config_manager, logging_service)
        
        # Inicializar UI
        self.init_ui()
        
        # Cargar datos
        self.roles = []
        self.licenses = []
        asyncio.create_task(self.load_data())
    
    def init_ui(self):
        """Inicializar interfaz de usuario."""
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        
        # Título
        self.title_label = QLabel("Creación de Usuario")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 15px;")
        self.main_layout.addWidget(self.title_label)
        
        # Scroll area para el contenido
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QHBoxLayout(scroll_content)
        
        # Panel izquierdo - Información del usuario
        self.info_panel = QGroupBox("Información del Usuario")
        self.info_layout = QFormLayout()
        
        # Campos de texto
        self.first_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.user_name_edit = QLineEdit()
        self.user_name_edit.setEnabled(False)
        self.user_name_edit.setToolTip("Se genera automáticamente a partir del correo electrónico")
        self.department_edit = QLineEdit()
        self.job_title_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.password_edit = QPasswordLineEdit()
        
        # Casillas de verificación
        self.is_active_check = QCheckBox("Usuario activo")
        self.is_active_check.setChecked(True)
        self.require_password_change_check = QCheckBox("Requerir cambio de contraseña en el próximo inicio de sesión")
        self.require_password_change_check.setChecked(True)
        
        # Añadir campos al layout
        self.info_layout.addRow("Nombre:", self.first_name_edit)
        self.info_layout.addRow("Apellido:", self.last_name_edit)
        self.info_layout.addRow("Correo electrónico:", self.email_edit)
        self.info_layout.addRow("Nombre de usuario:", self.user_name_edit)
        self.info_layout.addRow("Departamento:", self.department_edit)
        self.info_layout.addRow("Cargo:", self.job_title_edit)
        self.info_layout.addRow("Teléfono:", self.phone_edit)
        self.info_layout.addRow("Contraseña temporal:", self.password_edit)
        self.info_layout.addRow("", self.is_active_check)
        self.info_layout.addRow("", self.require_password_change_check)
        
        self.info_panel.setLayout(self.info_layout)
        
        # Panel derecho - Roles y licencias
        self.options_panel = QWidget()
        self.options_layout = QVBoxLayout(self.options_panel)
        
        # Roles
        self.roles_group = QGroupBox("Roles en Business Central")
        self.roles_layout = QVBoxLayout()
        self.roles_container = QWidget()
        self.roles_container_layout = QVBoxLayout(self.roles_container)
        self.roles_layout.addWidget(self.roles_container)
        self.roles_group.setLayout(self.roles_layout)
        self.options_layout.addWidget(self.roles_group)
        
        # Licencias
        self.licenses_group = QGroupBox("Licencias de Microsoft 365")
        self.licenses_layout = QVBoxLayout()
        self.licenses_container = QWidget()
        self.licenses_container_layout = QVBoxLayout(self.licenses_container)
        self.licenses_layout.addWidget(self.licenses_container)
        self.licenses_group.setLayout(self.licenses_layout)
        self.options_layout.addWidget(self.licenses_group)
        
        # Opciones adicionales
        self.additional_options_group = QGroupBox("Opciones adicionales")
        self.additional_options_layout = QVBoxLayout()
        
        self.create_mailbox_check = QCheckBox("Configurar buzón de correo")
        self.create_mailbox_check.setChecked(True)
        self.sync_to_bc_check = QCheckBox("Sincronizar con Business Central")
        self.sync_to_bc_check.setChecked(True)
        
        self.additional_options_layout.addWidget(self.create_mailbox_check)
        self.additional_options_layout.addWidget(self.sync_to_bc_check)
        self.additional_options_group.setLayout(self.additional_options_layout)
        
        self.options_layout.addWidget(self.additional_options_group)
        self.options_layout.addStretch()
        
        # Añadir paneles al scroll layout
        self.scroll_layout.addWidget(self.info_panel)
        self.scroll_layout.addWidget(self.options_panel)
        
        scroll_area.setWidget(scroll_content)
        self.main_layout.addWidget(scroll_area)
        
        # Botones de acción
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addStretch()
        
        self.clear_button = QPushButton("Limpiar")
        self.clear_button.clicked.connect(self.clear_form)
        
        self.create_button = QPushButton("Crear Usuario")
        self.create_button.setObjectName("PrimaryButton")
        self.create_button.clicked.connect(self.create_user)
        
        self.buttons_layout.addWidget(self.clear_button)
        self.buttons_layout.addWidget(self.create_button)
        
        self.main_layout.addLayout(self.buttons_layout)
        
        # Conectar señales
        self.email_edit.textChanged.connect(self.on_email_changed)
        self.first_name_edit.textChanged.connect(self.on_name_changed)
        self.last_name_edit.textChanged.connect(self.on_name_changed)
    
    async def load_data(self):
        """Cargar datos iniciales."""
        try:
            # Actualizar estado
            self.main_window.update_status("Cargando datos...")
            
            # Intentar cargar roles
            self.roles = await self.bc_service.get_roles()
            if not self.roles:
                # Si falla, usar roles predeterminados
                self.roles = await self.config_manager.get_available_roles()
            
            # Actualizar UI con roles
            self.update_roles_ui()
            
            # Intentar cargar licencias
            self.licenses = await self.graph_service.get_available_licenses()
            if not self.licenses:
                # Si falla, usar licencias predeterminadas
                self.licenses = await self.config_manager.get_available_licenses()
            
            # Actualizar UI con licencias
            self.update_licenses_ui()
            
            # Cargar configuración por defecto
            self.load_default_config()
            
            # Actualizar estado
            self.main_window.update_status("Datos cargados correctamente")
            
        except Exception as e:
            self.logging_service.log_error("Error al cargar datos en la vista de creación de usuario", e)
            self.main_window.show_error(f"Error al cargar datos: {str(e)}")
            self.main_window.update_status("Error al cargar datos")
    
    def update_roles_ui(self):
        """Actualizar interfaz de usuario con los roles disponibles."""
        # Limpiar contenedor existente
        # Eliminar widgets existentes en el layout
        while self.roles_container_layout.count():
            child = self.roles_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Añadir roles
        for role in self.roles:
            checkbox = QCheckBox(role.name)
            checkbox.setToolTip(role.description)
            checkbox.setChecked(role.is_selected)
            # Guardar referencia al objeto Role en el widget
            checkbox.role = role
            self.roles_container_layout.addWidget(checkbox)
        
        # Añadir espacio al final
        self.roles_container_layout.addStretch()
    
    def update_licenses_ui(self):
        """Actualizar interfaz de usuario con las licencias disponibles."""
        # Limpiar contenedor existente
        while self.licenses_container_layout.count():
            child = self.licenses_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Añadir licencias
        for license_obj in self.licenses:
            checkbox = QCheckBox(license_obj.name)
            checkbox.setToolTip(license_obj.description)
            checkbox.setChecked(license_obj.is_selected)
            # Guardar referencia al objeto License en el widget
            checkbox.license = license_obj
            self.licenses_container_layout.addWidget(checkbox)
        
        # Añadir espacio al final
        self.licenses_container_layout.addStretch()
    
    def load_default_config(self):
        """Cargar configuración por defecto."""
        # Obtener configuración
        config = self.config_manager.config
        
        # Establecer valores predeterminados
        if config["app"]["default_password"]:
            self.password_edit.setText(config["app"]["default_password"])
        
        self.require_password_change_check.setChecked(config["app"]["require_password_change"])
    
    def on_email_changed(self, email):
        """
        Manejar cambio en el campo de correo electrónico.
        
        Args:
            email (str): Nuevo valor del campo.
        """
        try:
            if not email:
                self.user_name_edit.setText("")
                return
            
            # Si el correo no tiene @, agregar el dominio predeterminado
            if "@" not in email:
                domain = self.config_manager.config["app"]["email_domain"]
                if domain:
                    email = f"{email}@{domain}"
            
            # Actualizar nombre de usuario
            self.user_name_edit.setText(email)
            
        except Exception as e:
            self.logging_service.log_error("Error al procesar cambio de correo electrónico", e)
    
    def on_name_changed(self):
        """Manejar cambio en los campos de nombre y apellido."""
        try:
            # Si el correo ya está definido, no actualizar automáticamente
            if self.email_edit.text():
                return
            
            first_name = self.first_name_edit.text().strip()
            last_name = self.last_name_edit.text().strip()
            
            if not first_name and not last_name:
                return
            
            # Generar sugerencia de correo
            email_suggestion = ""
            
            if first_name:
                email_suggestion = first_name.lower()
                
                if last_name:
                    # Usar inicial del apellido o apellido completo según preferencia
                    email_suggestion += "." + last_name.lower()
            elif last_name:
                email_suggestion = last_name.lower()
            
            # Limpiar caracteres no válidos
            email_suggestion = re.sub(r'[^a-z0-9._-]', '', email_suggestion)
            
            # Agregar dominio
            domain = self.config_manager.config["app"]["email_domain"]
            if domain and email_suggestion:
                self.email_edit.setText(f"{email_suggestion}@{domain}")
            
        except Exception as e:
            self.logging_service.log_error("Error al generar sugerencia de correo", e)
    
    def clear_form(self):
        """Limpiar formulario."""
        # Limpiar campos
        self.first_name_edit.setText("")
        self.last_name_edit.setText("")
        self.email_edit.setText("")
        self.user_name_edit.setText("")
        self.department_edit.setText("")
        self.job_title_edit.setText("")
        self.phone_edit.setText("")
        
        # Restaurar valores predeterminados
        self.password_edit.setText(self.config_manager.config["app"]["default_password"])
        self.is_active_check.setChecked(True)
        self.require_password_change_check.setChecked(self.config_manager.config["app"]["require_password_change"])
        self.create_mailbox_check.setChecked(True)
        self.sync_to_bc_check.setChecked(True)
        
        # Desmarcar roles
        for i in range(self.roles_container_layout.count()):
            widget = self.roles_container_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)
                if hasattr(widget, 'role'):
                    widget.role.is_selected = False
        
        # Desmarcar licencias
        for i in range(self.licenses_container_layout.count()):
            widget = self.licenses_container_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)
                if hasattr(widget, 'license'):
                    widget.license.is_selected = False
    
    @pyqtSlot()
    def create_user(self):
        """Crear nuevo usuario."""
        # Validar entrada
        if not self.validate_input():
            return
        
        # Deshabilitar botón durante el proceso
        self.create_button.setEnabled(False)
        self.main_window.update_status("Creando usuario...")
        
        # Crear objeto de usuario
        user = self.build_user_object()
        
        # Crear usuario
        asyncio.create_task(self.do_create_user(user))
    
    def validate_input(self):
        """
        Validar entrada del formulario.
        
        Returns:
            bool: True si la entrada es válida.
        """
        # Lista para acumular mensajes de error
        errors = []
        
        # Validar campos obligatorios
        if not self.first_name_edit.text().strip():
            errors.append("El nombre es obligatorio")
        
        if not self.last_name_edit.text().strip():
            errors.append("El apellido es obligatorio")
        
        if not self.email_edit.text().strip():
            errors.append("El correo electrónico es obligatorio")
        elif not self.is_valid_email(self.email_edit.text().strip()):
            errors.append("El formato del correo electrónico no es válido")
        
        if not self.password_edit.text():
            errors.append("La contraseña es obligatoria")
        elif len(self.password_edit.text()) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")
        
        # Validar que al menos un rol o una licencia esté seleccionada
        any_role_selected = False
        any_license_selected = False
        
        # Verificar roles seleccionados
        for i in range(self.roles_container_layout.count()):
            widget = self.roles_container_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget.isChecked():
                any_role_selected = True
                break
        
        # Verificar licencias seleccionadas
        for i in range(self.licenses_container_layout.count()):
            widget = self.licenses_container_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget.isChecked():
                any_license_selected = True
                break
        
        if self.sync_to_bc_check.isChecked() and not any_role_selected:
            errors.append("Debe seleccionar al menos un rol para Business Central")
        
        if not any_license_selected:
            errors.append("Debe seleccionar al menos una licencia de Microsoft 365")
        
        # Mostrar errores si hay
        if errors:
            QMessageBox.warning(
                self,
                "Validación",
                "\n".join(errors),
                QMessageBox.Ok
            )
            return False
        
        return True
    
    def is_valid_email(self, email):
        """
        Validar formato de correo electrónico.
        
        Args:
            email (str): Correo electrónico a validar.
            
        Returns:
            bool: True si el formato es válido.
        """
        # Expresión regular para validar correo
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def build_user_object(self):
        """
        Construir objeto User con los datos del formulario.
        
        Returns:
            User: Objeto de usuario.
        """
        user = User()
        
        # Información básica
        user.first_name = self.first_name_edit.text().strip()
        user.last_name = self.last_name_edit.text().strip()
        user.email = self.email_edit.text().strip()
        user.user_name = self.user_name_edit.text().strip()
        user.display_name = f"{user.first_name} {user.last_name}"
        user.department = self.department_edit.text().strip()
        user.job_title = self.job_title_edit.text().strip()
        user.phone_number = self.phone_edit.text().strip()
        user.is_active = self.is_active_check.isChecked()
        
        # Roles
        user.roles = []
        for i in range(self.roles_container_layout.count()):
            widget = self.roles_container_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and hasattr(widget, 'role'):
                role = widget.role
                role.is_selected = widget.isChecked()
                if role.is_selected:
                    user.roles.append(role)
        
        # Licencias
        user.licenses = []
        for i in range(self.licenses_container_layout.count()):
            widget = self.licenses_container_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and hasattr(widget, 'license'):
                license_obj = widget.license
                license_obj.is_selected = widget.isChecked()
                if license_obj.is_selected:
                    user.licenses.append(license_obj)
        
        return user
    
    async def do_create_user(self, user):
        """
        Crear usuario en Azure AD y Business Central.
        
        Args:
            user (User): Usuario a crear.
        """
        try:
            # Obtener contraseña
            password = self.password_edit.text()
            
            # Crear usuario en Azure AD primero
            await self.create_user_in_azure_ad(user, password)
            
            # Si está marcada la opción, sincronizar con Business Central
            if self.sync_to_bc_check.isChecked():
                await self.create_user_in_bc(user)
            
            # Mostrar mensaje de éxito
            self.main_window.show_success(f"Usuario {user.display_name} creado correctamente")
            
            # Limpiar el formulario
            self.clear_form()
            
            self.main_window.update_status("Usuario creado correctamente")
            
        except Exception as e:
            self.logging_service.log_error(f"Error al crear usuario: {str(e)}", e)
            self.main_window.show_error(f"Error al crear usuario: {str(e)}")
            self.main_window.update_status("Error al crear usuario")
            
        finally:
            # Volver a habilitar el botón
            self.create_button.setEnabled(True)
    
    async def create_user_in_azure_ad(self, user, password):
        """
        Crear usuario en Azure AD.
        
        Args:
            user (User): Usuario a crear.
            password (str): Contraseña inicial.
        """
        self.main_window.update_status("Creando usuario en Azure AD...")
        
        # Verificar si el usuario ya existe
        existing_user = await self.graph_service.get_user_by_email(user.email)
        if existing_user:
            raise Exception(f"Ya existe un usuario con el correo {user.email} en Azure AD")
        
        # Crear usuario
        user = await self.graph_service.create_user(user, password)
        
        if not user.azure_ad_id:
            raise Exception("Error al crear usuario en Azure AD: No se obtuvo ID")
        
        # Configurar buzón si está marcada la opción
        if self.create_mailbox_check.isChecked():
            await self.graph_service.create_mailbox(user.azure_ad_id)
        
        self.logging_service.log_info(f"Usuario creado en Azure AD: {user.email}")
    
    async def create_user_in_bc(self, user):
        """
        Crear usuario en Business Central.
        
        Args:
            user (User): Usuario a crear.
        """
        self.main_window.update_status("Creando usuario en Business Central...")
        
        # Verificar si el usuario ya existe
        existing_user = await self.bc_service.get_user_by_email(user.email)
        if existing_user:
            raise Exception(f"Ya existe un usuario con el correo {user.email} en Business Central")
        
        # Crear usuario
        user = await self.bc_service.create_user(user)
        
        if not user.bc_user_id:
            raise Exception("Error al crear usuario en Business Central: No se obtuvo ID")
        
        self.logging_service.log_info(f"Usuario creado en Business Central: {user.email}")