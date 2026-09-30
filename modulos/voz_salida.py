# voz_salida.py - Sintesis de voz con pyttsx3 (hilo dedicado)

import logging
import queue
import threading
import time

import config

logger = logging.getLogger("eyes")

_cola_voz = queue.Queue()
hablando = threading.Event()
_detener = threading.Event()
_hilo = None
_velocidad_actual = config.VOZ_VELOCIDAD
ultima_respuesta = ""
_cancelar = threading.Event()


def _buscar_voz_espanol(motor):
    voces = motor.getProperty("voices")
    for voz in voces:
        nombre = voz.name.lower()
        voz_id = voz.id.lower()
        langs = getattr(voz, "languages", [])
        if ("spanish" in nombre or "español" in nombre or
            "es-" in voz_id or "es_" in voz_id or
            any("es" in str(lang).lower() for lang in langs)):
            return voz
    return None


def _hilo_voz():
    global _velocidad_actual
    logger.info("Hilo de voz iniciado.")
    try:
        import pyttsx3
        motor = pyttsx3.init()
    except Exception as e:
        logger.error("Error al inicializar pyttsx3: %s", e)
        return

    voz_es = _buscar_voz_espanol(motor)
    if voz_es:
        motor.setProperty("voice", voz_es.id)
        logger.info("Voz en espanol configurada: %s", voz_es.name)
    motor.setProperty("rate", _velocidad_actual)
    motor.setProperty("volume", config.VOZ_VOLUMEN)

    while not _detener.is_set():
        try:
            mensaje = _cola_voz.get(timeout=0.5)
        except queue.Empty:
            continue
        if mensaje is None:
            break
        if isinstance(mensaje, dict):
            if "velocidad" in mensaje:
                _velocidad_actual = mensaje["velocidad"]
                motor.setProperty("rate", _velocidad_actual)
            continue

        _cancelar.clear()
        hablando.set()
        try:
            oraciones = _dividir_oraciones(mensaje)
            for oracion in oraciones:
                if _cancelar.is_set() or _detener.is_set():
                    break
                oracion = oracion.strip()
                if oracion:
                    motor.say(oracion)
                    motor.runAndWait()
        except Exception as e:
            logger.error("Error al hablar: %s", e)
        finally:
            hablando.clear()

    try: motor.stop()
    except: pass
    logger.info("Hilo de voz detenido.")


def _dividir_oraciones(texto):
    oraciones = []
    actual = ""
    for char in texto:
        actual += char
        if char in ".!?":
            oraciones.append(actual)
            actual = ""
    if actual.strip():
        oraciones.append(actual)
    if len(oraciones) <= 1 and len(texto) > 100:
        partes = texto.split(",")
        if len(partes) > 1:
            return [p.strip() for p in partes if p.strip()]
    return oraciones if oraciones else [texto]


def iniciar():
    global _hilo
    if _hilo is not None and _hilo.is_alive():
        return
    _detener.clear()
    _hilo = threading.Thread(target=_hilo_voz, daemon=True, name="voz_salida")
    _hilo.start()
    time.sleep(0.3)


def detener():
    _detener.set()
    _cancelar.set()
    try: _cola_voz.put_nowait(None)
    except queue.Full: pass
    if _hilo is not None:
        _hilo.join(timeout=3)
    while not _cola_voz.empty():
        try: _cola_voz.get_nowait()
        except queue.Empty: break
    logger.info("Sistema de voz detenido.")


def decir(texto, guardar_como_respuesta=True):
    global ultima_respuesta
    if not texto or not texto.strip():
        return
    if guardar_como_respuesta:
        ultima_respuesta = texto
    _cola_voz.put(texto)


def decir_y_esperar(texto, guardar_como_respuesta=True):
    decir(texto, guardar_como_respuesta)
    time.sleep(0.2)
    while hablando.is_set():
        time.sleep(0.1)
    time.sleep(0.2)


def cancelar():
    _cancelar.set()
    while not _cola_voz.empty():
        try: _cola_voz.get_nowait()
        except queue.Empty: break


def repetir():
    if ultima_respuesta:
        decir(ultima_respuesta, guardar_como_respuesta=False)
    else:
        decir("No tengo nada que repetir.", guardar_como_respuesta=False)


def cambiar_velocidad(nueva_velocidad):
    global _velocidad_actual
    nueva = max(config.VOZ_VELOCIDAD_MIN, min(config.VOZ_VELOCIDAD_MAX, nueva_velocidad))
    _velocidad_actual = nueva
    _cola_voz.put({"velocidad": nueva})


def mas_rapido():
    cambiar_velocidad(_velocidad_actual + config.VOZ_AJUSTE_PASO)
    decir("Velocidad aumentada.", guardar_como_respuesta=False)


def mas_lento():
    cambiar_velocidad(_velocidad_actual - config.VOZ_AJUSTE_PASO)
    decir("Velocidad reducida.", guardar_como_respuesta=False)


def obtener_velocidad():
    return _velocidad_actual


def esta_hablando():
    return hablando.is_set()
