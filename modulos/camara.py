"""
camara.py - Captura de video en tiempo real con OpenCV.
El bucle de la cámara corre en el hilo principal (requisito de OpenCV en Windows).
Proporciona frames a otros módulos sin bloquear.
"""

import logging
import threading
import time
from typing import Optional

import cv2
import numpy as np

import config

logger = logging.getLogger("eyes")

# Frame actual compartido entre hilos (protegido por lock)
_frame_actual: Optional[np.ndarray] = None
_frame_lock = threading.Lock()

# Contadores para la vista del maestro
_fps_actual: float = 0.0
_camara_activa = False

# Objeto VideoCapture
_cap: Optional[cv2.VideoCapture] = None


def iniciar() -> bool:
    """
    Abre la cámara. Retorna True si tuvo éxito.
    NOTA: No crea un hilo; la lectura de frames se hace desde el bucle principal.
    """
    global _cap, _camara_activa

    try:
        _cap = cv2.VideoCapture(config.CAMARA_INDICE)
        if not _cap.isOpened():
            logger.error(
                "No se pudo abrir la cámara (índice %d). "
                "Verifica que esté conectada y no la use otra app.",
                config.CAMARA_INDICE,
            )
            return False

        # Configurar resolución
        _cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMARA_ANCHO)
        _cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMARA_ALTO)
        _cap.set(cv2.CAP_PROP_FPS, config.CAMARA_FPS)

        _camara_activa = True
        ancho = int(_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info("Cámara abierta: %dx%d", ancho, alto)
        return True

    except Exception as e:
        logger.error("Error al abrir la cámara: %s", e)
        return False


def leer_frame() -> Optional[np.ndarray]:
    """
    Lee un frame de la cámara y lo almacena como frame actual.
    Retorna el frame o None si falló.
    Llamar desde el bucle principal (hilo principal).
    """
    global _frame_actual, _camara_activa

    if _cap is None or not _cap.isOpened():
        return None

    ret, frame = _cap.read()
    if not ret or frame is None:
        return None

    with _frame_lock:
        _frame_actual = frame.copy()

    return frame


def obtener_frame() -> Optional[np.ndarray]:
    """
    Obtiene una copia del frame actual (thread-safe).
    Otros módulos pueden llamar esto desde cualquier hilo.
    """
    with _frame_lock:
        if _frame_actual is not None:
            return _frame_actual.copy()
    return None


def esta_activa() -> bool:
    """Retorna True si la cámara está abierta y funcionando."""
    return _camara_activa and _cap is not None and _cap.isOpened()


def calcular_nitidez(frame: np.ndarray) -> float:
    """
    Calcula la nitidez del frame usando la varianza del Laplaciano.
    Mayor valor = más nítido.
    """
    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gris, cv2.CV_64F).var()


def frame_estable(frame_anterior: Optional[np.ndarray], frame_actual: np.ndarray,
                  umbral: float = 15.0) -> bool:
    """
    Compara dos frames para detectar si la imagen está quieta.
    Retorna True si la diferencia promedio es menor al umbral.
    """
    if frame_anterior is None:
        return False

    try:
        gris_ant = cv2.cvtColor(frame_anterior, cv2.COLOR_BGR2GRAY)
        gris_act = cv2.cvtColor(frame_actual, cv2.COLOR_BGR2GRAY)
        diferencia = cv2.absdiff(gris_ant, gris_act)
        promedio = diferencia.mean()
        return promedio < umbral
    except Exception:
        return False


def calcular_posicion_objeto(frame: np.ndarray, bbox: tuple) -> dict:
    """
    Calcula la posición de un objeto respecto al centro del frame.
    bbox: (x1, y1, x2, y2)
    Retorna: {"direccion": str, "centrado": bool, "distancia_relativa": float}
    """
    alto, ancho = frame.shape[:2]
    centro_frame_x = ancho // 2
    centro_frame_y = alto // 2

    x1, y1, x2, y2 = bbox
    centro_obj_x = (x1 + x2) // 2
    centro_obj_y = (y1 + y2) // 2

    # Tolerancia: 20% del tamaño del frame
    tol_x = ancho * 0.20
    tol_y = alto * 0.20

    dx = centro_obj_x - centro_frame_x
    dy = centro_obj_y - centro_frame_y

    # Distancia relativa al centro (0 = centrado, 1 = en el borde)
    dist_rel = ((dx / (ancho / 2)) ** 2 + (dy / (alto / 2)) ** 2) ** 0.5

    centrado = abs(dx) < tol_x and abs(dy) < tol_y

    # Determinar dirección para guía
    direcciones = []
    if dy < -tol_y:
        direcciones.append("arriba")
    elif dy > tol_y:
        direcciones.append("abajo")
    if dx < -tol_x:
        direcciones.append("a la izquierda")
    elif dx > tol_x:
        direcciones.append("a la derecha")

    if centrado:
        direccion = "centrado"
    elif direcciones:
        direccion = " y ".join(direcciones)
    else:
        direccion = "centrado"

    return {
        "direccion": direccion,
        "centrado": centrado,
        "distancia_relativa": min(dist_rel, 1.0),
        "dx": dx,
        "dy": dy,
    }


def detener():
    """Libera la cámara."""
    global _cap, _camara_activa, _frame_actual

    _camara_activa = False
    if _cap is not None:
        try:
            _cap.release()
        except Exception:
            pass
        _cap = None

    with _frame_lock:
        _frame_actual = None

    logger.info("Cámara liberada.")
