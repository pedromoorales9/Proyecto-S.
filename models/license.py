#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelo de datos para una licencia en el sistema de provisión.
"""

from typing import Optional


class License:
    """
    Clase que representa una licencia de Microsoft 365 en el sistema.
    
    Attributes:
        id (str): Identificador único de la licencia.
        name (str): Nombre de la licencia.
        sku_id (str): ID de SKU de la licencia en Microsoft 365.
        description (str): Descripción de la licencia.
        is_selected (bool): Indica si la licencia está seleccionada en la interfaz.
    """
    
    def __init__(self, id: str = "", name: str = "", sku_id: str = "", 
                 description: str = "", is_selected: bool = False):
        """
        Inicializar una nueva licencia.
        
        Args:
            id (str, optional): Identificador único de la licencia. Default es "".
            name (str, optional): Nombre de la licencia. Default es "".
            sku_id (str, optional): ID de SKU de la licencia. Default es "".
            description (str, optional): Descripción de la licencia. Default es "".
            is_selected (bool, optional): Indica si la licencia está seleccionada. Default es False.
        """
        self.id: str = id
        self.name: str = name
        self.sku_id: str = sku_id
        self.description: str = description
        self.is_selected: bool = is_selected
    
    def to_dict(self) -> dict:
        """
        Convertir el objeto a un diccionario.
        
        Returns:
            dict: Representación de la licencia como diccionario.
        """
        return {
            'id': self.id,
            'name': self.name,
            'sku_id': self.sku_id,
            'description': self.description,
            'is_selected': self.is_selected
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'License':
        """
        Crear un objeto License a partir de un diccionario.
        
        Args:
            data (dict): Diccionario con los datos de la licencia.
            
        Returns:
            License: Objeto License creado.
        """
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            sku_id=data.get('sku_id', ''),
            description=data.get('description', ''),
            is_selected=data.get('is_selected', False)
        )
    
    def __str__(self) -> str:
        """
        Obtener representación en cadena de la licencia.
        
        Returns:
            str: Nombre de la licencia.
        """
        return self.name
    
    def __eq__(self, other) -> bool:
        """
        Comparar dos licencias por id o sku_id.
        
        Args:
            other: Otra licencia para comparar.
            
        Returns:
            bool: True si las licencias tienen el mismo id o sku_id.
        """
        if not isinstance(other, License):
            return False
        # Comparar por id o por sku_id si los ids no coinciden
        return self.id == other.id or (self.sku_id and self.sku_id == other.sku_id)