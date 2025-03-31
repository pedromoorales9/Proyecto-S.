#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilidades para manejar código asíncrono en PyQt.
"""

import asyncio
import threading
import traceback
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class AsyncHelper(QObject):
    """Clase para ayudar a ejecutar código asíncrono en PyQt."""
    
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loop = None
        self.thread = None
    
    def run_async(self, coro):
        """
        Ejecutar una corutina de forma asíncrona.
        
        Args:
            coro: Corutina a ejecutar.
        """
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
            self.thread = threading.Thread(target=self._run_loop, args=(self.loop,))
            self.thread.daemon = True
            self.thread.start()
        
        asyncio.run_coroutine_threadsafe(self._run_coro(coro), self.loop)
    
    async def _run_coro(self, coro):
        try:
            result = await coro
            self.finished.emit(result)
        except Exception as e:
            traceback.print_exc()
            self.error.emit(e)
    
    def _run_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

# Instancia global del helper
async_helper = AsyncHelper()

def run_async(coro, callback=None, error_callback=None):
    """
    Ejecutar una corutina de forma asíncrona.
    
    Args:
        coro: Corutina a ejecutar.
        callback: Función a llamar cuando la corutina termine exitosamente.
        error_callback: Función a llamar cuando la corutina falle.
    """
    if callback:
        async_helper.finished.connect(callback)
    
    if error_callback:
        async_helper.error.connect(error_callback)
    
    async_helper.run_async(coro)
    
    # Desconectar callbacks después de usarlos
    def disconnect_callbacks():
        if callback and async_helper.finished.receivers(callback) > 0:
            async_helper.finished.disconnect(callback)
        
        if error_callback and async_helper.error.receivers(error_callback) > 0:
            async_helper.error.disconnect(error_callback)
    
    QTimer.singleShot(0, disconnect_callbacks)