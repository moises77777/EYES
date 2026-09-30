# registro.py - Configuracion de logging

import logging
import sys
from pathlib import Path
import config


def configurar_logging():
    Path(config.LOG_ARCHIVO).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("eyes")
    logger.setLevel(getattr(logging, config.LOG_NIVEL, logging.DEBUG))
    if logger.handlers:
        return logger

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")

    h_archivo = logging.FileHandler(config.LOG_ARCHIVO, encoding="utf-8")
    h_archivo.setLevel(logging.DEBUG)
    h_archivo.setFormatter(formato)
    logger.addHandler(h_archivo)

    h_consola = logging.StreamHandler(sys.stdout)
    h_consola.setLevel(logging.INFO)
    h_consola.setFormatter(formato)
    logger.addHandler(h_consola)

    logger.info("Sistema de registro iniciado.")
    return logger
