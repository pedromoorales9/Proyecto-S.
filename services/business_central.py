#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio para interactuar con la API de Business Central.
"""

import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
import aiohttp
import msal

from models.user import User
from models.role import Role


class BusinessCentralService:
    """Servicio para interactuar con la API de Business Central."""
    
    def __init__(self, config_manager, logging_service):
        """
        Inicializar el servicio de Business Central.
        
        Args:
            config_manager: Gestor de configuración.
            logging_service: Servicio de logging.
        """
        self.config_manager = config_manager
        self.logging_service = logging_service
        self._access_token = None
        self._app = None
    
    async def test_connection(self) -> bool:
        """
        Probar la conexión a Business Central.
        
        Returns:
            bool: True si la conexión es exitosa.
        """
        try:
            # Obtener token de acceso
            token = await self._get_access_token()
            if not token:
                return False
            
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            base_url = bc_config["base_url"].rstrip('/')
            api_version = bc_config["api_version"]
            company_id = bc_config["company_id"]
            
            # Probar una solicitud simple (obtener compañía)
            url = f"{base_url}/{api_version}/companies({company_id})"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    return response.status == 200
        except Exception as e:
            self.logging_service.log_error("Error al probar la conexión con Business Central", e)
            return False
    
    async def create_user(self, user: User) -> User:
        """
        Crear un nuevo usuario en Business Central.
        
        Args:
            user (User): Usuario a crear.
            
        Returns:
            User: Usuario creado con ID de Business Central.
        """
        try:
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            base_url = bc_config["base_url"].rstrip('/')
            api_version = bc_config["api_version"]
            company_id = bc_config["company_id"]
            
            url = f"{base_url}/{api_version}/companies({company_id})/users"
            
            # Construir cuerpo de la solicitud
            body = {
                "userName": user.user_name,
                "displayName": user.display_name or user.full_name,
                "email": user.email,
                "contactEmail": user.email,
                "authenticationEmail": user.email,
                "state": "Enabled" if user.is_active else "Disabled"
                # Agregar campos adicionales según sea necesario
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._get_headers(), json=body) as response:
                    if response.status in (200, 201):
                        # Éxito - actualizar usuario con ID de Business Central
                        bc_user_data = await response.json()
                        user.bc_user_id = bc_user_data.get('id')
                        user.exists_in_bc = True
                        
                        self.logging_service.log_info(f"Usuario creado en Business Central: {user.user_name}")
                        
                        # Asignar roles si aplica
                        if user.roles:
                            for role in [r for r in user.roles if r.is_selected]:
                                await self.assign_role_to_user(user.bc_user_id, role.id)
                        
                        return user
                    else:
                        error_data = await response.text()
                        error_msg = f"Error al crear usuario en Business Central: {response.status} - {error_data}"
                        self.logging_service.log_error(error_msg)
                        raise Exception(error_msg)
        except Exception as e:
            self.logging_service.log_error(f"Error al crear usuario en Business Central: {user.user_name}", e)
            raise
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Obtener un usuario por su ID.
        
        Args:
            user_id (str): ID del usuario en Business Central.
            
        Returns:
            Optional[User]: Usuario encontrado o None.
        """
        try:
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            base_url = bc_config["base_url"].rstrip('/')
            api_version = bc_config["api_version"]
            company_id = bc_config["company_id"]
            
            url = f"{base_url}/{api_version}/companies({company_id})/users({user_id})"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        bc_user_data = await response.json()
                        
                        # Convertir a modelo de usuario
                        user = User()
                        user.bc_user_id = bc_user_data.get('id')
                        user.user_name = bc_user_data.get('userName')
                        user.display_name = bc_user_data.get('displayName')
                        user.email = bc_user_data.get('email')
                        user.is_active = bc_user_data.get('state') == 'Enabled'
                        user.exists_in_bc = True
                        
                        # Obtener roles del usuario
                        user.roles = await self._get_user_roles(user_id)
                        
                        return user
                    else:
                        if response.status != 404:  # No registrar error si no se encontró
                            error_data = await response.text()
                            self.logging_service.log_error(f"Error al obtener usuario de Business Central: {response.status} - {error_data}")
                        return None
        except Exception as e:
            self.logging_service.log_error(f"Error al obtener usuario de Business Central: {user_id}", e)
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Obtener un usuario por su correo electrónico.
        
        Args:
            email (str): Correo electrónico del usuario.
            
        Returns:
            Optional[User]: Usuario encontrado o None.
        """
        try:
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            base_url = bc_config["base_url"].rstrip('/')
            api_version = bc_config["api_version"]
            company_id = bc_config["company_id"]
            
            # Filtrar por correo electrónico
            filter_query = f"email eq '{email}'"
            url = f"{base_url}/{api_version}/companies({company_id})/users?$filter={filter_query}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Verificar si se encontraron resultados
                        if 'value' in data and data['value']:
                            bc_user_data = data['value'][0]
                            
                            # Convertir a modelo de usuario
                            user = User()
                            user.bc_user_id = bc_user_data.get('id')
                            user.user_name = bc_user_data.get('userName')
                            user.display_name = bc_user_data.get('displayName')
                            user.email = bc_user_data.get('email')
                            user.is_active = bc_user_data.get('state') == 'Enabled'
                            user.exists_in_bc = True
                            
                            # Obtener roles del usuario
                            user.roles = await self._get_user_roles(user.bc_user_id)
                            
                            return user
                        
                        return None
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al buscar usuario por email en Business Central: {response.status} - {error_data}")
                        return None
        except Exception as e:
            self.logging_service.log_error(f"Error al buscar usuario por email en Business Central: {email}", e)
            return None
    
    async def get_users(self, top: Optional[int] = None, skip: Optional[int] = None, 
                      filter_query: Optional[str] = None) -> List[User]:
        """
        Obtener usuarios de Business Central.
        
        Args:
            top (int, optional): Número máximo de usuarios a obtener.
            skip (int, optional): Número de usuarios a omitir.
            filter_query (str, optional): Filtro OData para la consulta.
            
        Returns:
            List[User]: Lista de usuarios.
        """
        try:
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            base_url = bc_config["base_url"].rstrip('/')
            api_version = bc_config["api_version"]
            company_id = bc_config["company_id"]
            
            # Construir URL con parámetros
            url = f"{base_url}/{api_version}/companies({company_id})/users"
            params = []
            
            if top is not None:
                params.append(f"$top={top}")
            
            if skip is not None:
                params.append(f"$skip={skip}")
            
            if filter_query:
                params.append(f"$filter={filter_query}")
            
            if params:
                url += "?" + "&".join(params)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = []
                        
                        for bc_user_data in data.get('value', []):
                            user = User()
                            user.bc_user_id = bc_user_data.get('id')
                            user.user_name = bc_user_data.get('userName')
                            user.display_name = bc_user_data.get('displayName')
                            user.email = bc_user_data.get('email')
                            user.is_active = bc_user_data.get('state') == 'Enabled'
                            user.exists_in_bc = True
                            
                            result.append(user)
                        
                        return result
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al obtener usuarios de Business Central: {response.status} - {error_data}")
                        return []
        except Exception as e:
            self.logging_service.log_error("Error al obtener usuarios de Business Central", e)
            return []
    
    async def update_user(self, user: User) -> User:
        """
        Actualizar un usuario en Business Central.
        
        Args:
            user (User): Usuario a actualizar.
            
        Returns:
            User: Usuario actualizado.
        """
        try:
            if not user.bc_user_id:
                raise ValueError("El ID de usuario de Business Central es requerido para actualizar")
            
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            base_url = bc_config["base_url"].rstrip('/')
            api_version = bc_config["api_version"]
            company_id = bc_config["company_id"]
            
            url = f"{base_url}/{api_version}/companies({company_id})/users({user.bc_user_id})"
            
            # Construir cuerpo de la solicitud
            body = {
                "displayName": user.display_name or user.full_name,
                "email": user.email,
                "contactEmail": user.email,
                "state": "Enabled" if user.is_active else "Disabled"
                # Otros campos según sea necesario
            }
            
            # Business Central API utiliza PATCH para actualizaciones parciales
            headers = self._get_headers()
            headers["Content-Type"] = "application/json"
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=headers, json=body) as response:
                    if response.status in (200, 204):
                        self.logging_service.log_info(f"Usuario actualizado en Business Central: {user.user_name}")
                        return user
                    else:
                        error_data = await response.text()
                        error_msg = f"Error al actualizar usuario en Business Central: {response.status} - {error_data}"
                        self.logging_service.log_error(error_msg)
                        raise Exception(error_msg)
        except Exception as e:
            self.logging_service.log_error(f"Error al actualizar usuario en Business Central: {user.user_name}", e)
            raise
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Eliminar un usuario de Business Central.
        
        Args:
            user_id (str): ID del usuario en Business Central.
            
        Returns:
            bool: True si se eliminó correctamente.
        """
        try:
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            base_url = bc_config["base_url"].rstrip('/')
            api_version = bc_config["api_version"]
            company_id = bc_config["company_id"]
            
            url = f"{base_url}/{api_version}/companies({company_id})/users({user_id})"
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=self._get_headers()) as response:
                    if response.status in (200, 204):
                        self.logging_service.log_info(f"Usuario eliminado de Business Central: {user_id}")
                        return True
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al eliminar usuario de Business Central: {response.status} - {error_data}")
                        return False
        except Exception as e:
            self.logging_service.log_error(f"Error al eliminar usuario de Business Central: {user_id}", e)
            return False
    
    async def get_roles(self) -> List[Role]:
        """
        Obtener roles disponibles en Business Central.
        
        Returns:
            List[Role]: Lista de roles.
        """
        try:
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            base_url = bc_config["base_url"].rstrip('/')
            api_version = bc_config["api_version"]
            company_id = bc_config["company_id"]
            
            url = f"{base_url}/{api_version}/companies({company_id})/userPermissionSets"  # Ajustar según la API
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        roles = []
                        
                        for bc_role in data.get('value', []):
                            role = Role(
                                id=bc_role.get('id'),
                                name=bc_role.get('name'),
                                description=bc_role.get('description', '')
                            )
                            roles.append(role)
                        
                        return roles
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al obtener roles de Business Central: {response.status} - {error_data}")
                        
                        # Si falla, devolver los roles predeterminados de la configuración
                        return await self.config_manager.get_available_roles()
        except Exception as e:
            self.logging_service.log_error("Error al obtener roles de Business Central", e)
            
            # Si falla, devolver los roles predeterminados de la configuración
            return await self.config_manager.get_available_roles()
    
    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """
        Asignar un rol a un usuario.
        
        Args:
            user_id (str): ID del usuario en Business Central.
            role_id (str): ID del rol.
            
        Returns:
            bool: True si se asignó correctamente.
        """
        try:
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            base_url = bc_config["base_url"].rstrip('/')
            api_version = bc_config["api_version"]
            company_id = bc_config["company_id"]
            
            url = f"{base_url}/{api_version}/companies({company_id})/users({user_id})/userPermissions"  # Ajustar según la API
            
            # Construir cuerpo de la solicitud
            body = {
                "permissionSetId": role_id
                # Otros campos según sea necesario
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._get_headers(), json=body) as response:
                    if response.status in (200, 201, 204):
                        self.logging_service.log_info(f"Rol asignado a usuario en Business Central: Usuario {user_id}, Rol {role_id}")
                        return True
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al asignar rol a usuario en Business Central: {response.status} - {error_data}")
                        return False
        except Exception as e:
            self.logging_service.log_error(f"Error al asignar rol a usuario en Business Central: Usuario {user_id}, Rol {role_id}", e)
            return False
    
    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """
        Remover un rol de un usuario.
        
        Args:
            user_id (str): ID del usuario en Business Central.
            role_id (str): ID del rol.
            
        Returns:
            bool: True si se removió correctamente.
        """
        try:
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            base_url = bc_config["base_url"].rstrip('/')
            api_version = bc_config["api_version"]
            company_id = bc_config["company_id"]
            
            # Nota: Esta URL debe ajustarse según la estructura exacta de la API de Business Central
            url = f"{base_url}/{api_version}/companies({company_id})/users({user_id})/userPermissions(permissionSetId={role_id})"
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=self._get_headers()) as response:
                    if response.status in (200, 204):
                        self.logging_service.log_info(f"Rol removido de usuario en Business Central: Usuario {user_id}, Rol {role_id}")
                        return True
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al remover rol de usuario en Business Central: {response.status} - {error_data}")
                        return False
        except Exception as e:
            self.logging_service.log_error(f"Error al remover rol de usuario en Business Central: Usuario {user_id}, Rol {role_id}", e)
            return False
    
    async def validate_user_exists(self, user_id: str) -> bool:
        """
        Validar si un usuario existe en Business Central.
        
        Args:
            user_id (str): ID del usuario en Business Central.
            
        Returns:
            bool: True si el usuario existe.
        """
        try:
            user = await self.get_user(user_id)
            return user is not None
        except Exception as e:
            self.logging_service.log_error(f"Error al validar existencia de usuario en Business Central: {user_id}", e)
            return False
    
    async def validate_user_email(self, email: str) -> bool:
        """
        Validar si un correo electrónico ya está en uso.
        
        Args:
            email (str): Correo electrónico a validar.
            
        Returns:
            bool: True si el correo ya está en uso.
        """
        try:
            user = await self.get_user_by_email(email)
            return user is not None
        except Exception as e:
            self.logging_service.log_error(f"Error al validar email de usuario en Business Central: {email}", e)
            return False
    
    async def _get_user_roles(self, user_id: str) -> List[Role]:
        """
        Obtener roles asignados a un usuario.
        
        Args:
            user_id (str): ID del usuario en Business Central.
            
        Returns:
            List[Role]: Lista de roles asignados.
        """
        try:
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            base_url = bc_config["base_url"].rstrip('/')
            api_version = bc_config["api_version"]
            company_id = bc_config["company_id"]
            
            url = f"{base_url}/{api_version}/companies({company_id})/users({user_id})/userPermissions"  # Ajustar según la API
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        roles = []
                        
                        for bc_role in data.get('value', []):
                            role = Role(
                                id=bc_role.get('permissionSetId'),
                                name=bc_role.get('permissionSetName', ''),
                                is_selected=True
                            )
                            roles.append(role)
                        
                        return roles
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al obtener roles de usuario en Business Central: {response.status} - {error_data}")
                        return []
        except Exception as e:
            self.logging_service.log_error(f"Error al obtener roles de usuario en Business Central: {user_id}", e)
            return []
    
    async def _get_access_token(self) -> Optional[str]:
        """
        Obtener token de acceso para Business Central.
        
        Returns:
            Optional[str]: Token de acceso o None si hay error.
        """
        try:
            # Si ya tenemos un token, devolverlo
            if self._access_token:
                return self._access_token
            
            # Obtener configuración
            bc_config = self.config_manager.config["business_central"]
            tenant_id = bc_config["tenant_id"]
            client_id = bc_config["client_id"]
            client_secret = bc_config["client_secret"]
            
            # Scope para Business Central
            scope = f"{bc_config['base_url']}/.default"
            
            # Crear aplicación MSAL
            authority = f"https://login.microsoftonline.com/{tenant_id}"
            self._app = msal.ConfidentialClientApplication(
                client_id, 
                authority=authority,
                client_credential=client_secret
            )
            
            # Obtener token
            result = self._app.acquire_token_for_client(scopes=[scope])
            
            if "access_token" in result:
                self._access_token = result["access_token"]
                return self._access_token
            else:
                error_msg = f"Error al obtener token: {result.get('error')}: {result.get('error_description')}"
                self.logging_service.log_error(error_msg)
                return None
        except Exception as e:
            self.logging_service.log_error("Error al obtener token de acceso para Business Central", e)
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Obtener encabezados HTTP para las solicitudes a Business Central.
        
        Returns:
            Dict[str, str]: Encabezados HTTP.
        """
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }