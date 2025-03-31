#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio para gestionar los logs de la aplicación.
"""

import os
import csv
import logging
import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


class LogEntry:
    """
    Clase que representa una entrada de log.
    
    Attributes:
        timestamp (datetime): Fecha y hora del log.
        level (str): Nivel del log (INFO, WARNING, ERROR, DEBUG).
        message (str): Mensaje del log.
        exception (str): Excepción relacionada (si existe).
        source (str): Fuente del log.
    """
    
    def __init__(self, timestamp=None, level="INFO", message="", exception="", source=""):
        """
        Inicializar una nueva entrada de log.
        
        Args:
            timestamp (datetime, optional): Fecha y hora del log. Default es ahora.
            level (str, optional): Nivel del log. Default es "INFO".
            message (str, optional): Mensaje del log. Default es "".
            exception (str, optional): Excepción relacionada. Default es "".
            source (str, optional): Fuente del log. Default es "".
        """
        self.timestamp = timestamp or datetime.datetime.now()
        self.level = level
        self.message = message
        self.exception = exception
        self.source = source
    
    def __str__(self) -> str:
        """
        Obtener representación en cadena de la entrada de log.
        
        Returns:
            str: Representación formateada del log.
        """
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] [{self.level}] {self.message}"
    
    def to_dict(self) -> dict:
        """
        Convertir el objeto a un diccionario.
        
        Returns:
            dict: Representación de la entrada de log como diccionario.
        """
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'message': self.message,
            'exception': self.exception,
            'source': self.source
        }


class LoggingService:
    """Servicio para gestionar los logs de la aplicación."""
    
    def __init__(self, max_in_memory_logs: int = 200):
        """
        Inicializar el servicio de logging.
        
        Args:
            max_in_memory_logs (int, optional): Número máximo de logs en memoria. Default es 200.
        """
        self.logger = logging.getLogger('UserProvisioningTool')
        self.in_memory_logs: List[LogEntry] = []
        self.max_in_memory_logs = max_in_memory_logs
        
        # Crear directorio de logs si no existe
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.log_file_path = self.logs_dir / "app.log"
    
    def log_info(self, message: str) -> None:
        """
        Registrar un mensaje de información.
        
        Args:
            message (str): Mensaje a registrar.
        """
        self.logger.info(message)
        self._add_to_in_memory_logs("INFO", message)
    
    def log_warning(self, message: str) -> None:
        """
        Registrar un mensaje de advertencia.
        
        Args:
            message (str): Mensaje a registrar.
        """
        self.logger.warning(message)
        self._add_to_in_memory_logs("WARNING", message)
    
    def log_error(self, message: str, exception: Exception = None) -> None:
        """
        Registrar un mensaje de error.
        
        Args:
            message (str): Mensaje a registrar.
            exception (Exception, optional): Excepción relacionada. Default es None.
        """
        if exception:
            self.logger.error(message, exc_info=exception)
            self._add_to_in_memory_logs("ERROR", message, str(exception))
        else:
            self.logger.error(message)
            self._add_to_in_memory_logs("ERROR", message)
    
    def log_debug(self, message: str) -> None:
        """
        Registrar un mensaje de depuración.
        
        Args:
            message (str): Mensaje a registrar.
        """
        self.logger.debug(message)
        self._add_to_in_memory_logs("DEBUG", message)
    
    async def get_logs(self, start_date: Optional[datetime.datetime] = None, 
                     end_date: Optional[datetime.datetime] = None, 
                     log_level: Optional[str] = None, 
                     max_count: int = 100) -> List[LogEntry]:
        """
        Obtener logs filtrados.
        
        Args:
            start_date (datetime, optional): Fecha de inicio para filtrar. Default es None.
            end_date (datetime, optional): Fecha de fin para filtrar. Default es None.
            log_level (str, optional): Nivel de log para filtrar. Default es None.
            max_count (int, optional): Número máximo de logs a devolver. Default es 100.
            
        Returns:
            List[LogEntry]: Lista de entradas de log filtradas.
        """
        # Hacer una copia de los logs en memoria
        logs = self.in_memory_logs.copy()
        
        # Si no hay suficientes logs en memoria, intentar leerlos del archivo
        if len(logs) < max_count:
            await self._read_logs_from_file(logs)
        
        # Aplicar filtros
        if start_date:
            logs = [log for log in logs if log.timestamp >= start_date]
        
        if end_date:
            logs = [log for log in logs if log.timestamp <= end_date]
        
        if log_level:
            logs = [log for log in logs if log.level.upper() == log_level.upper()]
        
        # Ordenar por timestamp (más reciente primero)
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Limitar la cantidad
        if len(logs) > max_count:
            logs = logs[:max_count]
        
        return logs
    
    async def clear_logs(self) -> None:
        """Limpiar todos los logs en memoria y hacer backup del archivo."""
        # Limpiar logs en memoria
        self.in_memory_logs.clear()
        
        # Hacer backup del archivo de logs
        backup_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = f"{self.log_file_path}.bak.{backup_timestamp}"
        
        if os.path.exists(self.log_file_path):
            os.rename(self.log_file_path, backup_path)
            # Crear un nuevo archivo de log vacío
            with open(self.log_file_path, 'w', encoding='utf-8') as _:
                pass
    
    async def export_logs(self, file_path: str, 
                        start_date: Optional[datetime.datetime] = None, 
                        end_date: Optional[datetime.datetime] = None) -> str:
        """
        Exportar logs a un archivo CSV.
        
        Args:
            file_path (str): Ruta donde guardar el archivo.
            start_date (datetime, optional): Fecha de inicio para filtrar. Default es None.
            end_date (datetime, optional): Fecha de fin para filtrar. Default es None.
            
        Returns:
            str: Ruta del archivo exportado.
        """
        # Obtener los logs según los filtros
        logs = await self.get_logs(start_date, end_date, None, float('inf'))
        
        # Crear directorio de destino si no existe
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Escribir logs al archivo
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'level', 'message', 'exception', 'source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for log in logs:
                writer.writerow({
                    'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'level': log.level,
                    'message': log.message,
                    'exception': log.exception,
                    'source': log.source
                })
        
        return file_path
    
    def _add_to_in_memory_logs(self, level: str, message: str, exception: str = None) -> None:
        """
        Añadir un nuevo log a la lista en memoria.
        
        Args:
            level (str): Nivel del log.
            message (str): Mensaje del log.
            exception (str, optional): Excepción relacionada. Default es None.
        """
        log_entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=level,
            message=message,
            exception=exception,
            source="UserProvisioningTool"
        )
        
        self.in_memory_logs.append(log_entry)
        
        # Limitar la cantidad de logs en memoria
        if len(self.in_memory_logs) > self.max_in_memory_logs:
            # Remover los logs más antiguos
            excess = len(self.in_memory_logs) - self.max_in_memory_logs
            self.in_memory_logs = self.in_memory_logs[excess:]
    
    async def _read_logs_from_file(self, logs: List[LogEntry]) -> None:
        """
        Leer logs desde el archivo y añadirlos a la lista proporcionada.
        
        Args:
            logs (List[LogEntry]): Lista donde añadir los logs leídos.
        """
        if not os.path.exists(self.log_file_path):
            return
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    log_entry = self._parse_log_line(line)
                    if log_entry:
                        logs.append(log_entry)
        except Exception as e:
            print(f"Error reading log file: {str(e)}")
            # No registramos el error aquí para evitar recursión
    
    def _parse_log_line(self, line: str) -> Optional[LogEntry]:
        """
        Parsear una línea de log.
        
        Args:
            line (str): Línea de log a parsear.
            
        Returns:
            Optional[LogEntry]: Entrada de log parseada o None si hay error.
        """
        try:
            # Formato esperado: YYYY-MM-DD HH:MM:SS [Level] Message
            parts = line.split(' ', 2)
            if len(parts) < 3:
                return None
            
            date_time_str = parts[0] + ' ' + parts[1]
            rest = parts[2]
            
            level_start = rest.find('[')
            level_end = rest.find(']')
            
            if level_start == -1 or level_end == -1:
                return None
            
            level = rest[level_start+1:level_end]
            message = rest[level_end+1:].strip()
            
            try:
                timestamp = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                timestamp = datetime.datetime.now()
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=message,
                source="LogFile"
            )
        except Exception:
            # Ignorar líneas con formato incorrecto
            return None