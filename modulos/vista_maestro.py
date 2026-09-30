# vista_maestro.py - Ventana de la camara

import logging
import cv2
import numpy as np

logger = logging.getLogger("eyes")

NOMBRE_VENTANA = "EYES"
VERDE = (0, 255, 0)
NEGRO = (0, 0, 0)


def inicializar():
    cv2.namedWindow(NOMBRE_VENTANA, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(NOMBRE_VENTANA, 800, 600)
    logger.info("Ventana del maestro inicializada.")


def dibujar_deteccion(frame, bbox, nombre, confianza, color=VERDE):
    x1, y1, x2, y2 = [int(v) for v in bbox]
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    etiqueta = f"{nombre} {confianza:.0%}"
    (tw, th), _ = cv2.getTextSize(etiqueta, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
    cv2.putText(frame, etiqueta, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, NEGRO, 1)


def mostrar(frame, **kwargs):
    cv2.imshow(NOMBRE_VENTANA, frame)
    tecla = cv2.waitKey(1) & 0xFF
    return tecla


def destruir():
    try:
        cv2.destroyAllWindows()
        for _ in range(5):
            cv2.waitKey(1)
    except Exception:
        pass
    logger.info("Ventana del maestro cerrada.")
