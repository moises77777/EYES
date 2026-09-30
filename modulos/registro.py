"""
registro.py - Configuración de logging centralizado para EYES.
Registra eventos en archivo y en consola.
"""

import logging
import sys
from pathlib import Path

import config


def configurar_logging() -> logging.Logger:
    """Configura y devuelve el logger principal de EYES."""
    # Asegurar que el directorio de logs existe
    Path(config.LOG_ARCHIVO).parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("eyes")
    logger.setLevel(getattr(logging, config.LOG_NIVEL, logging.DEBUG))

    # Evitar duplicar handlers si se llama varias veces
    if logger.handlers:
        return logger

    # Formato del log
    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para archivo
    handler_archivo = logging.FileHandler(
        config.LOG_ARCHIVO, encoding="utf-8"
    )
    handler_archivo.setLevel(logging.DEBUG)
    handler_archivo.setFormatter(formato)
    logger.addHandler(handler_archivo)

    # Handler para consola (solo INFO y superior para no saturar)
    handler_consola = logging.StreamHandler(sys.stdout)
    handler_consola.setLevel(logging.INFO)
    handler_consola.setFormatter(formato)
    logger.addHandler(handler_consola)

    logger.info("Sistema de registro iniciado.")
    return logger
