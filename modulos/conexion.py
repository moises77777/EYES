# conexion.py - Verificar conexion a internet

import logging
import socket

logger = logging.getLogger("eyes")


def hay_internet(host="8.8.8.8", puerto=53, timeout=3.0):
    try:
        socket.setdefaulttimeout(timeout)
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((host, puerto))
        conn.close()
        return True
    except (socket.timeout, OSError):
        return False
