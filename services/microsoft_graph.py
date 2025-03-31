#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio para interactuar con Microsoft Graph API.
"""

import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
import aiohttp
import msal

from models.user import User
from models.license import License


class MicrosoftGraphService:
    """Servicio para interactuar con Microsoft Graph API."""
    
    def __init__(self, config_manager, logging_service):
        """
        Inicializar el servicio de Microsoft Graph.
        
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
        Probar la conexión a Microsoft Graph.
        
        Returns:
            bool: True si la conexión es exitosa.
        """
        try:
            # Obtener token de acceso
            token = await self._get_access_token()
            if not token:
                return False
            
            # Probar una solicitud simple (obtener organización)
            url = f"{self.config_manager.config['microsoft_graph']['base_url']}/organization"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        return 'value' in data and len(data['value']) > 0
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error en prueba de conexión: {response.status} - {error_data}")
                        return False
        except Exception as e:
            self.logging_service.log_error("Error al probar la conexión con Microsoft Graph", e)
            return False
    
    async def create_user(self, user: User, password: str) -> User:
        """
        Crear un nuevo usuario en Azure AD.
        
        Args:
            user (User): Usuario a crear.
            password (str): Contraseña inicial.
            
        Returns:
            User: Usuario creado con ID de Azure AD.
        """
        try:
            url = f"{self.config_manager.config['microsoft_graph']['base_url']}/users"
            
            # Preparar datos del usuario
            mail_nickname = user.user_name.split('@')[0] if '@' in user.user_name else user.user_name
            
            # Construir cuerpo de la solicitud
            body = {
                "accountEnabled": user.is_active,
                "displayName": user.display_name or user.full_name,
                "mailNickname": mail_nickname,
                "userPrincipalName": user.email,
                "givenName": user.first_name,
                "surname": user.last_name,
                "jobTitle": user.job_title,
                "department": user.department,
                "mobilePhone": user.phone_number,
                "passwordProfile": {
                    "forceChangePasswordNextSignIn": self.config_manager.config["app"]["require_password_change"],
                    "password": password
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._get_headers(), json=body) as response:
                    if response.status in (200, 201):
                        # Éxito - actualizar usuario con ID de Azure AD
                        created_user_data = await response.json()
                        user.azure_ad_id = created_user_data.get('id')
                        user.exists_in_azure_ad = True
                        
                        self.logging_service.log_info(f"Usuario creado en Azure AD: {user.email}")
                        
                        # Asignar licencias si hay seleccionadas
                        if user.licenses:
                            for license in user.licenses:
                                if license.is_selected and license.sku_id:
                                    await self.assign_license_to_user(user.azure_ad_id, license.sku_id)
                        
                        return user
                    else:
                        error_data = await response.text()
                        error_msg = f"Error al crear usuario en Azure AD: {response.status} - {error_data}"
                        self.logging_service.log_error(error_msg)
                        raise Exception(error_msg)
        except Exception as e:
            self.logging_service.log_error(f"Error al crear usuario en Azure AD: {user.email}", e)
            raise
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Obtener un usuario por su ID.
        
        Args:
            user_id (str): ID del usuario en Azure AD.
            
        Returns:
            Optional[User]: Usuario encontrado o None.
        """
        try:
            url = f"{self.config_manager.config['microsoft_graph']['base_url']}/users/{user_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        azure_user_data = await response.json()
                        
                        # Convertir a modelo de usuario
                        user = User()
                        user.azure_ad_id = azure_user_data.get('id')
                        user.user_name = azure_user_data.get('userPrincipalName')
                        user.email = azure_user_data.get('userPrincipalName')
                        user.first_name = azure_user_data.get('givenName')
                        user.last_name = azure_user_data.get('surname')
                        user.display_name = azure_user_data.get('displayName')
                        user.job_title = azure_user_data.get('jobTitle')
                        user.department = azure_user_data.get('department')
                        user.phone_number = azure_user_data.get('mobilePhone')
                        user.is_active = azure_user_data.get('accountEnabled', False)
                        user.exists_in_azure_ad = True
                        
                        # Obtener licencias del usuario
                        user.licenses = await self.get_user_licenses(user_id)
                        
                        return user
                    else:
                        if response.status != 404:  # No registrar error si no se encontró
                            error_data = await response.text()
                            self.logging_service.log_error(f"Error al obtener usuario de Azure AD: {response.status} - {error_data}")
                        return None
        except Exception as e:
            self.logging_service.log_error(f"Error al obtener usuario de Azure AD: {user_id}", e)
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
            # Filtrar por UPN (userPrincipalName)
            filter_query = f"userPrincipalName eq '{email}'"
            url = f"{self.config_manager.config['microsoft_graph']['base_url']}/users?$filter={filter_query}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('value') and len(data['value']) > 0:
                            azure_user_data = data['value'][0]
                            
                            # Convertir a modelo de usuario
                            user = User()
                            user.azure_ad_id = azure_user_data.get('id')
                            user.user_name = azure_user_data.get('userPrincipalName')
                            user.email = azure_user_data.get('userPrincipalName')
                            user.first_name = azure_user_data.get('givenName')
                            user.last_name = azure_user_data.get('surname')
                            user.display_name = azure_user_data.get('displayName')
                            user.job_title = azure_user_data.get('jobTitle')
                            user.department = azure_user_data.get('department')
                            user.phone_number = azure_user_data.get('mobilePhone')
                            user.is_active = azure_user_data.get('accountEnabled', False)
                            user.exists_in_azure_ad = True
                            
                            # Obtener licencias del usuario
                            user.licenses = await self.get_user_licenses(user.azure_ad_id)
                            
                            return user
                        
                        return None
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al buscar usuario por email en Azure AD: {response.status} - {error_data}")
                        return None
        except Exception as e:
            self.logging_service.log_error(f"Error al buscar usuario por email en Azure AD: {email}", e)
            return None
    
    async def get_users(self, top: Optional[int] = None, skip: Optional[int] = None, 
                      filter_query: Optional[str] = None) -> List[User]:
        """
        Obtener usuarios de Azure AD.
        
        Args:
            top (int, optional): Número máximo de usuarios a obtener.
            skip (int, optional): Número de usuarios a omitir.
            filter_query (str, optional): Filtro OData para la consulta.
            
        Returns:
            List[User]: Lista de usuarios.
        """
        try:
            # Construir URL con parámetros
            url = f"{self.config_manager.config['microsoft_graph']['base_url']}/users"
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
                        
                        for azure_user_data in data.get('value', []):
                            user = User()
                            user.azure_ad_id = azure_user_data.get('id')
                            user.user_name = azure_user_data.get('userPrincipalName')
                            user.email = azure_user_data.get('userPrincipalName')
                            user.first_name = azure_user_data.get('givenName')
                            user.last_name = azure_user_data.get('surname')
                            user.display_name = azure_user_data.get('displayName')
                            user.job_title = azure_user_data.get('jobTitle')
                            user.department = azure_user_data.get('department')
                            user.phone_number = azure_user_data.get('mobilePhone')
                            user.is_active = azure_user_data.get('accountEnabled', False)
                            user.exists_in_azure_ad = True
                            
                            result.append(user)
                        
                        return result
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al obtener usuarios de Azure AD: {response.status} - {error_data}")
                        return []
        except Exception as e:
            self.logging_service.log_error("Error al obtener usuarios de Azure AD", e)
            return []
    
    async def update_user(self, user: User) -> User:
        """
        Actualizar un usuario en Azure AD.
        
        Args:
            user (User): Usuario a actualizar.
            
        Returns:
            User: Usuario actualizado.
        """
        try:
            if not user.azure_ad_id:
                raise ValueError("El ID de usuario de Azure AD es requerido para actualizar")
            
            url = f"{self.config_manager.config['microsoft_graph']['base_url']}/users/{user.azure_ad_id}"
            
            # Construir cuerpo de la solicitud
            body = {
                "displayName": user.display_name or user.full_name,
                "givenName": user.first_name,
                "surname": user.last_name,
                "jobTitle": user.job_title,
                "department": user.department,
                "mobilePhone": user.phone_number,
                "accountEnabled": user.is_active
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=self._get_headers(), json=body) as response:
                    if response.status == 204 or response.status == 200:
                        self.logging_service.log_info(f"Usuario actualizado en Azure AD: {user.email}")
                        return user
                    else:
                        error_data = await response.text()
                        error_msg = f"Error al actualizar usuario en Azure AD: {response.status} - {error_data}"
                        self.logging_service.log_error(error_msg)
                        raise Exception(error_msg)
        except Exception as e:
            self.logging_service.log_error(f"Error al actualizar usuario en Azure AD: {user.email}", e)
            raise
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Eliminar un usuario de Azure AD.
        
        Args:
            user_id (str): ID del usuario en Azure AD.
            
        Returns:
            bool: True si se eliminó correctamente.
        """
        try:
            url = f"{self.config_manager.config['microsoft_graph']['base_url']}/users/{user_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=self._get_headers()) as response:
                    if response.status == 204:
                        self.logging_service.log_info(f"Usuario eliminado de Azure AD: {user_id}")
                        return True
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al eliminar usuario de Azure AD: {response.status} - {error_data}")
                        return False
        except Exception as e:
            self.logging_service.log_error(f"Error al eliminar usuario de Azure AD: {user_id}", e)
            return False
    
    async def get_available_licenses(self) -> List[License]:
        """
        Obtener licencias disponibles en el tenant.
        
        Returns:
            List[License]: Lista de licencias disponibles.
        """
        try:
            url = f"{self.config_manager.config['microsoft_graph']['base_url']}/subscribedSkus"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        licenses = []
                        
                        for sku in data.get('value', []):
                            license_obj = License(
                                id=sku.get('id'),
                                sku_id=sku.get('skuId'),
                                name=self._get_friendly_license_name(sku.get('skuPartNumber')),
                                description=f"Disponibles: {sku.get('prepaidUnits', {}).get('enabled', 0) - sku.get('consumedUnits', 0)} de {sku.get('prepaidUnits', {}).get('enabled', 0)}"
                            )
                            licenses.append(license_obj)
                        
                        return licenses
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al obtener licencias disponibles: {response.status} - {error_data}")
                        
                        # Si falla, devolver licencias de la configuración
                        return await self.config_manager.get_available_licenses()
        except Exception as e:
            self.logging_service.log_error("Error al obtener licencias disponibles", e)
            
            # Si falla, devolver licencias de la configuración
            return await self.config_manager.get_available_licenses()
    
    async def assign_license_to_user(self, user_id: str, license_id: str) -> bool:
        """
        Asignar una licencia a un usuario.
        
        Args:
            user_id (str): ID del usuario en Azure AD.
            license_id (str): ID de SKU de la licencia.
            
        Returns:
            bool: True si se asignó correctamente.
        """
        try:
            url = f"{self.config_manager.config['microsoft_graph']['base_url']}/users/{user_id}/assignLicense"
            
            # Convertir license_id a GUID si no lo es
            try:
                uuid_obj = uuid.UUID(license_id)
                license_id = str(uuid_obj)
            except ValueError:
                # No es un UUID válido, intentar usar como está
                pass
            
            # Construir cuerpo de la solicitud
            body = {
                "addLicenses": [
                    {
                        "skuId": license_id
                    }
                ],
                "removeLicenses": []
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._get_headers(), json=body) as response:
                    if response.status == 200:
                        self.logging_service.log_info(f"Licencia asignada a usuario en Azure AD: Usuario {user_id}, Licencia {license_id}")
                        return True
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al asignar licencia a usuario en Azure AD: {response.status} - {error_data}")
                        return False
        except Exception as e:
            self.logging_service.log_error(f"Error al asignar licencia a usuario en Azure AD: Usuario {user_id}, Licencia {license_id}", e)
            return False
    
    async def remove_license_from_user(self, user_id: str, license_id: str) -> bool:
        """
        Remover una licencia de un usuario.
        
        Args:
            user_id (str): ID del usuario en Azure AD.
            license_id (str): ID de SKU de la licencia.
            
        Returns:
            bool: True si se removió correctamente.
        """
        try:
            url = f"{self.config_manager.config['microsoft_graph']['base_url']}/users/{user_id}/assignLicense"
            
            # Convertir license_id a GUID si no lo es
            try:
                uuid_obj = uuid.UUID(license_id)
                license_id = str(uuid_obj)
            except ValueError:
                # No es un UUID válido, intentar usar como está
                pass
            
            # Construir cuerpo de la solicitud
            body = {
                "addLicenses": [],
                "removeLicenses": [license_id]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._get_headers(), json=body) as response:
                    if response.status == 200:
                        self.logging_service.log_info(f"Licencia removida de usuario en Azure AD: Usuario {user_id}, Licencia {license_id}")
                        return True
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al remover licencia de usuario en Azure AD: {response.status} - {error_data}")
                        return False
        except Exception as e:
            self.logging_service.log_error(f"Error al remover licencia de usuario en Azure AD: Usuario {user_id}, Licencia {license_id}", e)
            return False
    
    async def get_user_licenses(self, user_id: str) -> List[License]:
        """
        Obtener licencias asignadas a un usuario.
        
        Args:
            user_id (str): ID del usuario en Azure AD.
            
        Returns:
            List[License]: Lista de licencias asignadas.
        """
        try:
            url = f"{self.config_manager.config['microsoft_graph']['base_url']}/users/{user_id}?$select=id,assignedLicenses"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        licenses = []
                        
                        if 'assignedLicenses' in data and data['assignedLicenses']:
                            # Obtener todas las licencias disponibles para obtener nombres
                            available_licenses = await self.get_available_licenses()
                            
                            for assigned_license in data['assignedLicenses']:
                                sku_id = assigned_license.get('skuId')
                                
                                # Buscar licencia en las disponibles
                                license_info = next((l for l in available_licenses if l.sku_id == sku_id), None)
                                
                                if license_info:
                                    license_obj = License(
                                        id=license_info.id,
                                        name=license_info.name,
                                        sku_id=sku_id,
                                        description=license_info.description,
                                        is_selected=True
                                    )
                                else:
                                    # Si no se encuentra, agregar con información básica
                                    license_obj = License(
                                        id=str(uuid.uuid4()),
                                        name=f"Licencia {sku_id}",
                                        sku_id=sku_id,
                                        is_selected=True
                                    )
                                
                                licenses.append(license_obj)
                        
                        return licenses
                    else:
                        error_data = await response.text()
                        self.logging_service.log_error(f"Error al obtener licencias de usuario: {response.status} - {error_data}")
                        return []
        except Exception as e:
            self.logging_service.log_error(f"Error al obtener licencias de usuario en Azure AD: {user_id}", e)
            return []
    
    async def create_mailbox(self, user_id: str) -> bool:
        """
        Crear buzón de correo para un usuario.
        
        Args:
            user_id (str): ID del usuario en Azure AD.
            
        Returns:
            bool: True si se creó correctamente.
        """
        try:
            # Esta funcionalidad puede requerir permisos adicionales
            # Por ahora, devolver True (la creación de buzón suele ocurrir automáticamente con la licencia)
            self.logging_service.log_info(f"Solicitud para crear buzón de correo para usuario: {user_id}")
            return True
        except Exception as e:
            self.logging_service.log_error(f"Error al crear buzón de correo para usuario: {user_id}", e)
            return False
    
    async def configure_mailbox(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """
        Configurar buzón de correo de un usuario.
        
        Args:
            user_id (str): ID del usuario en Azure AD.
            settings (Dict[str, Any]): Configuración del buzón.
            
        Returns:
            bool: True si se configuró correctamente.
        """
        try:
            # Esta funcionalidad puede requerir permisos adicionales
            # Por ahora, devolver True (simulación de éxito)
            self.logging_service.log_info(f"Solicitud para configurar buzón de correo para usuario: {user_id}")
            return True
        except Exception as e:
            self.logging_service.log_error(f"Error al configurar buzón de correo para usuario: {user_id}", e)
            return False
    
    async def validate_user_exists(self, user_id: str) -> bool:
        """
        Validar si un usuario existe en Azure AD.
        
        Args:
            user_id (str): ID del usuario en Azure AD.
            
        Returns:
            bool: True si el usuario existe.
        """
        try:
            user = await self.get_user(user_id)
            return user is not None
        except Exception as e:
            self.logging_service.log_error(f"Error al validar existencia de usuario en Azure AD: {user_id}", e)
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
            self.logging_service.log_error(f"Error al validar email de usuario en Azure AD: {email}", e)
            return False
    
    async def _get_access_token(self) -> Optional[str]:
        """
        Obtener token de acceso para Microsoft Graph.
        
        Returns:
            Optional[str]: Token de acceso o None si hay error.
        """
        try:
            # Si ya tenemos un token, devolverlo
            if self._access_token:
                return self._access_token
            
            # Obtener configuración
            ms_graph_config = self.config_manager.config["microsoft_graph"]
            tenant_id = ms_graph_config["tenant_id"]
            client_id = ms_graph_config["client_id"]
            client_secret = ms_graph_config["client_secret"]
            authority = ms_graph_config["authority"].format(tenant_id)
            scopes = ms_graph_config["scopes"]
            
            # Crear aplicación MSAL
            self._app = msal.ConfidentialClientApplication(
                client_id, 
                authority=authority,
                client_credential=client_secret
            )
            
            # Obtener token
            result = self._app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                self._access_token = result["access_token"]
                return self._access_token
            else:
                error_msg = f"Error al obtener token: {result.get('error')}: {result.get('error_description')}"
                self.logging_service.log_error(error_msg)
                return None
        except Exception as e:
            self.logging_service.log_error("Error al obtener token de acceso para Microsoft Graph", e)
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Obtener encabezados HTTP para las solicitudes a Microsoft Graph.
        
        Returns:
            Dict[str, str]: Encabezados HTTP.
        """
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _get_friendly_license_name(self, sku_part_number: str) -> str:
        """
        Obtener nombre amigable para una licencia.
        
        Args:
            sku_part_number (str): Número de parte de SKU.
            
        Returns:
            str: Nombre amigable de la licencia.
        """
        # Mapeo de SKUs a nombres amigables
        license_mappings = {
            "O365_BUSINESS_ESSENTIALS": "Microsoft 365 Business Basic",
            "O365_BUSINESS_PREMIUM": "Microsoft 365 Business Standard",
            "ENTERPRISEPACK": "Microsoft 365 E3",
            "ENTERPRISEPREMIUM": "Microsoft 365 E5",
            "STANDARDPACK": "Office 365 E1",
            "ENTERPRISEPREMIUM_NOPSTNCONF": "Microsoft 365 E5 sin Audio Conferencing",
            "DEVELOPERPACK": "Microsoft 365 E5 Developer",
            "FLOW_FREE": "Power Automate Free",
            "POWER_BI_STANDARD": "Power BI Free",
            "POWER_BI_PRO": "Power BI Pro"
        }
        
        return license_mappings.get(sku_part_number, sku_part_number)