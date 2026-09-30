"""
vista_maestro.py - Ventana visual para la demostración.
Muestra el video en vivo con overlays informativos:
  - Recuadros sobre objetos/texto detectados
  - Marca en el centro de la imagen
  - Modo actual (ESPERANDO / LEER / IDENTIFICAR / BUSCAR)
  - Último comando y última respuesta
  - Estado de conexión
  - Registros pendientes de sincronizar
  - FPS

Esta ventana es solo para que el maestro vea la demo.
El usuario final no la necesita.
"""

import logging
import time

import cv2
import numpy as np

from modulos.conexion import hay_internet

logger = logging.getLogger("eyes")

# Colores (BGR)
VERDE = (0, 255, 0)
ROJO = (0, 0, 255)
AMARILLO = (0, 255, 255)
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
AZUL = (255, 180, 0)
GRIS = (180, 180, 180)
NARANJA = (0, 140, 255)

# Colores por modo
COLORES_MODO = {
    "ESPERANDO": GRIS,
    "LEER": AZUL,
    "IDENTIFICAR": VERDE,
    "BUSCAR": NARANJA,
}

# Nombre de la ventana
NOMBRE_VENTANA = "EYES - Vista del Maestro"

# FPS
_tiempo_anterior = time.time()
_fps = 0.0
_frame_count = 0


def inicializar():
    """Crea la ventana de OpenCV."""
    cv2.namedWindow(NOMBRE_VENTANA, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(NOMBRE_VENTANA, 800, 600)
    logger.info("Ventana del maestro inicializada.")


def _calcular_fps():
    """Calcula los FPS."""
    global _tiempo_anterior, _fps, _frame_count
    _frame_count += 1
    ahora = time.time()
    elapsed = ahora - _tiempo_anterior
    if elapsed >= 1.0:
        _fps = _frame_count / elapsed
        _frame_count = 0
        _tiempo_anterior = ahora
    return _fps


def _dibujar_centro(frame: np.ndarray):
    """Dibuja una marca en el centro de la imagen."""
    alto, ancho = frame.shape[:2]
    cx, cy = ancho // 2, alto // 2
    tam = 20

    # Cruz en el centro
    cv2.line(frame, (cx - tam, cy), (cx + tam, cy), VERDE, 2)
    cv2.line(frame, (cx, cy - tam), (cx, cy + tam), VERDE, 2)

    # Zona de tolerancia (rectángulo)
    tol_x = int(ancho * 0.20)
    tol_y = int(alto * 0.20)
    cv2.rectangle(
        frame,
        (cx - tol_x, cy - tol_y),
        (cx + tol_x, cy + tol_y),
        VERDE, 1,
    )


def _dibujar_barra_info(frame: np.ndarray, modo: str, ultimo_comando: str,
                         ultima_respuesta: str, en_linea: bool,
                         pendientes: int, fps: float):
    """Dibuja la barra de información superior e inferior."""
    alto, ancho = frame.shape[:2]
    color_modo = COLORES_MODO.get(modo, GRIS)

    # --- Barra superior ---
    cv2.rectangle(frame, (0, 0), (ancho, 45), NEGRO, -1)

    # Modo actual
    cv2.putText(frame, f"MODO: {modo}", (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_modo, 2)

    # Estado de conexión
    estado_txt = "EN LINEA" if en_linea else "SIN CONEXION"
    estado_color = VERDE if en_linea else ROJO
    cv2.putText(frame, estado_txt, (ancho - 200, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, estado_color, 1)

    # FPS
    cv2.putText(frame, f"FPS: {fps:.0f}", (ancho - 200, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLANCO, 1)

    # Pendientes de sincronizar
    if pendientes > 0:
        cv2.putText(frame, f"Pendientes: {pendientes}", (ancho - 400, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, AMARILLO, 1)

    # --- Barra inferior ---
    cv2.rectangle(frame, (0, alto - 55), (ancho, alto), NEGRO, -1)

    # Último comando
    cmd_txt = f"Comando: {ultimo_comando}" if ultimo_comando else "Comando: (esperando...)"
    # Truncar si es muy largo
    if len(cmd_txt) > 70:
        cmd_txt = cmd_txt[:70] + "..."
    cv2.putText(frame, cmd_txt, (10, alto - 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, AMARILLO, 1)

    # Última respuesta
    resp_txt = f"Respuesta: {ultima_respuesta}" if ultima_respuesta else "Respuesta: ---"
    if len(resp_txt) > 70:
        resp_txt = resp_txt[:70] + "..."
    cv2.putText(frame, resp_txt, (10, alto - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, BLANCO, 1)


def dibujar_deteccion(frame: np.ndarray, bbox: tuple, nombre: str,
                       confianza: float, color: tuple = VERDE):
    """
    Dibuja un recuadro de detección sobre un objeto.
    bbox: (x1, y1, x2, y2)
    """
    x1, y1, x2, y2 = [int(v) for v in bbox]
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    # Etiqueta con fondo
    etiqueta = f"{nombre} {confianza:.0%}"
    (tw, th), _ = cv2.getTextSize(etiqueta, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
    cv2.putText(frame, etiqueta, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, NEGRO, 1)


def dibujar_zona_texto(frame: np.ndarray, bbox: list, texto: str = ""):
    """
    Dibuja un recuadro sobre una zona de texto detectada.
    bbox: lista de 4 puntos [[x,y], [x,y], [x,y], [x,y]]
    """
    pts = np.array(bbox, dtype=np.int32)
    cv2.polylines(frame, [pts], True, AZUL, 2)
    if texto:
        x, y = pts[0]
        cv2.putText(frame, texto[:50], (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, AZUL, 1)


def mostrar(frame: np.ndarray, modo: str = "ESPERANDO",
            ultimo_comando: str = "", ultima_respuesta: str = "",
            pendientes: int = 0) -> int:
    """
    Muestra el frame con toda la información superpuesta.
    Retorna el código de tecla presionada (o -1 si no hay).
    """
    fps = _calcular_fps()

    # Verificar conexión (no hacerlo cada frame, cachear)
    en_linea = _check_internet_cache()

    # Dibujar overlays
    _dibujar_centro(frame)
    _dibujar_barra_info(
        frame, modo, ultimo_comando, ultima_respuesta,
        en_linea, pendientes, fps,
    )

    # Mostrar
    cv2.imshow(NOMBRE_VENTANA, frame)
    tecla = cv2.waitKey(1) & 0xFF
    return tecla


# Cache de internet (no verificar cada frame)
_internet_cache = True
_internet_cache_tiempo = 0


def _check_internet_cache() -> bool:
    """Verifica internet cada 10 segundos (no cada frame)."""
    global _internet_cache, _internet_cache_tiempo
    ahora = time.time()
    if ahora - _internet_cache_tiempo > 10:
        _internet_cache = hay_internet()
        _internet_cache_tiempo = ahora
    return _internet_cache


def destruir():
    """Cierra la ventana."""
    try:
        cv2.destroyAllWindows()
        # Necesario en Windows para que destroyAllWindows tenga efecto
        for _ in range(5):
            cv2.waitKey(1)
    except Exception:
        pass
    logger.info("Ventana del maestro cerrada.")
