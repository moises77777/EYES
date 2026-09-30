"""
detector_objetos.py - Detección de objetos con YOLO (ultralytics).
Carga el modelo una sola vez y lo reutiliza.
Traduce las clases COCO al español usando el catálogo de la BD.
Maneja objetos personales y advertencias.
"""

import logging
import os
import time
import threading
from typing import Optional

import numpy as np

import config

logger = logging.getLogger("eyes")

# Modelo YOLO (se carga una sola vez)
_modelo = None
_modelo_lock = threading.Lock()

# Cache del catálogo (clase_modelo -> datos del catálogo)
_cache_catalogo: dict = {}

# Control de repeticiones: no decir el mismo objeto antes de N segundos
_ultimo_dicho: dict = {}  # clase -> timestamp


def inicializar() -> bool:
    """
    Carga el modelo YOLO. Retorna True si tuvo éxito.
    Llamar una vez al inicio.
    """
    global _modelo

    # Elegir modelo
    if config.YOLO_USAR_MODELO_PROPIO and os.path.isfile(config.YOLO_MODELO_PROPIO_RUTA):
        ruta = config.YOLO_MODELO_PROPIO_RUTA
        logger.info("Usando modelo YOLO propio: %s", ruta)
    elif os.path.isfile(config.YOLO_MODELO_RUTA):
        ruta = config.YOLO_MODELO_RUTA
        logger.info("Usando modelo YOLO preentrenado: %s", ruta)
    else:
        logger.error(
            "Modelo YOLO no encontrado. Se esperaba en: %s o %s",
            config.YOLO_MODELO_RUTA, config.YOLO_MODELO_PROPIO_RUTA,
        )
        return False

    try:
        from ultralytics import YOLO
        _modelo = YOLO(ruta)
        _modelo.to(config.YOLO_DISPOSITIVO)
        n_clases = len(_modelo.names)
        logger.info("YOLO cargado: %d clases, dispositivo: %s", n_clases, config.YOLO_DISPOSITIVO)
        # Cargar catálogo en cache
        _cargar_cache_catalogo()
        return True
    except Exception as e:
        logger.error("Error al cargar YOLO: %s", e)
        return False


def _cargar_cache_catalogo():
    """Carga el catálogo de la BD para traducir clases COCO al español."""
    global _cache_catalogo
    try:
        from database import obtener_catalogo
        catalogo = obtener_catalogo()
        _cache_catalogo = {}
        for obj in catalogo:
            _cache_catalogo[obj["clase_modelo"]] = obj
        logger.info("Cache de catálogo cargado: %d objetos.", len(_cache_catalogo))
    except Exception as e:
        logger.error("Error al cargar cache de catálogo: %s", e)


def detectar(frame: np.ndarray) -> list[dict]:
    """
    Detecta objetos en un frame.
    Retorna lista de detecciones, cada una con:
      - clase: nombre de la clase en inglés (COCO)
      - nombre_es: nombre en español (del catálogo o traducción directa)
      - confianza: float 0-1
      - bbox: (x1, y1, x2, y2)
      - categoria: categoría del catálogo
      - advertencia: texto de advertencia (o None)
      - nombre_personal: nombre personal del usuario (o None)
    """
    if _modelo is None:
        return []

    try:
        # Reducir resolución para que YOLO sea más rápido en CPU
        import cv2
        alto_orig, ancho_orig = frame.shape[:2]
        frame_peq = cv2.resize(frame, (320, 240))
        escala_x = ancho_orig / 320
        escala_y = alto_orig / 240

        resultados = _modelo(frame_peq, verbose=False, conf=config.YOLO_CONFIANZA_MINIMA)
    except Exception as e:
        logger.error("Error en detección YOLO: %s", e)
        return []

    detecciones = []
    for r in resultados:
        if r.boxes is None:
            continue
        for box in r.boxes:
            clase_id = int(box.cls[0])
            confianza = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            # Escalar coordenadas de vuelta al tamaño original
            x1 = x1 * escala_x
            y1 = y1 * escala_y
            x2 = x2 * escala_x
            y2 = y2 * escala_y

            # Nombre de la clase en inglés
            clase_nombre = _modelo.names.get(clase_id, f"clase_{clase_id}")

            # Buscar en catálogo
            info_catalogo = _cache_catalogo.get(clase_nombre)

            if info_catalogo:
                nombre_es = info_catalogo["nombre_es"]
                categoria = info_catalogo["categoria"]
                advertencia = info_catalogo.get("advertencia")
            else:
                # Clase no está en el catálogo: usar el nombre en inglés
                nombre_es = clase_nombre
                categoria = "otro"
                advertencia = None

            detecciones.append({
                "clase": clase_nombre,
                "nombre_es": nombre_es,
                "confianza": confianza,
                "bbox": (int(x1), int(y1), int(x2), int(y2)),
                "categoria": categoria,
                "advertencia": advertencia,
                "nombre_personal": None,  # Se llena después
            })

    return detecciones


def buscar_objeto_personal_en_detecciones(
    detecciones: list[dict], id_usuario: int
) -> list[dict]:
    """
    Revisa si alguna detección coincide con un objeto personal del usuario.
    Modifica las detecciones in-place agregando nombre_personal.
    """
    try:
        from database import obtener_objetos_personales
        personales = obtener_objetos_personales(id_usuario)
    except Exception:
        return detecciones

    if not personales:
        return detecciones

    # Crear diccionario clase -> nombre_personal
    mapa_personales = {}
    for p in personales:
        if p.get("clase_modelo"):
            mapa_personales[p["clase_modelo"]] = p["nombre_personal"]

    for det in detecciones:
        if det["clase"] in mapa_personales:
            det["nombre_personal"] = mapa_personales[det["clase"]]

    return detecciones


def obtener_mejor_deteccion(detecciones: list[dict]) -> Optional[dict]:
    """
    De una lista de detecciones, retorna la de mayor confianza
    que esté más cerca del centro (para cuando hay varios objetos).
    """
    if not detecciones:
        return None
    # Ordenar por confianza descendente
    return max(detecciones, key=lambda d: d["confianza"])


def ya_fue_dicho(clase: str) -> bool:
    """
    Verifica si un objeto ya fue dicho recientemente.
    Evita repetir el mismo objeto en bucle.
    """
    ahora = time.time()
    ultimo = _ultimo_dicho.get(clase, 0)
    return (ahora - ultimo) < config.ESTABILIDAD_REPETIR_SEGUNDOS


def marcar_como_dicho(clase: str):
    """Marca un objeto como recientemente dicho."""
    _ultimo_dicho[clase] = time.time()


def limpiar_dichos():
    """Limpia el registro de objetos dichos (al cambiar de modo)."""
    _ultimo_dicho.clear()


def obtener_nombres_modelo() -> dict:
    """Retorna el diccionario id -> nombre de las clases del modelo."""
    if _modelo is None:
        return {}
    return dict(_modelo.names)
