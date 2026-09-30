# guia_sonido.py - Pitidos de guia (tipo sensor de reversa)

import logging
import math
import threading
import time

import numpy as np
import sounddevice as sd
import config
from modulos.voz_salida import hablando as voz_hablando

logger = logging.getLogger("eyes")

_detener = threading.Event()
_hilo = None
_activo = threading.Event()
_distancia = 1.0
_distancia_lock = threading.Lock()
_centrado = threading.Event()
_FS = 44100


def _generar_tono(frecuencia, duracion, volumen=0.5):
    t = np.linspace(0, duracion, int(_FS * duracion), endpoint=False)
    envolvente = np.ones_like(t)
    fade = int(0.005 * _FS)
    if fade > 0 and len(t) > fade * 2:
        envolvente[:fade] = np.linspace(0, 1, fade)
        envolvente[-fade:] = np.linspace(1, 0, fade)
    tono = volumen * np.sin(2 * math.pi * frecuencia * t) * envolvente
    return tono.astype(np.float32)


def _reproducir_tono(frecuencia, duracion, volumen=None):
    if voz_hablando.is_set():
        return
    if volumen is None:
        volumen = config.SONIDO_VOLUMEN
    try:
        tono = _generar_tono(frecuencia, duracion, volumen)
        sd.play(tono, _FS, blocking=True)
    except Exception as e:
        logger.debug("Error tono: %s", e)


def _hilo_guia():
    logger.info("Hilo de guia por sonido iniciado.")
    while not _detener.is_set():
        _activo.wait(timeout=0.5)
        if _detener.is_set():
            break
        if not _activo.is_set():
            continue
        if voz_hablando.is_set():
            time.sleep(0.2)
            continue
        if _centrado.is_set():
            _reproducir_tono(config.SONIDO_FRECUENCIA_LISTO, config.SONIDO_DURACION * 2)
            time.sleep(0.8)
            continue
        with _distancia_lock:
            dist = _distancia
        intervalo = 0.15 + dist * 0.65
        freq = config.SONIDO_FRECUENCIA_LEJOS + (
            (config.SONIDO_FRECUENCIA_CERCA - config.SONIDO_FRECUENCIA_LEJOS) * (1 - dist))
        _reproducir_tono(freq, config.SONIDO_DURACION)
        _detener.wait(intervalo)
    logger.info("Hilo de guia por sonido detenido.")


def iniciar():
    global _hilo
    if _hilo is not None and _hilo.is_alive():
        return
    _detener.clear()
    _activo.clear()
    _hilo = threading.Thread(target=_hilo_guia, daemon=True, name="guia_sonido")
    _hilo.start()


def detener():
    _detener.set()
    _activo.set()
    if _hilo is not None:
        _hilo.join(timeout=2)
    logger.info("Guia por sonido detenida.")


def activar():
    _activo.set()


def desactivar():
    _activo.clear()
    _centrado.clear()


def actualizar_distancia(distancia_relativa):
    with _distancia_lock:
        global _distancia
        _distancia = max(0.0, min(1.0, distancia_relativa))


def marcar_centrado(centrado):
    if centrado:
        _centrado.set()
    else:
        _centrado.clear()


def esta_activo():
    return _activo.is_set()
