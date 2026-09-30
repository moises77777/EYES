# voz_entrada.py - Reconocimiento de voz con Vosk (hilo dedicado)

import json
import logging
import os
import queue
import threading

import config

logger = logging.getLogger("eyes")

_cola_audio = queue.Queue()
cola_comandos = queue.Queue()
_detener = threading.Event()
_pausado = threading.Event()
ultimo_comando = ""
_hilo = None
_callback_comando = None
_stream = None


def _callback_audio(indata, frames, time_info, status):
    _cola_audio.put(bytes(indata))


def _hilo_reconocimiento():
    global ultimo_comando
    logger.info("Hilo de reconocimiento de voz iniciado.")

    if not os.path.isdir(config.VOSK_MODELO_RUTA):
        logger.error("Modelo Vosk no encontrado en: %s", config.VOSK_MODELO_RUTA)
        return

    try:
        from vosk import Model, KaldiRecognizer, SetLogLevel
        SetLogLevel(-1)
        modelo = Model(config.VOSK_MODELO_RUTA)
        reconocedor = KaldiRecognizer(modelo, config.VOSK_FRECUENCIA_MUESTREO)
        reconocedor.SetWords(True)
        logger.info("Modelo Vosk cargado correctamente.")
    except Exception as e:
        logger.error("Error al cargar Vosk: %s", e)
        return

    while not _detener.is_set():
        try:
            datos = _cola_audio.get(timeout=0.5)
        except queue.Empty:
            continue
        if _pausado.is_set():
            continue
        try:
            if reconocedor.AcceptWaveform(datos):
                resultado = json.loads(reconocedor.Result())
                texto = resultado.get("text", "").strip()
                if texto:
                    logger.info("Reconocido: '%s'", texto)
                    ultimo_comando = texto
                    cola_comandos.put(texto)
                    if _callback_comando:
                        try: _callback_comando(texto)
                        except: pass
        except Exception as e:
            logger.error("Error en reconocimiento: %s", e)

    logger.info("Hilo de reconocimiento de voz detenido.")


def iniciar(callback=None):
    global _hilo, _callback_comando, _stream
    _callback_comando = callback
    if _hilo is not None and _hilo.is_alive():
        return
    _detener.clear()
    _pausado.clear()
    try:
        import sounddevice as sd
        _stream = sd.RawInputStream(
            samplerate=config.VOSK_FRECUENCIA_MUESTREO,
            blocksize=config.VOSK_BLOQUE_TAMANO,
            dtype="int16", channels=1, callback=_callback_audio)
        _stream.start()
        logger.info("Stream de audio iniciado (microfono activo).")
    except Exception as e:
        logger.error("Error al abrir el microfono: %s", e)
        return
    _hilo = threading.Thread(target=_hilo_reconocimiento, daemon=True, name="voz_entrada")
    _hilo.start()


def detener():
    global _stream
    _detener.set()
    if _stream is not None:
        try: _stream.stop(); _stream.close()
        except: pass
        _stream = None
    if _hilo is not None:
        _hilo.join(timeout=3)
    for cola in [_cola_audio, cola_comandos]:
        while not cola.empty():
            try: cola.get_nowait()
            except queue.Empty: break
    logger.info("Reconocimiento de voz detenido.")


def pausar():
    _pausado.set()


def reanudar():
    while not _cola_audio.empty():
        try: _cola_audio.get_nowait()
        except queue.Empty: break
    _pausado.clear()


def obtener_comando(timeout=None):
    try:
        return cola_comandos.get(timeout=timeout)
    except queue.Empty:
        return None


def hay_comando():
    return not cola_comandos.empty()


def limpiar_cola():
    while not cola_comandos.empty():
        try: cola_comandos.get_nowait()
        except queue.Empty: break
