"""
voz_salida.py - Síntesis de voz con pyttsx3.
El motor se crea y ejecuta en UN SOLO hilo dedicado con una cola de mensajes.
Nunca se llama al motor desde otro hilo (pyttsx3 no es thread-safe).
"""

import logging
import queue
import threading
import time

import config

logger = logging.getLogger("eyes")

# Cola de mensajes para el hilo de voz
_cola_voz: queue.Queue = queue.Queue()

# Evento para saber si el motor está hablando (para silenciar el micro)
hablando = threading.Event()

# Evento para detener el hilo
_detener = threading.Event()

# Hilo de voz
_hilo: threading.Thread | None = None

# Velocidad actual (puede cambiarla el usuario)
_velocidad_actual: int = config.VOZ_VELOCIDAD

# Última respuesta dicha (para el comando "repetir")
ultima_respuesta: str = ""

# Bandera para cancelar lo que se está diciendo
_cancelar = threading.Event()


def _buscar_voz_espanol(motor):
    """Busca una voz en español en las voces disponibles de Windows."""
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
    """
    Hilo dedicado para pyttsx3.
    El motor se crea aquí dentro y nunca sale de este hilo.
    Escucha la cola y habla los mensajes en orden.
    """
    global _velocidad_actual
    logger.info("Hilo de voz iniciado.")

    try:
        import pyttsx3
        motor = pyttsx3.init()
    except Exception as e:
        logger.error("Error al inicializar pyttsx3: %s", e)
        return

    # Configurar voz en español
    voz_es = _buscar_voz_espanol(motor)
    if voz_es:
        motor.setProperty("voice", voz_es.id)
        logger.info("Voz en español configurada: %s", voz_es.name)
    else:
        logger.warning("No se encontró voz en español. Usando voz predeterminada.")
        voces = motor.getProperty("voices")
        if voces:
            logger.info("Voces disponibles: %s", [v.name for v in voces])

    # Configurar velocidad y volumen
    motor.setProperty("rate", _velocidad_actual)
    motor.setProperty("volume", config.VOZ_VOLUMEN)

    while not _detener.is_set():
        try:
            # Esperar un mensaje con timeout para revisar si hay que detenerse
            mensaje = _cola_voz.get(timeout=0.5)
        except queue.Empty:
            continue

        if mensaje is None:
            # Señal de cierre
            break

        # Si es un comando de cambio de velocidad
        if isinstance(mensaje, dict):
            if "velocidad" in mensaje:
                _velocidad_actual = mensaje["velocidad"]
                motor.setProperty("rate", _velocidad_actual)
                logger.debug("Velocidad de voz cambiada a: %d", _velocidad_actual)
            continue

        # Hablar el mensaje
        _cancelar.clear()
        hablando.set()
        logger.debug("Hablando: %s", mensaje[:80])

        try:
            # Dividir en oraciones para poder cancelar entre ellas
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

    # Limpieza
    try:
        motor.stop()
    except Exception:
        pass
    logger.info("Hilo de voz detenido.")


def _dividir_oraciones(texto: str) -> list[str]:
    """Divide el texto en oraciones para poder cancelar entre ellas."""
    # Dividir por puntos, signos de exclamación e interrogación
    oraciones = []
    actual = ""
    for char in texto:
        actual += char
        if char in ".!?":
            oraciones.append(actual)
            actual = ""
    if actual.strip():
        oraciones.append(actual)
    # Si el texto no tiene puntuación, dividir por comas en textos largos
    if len(oraciones) <= 1 and len(texto) > 100:
        partes = texto.split(",")
        if len(partes) > 1:
            return [p.strip() for p in partes if p.strip()]
    return oraciones if oraciones else [texto]


def iniciar():
    """Inicia el hilo de voz. Llamar una vez al inicio de la aplicación."""
    global _hilo
    if _hilo is not None and _hilo.is_alive():
        logger.warning("El hilo de voz ya está corriendo.")
        return

    _detener.clear()
    _hilo = threading.Thread(target=_hilo_voz, daemon=True, name="voz_salida")
    _hilo.start()
    # Dar tiempo a que el motor se inicialice
    time.sleep(0.3)


def detener():
    """Detiene el hilo de voz. Llamar al cerrar la aplicación."""
    _detener.set()
    _cancelar.set()
    # Enviar None para desbloquear la cola
    try:
        _cola_voz.put_nowait(None)
    except queue.Full:
        pass
    if _hilo is not None:
        _hilo.join(timeout=3)
    # Vaciar la cola
    while not _cola_voz.empty():
        try:
            _cola_voz.get_nowait()
        except queue.Empty:
            break
    logger.info("Sistema de voz detenido.")


def decir(texto: str, guardar_como_respuesta: bool = True):
    """
    Encola un mensaje para que el hilo de voz lo diga.
    No bloquea: retorna inmediatamente.
    guardar_como_respuesta: si True, guarda como última respuesta para "repetir".
    """
    global ultima_respuesta
    if not texto or not texto.strip():
        return
    if guardar_como_respuesta:
        ultima_respuesta = texto
    _cola_voz.put(texto)


def decir_y_esperar(texto: str, guardar_como_respuesta: bool = True):
    """
    Encola un mensaje y espera a que termine de hablar.
    Útil para preguntas donde necesitas la respuesta del usuario después.
    """
    decir(texto, guardar_como_respuesta)
    # Esperar a que empiece a hablar
    time.sleep(0.2)
    # Esperar a que termine
    while hablando.is_set():
        time.sleep(0.1)
    # Pequeña pausa después de hablar
    time.sleep(0.2)


def cancelar():
    """Cancela lo que se está diciendo y vacía la cola."""
    _cancelar.set()
    # Vaciar la cola de mensajes pendientes
    while not _cola_voz.empty():
        try:
            _cola_voz.get_nowait()
        except queue.Empty:
            break


def repetir():
    """Repite la última respuesta."""
    if ultima_respuesta:
        decir(ultima_respuesta, guardar_como_respuesta=False)
    else:
        decir("No tengo nada que repetir.", guardar_como_respuesta=False)


def cambiar_velocidad(nueva_velocidad: int):
    """Cambia la velocidad de la voz (dentro de los límites configurados)."""
    global _velocidad_actual
    nueva = max(config.VOZ_VELOCIDAD_MIN, min(config.VOZ_VELOCIDAD_MAX, nueva_velocidad))
    _velocidad_actual = nueva
    _cola_voz.put({"velocidad": nueva})


def mas_rapido():
    """Aumenta la velocidad de la voz."""
    nueva = _velocidad_actual + config.VOZ_AJUSTE_PASO
    cambiar_velocidad(nueva)
    decir(f"Velocidad aumentada.", guardar_como_respuesta=False)


def mas_lento():
    """Reduce la velocidad de la voz."""
    nueva = _velocidad_actual - config.VOZ_AJUSTE_PASO
    cambiar_velocidad(nueva)
    decir(f"Velocidad reducida.", guardar_como_respuesta=False)


def obtener_velocidad() -> int:
    """Retorna la velocidad actual."""
    return _velocidad_actual


def esta_hablando() -> bool:
    """Retorna True si el motor está hablando."""
    return hablando.is_set()
