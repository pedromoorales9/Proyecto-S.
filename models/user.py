#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelo de datos para un usuario en el sistema de provisión.
"""

from datetime import datetime
from typing import List, Optional


class User:
    """
    Clase que representa un usuario en el sistema.
    
    Attributes:
        id (str): Identificador único del usuario.
        user_name (str): Nombre de usuario.
        email (str): Correo electrónico del usuario.
        first_name (str): Nombre del usuario.
        last_name (str): Apellido del usuario.
        display_name (str): Nombre para mostrar del usuario.
        job_title (str): Cargo o puesto del usuario.
        department (str): Departamento al que pertenece el usuario.
        phone_number (str): Número de teléfono del usuario.
        is_active (bool): Indica si el usuario está activo.
        roles (List): Lista de roles asignados al usuario.
        licenses (List): Lista de licencias asignadas al usuario.
        bc_user_id (str): ID del usuario en Business Central.
        exists_in_bc (bool): Indica si el usuario existe en Business Central.
        azure_ad_id (str): ID del usuario en Azure AD.
        exists_in_azure_ad (bool): Indica si el usuario existe en Azure AD.
        created_date (datetime): Fecha de creación del usuario.
    """
    
    def __init__(self):
        """Inicializar un nuevo usuario con valores predeterminados."""
        self.id: str = ""
        self.user_name: str = ""
        self.email: str = ""
        self.first_name: str = ""
        self.last_name: str = ""
        self.display_name: str = ""
        self.job_title: str = ""
        self.department: str = ""
        self.phone_number: str = ""
        self.is_active: bool = True
        self.roles: List = []
        self.licenses: List = []
        
        # Para Business Central
        self.bc_user_id: str = ""
        self.exists_in_bc: bool = False
        
        # Para Microsoft Graph/Azure AD
        self.azure_ad_id: str = ""
        self.exists_in_azure_ad: bool = False
        
        # Metadatos
        self.created_date: datetime = datetime.now()
    
    @property
    def full_name(self) -> str:
        """Obtener el nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def status(self) -> str:
        """Obtener el estado del usuario como texto."""
        return "Activo" if self.is_active else "Inactivo"
    
    def update_display_name(self) -> None:
        """Actualizar el nombre para mostrar basado en el nombre y apellido."""
        if not self.display_name and self.first_name and self.last_name:
            self.display_name = self.full_name
    
    def to_dict(self) -> dict:
        """
        Convertir el objeto a un diccionario.
        
        Returns:
            dict: Representación del usuario como diccionario.
        """
        return {
            'id': self.id,
            'user_name': self.user_name,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'display_name': self.display_name,
            'job_title': self.job_title,
            'department': self.department,
            'phone_number': self.phone_number,
            'is_active': self.is_active,
            'roles': [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.roles],
            'licenses': [l.to_dict() if hasattr(l, 'to_dict') else l for l in self.licenses],
            'bc_user_id': self.bc_user_id,
            'exists_in_bc': self.exists_in_bc,
            'azure_ad_id': self.azure_ad_id,
            'exists_in_azure_ad': self.exists_in_azure_ad,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """
        Crear un objeto User a partir de un diccionario.
        
        Args:
            data (dict): Diccionario con los datos del usuario.
            
        Returns:
            User: Objeto User creado.
        """
        from models.role import Role
        from models.license import License
        
        user = cls()
        user.id = data.get('id', '')
        user.user_name = data.get('user_name', '')
        user.email = data.get('email', '')
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        user.display_name = data.get('display_name', '')
        user.job_title = data.get('job_title', '')
        user.department = data.get('department', '')
        user.phone_number = data.get('phone_number', '')
        user.is_active = data.get('is_active', True)
        
        # Convertir roles si es necesario
        roles_data = data.get('roles', [])
        user.roles = [Role.from_dict(r) if isinstance(r, dict) else r for r in roles_data]
        
        # Convertir licencias si es necesario
        licenses_data = data.get('licenses', [])
        user.licenses = [License.from_dict(l) if isinstance(l, dict) else l for l in licenses_data]
        
        user.bc_user_id = data.get('bc_user_id', '')
        user.exists_in_bc = data.get('exists_in_bc', False)
        user.azure_ad_id = data.get('azure_ad_id', '')
        user.exists_in_azure_ad = data.get('exists_in_azure_ad', False)
        
        # Convertir fecha si existe
        created_date = data.get('created_date')
        if created_date:
            try:
                user.created_date = datetime.fromisoformat(created_date)
            except (ValueError, TypeError):
                user.created_date = datetime.now()
        
        return user