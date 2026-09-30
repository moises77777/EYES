# main.py - Punto de entrada de EYES
# Comandos de voz: "que es esto", "guardar esto", "ayuda", "salir",
#                  "mas rapido", "mas lento", "historial", "repetir"

import sys
import time
import threading

import cv2
import config

from modulos.registro import configurar_logging
logger = configurar_logging()


class EstadoApp:
    def __init__(self):
        self.usuario = None
        self.modo_actual = "ESPERANDO"
        self.ultimo_texto_leido = ""
        self.ultimo_objeto = ""
        self.ultima_clase = ""
        self.ultima_categoria = ""
        self.ejecutando = True
        self.ultimo_comando = ""
        self.ultima_respuesta = ""
        self.objeto_buscado = ""
        self.frames_estables = 0
        self.deteccion_estable = None


estado = EstadoApp()


def primer_uso():
    from modulos import voz_salida, voz_entrada
    from modulos.comandos import interpretar
    from database import crear_usuario, actualizar_velocidad_voz, guardar_configuracion

    logger.info("Iniciando primer uso (registro por voz).")

    voz_entrada.pausar()
    voz_salida.decir_y_esperar(
        "Hola, soy EYES, tu asistente para identificar cosas en tu casa. "
        "Voy a configurarme para ti."
    )

    nombre = None
    while nombre is None:
        voz_salida.decir_y_esperar("Como te llamas?")
        voz_entrada.reanudar()
        voz_entrada.limpiar_cola()
        texto = voz_entrada.obtener_comando(timeout=10)
        voz_entrada.pausar()

        if texto:
            nombre_limpio = _limpiar_nombre(texto)
            if nombre_limpio:
                voz_salida.decir_y_esperar(f"Te llamas {nombre_limpio}? Di si o no.")
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
                    voz_salida.decir_y_esperar("No escuche tu respuesta. Intentemos de nuevo.")
            else:
                voz_salida.decir_y_esperar("No entendi tu nombre. Por favor repitelo.")
        else:
            voz_salida.decir_y_esperar("No escuche nada. Habla cerca del microfono.")

    id_usuario = crear_usuario(nombre, voz_salida.obtener_velocidad())
    if id_usuario is None:
        logger.error("No se pudo crear el usuario.")
        voz_salida.decir_y_esperar("Hubo un error al guardar tu nombre, pero continuare.")
        estado.usuario = {"id": 1, "nombre": nombre, "velocidad_voz": 175}
    else:
        from database import obtener_usuario
        estado.usuario = obtener_usuario()

    logger.info("Usuario registrado: %s (ID: %s)", nombre, estado.usuario.get("id"))

    voz_salida.decir_y_esperar(
        f"Bien, {nombre}. Ahora voy a ajustar la velocidad de mi voz. "
        "Dime: mas rapido, mas lento, o asi esta bien."
    )

    ajustando = True
    while ajustando:
        voz_salida.decir_y_esperar(
            "Esta es la velocidad actual. "
            "Mas rapido, mas lento, o asi esta bien?"
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
            else:
                ajustando = False
        else:
            ajustando = False

    velocidad = voz_salida.obtener_velocidad()
    if estado.usuario and estado.usuario.get("id"):
        actualizar_velocidad_voz(estado.usuario["id"], velocidad)
        guardar_configuracion(estado.usuario["id"], "velocidad_voz", str(velocidad))

    voz_salida.decir_y_esperar(f"Perfecto, {nombre}. Te explico como funciono.")
    time.sleep(0.3)
    voz_salida.decir_y_esperar("Di que es esto para identificar un objeto.")
    time.sleep(0.2)
    voz_salida.decir_y_esperar("Di ayuda en cualquier momento para los comandos.")
    time.sleep(0.2)
    voz_salida.decir_y_esperar("Di salir para cerrar.")
    time.sleep(0.3)
    voz_salida.decir_y_esperar(f"Listo, {nombre}. Dime que quieres hacer.")

    logger.info("Primer uso completado para: %s", nombre)


def _limpiar_nombre(texto):
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


def _responder(texto):
    estado.ultima_respuesta = texto


def procesar_comando(texto):
    from modulos import voz_salida, voz_entrada
    from modulos.comandos import interpretar, TEXTO_AYUDA
    from database import obtener_historial_reciente, obtener_objetos_personales

    estado.ultimo_comando = texto
    resultado = interpretar(texto)
    cmd = resultado["comando"]
    arg = resultado["argumento"]

    logger.info("Comando: %s (texto: '%s', arg: %s)", cmd, texto, arg)
    voz_entrada.pausar()

    if cmd == "identificar":
        from modulos import detector_objetos
        estado.modo_actual = "IDENTIFICAR"
        detector_objetos.limpiar_dichos()
        msg = "Modo identificar activado. Muestra el objeto a la camara."
        _responder(msg)
        voz_salida.decir_y_esperar(msg)

    elif cmd == "repetir":
        voz_salida.repetir()

    elif cmd == "historial":
        if estado.usuario:
            historial = obtener_historial_reciente(estado.usuario["id"], 5)
            if historial:
                msg = f"Ultimas {len(historial)} cosas:"
                _responder(msg)
                voz_salida.decir_y_esperar(msg)
                for i, h in enumerate(historial, 1):
                    modo = h.get("modo", "")
                    resultado_h = h.get("resultado", "sin resultado")
                    if len(resultado_h) > 80:
                        resultado_h = resultado_h[:80]
                    voz_salida.decir_y_esperar(f"{i}. {modo}: {resultado_h}")
            else:
                msg = "No hay historial todavia."
                _responder(msg)
                voz_salida.decir_y_esperar(msg)

    elif cmd == "guardar":
        if estado.ultima_clase and estado.ultimo_objeto:
            from database import guardar_objeto_personal
            voz_salida.decir_y_esperar(
                f"Voy a guardar {estado.ultimo_objeto}. Como quieres que lo llame?")
            voz_entrada.reanudar()
            voz_entrada.limpiar_cola()
            nombre_personal = voz_entrada.obtener_comando(timeout=10)
            voz_entrada.pausar()
            if nombre_personal:
                from modulos.comandos import interpretar as _interp
                r = _interp(nombre_personal)
                if r["comando"] in ("detener", "cancelar"):
                    msg = "Guardar cancelado."
                else:
                    id_obj = guardar_objeto_personal(
                        estado.usuario["id"], nombre_personal,
                        estado.ultima_clase, estado.ultima_categoria or "otro")
                    msg = f"Guardado como {nombre_personal}." if id_obj else "Error al guardar."
            else:
                msg = "No escuche el nombre. No se guardo."
            _responder(msg)
            voz_salida.decir_y_esperar(msg)
        else:
            msg = "Primero identifica un objeto con la camara."
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
                msg = "No tienes objetos guardados."
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
            msg = "No hay ningun modo activo. Di ayuda para los comandos."
        _responder(msg)
        voz_salida.decir_y_esperar(msg)

    elif cmd == "salir":
        nombre = estado.usuario["nombre"] if estado.usuario else ""
        msg = f"Hasta luego{', ' + nombre if nombre else ''}. Cerrando EYES."
        _responder(msg)
        voz_salida.decir_y_esperar(msg)
        estado.ejecutando = False

    elif cmd in ("si", "no"):
        pass

    else:
        msg = "No te entendi. Di ayuda para los comandos."
        _responder(msg)
        voz_salida.decir_y_esperar(msg)

    voz_entrada.reanudar()
    voz_entrada.limpiar_cola()


# Hilo YOLO separado
_detecciones_lock = threading.Lock()
_detecciones_compartidas = []
_frame_para_yolo = None
_frame_yolo_lock = threading.Lock()
_yolo_activo = threading.Event()
_yolo_detener = threading.Event()


def _hilo_yolo():
    from modulos import detector_objetos
    logger.info("Hilo YOLO iniciado.")
    while not _yolo_detener.is_set():
        if not _yolo_activo.is_set():
            time.sleep(0.1)
            continue
        with _frame_yolo_lock:
            frame = _frame_para_yolo
        if frame is None:
            time.sleep(0.05)
            continue
        try:
            dets = detector_objetos.detectar(frame)
            if estado.usuario and dets:
                detector_objetos.buscar_objeto_personal_en_detecciones(dets, estado.usuario["id"])
        except Exception as e:
            logger.error("Error en hilo YOLO: %s", e)
            dets = []
        with _detecciones_lock:
            global _detecciones_compartidas
            _detecciones_compartidas = dets
        time.sleep(0.1)
    logger.info("Hilo YOLO detenido.")


def bucle_principal():
    global _frame_para_yolo

    from modulos import voz_salida, voz_entrada, camara, guia_sonido, vista_maestro
    from modulos import detector_objetos
    from sincronizacion import pendientes_por_sincronizar
    from database import guardar_historial

    logger.info("Bucle principal con camara iniciado.")

    if not camara.iniciar():
        logger.warning("Camara no disponible.")
        voz_entrada.pausar()
        voz_salida.decir_y_esperar("No pude abrir la camara.")
        voz_entrada.reanudar()

    yolo_ok = detector_objetos.inicializar()

    hilo_det = None
    if yolo_ok:
        _yolo_detener.clear()
        hilo_det = threading.Thread(target=_hilo_yolo, daemon=True, name="yolo")
        hilo_det.start()

    guia_sonido.iniciar()

    if camara.esta_activa():
        vista_maestro.inicializar()

    detecciones_actuales = []
    frame_anterior = None

    while estado.ejecutando:
        frame = None
        if camara.esta_activa():
            frame = camara.leer_frame()

        if voz_salida.esta_hablando():
            voz_entrada.pausar()
        else:
            if voz_entrada._pausado.is_set() and not voz_salida.esta_hablando():
                voz_entrada.reanudar()
                voz_entrada.limpiar_cola()

        texto = voz_entrada.obtener_comando(timeout=0.03)
        if texto:
            procesar_comando(texto)

        if frame is not None:
            necesita_yolo = estado.modo_actual in ("IDENTIFICAR", "BUSCAR")

            if necesita_yolo and yolo_ok:
                _yolo_activo.set()
                with _frame_yolo_lock:
                    _frame_para_yolo = frame.copy()
            else:
                _yolo_activo.clear()

            with _detecciones_lock:
                detecciones_actuales = list(_detecciones_compartidas)

            if estado.modo_actual == "IDENTIFICAR" and yolo_ok:
                for det in detecciones_actuales:
                    nombre_mostrar = det.get("nombre_personal") or det["nombre_es"]
                    vista_maestro.dibujar_deteccion(
                        frame, det["bbox"], nombre_mostrar, det["confianza"])

                mejor = detector_objetos.obtener_mejor_deteccion(detecciones_actuales)
                if mejor:
                    pos = camara.calcular_posicion_objeto(frame, mejor["bbox"])
                    guia_sonido.activar()
                    guia_sonido.actualizar_distancia(pos["distancia_relativa"])
                    guia_sonido.marcar_centrado(pos["centrado"])

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
                                if estado.usuario:
                                    nombre_h = mejor.get("nombre_personal") or mejor["nombre_es"]
                                    guardar_historial(
                                        estado.usuario["id"], "identificar",
                                        nombre_h, mejor["confianza"])
                                estado.frames_estables = 0
                    else:
                        estado.frames_estables = 0
                else:
                    guia_sonido.desactivar()
                    estado.frames_estables = 0
            else:
                if estado.modo_actual == "ESPERANDO":
                    guia_sonido.desactivar()
                    detecciones_actuales = []

            frame_anterior = frame.copy()

            tecla = vista_maestro.mostrar(frame)
            if tecla == 27:
                logger.info("ESC presionado. Cerrando.")
                estado.ejecutando = False
        else:
            time.sleep(0.05)

    _yolo_detener.set()
    _yolo_activo.clear()
    if hilo_det and hilo_det.is_alive():
        hilo_det.join(timeout=3)
    guia_sonido.detener()
    camara.detener()
    vista_maestro.destruir()


def _decir_identificacion(deteccion, voz_salida, voz_entrada):
    nombre = deteccion.get("nombre_personal") or deteccion["nombre_es"]
    confianza = deteccion["confianza"]

    estado.ultimo_objeto = nombre
    estado.ultima_clase = deteccion["clase"]
    estado.ultima_categoria = deteccion.get("categoria", "otro")

    if deteccion.get("nombre_personal"):
        msg = f"Es {nombre}."
    elif confianza >= 0.85:
        msg = f"Es {nombre}."
    else:
        msg = f"Parece ser {nombre}."

    _responder(msg)
    voz_salida.decir(msg)

    if deteccion.get("advertencia"):
        voz_salida.decir(deteccion["advertencia"])


def main():
    logger.info("=" * 50)
    logger.info("EYES - Iniciando aplicacion")
    logger.info("=" * 50)

    from database import inicializar_sqlite
    if not inicializar_sqlite():
        logger.critical("No se pudo inicializar la base de datos.")
        sys.exit(1)

    from database import obtener_catalogo
    if not obtener_catalogo():
        from seed import poblar_catalogo
        poblar_catalogo()

    from sincronizacion import sincronizar_al_inicio, iniciar_sincronizacion
    sincronizar_al_inicio()
    iniciar_sincronizacion()

    from modulos import voz_salida
    voz_salida.iniciar()
    time.sleep(0.5)

    from modulos import voz_entrada
    voz_entrada.iniciar()
    time.sleep(0.5)

    from database import obtener_usuario
    estado.usuario = obtener_usuario()

    try:
        if estado.usuario and estado.usuario.get("primer_uso_completado"):
            nombre = estado.usuario["nombre"]
            velocidad = estado.usuario.get("velocidad_voz", 175)
            voz_salida.cambiar_velocidad(velocidad)
            time.sleep(0.3)
            voz_entrada.pausar()
            voz_salida.decir_y_esperar(f"Hola {nombre}, dime que quieres hacer.")
            voz_entrada.reanudar()
            voz_entrada.limpiar_cola()
            logger.info("Usuario existente: %s (velocidad: %d)", nombre, velocidad)
        else:
            primer_uso()

        bucle_principal()

    except KeyboardInterrupt:
        logger.info("Interrupcion del usuario (Ctrl+C).")
        print("\nCerrando EYES...")
    except Exception as e:
        logger.critical("Error critico: %s", e, exc_info=True)
    finally:
        logger.info("Cerrando EYES...")
        voz_entrada.detener()
        voz_salida.detener()
        from sincronizacion import detener_sincronizacion
        detener_sincronizacion()
        try:
            cv2.destroyAllWindows()
        except:
            pass
        logger.info("EYES finalizado correctamente.")


if __name__ == "__main__":
    main()
