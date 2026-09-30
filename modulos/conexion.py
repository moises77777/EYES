"""
conexion.py - Verificación de conexión a internet.
"""

import logging
import socket

logger = logging.getLogger("eyes")


def hay_internet(host: str = "8.8.8.8", puerto: int = 53, timeout: float = 3.0) -> bool:
    """
    Verifica si hay conexión a internet intentando conectar a DNS de Google.
    Retorna True si hay conexión, False si no.
    """
    try:
        socket.setdefaulttimeout(timeout)
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((host, puerto))
        conn.close()
        return True
    except (socket.timeout, OSError):
        return False
