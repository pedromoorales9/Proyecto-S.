#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestión de la configuración de la aplicación.
"""

import os
import json
import uuid
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

from models.role import Role
from models.license import License


class ConfigManager:
    """Gestiona la configuración de la aplicación."""
    
    def __init__(self, logging_service):
        """
        Inicializar el gestor de configuración.
        
        Args:
            logging_service: Servicio de logging.
        """
        self.logging_service = logging_service
        
        # Ubicación del archivo de configuración
        self.config_dir = Path(os.path.expanduser("~")) / ".user_provisioning_tool"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file_path = self.config_dir / "config.json"
        
        # Archivo de configuración por defecto
        self.default_config_path = Path("config/config.json")
        
        # Configuración actual
        self.config = {
            # Business Central
            "business_central": {
                "base_url": "",
                "tenant_id": "",
                "client_id": "",
                "client_secret": "",
                "company_id": "",
                "api_version": "v2.0"
            },
            # Microsoft Graph
            "microsoft_graph": {
                "base_url": "https://graph.microsoft.com/v1.0",
                "tenant_id": "",
                "client_id": "",
                "client_secret": "",
                "authority": "https://login.microsoftonline.com/{0}/v2.0",
                "scopes": ["https://graph.microsoft.com/.default"]
            },
            # App
            "app": {
                "encryption_key": "",
                "default_roles": [],
                "default_licenses": [],
                "email_domain": "empresa.com",
                "log_retention_days": 30,
                "enable_detailed_logging": True,
                "require_password_change": True,
                "default_password": "Temporal123!",
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def load_config(self) -> None:
        """Cargar la configuración desde el archivo."""
        try:
            # Cargar configuración desde archivo si existe
            if self.config_file_path.exists():
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    stored_config = json.load(f)
                
                if stored_config:
                    self.config = stored_config
                    self.logging_service.log_info("Configuración cargada desde archivo local")
                    return
            
            # Si no hay archivo personal, intentar cargar desde archivo por defecto
            if self.default_config_path.exists():
                with open(self.default_config_path, 'r', encoding='utf-8') as f:
                    default_config = json.load(f)
                
                if default_config:
                    self.config = default_config
                    self.logging_service.log_info("Configuración cargada desde archivo por defecto")
                    
                    # Generar clave de encriptación si no existe
                    if not self.config["app"]["encryption_key"]:
                        self.config["app"]["encryption_key"] = self.generate_encryption_key()
                    
                    # Guardar configuración
                    self.save_config()
                    return
            
            # Si no hay archivos, generar clave de encriptación por defecto
            if not self.config["app"]["encryption_key"]:
                self.config["app"]["encryption_key"] = self.generate_encryption_key()
                
                # Guardar configuración inicial
                self.save_config()
                self.logging_service.log_info("Configuración inicial generada")
            
        except Exception as e:
            self.logging_service.log_error("Error al cargar la configuración", e)
            
            # Crear configuración predeterminada
            self.config = {
                # Business Central
                "business_central": {
                    "base_url": "",
                    "tenant_id": "",
                    "client_id": "",
                    "client_secret": "",
                    "company_id": "",
                    "api_version": "v2.0"
                },
                # Microsoft Graph
                "microsoft_graph": {
                    "base_url": "https://graph.microsoft.com/v1.0",
                    "tenant_id": "",
                    "client_id": "",
                    "client_secret": "",
                    "authority": "https://login.microsoftonline.com/{0}/v2.0",
                    "scopes": ["https://graph.microsoft.com/.default"]
                },
                # App
                "app": {
                    "encryption_key": self.generate_encryption_key(),
                    "default_roles": [],
                    "default_licenses": [],
                    "email_domain": "empresa.com",
                    "log_retention_days": 30,
                    "enable_detailed_logging": True,
                    "require_password_change": True,
                    "default_password": "Temporal123!",
                    "last_updated": datetime.now().isoformat()
                }
            }
    
    def save_config(self) -> None:
        """Guardar la configuración en el archivo."""
        try:
            # Actualizar fecha de última modificación
            self.config["app"]["last_updated"] = datetime.now().isoformat()
            
            # Guardar configuración
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            
            self.logging_service.log_info("Configuración guardada correctamente")
        except Exception as e:
            self.logging_service.log_error("Error al guardar la configuración", e)
            raise
    
    def is_configuration_complete(self) -> bool:
        """
        Verificar si la configuración está completa.
        
        Returns:
            bool: True si la configuración está completa.
        """
        return (
            self.is_business_central_config_complete() and
            self.is_microsoft_graph_config_complete() and
            self.is_app_config_complete()
        )
    
    def is_business_central_config_complete(self) -> bool:
        """
        Verificar si la configuración de Business Central está completa.
        
        Returns:
            bool: True si la configuración de Business Central está completa.
        """
        bc_config = self.config["business_central"]
        return (
            bool(bc_config["base_url"]) and
            bool(bc_config["tenant_id"]) and
            bool(bc_config["client_id"]) and
            bool(bc_config["client_secret"]) and
            bool(bc_config["company_id"])
        )
    
    def is_microsoft_graph_config_complete(self) -> bool:
        """
        Verificar si la configuración de Microsoft Graph está completa.
        
        Returns:
            bool: True si la configuración de Microsoft Graph está completa.
        """
        mg_config = self.config["microsoft_graph"]
        return (
            bool(mg_config["base_url"]) and
            bool(mg_config["tenant_id"]) and
            bool(mg_config["client_id"]) and
            bool(mg_config["client_secret"])
        )
    
    def is_app_config_complete(self) -> bool:
        """
        Verificar si la configuración de la aplicación está completa.
        
        Returns:
            bool: True si la configuración de la aplicación está completa.
        """
        app_config = self.config["app"]
        return (
            bool(app_config["encryption_key"]) and
            bool(app_config["email_domain"])
        )
    
    async def get_available_roles(self) -> List[Role]:
        """
        Obtener roles disponibles.
        
        Returns:
            List[Role]: Lista de roles disponibles.
        """
        roles = []
        
        # Obtener roles desde la configuración
        roles_data = self.config["app"]["default_roles"]
        for role_data in roles_data:
            role = Role.from_dict(role_data)
            roles.append(role)
        
        return roles
    
    async def save_role(self, role: Role) -> None:
        """
        Guardar un rol en la configuración.
        
        Args:
            role (Role): Rol a guardar.
        """
        # Obtener roles actuales
        roles_data = self.config["app"]["default_roles"]
        
        # Buscar si ya existe
        found = False
        for i, r in enumerate(roles_data):
            if r["id"] == role.id:
                # Actualizar
                roles_data[i] = role.to_dict()
                found = True
                break
        
        if not found:
            # Si es nuevo, generar ID si no tiene
            if not role.id:
                role.id = str(uuid.uuid4())
            
            # Agregar
            roles_data.append(role.to_dict())
        
        # Guardar configuración
        self.save_config()
    
    async def delete_role(self, role_id: str) -> None:
        """
        Eliminar un rol de la configuración.
        
        Args:
            role_id (str): ID del rol a eliminar.
        """
        # Obtener roles actuales
        roles_data = self.config["app"]["default_roles"]
        
        # Filtrar
        self.config["app"]["default_roles"] = [r for r in roles_data if r["id"] != role_id]
        
        # Guardar configuración
        self.save_config()
    
    async def get_available_licenses(self) -> List[License]:
        """
        Obtener licencias disponibles.
        
        Returns:
            List[License]: Lista de licencias disponibles.
        """
        licenses = []
        
        # Obtener licencias desde la configuración
        licenses_data = self.config["app"]["default_licenses"]
        for license_data in licenses_data:
            license_obj = License.from_dict(license_data)
            licenses.append(license_obj)
        
        return licenses
    
    async def save_license(self, license_obj: License) -> None:
        """
        Guardar una licencia en la configuración.
        
        Args:
            license_obj (License): Licencia a guardar.
        """
        # Obtener licencias actuales
        licenses_data = self.config["app"]["default_licenses"]
        
        # Buscar si ya existe
        found = False
        for i, l in enumerate(licenses_data):
            if l["id"] == license_obj.id:
                # Actualizar
                licenses_data[i] = license_obj.to_dict()
                found = True
                break
        
        if not found:
            # Si es nueva, generar ID si no tiene
            if not license_obj.id:
                license_obj.id = str(uuid.uuid4())
            
            # Agregar
            licenses_data.append(license_obj.to_dict())
        
        # Guardar configuración
        self.save_config()
    
    async def delete_license(self, license_id: str) -> None:
        """
        Eliminar una licencia de la configuración.
        
        Args:
            license_id (str): ID de la licencia a eliminar.
        """
        # Obtener licencias actuales
        licenses_data = self.config["app"]["default_licenses"]
        
        # Filtrar
        self.config["app"]["default_licenses"] = [l for l in licenses_data if l["id"] != license_id]
        
        # Guardar configuración
        self.save_config()
    
    def encrypt_string(self, plain_text: str) -> str:
        """
        Encriptar una cadena con la clave de encriptación.
        
        Args:
            plain_text (str): Texto a encriptar.
            
        Returns:
            str: Texto encriptado en base64.
        """
        if not plain_text:
            return plain_text
        
        try:
            # Obtener clave de encriptación
            key_bytes = self._ensure_valid_key(self.config["app"]["encryption_key"])
            
            # Crear cifrador AES
            cipher = AES.new(key_bytes, AES.MODE_CBC)
            
            # Encriptar
            ct_bytes = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))
            
            # Combinar IV y texto cifrado y convertir a base64
            iv = base64.b64encode(cipher.iv).decode('utf-8')
            ct = base64.b64encode(ct_bytes).decode('utf-8')
            
            return f"{iv}:{ct}"
        except Exception as e:
            self.logging_service.log_error("Error al encriptar texto", e)
            return plain_text
    
    def decrypt_string(self, cipher_text: str) -> str:
        """
        Desencriptar una cadena con la clave de encriptación.
        
        Args:
            cipher_text (str): Texto encriptado en base64.
            
        Returns:
            str: Texto desencriptado.
        """
        if not cipher_text or ":" not in cipher_text:
            return cipher_text
        
        try:
            # Obtener clave de encriptación
            key_bytes = self._ensure_valid_key(self.config["app"]["encryption_key"])
            
            # Separar IV y texto cifrado
            iv, ct = cipher_text.split(":")
            iv_bytes = base64.b64decode(iv)
            ct_bytes = base64.b64decode(ct)
            
            # Crear descifrador AES
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
            
            # Desencriptar
            pt_bytes = unpad(cipher.decrypt(ct_bytes), AES.block_size)
            
            return pt_bytes.decode('utf-8')
        except Exception as e:
            self.logging_service.log_error("Error al desencriptar texto", e)
            return cipher_text
    
    def generate_encryption_key(self) -> str:
        """
        Generar una nueva clave de encriptación.
        
        Returns:
            str: Clave de encriptación en base64.
        """
        # Generar 32 bytes aleatorios (256 bits)
        key_bytes = get_random_bytes(32)
        return base64.b64encode(key_bytes).decode('utf-8')
    
    def _ensure_valid_key(self, key: str) -> bytes:
        """
        Asegurar que la clave tiene el tamaño correcto para AES.
        
        Args:
            key (str): Clave en base64 o texto plano.
            
        Returns:
            bytes: Clave en bytes de 32 bytes (256 bits).
        """
        if not key:
            key = self.generate_encryption_key()
        
        # Intentar decodificar de base64
        try:
            key_bytes = base64.b64decode(key)
        except:
            key_bytes = key.encode('utf-8')
        
        # Ajustar tamaño (AES-256 necesita 32 bytes)
        if len(key_bytes) < 32:
            key_bytes = key_bytes + b'\0' * (32 - len(key_bytes))
        elif len(key_bytes) > 32:
            key_bytes = key_bytes[:32]
        
        return key_bytes