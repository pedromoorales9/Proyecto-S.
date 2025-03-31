#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vista de asignación de licencias.
"""

import asyncio
import math
from async_utils import run_async  # Añadir esta importación
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QListWidget, QListWidgetItem, QGroupBox, QScrollArea, QCheckBox,
    QFrame, QSplitter, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot, QSize

from models.user import User
from models.license import License
from services.microsoft_graph import MicrosoftGraphService


class LicenseAssignmentView(QWidget):
    """Vista para la asignación de licencias."""
    
    def __init__(self, config_manager, logging_service, main_window):
        """
        Inicializar la vista de asignación de licencias.
        
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
        self.graph_service = MicrosoftGraphService(config_manager, logging_service)
        
        # Variables de estado
        self.all_users = []
        self.selected_user = None
        self.available_licenses = []
        self.user_licenses = []
        self.current_page = 1
        self.page_size = 20
        self.total_pages = 1
        self.has_changes = False
        
        # Inicializar UI
        self.init_ui()
        
        # Cargar datos
        run_async(self.load_users())  # MODIFICADO
    
    def init_ui(self):
        """Inicializar interfaz de usuario."""
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        
        # Título
        self.title_label = QLabel("Asignación de Licencias")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 15px;")
        self.main_layout.addWidget(self.title_label)
        
        # Búsqueda
        self.search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar por correo electrónico o nombre de usuario")
        self.search_edit.returnPressed.connect(self.search_users)
        
        self.search_button = QPushButton("Buscar")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(self.search_users)
        
        self.search_layout.addWidget(self.search_edit)
        self.search_layout.addWidget(self.search_button)
        
        self.main_layout.addLayout(self.search_layout)
        
        # Contenido principal - Splitter
        self.content_splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo - Lista de usuarios
        self.users_panel = QGroupBox("Usuarios")
        self.users_layout = QVBoxLayout()
        
        self.users_list = QListWidget()
        self.users_list.currentItemChanged.connect(self.on_user_selected)
        
        self.users_layout.addWidget(self.users_list)
        self.users_panel.setLayout(self.users_layout)
        
        # Panel derecho - Detalles y licencias
        self.details_panel = QGroupBox("Detalles del Usuario")
        self.details_layout = QVBoxLayout()
        
        # Información del usuario
        self.user_info_frame = QFrame()
        self.user_info_layout = QVBoxLayout(self.user_info_frame)
        
        self.user_name_label = QLabel("Seleccione un usuario")
        self.user_name_label.setStyleSheet("font-weight: bold;")
        self.user_email_label = QLabel("")
        self.user_department_label = QLabel("")
        
        self.user_info_layout.addWidget(self.user_name_label)
        self.user_info_layout.addWidget(self.user_email_label)
        self.user_info_layout.addWidget(self.user_department_label)
        self.user_info_layout.addStretch()
        
        # Licencias
        self.licenses_group = QGroupBox("Licencias de Microsoft 365")
        self.licenses_layout = QVBoxLayout()
        
        self.licenses_scroll = QScrollArea()
        self.licenses_scroll.setWidgetResizable(True)
        self.licenses_container = QWidget()
        self.licenses_container_layout = QVBoxLayout(self.licenses_container)
        self.licenses_scroll.setWidget(self.licenses_container)
        
        self.licenses_layout.addWidget(self.licenses_scroll)
        self.licenses_group.setLayout(self.licenses_layout)
        
        # Botón de guardar
        self.save_button = QPushButton("Guardar Cambios")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self.save_licenses)
        self.save_button.setEnabled(False)
        
        # Añadir widgets al layout de detalles
        self.details_layout.addWidget(self.user_info_frame)
        self.details_layout.addWidget(self.licenses_group)
        self.details_layout.addWidget(self.save_button)
        
        self.details_panel.setLayout(self.details_layout)
        
        # Añadir paneles al splitter
        self.content_splitter.addWidget(self.users_panel)
        self.content_splitter.addWidget(self.details_panel)
        self.content_splitter.setSizes([300, 400])  # Tamaño inicial
        
        self.main_layout.addWidget(self.content_splitter)
        
        # Paginación
        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.addStretch()
        
        self.prev_button = QPushButton("< Anterior")
        self.prev_button.clicked.connect(self.prev_page)
        self.prev_button.setEnabled(False)
        
        self.page_label = QLabel("Página 1 de 1")
        
        self.next_button = QPushButton("Siguiente >")
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)
        
        self.pagination_layout.addWidget(self.prev_button)
        self.pagination_layout.addWidget(self.page_label)
        self.pagination_layout.addWidget(self.next_button)
        self.pagination_layout.addStretch()
        
        self.main_layout.addLayout(self.pagination_layout)
    
    async def load_users(self, search_term=None):
        """
        Cargar usuarios desde Microsoft Graph.
        
        Args:
            search_term (str, optional): Término de búsqueda. Default es None.
        """
        try:
            self.main_window.update_status("Cargando usuarios...")
            
            # Cargar usuarios desde Microsoft Graph
            if search_term:
                # Buscar por término
                filter_query = f"startswith(displayName,'{search_term}') or startswith(userPrincipalName,'{search_term}')"
                self.all_users = await self.graph_service.get_users(filter_query=filter_query)
            else:
                # Cargar todos los usuarios (paginado)
                self.all_users = await self.graph_service.get_users(top=100)
            
            # Actualizar paginación
            self.update_pagination()
            
            # Mostrar usuarios
            self.display_current_page()
            
            self.main_window.update_status("Usuarios cargados")
            
        except Exception as e:
            self.logging_service.log_error("Error al cargar usuarios", e)
            self.main_window.show_error(f"Error al cargar usuarios: {str(e)}")
            self.main_window.update_status("Error al cargar usuarios")
    
    async def load_available_licenses(self):
        """Cargar licencias disponibles."""
        try:
            # Cargar licencias disponibles
            self.available_licenses = await self.graph_service.get_available_licenses()
            
            if not self.available_licenses:
                # Si no hay licencias disponibles, usar las predeterminadas
                self.available_licenses = await self.config_manager.get_available_licenses()
            
        except Exception as e:
            self.logging_service.log_error("Error al cargar licencias disponibles", e)
            self.main_window.show_error(f"Error al cargar licencias disponibles: {str(e)}")
    
    async def load_user_licenses(self, user_id):
        """
        Cargar licencias del usuario.
        
        Args:
            user_id (str): ID del usuario en Azure AD.
        """
        try:
            # Cargar licencias del usuario
            self.user_licenses = await self.graph_service.get_user_licenses(user_id)
            
            # Si no hay licencias disponibles cargadas, cargarlas
            if not self.available_licenses:
                await self.load_available_licenses()
            
            # Combinar licencias disponibles con las del usuario
            combined_licenses = []
            
            for license_obj in self.available_licenses:
                combined_license = License(
                    id=license_obj.id,
                    name=license_obj.name,
                    sku_id=license_obj.sku_id,
                    description=license_obj.description,
                    is_selected=False
                )
                
                # Verificar si la licencia está asignada al usuario
                for user_license in self.user_licenses:
                    if user_license.sku_id == license_obj.sku_id:
                        combined_license.is_selected = True
                        break
                
                combined_licenses.append(combined_license)
            
            # Mostrar licencias en la interfaz
            self.update_licenses_ui(combined_licenses)
            
            # Desactivar botón de guardar hasta que haya cambios
            self.has_changes = False
            self.save_button.setEnabled(False)
            
        except Exception as e:
            self.logging_service.log_error(f"Error al cargar licencias del usuario: {user_id}", e)
            self.main_window.show_error(f"Error al cargar licencias del usuario: {str(e)}")
    
    def update_licenses_ui(self, licenses):
        """
        Actualizar interfaz de usuario con las licencias.
        
        Args:
            licenses (List[License]): Lista de licencias.
        """
        # Limpiar contenedor existente
        while self.licenses_container_layout.count():
            child = self.licenses_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Añadir licencias
        for license_obj in licenses:
            checkbox = QCheckBox(license_obj.name)
            checkbox.setToolTip(license_obj.description)
            checkbox.setChecked(license_obj.is_selected)
            # Guardar referencia al objeto License en el widget
            checkbox.license = license_obj
            checkbox.stateChanged.connect(self.on_license_changed)
            self.licenses_container_layout.addWidget(checkbox)
        
        # Añadir espacio al final
        self.licenses_container_layout.addStretch()
    
    def update_pagination(self):
        """Actualizar controles de paginación."""
        if not self.all_users:
            self.total_pages = 1
        else:
            self.total_pages = math.ceil(len(self.all_users) / self.page_size)
        
        if self.total_pages == 0:
            self.total_pages = 1
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        
        self.page_label.setText(f"Página {self.current_page} de {self.total_pages}")
        
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)
    
    def display_current_page(self):
        """Mostrar página actual de usuarios."""
        # Limpiar lista
        self.users_list.clear()
        
        if not self.all_users:
            return
        
        # Calcular índices
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.all_users))
        
        # Añadir usuarios
        for i in range(start_idx, end_idx):
            user = self.all_users[i]
            item = QListWidgetItem(f"{user.display_name} ({user.email})")
            item.setData(Qt.UserRole, user)
            self.users_list.addItem(item)
    
    @pyqtSlot()
    def prev_page(self):
        """Ir a la página anterior."""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_pagination()
            self.display_current_page()
    
    @pyqtSlot()
    def next_page(self):
        """Ir a la página siguiente."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_pagination()
            self.display_current_page()
    
    @pyqtSlot()
    def search_users(self):
        """Buscar usuarios según el término de búsqueda."""
        search_term = self.search_edit.text().strip()
        run_async(self.load_users(search_term))  # MODIFICADO
    
    def on_user_selected(self, current, previous):
        """
        Manejar selección de usuario.
        
        Args:
            current: Item actual seleccionado.
            previous: Item previamente seleccionado.
        """
        if current:
            user = current.data(Qt.UserRole)
            self.selected_user = user
            
            # Actualizar información del usuario
            self.user_name_label.setText(user.display_name)
            self.user_email_label.setText(f"Email: {user.email}")
            self.user_department_label.setText(f"Departamento: {user.department or 'No especificado'}")
            
            # Cargar licencias del usuario
            run_async(self.load_user_licenses(user.azure_ad_id))  # MODIFICADO
        else:
            self.selected_user = None
            self.user_name_label.setText("Seleccione un usuario")
            self.user_email_label.setText("")
            self.user_department_label.setText("")
            
            # Limpiar licencias
            while self.licenses_container_layout.count():
                child = self.licenses_container_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            self.save_button.setEnabled(False)
    
    def on_license_changed(self, state):
        """
        Manejar cambio en la selección de licencias.
        
        Args:
            state: Estado del checkbox.
        """
        self.has_changes = True
        self.save_button.setEnabled(True)
    
    @pyqtSlot()
    def save_licenses(self):
        """Guardar cambios en las licencias del usuario."""
        if not self.selected_user or not self.has_changes:
            return
        
        # Desactivar botón durante el proceso
        self.save_button.setEnabled(False)
        self.main_window.update_status("Guardando cambios de licencias...")
        
        # Obtener licencias seleccionadas
        licenses_to_add = []
        licenses_to_remove = []
        
        for i in range(self.licenses_container_layout.count()):
            widget = self.licenses_container_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and hasattr(widget, 'license'):
                license_obj = widget.license
                
                # Verificar si la licencia estaba asignada originalmente
                was_assigned = False
                for user_license in self.user_licenses:
                    if user_license.sku_id == license_obj.sku_id:
                        was_assigned = True
                        break
                
                if widget.isChecked() and not was_assigned:
                    licenses_to_add.append(license_obj)
                elif not widget.isChecked() and was_assigned:
                    licenses_to_remove.append(license_obj)
        
        # Ejecutar tarea asíncrona
        run_async(self.update_user_licenses(licenses_to_add, licenses_to_remove), callback=self.on_licenses_updated, error_callback=self.on_licenses_error)  # MODIFICADO
    
    def on_licenses_updated(self, _):
        """Manejar la actualización exitosa de licencias."""
        self.main_window.show_success("Licencias actualizadas correctamente")
        self.main_window.update_status("Licencias actualizadas")
        
        # Recargar licencias del usuario
        run_async(self.load_user_licenses(self.selected_user.azure_ad_id))  # MODIFICADO
    
    def on_licenses_error(self, error):
        """Manejar errores en la actualización de licencias."""
        self.logging_service.log_error(
            f"Error al actualizar licencias del usuario: {self.selected_user.email}", error)
        self.main_window.show_error(f"Error al actualizar licencias: {str(error)}")
        self.main_window.update_status("Error al actualizar licencias")
        self.save_button.setEnabled(True)
    
    async def update_user_licenses(self, licenses_to_add, licenses_to_remove):
        """
        Actualizar licencias del usuario.
        
        Args:
            licenses_to_add (List[License]): Licencias a añadir.
            licenses_to_remove (List[License]): Licencias a quitar.
        """
        # Añadir licencias
        for license_obj in licenses_to_add:
            await self.graph_service.assign_license_to_user(
                self.selected_user.azure_ad_id, license_obj.sku_id)
        
        # Quitar licencias
        for license_obj in licenses_to_remove:
            await self.graph_service.remove_license_from_user(
                self.selected_user.azure_ad_id, license_obj.sku_id)
        
        return True