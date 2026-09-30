"""
main.py - Punto de entrada principal de EYES.
Flujo:
  1. Inicializar base de datos, catálogo y sincronización.
  2. Iniciar voz de salida, voz de entrada, cámara y guía por sonido.
  3. Si es primer uso: registro por voz.
  4. Si ya existe usuario: saludar.
  5. Bucle principal: cámara + comandos de voz + vista del maestro.
"""

import sys
import time
import threading

import cv2
import config

# Configurar logging primero
from modulos.registro import configurar_logging
logger = configurar_logging()


# =============================================================
# ESTADO GLOBAL DE LA APLICACIÓN
# =============================================================
class EstadoApp:
    """Estado compartido de la aplicación."""
    def __init__(self):
        self.usuario = None             # Datos del usuario activo
        self.modo_actual = "ESPERANDO"  # ESPERANDO, LEER, IDENTIFICAR, BUSCAR
        self.ultimo_texto_leido = ""    # Último texto leído por OCR
        self.ultimo_objeto = ""         # Último objeto identificado (nombre español)
        self.ultima_clase = ""          # Última clase de modelo detectada (inglés)
        self.ultima_categoria = ""      # Última categoría del objeto
        self.ejecutando = True          # False para salir del bucle principal
        self.ultimo_comando = ""        # Último comando de voz escuchado
        self.ultima_respuesta = ""      # Última respuesta dada
        self.objeto_buscado = ""        # Objeto que se está buscando
        self.frames_estables = 0        # Contador de frames estables con la misma detección
        self.deteccion_estable = None   # Última detección estable (para confirmar)


estado = EstadoApp()


# =============================================================
# PRIMER USO - REGISTRO POR VOZ
# =============================================================
def primer_uso():
    """
    Registro por voz del primer uso.
    Pregunta nombre, velocidad de voz, y da un tutorial corto.
    Todo por voz, sin teclado.
    """
    from modulos import voz_salida, voz_entrada
    from modulos.comandos import interpretar
    from database import crear_usuario, actualizar_velocidad_voz, guardar_configuracion

    logger.info("Iniciando primer uso (registro por voz).")

    # --- Presentación ---
    voz_entrada.pausar()
    voz_salida.decir_y_esperar(
        "Hola, soy EYES, tu asistente para leer, identificar y buscar "
        "cosas en tu casa. Voy a configurarme para ti."
    )

    # --- Preguntar nombre ---
    nombre = None
    while nombre is None:
        voz_salida.decir_y_esperar("¿Cómo te llamas?")
        voz_entrada.reanudar()
        voz_entrada.limpiar_cola()

        texto = voz_entrada.obtener_comando(timeout=10)
        voz_entrada.pausar()

        if texto:
            nombre_limpio = _limpiar_nombre(texto)
            if nombre_limpio:
                voz_salida.decir_y_esperar(
                    f"¿Te llamas {nombre_limpio}? Di sí o no."
                )
                voz_entrada.reanudar()
                voz_entrada.limpiar_cola()

                respuesta = voz_entrada.obtener_comando(timeout=8)
                voz_entrada.pausar()

                if respuesta:
                    cmd = interpretar(respuesta)
                    if cmd["comando"] == "si":
                        nombre = nombre_limpio
                    else:
                        voz_salida.decir_y_esperar("De acuerdo, intentemos de nuevo.")
                else:
                    voz_salida.decir_y_esperar("No escuché tu respuesta. Intentemos de nuevo.")
            else:
                voz_salida.decir_y_esperar("No entendí tu nombre. Por favor repítelo.")
        else:
            voz_salida.decir_y_esperar(
                "No escuché nada. Asegúrate de hablar cerca del micrófono."
            )

    # --- Crear usuario ---
    id_usuario = crear_usuario(nombre, voz_salida.obtener_velocidad())
    if id_usuario is None:
        logger.error("No se pudo crear el usuario.")
        voz_salida.decir_y_esperar("Hubo un error al guardar tu nombre, pero continuaré.")
        estado.usuario = {"id": 1, "nombre": nombre, "velocidad_voz": 175}
    else:
        from database import obtener_usuario
        estado.usuario = obtener_usuario()

    logger.info("Usuario registrado: %s (ID: %s)", nombre, estado.usuario.get("id"))

    # --- Ajustar velocidad de voz ---
    voz_salida.decir_y_esperar(
        f"Bien, {nombre}. Ahora voy a ajustar la velocidad de mi voz. "
        "Te voy a hablar y tú me dices: más rápido, más lento, o así está bien."
    )

    ajustando = True
    while ajustando:
        voz_salida.decir_y_esperar(
            "Esta es la velocidad actual de mi voz. "
            "¿Quieres que hable más rápido, más lento, o así está bien?"
        )
        voz_entrada.reanudar()
        voz_entrada.limpiar_cola()

        respuesta = voz_entrada.obtener_comando(timeout=8)
        voz_entrada.pausar()

        if respuesta:
            cmd = interpretar(respuesta)
            if cmd["comando"] == "mas_rapido":
                voz_salida.mas_rapido()
                time.sleep(0.5)
            elif cmd["comando"] == "mas_lento":
                voz_salida.mas_lento()
                time.sleep(0.5)
            elif cmd["comando"] in ("si", None):
                ajustando = False
            else:
                ajustando = False
        else:
            ajustando = False

    # Guardar velocidad elegida
    velocidad = voz_salida.obtener_velocidad()
    if estado.usuario and estado.usuario.get("id"):
        actualizar_velocidad_voz(estado.usuario["id"], velocidad)
        guardar_configuracion(estado.usuario["id"], "velocidad_voz", str(velocidad))

    # --- Tutorial corto ---
    voz_salida.decir_y_esperar(
        f"Perfecto, {nombre}. Te explico rápidamente cómo funciono."
    )
    time.sleep(0.3)
    voz_salida.decir_y_esperar(
        "Di leer para que lea un texto frente a la cámara."
    )
    time.sleep(0.2)
    voz_salida.decir_y_esperar(
        "Di qué es esto para identificar un objeto."
    )
    time.sleep(0.2)
    voz_salida.decir_y_esperar(
        "Di busca y el nombre del objeto para buscarlo con la cámara."
    )
    time.sleep(0.2)
    voz_salida.decir_y_esperar(
        "Di ayuda en cualquier momento para recordar los comandos."
    )
    time.sleep(0.2)
    voz_salida.decir_y_esperar(
        "Di salir para cerrar la aplicación."
    )
    time.sleep(0.3)
    voz_salida.decir_y_esperar(
        f"Listo, {nombre}. Dime qué quieres hacer."
    )

    logger.info("Primer uso completado para: %s", nombre)


def _limpiar_nombre(texto: str) -> str:
    """Limpia el texto para extraer solo el nombre."""
    import unicodedata
    texto = texto.strip()
    texto_norm = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )
    prefijos = [
        "me llamo ", "mi nombre es ", "soy ", "yo soy ", "yo me llamo ",
        "me dicen ", "dime ", "llamame ", "puedes decirme ",
        "mi nombre ", "nombre ",
    ]
    for prefijo in prefijos:
        prefijo_norm = "".join(
            c for c in unicodedata.normalize("NFD", prefijo)
            if unicodedata.category(c) != "Mn"
        )
        if texto_norm.startswith(prefijo_norm):
            texto = texto[len(prefijo):].strip()
            break
    if texto:
        texto = texto.title()
    return texto


# =============================================================
# RESPONDER A UN COMANDO DE VOZ
# =============================================================
def _responder(texto: str):
    """Guarda el texto como última respuesta y lo actualiza en el estado."""
    estado.ultima_respuesta = texto


def procesar_comando(texto: str):
    """
    Procesa un comando de voz reconocido.
    Los modos de cámara se implementarán en fases posteriores.
    """
    from modulos import voz_salida, voz_entrada
    from modulos.comandos import interpretar, TEXTO_AYUDA
    from database import (
        obtener_historial_reciente, obtener_objetos_personales,
    )

    estado.ultimo_comando = texto
    resultado = interpretar(texto)
    cmd = resultado["comando"]
    arg = resultado["argumento"]

    logger.info("Comando: %s (texto: '%s', arg: %s)", cmd, texto, arg)

    voz_entrada.pausar()

    if cmd == "leer":
        estado.modo_actual = "LEER"
        msg = "Modo lectura activado. Apunta la cámara al texto."
        _responder(msg)
        voz_salida.decir_y_esperar(msg)
        # El modo queda activo; el bucle principal procesará frames
        # Se sale con "detener" o al detectar texto

    elif cmd == "identificar":
        from modulos import detector_objetos
        estado.modo_actual = "IDENTIFICAR"
        detector_objetos.limpiar_dichos()
        msg = "Modo identificar activado. Muestra el objeto a la cámara."
        _responder(msg)
        voz_salida.decir_y_esperar(msg)
        # El modo queda activo; el bucle principal hará la detección YOLO

    elif cmd == "buscar":
        estado.modo_actual = "BUSCAR"
        if not arg:
            voz_salida.decir_y_esperar("¿Qué quieres que busque?")
            voz_entrada.reanudar()
            voz_entrada.limpiar_cola()
            resp = voz_entrada.obtener_comando(timeout=8)
            voz_entrada.pausar()
            if resp:
                arg = resp
        if arg:
            estado.objeto_buscado = arg
            msg = f"Buscando {arg}. Mueve la cámara despacio."
            _responder(msg)
            voz_salida.decir_y_esperar(msg)
        else:
            estado.modo_actual = "ESPERANDO"

    elif cmd == "repetir":
        voz_salida.repetir()

    elif cmd == "resumir":
        if estado.ultimo_texto_leido:
            msg = "La función de resumen estará disponible pronto."
        else:
            msg = "No he leído nada todavía. Primero di leer."
        _responder(msg)
        voz_salida.decir_y_esperar(msg)

    elif cmd == "pregunta":
        if arg:
            msg = "La función de preguntas estará disponible pronto."
        else:
            msg = "¿Qué quieres preguntar?"
        _responder(msg)
        voz_salida.decir_y_esperar(msg)

    elif cmd == "historial":
        if estado.usuario:
            historial = obtener_historial_reciente(estado.usuario["id"], 5)
            if historial:
                msg = f"Últimas {len(historial)} cosas:"
                _responder(msg)
                voz_salida.decir_y_esperar(msg)
                for i, h in enumerate(historial, 1):
                    modo = h.get("modo", "")
                    resultado_h = h.get("resultado", "sin resultado")
                    if len(resultado_h) > 80:
                        resultado_h = resultado_h[:80]
                    voz_salida.decir_y_esperar(f"{i}. {modo}: {resultado_h}")
            else:
                msg = "No hay historial todavía."
                _responder(msg)
                voz_salida.decir_y_esperar(msg)
        else:
            msg = "No hay historial disponible."
            _responder(msg)
            voz_salida.decir_y_esperar(msg)

    elif cmd == "guardar":
        # Guardar el último objeto identificado como objeto personal
        if estado.ultima_clase and estado.ultimo_objeto:
            from database import guardar_objeto_personal
            voz_salida.decir_y_esperar(
                f"Voy a guardar {estado.ultimo_objeto}. "
                "¿Cómo quieres que lo llame? Por ejemplo, mi medicina de la presión."
            )
            voz_entrada.reanudar()
            voz_entrada.limpiar_cola()
            nombre_personal = voz_entrada.obtener_comando(timeout=10)
            voz_entrada.pausar()

            if nombre_personal:
                from modulos.comandos import interpretar as _interp
                r = _interp(nombre_personal)
                if r["comando"] == "detener" or r["comando"] == "cancelar":
                    msg = "Guardar cancelado."
                else:
                    id_obj = guardar_objeto_personal(
                        estado.usuario["id"],
                        nombre_personal,
                        estado.ultima_clase,
                        estado.ultima_categoria or "otro",
                    )
                    if id_obj:
                        msg = f"Guardado como {nombre_personal}."
                    else:
                        msg = "Hubo un error al guardar."
            else:
                msg = "No escuché el nombre. No se guardó."
            _responder(msg)
            voz_salida.decir_y_esperar(msg)
        else:
            msg = "Primero identifica un objeto con la cámara."
            _responder(msg)
            voz_salida.decir_y_esperar(msg)

    elif cmd == "que_hay_guardado":
        if estado.usuario:
            personales = obtener_objetos_personales(estado.usuario["id"])
            if personales:
                msg = f"Tienes {len(personales)} objetos guardados."
                _responder(msg)
                voz_salida.decir_y_esperar(msg)
                for obj in personales:
                    voz_salida.decir_y_esperar(obj["nombre_personal"])
            else:
                msg = "No tienes objetos guardados todavía."
                _responder(msg)
                voz_salida.decir_y_esperar(msg)
        else:
            msg = "No hay objetos guardados."
            _responder(msg)
            voz_salida.decir_y_esperar(msg)

    elif cmd == "mas_rapido":
        voz_salida.mas_rapido()
        _responder("Velocidad aumentada.")
        if estado.usuario:
            from database import actualizar_velocidad_voz
            actualizar_velocidad_voz(estado.usuario["id"], voz_salida.obtener_velocidad())

    elif cmd == "mas_lento":
        voz_salida.mas_lento()
        _responder("Velocidad reducida.")
        if estado.usuario:
            from database import actualizar_velocidad_voz
            actualizar_velocidad_voz(estado.usuario["id"], voz_salida.obtener_velocidad())

    elif cmd == "ayuda":
        _responder("Ayuda")
        voz_salida.decir_y_esperar(TEXTO_AYUDA)

    elif cmd == "detener":
        if estado.modo_actual != "ESPERANDO":
            from modulos import guia_sonido, detector_objetos
            guia_sonido.desactivar()
            detector_objetos.limpiar_dichos()
            msg = "Modo cancelado."
            estado.modo_actual = "ESPERANDO"
        else:
            msg = "No hay ningún modo activo. Di ayuda para los comandos."
        _responder(msg)
        voz_salida.decir_y_esperar(msg)

    elif cmd == "salir":
        nombre = estado.usuario["nombre"] if estado.usuario else ""
        msg = f"Hasta luego{', ' + nombre if nombre else ''}. Cerrando EYES."
        _responder(msg)
        voz_salida.decir_y_esperar(msg)
        estado.ejecutando = False

    elif cmd in ("si", "no"):
        msg = "No hay ninguna pregunta pendiente. Di ayuda para los comandos."
        _responder(msg)
        voz_salida.decir_y_esperar(msg)

    else:
        msg = "No te entendí. Di ayuda para escuchar los comandos."
        _responder(msg)
        voz_salida.decir_y_esperar(msg)

    voz_entrada.reanudar()
    voz_entrada.limpiar_cola()


# =============================================================
# BUCLE PRINCIPAL CON CÁMARA
# =============================================================

# YOLO corre en un hilo separado para no bloquear la cámara/voz
_detecciones_lock = threading.Lock()
_detecciones_compartidas: list = []
_frame_para_yolo = None
_frame_yolo_lock = threading.Lock()
_yolo_activo = threading.Event()
_yolo_detener = threading.Event()


def _hilo_yolo():
    """Hilo que corre YOLO sin bloquear el bucle principal."""
    from modulos import detector_objetos

    logger.info("Hilo YOLO iniciado.")
    while not _yolo_detener.is_set():
        # Esperar hasta que el modo requiera detección
        if not _yolo_activo.is_set():
            time.sleep(0.1)
            continue

        # Tomar el frame actual
        with _frame_yolo_lock:
            frame = _frame_para_yolo

        if frame is None:
            time.sleep(0.05)
            continue

        # Detectar (esto es lo lento ~0.5-2s en CPU)
        try:
            dets = detector_objetos.detectar(frame)
            # Agregar nombres personales
            if estado.usuario and dets:
                detector_objetos.buscar_objeto_personal_en_detecciones(
                    dets, estado.usuario["id"]
                )
        except Exception as e:
            logger.error("Error en hilo YOLO: %s", e)
            dets = []

        # Publicar resultados
        with _detecciones_lock:
            global _detecciones_compartidas
            _detecciones_compartidas = dets

        # Pausa breve para no saturar CPU
        time.sleep(0.1)

    logger.info("Hilo YOLO detenido.")


def bucle_principal():
    """
    Bucle principal que combina:
    - Captura de cámara (hilo principal, requisito de OpenCV en Windows)
    - Escucha de comandos de voz (no bloqueante)
    - Detección de objetos con YOLO (hilo separado, no bloquea)
    - Vista del maestro con overlays
    - Guía por sonido
    ESC cierra la app (solo para la demo).
    """
    global _frame_para_yolo

    from modulos import voz_salida, voz_entrada, camara, guia_sonido, vista_maestro
    from modulos import detector_objetos
    from sincronizacion import pendientes_por_sincronizar
    from database import guardar_historial

    logger.info("Bucle principal con cámara iniciado.")

    # Iniciar cámara
    if not camara.iniciar():
        logger.warning("Cámara no disponible. Continuando sin video.")
        voz_entrada.pausar()
        voz_salida.decir_y_esperar(
            "No pude abrir la cámara. Las funciones de lectura e identificación "
            "no estarán disponibles."
        )
        voz_entrada.reanudar()

    # Iniciar YOLO
    yolo_ok = detector_objetos.inicializar()
    if not yolo_ok:
        logger.warning("YOLO no disponible. La identificación no funcionará.")

    # Iniciar hilo de YOLO (separado del bucle principal)
    hilo_det = None
    if yolo_ok:
        _yolo_detener.clear()
        hilo_det = threading.Thread(target=_hilo_yolo, daemon=True, name="yolo")
        hilo_det.start()

    # Iniciar guía por sonido (no activa aún)
    guia_sonido.iniciar()

    # Inicializar ventana del maestro
    if camara.esta_activa():
        vista_maestro.inicializar()

    # Variables de estado para detección
    detecciones_actuales = []
    frame_anterior = None
    frame_count = 0

    while estado.ejecutando:
        # --- 1. Captura de cámara (no bloqueante) ---
        frame = None
        if camara.esta_activa():
            frame = camara.leer_frame()

        # --- 2. Verificar comandos de voz (no bloqueante) ---
        if voz_salida.esta_hablando():
            voz_entrada.pausar()
        else:
            if voz_entrada._pausado.is_set() and not voz_salida.esta_hablando():
                voz_entrada.reanudar()
                voz_entrada.limpiar_cola()

        texto = voz_entrada.obtener_comando(timeout=0.03)
        if texto:
            procesar_comando(texto)

        # --- 3. Procesamiento según modo activo ---
        if frame is not None:
            frame_count += 1
            necesita_yolo = estado.modo_actual in ("IDENTIFICAR", "BUSCAR")

            # Activar/desactivar hilo YOLO según modo
            if necesita_yolo and yolo_ok:
                _yolo_activo.set()
                # Enviar frame al hilo YOLO
                with _frame_yolo_lock:
                    _frame_para_yolo = frame.copy()
            else:
                _yolo_activo.clear()

            # Leer detecciones del hilo YOLO (nunca bloquea)
            with _detecciones_lock:
                detecciones_actuales = list(_detecciones_compartidas)

            # -- MODO IDENTIFICAR --
            if estado.modo_actual == "IDENTIFICAR" and yolo_ok:
                # Dibujar detecciones en la vista
                for det in detecciones_actuales:
                    nombre_mostrar = det.get("nombre_personal") or det["nombre_es"]
                    vista_maestro.dibujar_deteccion(
                        frame, det["bbox"], nombre_mostrar, det["confianza"],
                    )

                # Mejor detección
                mejor = detector_objetos.obtener_mejor_deteccion(detecciones_actuales)
                if mejor:
                    # Guía por sonido para centrar
                    pos = camara.calcular_posicion_objeto(frame, mejor["bbox"])
                    guia_sonido.activar()
                    guia_sonido.actualizar_distancia(pos["distancia_relativa"])
                    guia_sonido.marcar_centrado(pos["centrado"])

                    # Si está centrado y estable, decir el nombre
                    if pos["centrado"]:
                        es_estable = camara.frame_estable(frame_anterior, frame)
                        if es_estable:
                            estado.frames_estables += 1
                        else:
                            estado.frames_estables = 0

                        if estado.frames_estables >= config.ESTABILIDAD_FRAMES:
                            clase = mejor["clase"]
                            if not detector_objetos.ya_fue_dicho(clase):
                                _decir_identificacion(mejor, voz_salida, voz_entrada)
                                detector_objetos.marcar_como_dicho(clase)
                                # Guardar en historial
                                if estado.usuario:
                                    nombre_h = mejor.get("nombre_personal") or mejor["nombre_es"]
                                    guardar_historial(
                                        estado.usuario["id"], "identificar",
                                        nombre_h, mejor["confianza"],
                                    )
                                estado.frames_estables = 0
                    else:
                        estado.frames_estables = 0
                else:
                    guia_sonido.desactivar()
                    estado.frames_estables = 0

            # -- MODO BUSCAR (se implementará completo en Fase 6) --
            elif estado.modo_actual == "BUSCAR" and yolo_ok:
                for det in detecciones_actuales:
                    vista_maestro.dibujar_deteccion(
                        frame, det["bbox"], det["nombre_es"], det["confianza"],
                    )

            # -- Otros modos: sin detección --
            else:
                if estado.modo_actual == "ESPERANDO":
                    guia_sonido.desactivar()
                    detecciones_actuales = []

            frame_anterior = frame.copy()

            # --- 4. Actualizar vista del maestro ---
            pendientes = pendientes_por_sincronizar()
            tecla = vista_maestro.mostrar(
                frame,
                modo=estado.modo_actual,
                ultimo_comando=estado.ultimo_comando,
                ultima_respuesta=estado.ultima_respuesta,
                pendientes=pendientes,
            )

            # ESC para cerrar (solo demo)
            if tecla == 27:
                logger.info("ESC presionado. Cerrando.")
                estado.ejecutando = False
        else:
            time.sleep(0.05)

    # --- Limpieza ---
    _yolo_detener.set()
    _yolo_activo.clear()
    if hilo_det and hilo_det.is_alive():
        hilo_det.join(timeout=3)
    guia_sonido.detener()
    camara.detener()
    vista_maestro.destruir()


def _decir_identificacion(deteccion: dict, voz_salida, voz_entrada):
    """Dice el nombre del objeto identificado con su advertencia si aplica."""
    nombre = deteccion.get("nombre_personal") or deteccion["nombre_es"]
    confianza = deteccion["confianza"]

    # Guardar en estado
    estado.ultimo_objeto = nombre
    estado.ultima_clase = deteccion["clase"]
    estado.ultima_categoria = deteccion.get("categoria", "otro")

    if deteccion.get("nombre_personal"):
        msg = f"Es {nombre}."
    else:
        if confianza >= 0.85:
            msg = f"Es {nombre}."
        else:
            msg = f"Parece ser {nombre}."

    _responder(msg)
    # NO bloquear: usar decir() en vez de decir_y_esperar()
    voz_salida.decir(msg)

    # Advertencia
    if deteccion.get("advertencia"):
        voz_salida.decir(deteccion["advertencia"])


# =============================================================
# FUNCIÓN PRINCIPAL
# =============================================================
def main():
    """Función principal de EYES."""
    logger.info("=" * 50)
    logger.info("EYES - Iniciando aplicación")
    logger.info("=" * 50)

    # --- Paso 1: Inicializar base de datos local ---
    from database import inicializar_sqlite
    if not inicializar_sqlite():
        logger.critical("No se pudo inicializar la base de datos local. Saliendo.")
        print("ERROR: No se pudo inicializar la base de datos. Revisa los logs.")
        sys.exit(1)

    # --- Paso 2: Poblar catálogo si está vacío ---
    from database import obtener_catalogo
    catalogo = obtener_catalogo()
    if not catalogo:
        logger.info("Catálogo vacío. Poblando con datos iniciales...")
        from seed import poblar_catalogo
        poblar_catalogo()

    # --- Paso 3: Sincronizar con la nube (si hay internet) ---
    from sincronizacion import sincronizar_al_inicio, iniciar_sincronizacion
    sincronizar_al_inicio()
    hilo_sync = iniciar_sincronizacion()

    # --- Paso 4: Iniciar voz de salida ---
    from modulos import voz_salida
    voz_salida.iniciar()
    time.sleep(0.5)

    # --- Paso 5: Iniciar voz de entrada ---
    from modulos import voz_entrada
    voz_entrada.iniciar()
    time.sleep(0.5)

    # --- Paso 6: Verificar usuario / Primer uso ---
    from database import obtener_usuario
    estado.usuario = obtener_usuario()

    try:
        if estado.usuario and estado.usuario.get("primer_uso_completado"):
            # Usuario existente: saludar
            nombre = estado.usuario["nombre"]
            velocidad = estado.usuario.get("velocidad_voz", 175)
            voz_salida.cambiar_velocidad(velocidad)
            time.sleep(0.3)

            voz_entrada.pausar()
            voz_salida.decir_y_esperar(f"Hola {nombre}, dime qué quieres hacer.")
            voz_entrada.reanudar()
            voz_entrada.limpiar_cola()

            logger.info("Usuario existente: %s (velocidad: %d)", nombre, velocidad)
        else:
            # Primer uso: registro por voz
            primer_uso()

        # --- Paso 7: Bucle principal con cámara ---
        bucle_principal()

    except KeyboardInterrupt:
        logger.info("Interrupción del usuario (Ctrl+C).")
        print("\nCerrando EYES...")
    except Exception as e:
        logger.critical("Error crítico: %s", e, exc_info=True)
        print(f"\nError: {e}")
    finally:
        # --- Limpieza ---
        logger.info("Cerrando EYES...")
        voz_entrada.detener()
        voz_salida.detener()
        from sincronizacion import detener_sincronizacion
        detener_sincronizacion()
        # Asegurar que la ventana se cierre
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        logger.info("EYES finalizado correctamente.")


if __name__ == "__main__":
    main()
