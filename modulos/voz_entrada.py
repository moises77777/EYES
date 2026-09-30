"""
voz_entrada.py - Reconocimiento de voz con Vosk + sounddevice.
Corre en su propio hilo. Mientras la app habla, ignora el micrófono
para que no se escuche a sí misma.
"""

import json
import logging
import os
import queue
import threading
import time
from typing import Callable, Optional

import config

logger = logging.getLogger("eyes")

# Cola de audio crudo del micrófono
_cola_audio: queue.Queue = queue.Queue()

# Cola de texto reconocido (otros módulos leen de aquí)
cola_comandos: queue.Queue = queue.Queue()

# Eventos de control
_detener = threading.Event()
_pausado = threading.Event()  # Cuando está en set, el reconocimiento se pausa

# Último texto reconocido (para la vista del maestro)
ultimo_comando: str = ""

# Hilo de reconocimiento
_hilo: threading.Thread | None = None

# Callback opcional (para procesamiento inmediato)
_callback_comando: Optional[Callable[[str], None]] = None


def _callback_audio(indata, frames, time_info, status):
    """
    Callback de sounddevice: recibe audio del micrófono y lo encola.
    Se ejecuta en un hilo de audio del sistema, debe ser muy rápido.
    """
    if status:
        logger.debug("Estado del audio: %s", status)
    # Copiar los datos para evitar problemas de buffer
    _cola_audio.put(bytes(indata))


def _hilo_reconocimiento():
    """
    Hilo dedicado para Vosk.
    Lee audio de la cola, lo procesa y produce texto reconocido.
    """
    global ultimo_comando
    logger.info("Hilo de reconocimiento de voz iniciado.")

    # Verificar que el modelo existe
    if not os.path.isdir(config.VOSK_MODELO_RUTA):
        logger.error(
            "Modelo Vosk no encontrado en: %s. "
            "Descárgalo de https://alphacephei.com/vosk/models",
            config.VOSK_MODELO_RUTA,
        )
        return

    try:
        from vosk import Model, KaldiRecognizer

        # Suprimir los mensajes de log de Vosk en consola
        from vosk import SetLogLevel
        SetLogLevel(-1)

        modelo = Model(config.VOSK_MODELO_RUTA)
        reconocedor = KaldiRecognizer(modelo, config.VOSK_FRECUENCIA_MUESTREO)
        reconocedor.SetWords(True)
        logger.info("Modelo Vosk cargado correctamente.")
    except Exception as e:
        logger.error("Error al cargar modelo Vosk: %s", e)
        return

    while not _detener.is_set():
        try:
            # Obtener audio de la cola
            datos = _cola_audio.get(timeout=0.5)
        except queue.Empty:
            continue

        # Si está pausado (la app está hablando), descartar el audio
        if _pausado.is_set():
            continue

        # Procesar el audio
        try:
            if reconocedor.AcceptWaveform(datos):
                resultado = json.loads(reconocedor.Result())
                texto = resultado.get("text", "").strip()
                if texto:
                    logger.info("Reconocido: '%s'", texto)
                    ultimo_comando = texto
                    cola_comandos.put(texto)
                    if _callback_comando:
                        try:
                            _callback_comando(texto)
                        except Exception as e:
                            logger.error("Error en callback de comando: %s", e)
            else:
                # Resultado parcial (se podría usar para feedback visual)
                parcial = json.loads(reconocedor.PartialResult())
                texto_parcial = parcial.get("partial", "")
                if texto_parcial:
                    logger.debug("Parcial: '%s'", texto_parcial)
        except Exception as e:
            logger.error("Error en reconocimiento: %s", e)

    logger.info("Hilo de reconocimiento de voz detenido.")


def iniciar(callback: Optional[Callable[[str], None]] = None):
    """
    Inicia el reconocimiento de voz.
    callback: función opcional que se llama inmediatamente con cada comando.
    """
    global _hilo, _callback_comando, _stream
    _callback_comando = callback

    if _hilo is not None and _hilo.is_alive():
        logger.warning("El reconocimiento de voz ya está corriendo.")
        return

    _detener.clear()
    _pausado.clear()

    # Iniciar el stream de audio
    try:
        import sounddevice as sd
        _stream = sd.RawInputStream(
            samplerate=config.VOSK_FRECUENCIA_MUESTREO,
            blocksize=config.VOSK_BLOQUE_TAMANO,
            dtype="int16",
            channels=1,
            callback=_callback_audio,
        )
        _stream.start()
        logger.info("Stream de audio iniciado (micrófono activo).")
    except Exception as e:
        logger.error("Error al abrir el micrófono: %s", e)
        return

    # Iniciar hilo de reconocimiento
    _hilo = threading.Thread(
        target=_hilo_reconocimiento, daemon=True, name="voz_entrada"
    )
    _hilo.start()


# Variable del stream a nivel de módulo
_stream = None


def detener():
    """Detiene el reconocimiento de voz y libera el micrófono."""
    global _stream
    _detener.set()

    # Detener stream de audio
    if _stream is not None:
        try:
            _stream.stop()
            _stream.close()
        except Exception:
            pass
        _stream = None

    # Esperar al hilo
    if _hilo is not None:
        _hilo.join(timeout=3)

    # Vaciar colas
    for cola in [_cola_audio, cola_comandos]:
        while not cola.empty():
            try:
                cola.get_nowait()
            except queue.Empty:
                break

    logger.info("Reconocimiento de voz detenido.")


def pausar():
    """Pausa el reconocimiento (mientras la app habla, para no escucharse)."""
    _pausado.set()


def reanudar():
    """Reanuda el reconocimiento después de hablar."""
    # Vaciar la cola de audio acumulado mientras estaba pausado
    while not _cola_audio.empty():
        try:
            _cola_audio.get_nowait()
        except queue.Empty:
            break
    _pausado.clear()


def obtener_comando(timeout: float = None) -> Optional[str]:
    """
    Obtiene el siguiente comando reconocido.
    Bloquea hasta que haya un comando o se cumpla el timeout.
    Retorna None si no hay comando en el tiempo dado.
    """
    try:
        return cola_comandos.get(timeout=timeout)
    except queue.Empty:
        return None


def hay_comando() -> bool:
    """Retorna True si hay un comando pendiente en la cola."""
    return not cola_comandos.empty()


def limpiar_cola():
    """Vacía la cola de comandos pendientes."""
    while not cola_comandos.empty():
        try:
            cola_comandos.get_nowait()
        except queue.Empty:
            break
