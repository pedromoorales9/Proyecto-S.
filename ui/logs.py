#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vista de logs del sistema.
"""

import os
import asyncio
import datetime
from async_utils import run_async  # Añadir esta importación
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit,
    QFileDialog, QMessageBox, QHeaderView, QCheckBox, QFrame,
    QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSlot, QDate


class LogsView(QWidget):
    """Vista para visualizar y gestionar los logs del sistema."""
    
    def __init__(self, logging_service, main_window):
        """
        Inicializar la vista de logs.
        
        Args:
            logging_service: Servicio de logging.
            main_window: Ventana principal.
        """
        super().__init__()
        
        # Guardar referencias
        self.logging_service = logging_service
        self.main_window = main_window
        
        # Inicializar UI
        self.init_ui()
        
        # Cargar logs
        run_async(self.load_logs())  # MODIFICADO
    
    def init_ui(self):
        """Inicializar interfaz de usuario."""
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        
        # Título
        self.title_label = QLabel("Logs del Sistema")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 15px;")
        self.main_layout.addWidget(self.title_label)
        
        # Filtros
        self.filters_frame = QFrame()
        self.filters_layout = QGridLayout(self.filters_frame)
        
        # Nivel de log
        self.level_label = QLabel("Nivel:")
        self.level_combo = QComboBox()
        self.level_combo.addItem("Todos")
        self.level_combo.addItem("INFO")
        self.level_combo.addItem("WARNING")
        self.level_combo.addItem("ERROR")
        self.level_combo.addItem("DEBUG")
        
        # Fechas
        self.start_date_label = QLabel("Desde:")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        
        self.end_date_label = QLabel("Hasta:")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        
        # Botones de filtro
        self.apply_filter_button = QPushButton("Aplicar Filtros")
        self.apply_filter_button.setObjectName("PrimaryButton")
        self.apply_filter_button.clicked.connect(self.apply_filters)
        
        self.clear_filter_button = QPushButton("Limpiar Filtros")
        self.clear_filter_button.clicked.connect(self.clear_filters)
        
        # Añadir widgets al layout de filtros
        self.filters_layout.addWidget(self.level_label, 0, 0)
        self.filters_layout.addWidget(self.level_combo, 0, 1)
        self.filters_layout.addWidget(self.start_date_label, 0, 2)
        self.filters_layout.addWidget(self.start_date_edit, 0, 3)
        self.filters_layout.addWidget(self.end_date_label, 0, 4)
        self.filters_layout.addWidget(self.end_date_edit, 0, 5)
        self.filters_layout.addWidget(self.apply_filter_button, 1, 4)
        self.filters_layout.addWidget(self.clear_filter_button, 1, 5)
        
        self.main_layout.addWidget(self.filters_frame)
        
        # Tabla de logs
        self.logs_table = QTableWidget(0, 4)  # 0 filas, 4 columnas
        self.logs_table.setHorizontalHeaderLabels(["Fecha y Hora", "Nivel", "Mensaje", "Fuente"])
        self.logs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.logs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.logs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.logs_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.setAlternatingRowColors(True)
        
        self.main_layout.addWidget(self.logs_table)
        
        # Botones de acción
        self.buttons_layout = QHBoxLayout()
        
        # Botones izquierdos
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.clicked.connect(self.refresh_logs)
        
        self.clear_logs_button = QPushButton("Limpiar Logs")
        self.clear_logs_button.clicked.connect(self.clear_logs)
        
        self.buttons_layout.addWidget(self.refresh_button)
        self.buttons_layout.addWidget(self.clear_logs_button)
        
        self.buttons_layout.addStretch()
        
        # Botones derechos
        self.export_button = QPushButton("Exportar")
        self.export_button.setObjectName("PrimaryButton")
        self.export_button.clicked.connect(self.export_logs)
        
        self.buttons_layout.addWidget(self.export_button)
        
        self.main_layout.addLayout(self.buttons_layout)
    
    async def load_logs(self):
        """Cargar logs del sistema."""
        try:
            # Actualizar estado
            self.main_window.update_status("Cargando logs...")
            
            # Obtener valores de filtro
            start_date = None
            if self.start_date_edit.date() != QDate(1752, 9, 14):  # Fecha por defecto
                start_date = datetime.datetime.combine(
                    self.start_date_edit.date().toPyDate(), 
                    datetime.time.min
                )
            
            end_date = None
            if self.end_date_edit.date() != QDate(1752, 9, 14):  # Fecha por defecto
                end_date = datetime.datetime.combine(
                    self.end_date_edit.date().toPyDate(),
                    datetime.time.max
                )
            
            log_level = None
            if self.level_combo.currentIndex() > 0:  # Si no es "Todos"
                log_level = self.level_combo.currentText()
            
            # Cargar logs con filtros
            logs = await self.logging_service.get_logs(
                start_date=start_date, 
                end_date=end_date, 
                log_level=log_level, 
                max_count=500
            )
            
            # Actualizar tabla
            self.update_logs_table(logs)
            
            # Actualizar estado
            self.main_window.update_status(f"Se han cargado {len(logs)} logs")
            
        except Exception as e:
            self.logging_service.log_error(f"Error al cargar logs: {str(e)}", e)
            self.main_window.show_error(f"Error al cargar logs: {str(e)}")
            self.main_window.update_status("Error al cargar logs")
    
    def update_logs_table(self, logs):
        """
        Actualizar tabla de logs.
        
        Args:
            logs (List[LogEntry]): Lista de entradas de log.
        """
        # Limpiar tabla
        self.logs_table.setRowCount(0)
        
        # Añadir logs
        for i, log in enumerate(logs):
            self.logs_table.insertRow(i)
            
            # Fecha y hora
            date_item = QTableWidgetItem(log.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)  # No editable
            self.logs_table.setItem(i, 0, date_item)
            
            # Nivel
            level_item = QTableWidgetItem(log.level)
            level_item.setFlags(level_item.flags() & ~Qt.ItemIsEditable)  # No editable
            
            # Establecer color de fondo según nivel
            if log.level == "ERROR":
                level_item.setBackground(Qt.red)
                level_item.setForeground(Qt.white)
            elif log.level == "WARNING":
                level_item.setBackground(Qt.yellow)
            
            self.logs_table.setItem(i, 1, level_item)
            
            # Mensaje
            message_item = QTableWidgetItem(log.message)
            message_item.setFlags(message_item.flags() & ~Qt.ItemIsEditable)  # No editable
            self.logs_table.setItem(i, 2, message_item)
            
            # Fuente
            source_item = QTableWidgetItem(log.source)
            source_item.setFlags(source_item.flags() & ~Qt.ItemIsEditable)  # No editable
            self.logs_table.setItem(i, 3, source_item)
    
    @pyqtSlot()
    def apply_filters(self):
        """Aplicar filtros y recargar logs."""
        run_async(self.load_logs())  # MODIFICADO
    
    @pyqtSlot()
    def clear_filters(self):
        """Limpiar filtros y recargar logs."""
        # Restaurar valores predeterminados
        self.level_combo.setCurrentIndex(0)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.end_date_edit.setDate(QDate.currentDate())
        
        # Recargar logs
        run_async(self.load_logs())  # MODIFICADO
    
    @pyqtSlot()
    def refresh_logs(self):
        """Refrescar logs."""
        run_async(self.load_logs())  # MODIFICADO
    
    @pyqtSlot()
    def clear_logs(self):
        """Limpiar todos los logs."""
        # Pedir confirmación
        response = QMessageBox.warning(
            self,
            "Confirmar limpieza de logs",
            "¿Está seguro de que desea limpiar todos los logs? Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if response == QMessageBox.Yes:
            run_async(self.do_clear_logs())  # MODIFICADO
    
    @pyqtSlot()
    def export_logs(self):
        """Exportar logs a un archivo CSV."""
        try:
            # Mostrar diálogo para guardar archivo
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Logs",
                f"logs_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                "Archivos CSV (*.csv);;Todos los archivos (*.*)"
            )
            
            if file_path:
                # Obtener valores de filtro
                start_date = None
                if self.start_date_edit.date() != QDate(1752, 9, 14):  # Fecha por defecto
                    start_date = datetime.datetime.combine(
                        self.start_date_edit.date().toPyDate(), 
                        datetime.time.min
                    )
                
                end_date = None
                if self.end_date_edit.date() != QDate(1752, 9, 14):  # Fecha por defecto
                    end_date = datetime.datetime.combine(
                        self.end_date_edit.date().toPyDate(),
                        datetime.time.max
                    )
                
                # Exportar logs
                run_async(self.do_export_logs(file_path, start_date, end_date))  # MODIFICADO
                
        except Exception as e:
            self.logging_service.log_error(f"Error al exportar logs: {str(e)}", e)
            self.main_window.show_error(f"Error al exportar logs: {str(e)}")