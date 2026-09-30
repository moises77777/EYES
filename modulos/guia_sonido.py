"""
guia_sonido.py - Guía por sonido tipo sensor de reversa.
Pitidos más rápidos cuando el objeto está más cerca del centro.
Tono especial cuando está centrado ("listo").
Corre en su propio hilo; nunca se encima con la voz.
"""

import logging
import math
import threading
import time

import numpy as np
import sounddevice as sd

import config
from modulos.voz_salida import hablando as voz_hablando

logger = logging.getLogger("eyes")

# Estado del sonido
_detener = threading.Event()
_hilo: threading.Thread | None = None
_activo = threading.Event()  # Si está en set, los pitidos suenan

# Distancia relativa actual (0 = centrado, 1 = lejos)
_distancia: float = 1.0
_distancia_lock = threading.Lock()

# Estado de centrado
_centrado = threading.Event()

# Frecuencia de muestreo para generar tonos
_FS = 44100


def _generar_tono(frecuencia: float, duracion: float, volumen: float = 0.5) -> np.ndarray:
    """Genera un tono sinusoidal como array de numpy."""
    t = np.linspace(0, duracion, int(_FS * duracion), endpoint=False)
    # Envolvente suave para evitar clics
    envolvente = np.ones_like(t)
    fade = int(0.005 * _FS)  # 5ms de fade
    if fade > 0 and len(t) > fade * 2:
        envolvente[:fade] = np.linspace(0, 1, fade)
        envolvente[-fade:] = np.linspace(1, 0, fade)
    tono = volumen * np.sin(2 * math.pi * frecuencia * t) * envolvente
    return tono.astype(np.float32)


def _reproducir_tono(frecuencia: float, duracion: float, volumen: float = None):
    """Reproduce un tono corto. No bloquea si la voz está hablando."""
    if voz_hablando.is_set():
        return  # No encimarse con la voz

    if volumen is None:
        volumen = config.SONIDO_VOLUMEN

    try:
        tono = _generar_tono(frecuencia, duracion, volumen)
        sd.play(tono, _FS, blocking=True)
    except Exception as e:
        logger.debug("Error al reproducir tono: %s", e)


def _hilo_guia():
    """Hilo que produce pitidos según la distancia al centro."""
    logger.info("Hilo de guía por sonido iniciado.")

    while not _detener.is_set():
        # Esperar a que se active la guía
        _activo.wait(timeout=0.5)
        if _detener.is_set():
            break
        if not _activo.is_set():
            continue

        # No hacer sonido si la voz está hablando
        if voz_hablando.is_set():
            time.sleep(0.2)
            continue

        # Verificar si está centrado
        if _centrado.is_set():
            # Tono de "listo"
            _reproducir_tono(
                config.SONIDO_FRECUENCIA_LISTO,
                config.SONIDO_DURACION * 2,
            )
            time.sleep(0.8)
            continue

        # Obtener distancia actual
        with _distancia_lock:
            dist = _distancia

        # Calcular intervalo: más rápido cuanto más cerca
        # dist 0.0 (muy cerca) -> intervalo 0.15s
        # dist 1.0 (lejos)     -> intervalo 0.8s
        intervalo = 0.15 + dist * 0.65

        # Calcular frecuencia: más aguda cuanto más cerca
        freq = config.SONIDO_FRECUENCIA_LEJOS + (
            (config.SONIDO_FRECUENCIA_CERCA - config.SONIDO_FRECUENCIA_LEJOS)
            * (1 - dist)
        )

        _reproducir_tono(freq, config.SONIDO_DURACION)
        _detener.wait(intervalo)  # Espera interrumpible

    logger.info("Hilo de guía por sonido detenido.")


def iniciar():
    """Inicia el hilo de guía por sonido (no activa los pitidos todavía)."""
    global _hilo
    if _hilo is not None and _hilo.is_alive():
        return

    _detener.clear()
    _activo.clear()
    _hilo = threading.Thread(target=_hilo_guia, daemon=True, name="guia_sonido")
    _hilo.start()


def detener():
    """Detiene el hilo de guía por sonido."""
    _detener.set()
    _activo.set()  # Desbloquear el wait
    if _hilo is not None:
        _hilo.join(timeout=2)
    logger.info("Guía por sonido detenida.")


def activar():
    """Activa los pitidos de guía."""
    _activo.set()


def desactivar():
    """Desactiva los pitidos de guía."""
    _activo.clear()
    _centrado.clear()


def actualizar_distancia(distancia_relativa: float):
    """
    Actualiza la distancia relativa al centro.
    0.0 = objeto centrado, 1.0 = objeto lejos del centro.
    """
    with _distancia_lock:
        global _distancia
        _distancia = max(0.0, min(1.0, distancia_relativa))


def marcar_centrado(centrado: bool):
    """Marca si el objeto está centrado (cambia al tono de 'listo')."""
    if centrado:
        _centrado.set()
    else:
        _centrado.clear()


def esta_activo() -> bool:
    """Retorna True si la guía por sonido está activa."""
    return _activo.is_set()
