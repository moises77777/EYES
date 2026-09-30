# camara.py - Captura de video con OpenCV

import logging
import threading

import cv2
import numpy as np
import config

logger = logging.getLogger("eyes")

_frame_actual = None
_frame_lock = threading.Lock()
_camara_activa = False
_cap = None


def iniciar():
    global _cap, _camara_activa
    try:
        _cap = cv2.VideoCapture(config.CAMARA_INDICE)
        if not _cap.isOpened():
            logger.error("No se pudo abrir la camara (indice %d).", config.CAMARA_INDICE)
            return False
        _cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMARA_ANCHO)
        _cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMARA_ALTO)
        _cap.set(cv2.CAP_PROP_FPS, config.CAMARA_FPS)
        _camara_activa = True
        ancho = int(_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info("Camara abierta: %dx%d", ancho, alto)
        return True
    except Exception as e:
        logger.error("Error al abrir la camara: %s", e)
        return False


def leer_frame():
    global _frame_actual, _camara_activa
    if _cap is None or not _cap.isOpened():
        return None
    ret, frame = _cap.read()
    if not ret or frame is None:
        return None
    with _frame_lock:
        _frame_actual = frame.copy()
    return frame


def obtener_frame():
    with _frame_lock:
        if _frame_actual is not None:
            return _frame_actual.copy()
    return None


def esta_activa():
    return _camara_activa and _cap is not None and _cap.isOpened()


def frame_estable(frame_anterior, frame_actual, umbral=15.0):
    if frame_anterior is None:
        return False
    try:
        gris_ant = cv2.cvtColor(frame_anterior, cv2.COLOR_BGR2GRAY)
        gris_act = cv2.cvtColor(frame_actual, cv2.COLOR_BGR2GRAY)
        diferencia = cv2.absdiff(gris_ant, gris_act)
        return diferencia.mean() < umbral
    except:
        return False


def calcular_posicion_objeto(frame, bbox):
    alto, ancho = frame.shape[:2]
    cx, cy = ancho // 2, alto // 2
    x1, y1, x2, y2 = bbox
    ox, oy = (x1 + x2) // 2, (y1 + y2) // 2
    tol_x = ancho * 0.20
    tol_y = alto * 0.20
    dx = ox - cx
    dy = oy - cy
    dist_rel = ((dx / (ancho / 2)) ** 2 + (dy / (alto / 2)) ** 2) ** 0.5
    centrado = abs(dx) < tol_x and abs(dy) < tol_y

    direcciones = []
    if dy < -tol_y: direcciones.append("arriba")
    elif dy > tol_y: direcciones.append("abajo")
    if dx < -tol_x: direcciones.append("a la izquierda")
    elif dx > tol_x: direcciones.append("a la derecha")

    direccion = "centrado" if centrado else (" y ".join(direcciones) if direcciones else "centrado")
    return {"direccion": direccion, "centrado": centrado,
            "distancia_relativa": min(dist_rel, 1.0), "dx": dx, "dy": dy}


def detener():
    global _cap, _camara_activa, _frame_actual
    _camara_activa = False
    if _cap is not None:
        try: _cap.release()
        except: pass
        _cap = None
    with _frame_lock:
        _frame_actual = None
    logger.info("Camara liberada.")
