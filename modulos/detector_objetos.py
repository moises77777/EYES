# detector_objetos.py - Deteccion de objetos con YOLO

import logging
import os
import time
import threading

import numpy as np
import config

logger = logging.getLogger("eyes")

_modelo = None
_modelo_lock = threading.Lock()
_cache_catalogo = {}
_ultimo_dicho = {}


def inicializar():
    global _modelo
    if config.YOLO_USAR_MODELO_PROPIO and os.path.isfile(config.YOLO_MODELO_PROPIO_RUTA):
        ruta = config.YOLO_MODELO_PROPIO_RUTA
        logger.info("Usando modelo YOLO propio: %s", ruta)
    elif os.path.isfile(config.YOLO_MODELO_RUTA):
        ruta = config.YOLO_MODELO_RUTA
        logger.info("Usando modelo YOLO preentrenado: %s", ruta)
    else:
        logger.error("Modelo YOLO no encontrado.")
        return False
    try:
        from ultralytics import YOLO
        _modelo = YOLO(ruta)
        _modelo.to(config.YOLO_DISPOSITIVO)
        logger.info("YOLO cargado: %d clases", len(_modelo.names))
        _cargar_cache_catalogo()
        return True
    except Exception as e:
        logger.error("Error al cargar YOLO: %s", e)
        return False


def _cargar_cache_catalogo():
    global _cache_catalogo
    try:
        from database import obtener_catalogo
        catalogo = obtener_catalogo()
        _cache_catalogo = {obj["clase_modelo"]: obj for obj in catalogo}
        logger.info("Cache catalogo: %d objetos.", len(_cache_catalogo))
    except Exception as e:
        logger.error("Error cache catalogo: %s", e)


def detectar(frame):
    if _modelo is None:
        return []
    try:
        import cv2
        alto_orig, ancho_orig = frame.shape[:2]
        frame_peq = cv2.resize(frame, (320, 240))
        escala_x = ancho_orig / 320
        escala_y = alto_orig / 240
        resultados = _modelo(frame_peq, verbose=False, conf=config.YOLO_CONFIANZA_MINIMA)
    except Exception as e:
        logger.error("Error YOLO: %s", e)
        return []

    detecciones = []
    for r in resultados:
        if r.boxes is None:
            continue
        for box in r.boxes:
            clase_id = int(box.cls[0])
            confianza = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            x1, y1 = x1 * escala_x, y1 * escala_y
            x2, y2 = x2 * escala_x, y2 * escala_y
            clase_nombre = _modelo.names.get(clase_id, f"clase_{clase_id}")
            info = _cache_catalogo.get(clase_nombre)
            if info:
                nombre_es = info["nombre_es"]
                categoria = info["categoria"]
                advertencia = info.get("advertencia")
            else:
                nombre_es = clase_nombre
                categoria = "otro"
                advertencia = None
            detecciones.append({
                "clase": clase_nombre, "nombre_es": nombre_es,
                "confianza": confianza, "bbox": (int(x1), int(y1), int(x2), int(y2)),
                "categoria": categoria, "advertencia": advertencia,
                "nombre_personal": None,
            })
    return detecciones


def buscar_objeto_personal_en_detecciones(detecciones, id_usuario):
    try:
        from database import obtener_objetos_personales
        personales = obtener_objetos_personales(id_usuario)
    except:
        return detecciones
    if not personales:
        return detecciones
    mapa = {p["clase_modelo"]: p["nombre_personal"] for p in personales if p.get("clase_modelo")}
    for det in detecciones:
        if det["clase"] in mapa:
            det["nombre_personal"] = mapa[det["clase"]]
    return detecciones


def obtener_mejor_deteccion(detecciones):
    if not detecciones:
        return None
    return max(detecciones, key=lambda d: d["confianza"])


def ya_fue_dicho(clase):
    return (time.time() - _ultimo_dicho.get(clase, 0)) < config.ESTABILIDAD_REPETIR_SEGUNDOS


def marcar_como_dicho(clase):
    _ultimo_dicho[clase] = time.time()


def limpiar_dichos():
    _ultimo_dicho.clear()


def obtener_nombres_modelo():
    if _modelo is None:
        return {}
    return dict(_modelo.names)
