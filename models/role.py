#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelo de datos para un rol en el sistema de provisión.
"""

from typing import Optional


class Role:
    """
    Clase que representa un rol en el sistema.
    
    Attributes:
        id (str): Identificador único del rol.
        name (str): Nombre del rol.
        description (str): Descripción del rol.
        is_selected (bool): Indica si el rol está seleccionado en la interfaz.
    """
    
    def __init__(self, id: str = "", name: str = "", description: str = "", is_selected: bool = False):
        """
        Inicializar un nuevo rol.
        
        Args:
            id (str, optional): Identificador único del rol. Default es "".
            name (str, optional): Nombre del rol. Default es "".
            description (str, optional): Descripción del rol. Default es "".
            is_selected (bool, optional): Indica si el rol está seleccionado. Default es False.
        """
        self.id: str = id
        self.name: str = name
        self.description: str = description
        self.is_selected: bool = is_selected
    
    def to_dict(self) -> dict:
        """
        Convertir el objeto a un diccionario.
        
        Returns:
            dict: Representación del rol como diccionario.
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_selected': self.is_selected
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Role':
        """
        Crear un objeto Role a partir de un diccionario.
        
        Args:
            data (dict): Diccionario con los datos del rol.
            
        Returns:
            Role: Objeto Role creado.
        """
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            is_selected=data.get('is_selected', False)
        )
    
    def __str__(self) -> str:
        """
        Obtener representación en cadena del rol.
        
        Returns:
            str: Nombre del rol.
        """
        return self.name
    
    def __eq__(self, other) -> bool:
        """
        Comparar dos roles por id.
        
        Args:
            other: Otro rol para comparar.
            
        Returns:
            bool: True si los roles tienen el mismo id.
        """
        if not isinstance(other, Role):
            return False
        return self.id == other.id