"""
prueba_fase5.py - Prueba interactiva de la Fase 5.
Abre la cámara, detecta objetos con YOLO en tiempo real,
los muestra en la ventana del maestro y dice sus nombres en español.

Ejecutar desde eyes/: .venv\Scripts\python.exe scripts\prueba_fase5.py
Presiona ESC para cerrar.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from modulos.registro import configurar_logging
logger = configurar_logging()


def main():
    print("\n" + "=" * 60)
    print("  EYES - Prueba de Fase 5")
    print("  Identificación de objetos con YOLO en tiempo real")
    print("=" * 60)
    print("  Apunta objetos a la cámara y EYES los identificará.")
    print("  La guía por sonido te ayudará a centrar el objeto.")
    print("  Al centrar un objeto estable, dirá su nombre.")
    print("  Presiona ESC para cerrar.")
    print("-" * 60)

    import cv2
    import config
    from database import inicializar_sqlite
    from modulos import camara, detector_objetos, guia_sonido, vista_maestro, voz_salida

    inicializar_sqlite()

    # Iniciar voz
    voz_salida.iniciar()
    time.sleep(0.5)

    # Iniciar YOLO
    print("  Cargando YOLO (puede tardar unos segundos)...")
    if not detector_objetos.inicializar():
        print("  [FALLO] No se pudo cargar YOLO.")
        voz_salida.detener()
        return

    print(f"  [OK] YOLO listo ({len(detector_objetos.obtener_nombres_modelo())} clases).")

    # Iniciar cámara
    if not camara.iniciar():
        print("  [FALLO] No se pudo abrir la cámara.")
        voz_salida.detener()
        return

    print("  [OK] Cámara abierta.")

    # Iniciar guía y ventana
    guia_sonido.iniciar()
    vista_maestro.inicializar()

    voz_salida.decir_y_esperar("Modo identificar activo. Muestra un objeto a la cámara.")

    frame_anterior = None
    frames_estables = 0
    frame_count = 0
    detecciones = []

    while True:
        frame = camara.leer_frame()
        if frame is None:
            time.sleep(0.05)
            continue

        frame_count += 1

        # Detectar cada 10 frames (YOLO en CPU es lento)
        if frame_count % 10 == 0:
            detecciones = detector_objetos.detectar(frame)

        # Dibujar detecciones
        for det in detecciones:
            vista_maestro.dibujar_deteccion(
                frame, det["bbox"], det["nombre_es"], det["confianza"],
            )

        # Mejor detección
        mejor = detector_objetos.obtener_mejor_deteccion(detecciones)
        if mejor:
            pos = camara.calcular_posicion_objeto(frame, mejor["bbox"])
            guia_sonido.activar()
            guia_sonido.actualizar_distancia(pos["distancia_relativa"])
            guia_sonido.marcar_centrado(pos["centrado"])

            if pos["centrado"]:
                es_estable = camara.frame_estable(frame_anterior, frame)
                if es_estable:
                    frames_estables += 1
                else:
                    frames_estables = 0

                if frames_estables >= config.ESTABILIDAD_FRAMES:
                    clase = mejor["clase"]
                    if not detector_objetos.ya_fue_dicho(clase):
                        nombre = mejor["nombre_es"]
                        conf = mejor["confianza"]
                        if conf >= 0.85:
                            msg = f"Es {nombre}."
                        else:
                            msg = f"Parece ser {nombre}."
                        print(f"  >> {msg} (conf: {conf:.0%})")
                        voz_salida.decir_y_esperar(msg)
                        if mejor.get("advertencia"):
                            voz_salida.decir_y_esperar(mejor["advertencia"])
                        detector_objetos.marcar_como_dicho(clase)
                        frames_estables = 0
            else:
                frames_estables = 0
        else:
            guia_sonido.desactivar()
            frames_estables = 0

        frame_anterior = frame.copy()

        tecla = vista_maestro.mostrar(
            frame,
            modo="IDENTIFICAR",
            ultimo_comando="Identificar",
            ultima_respuesta=f"{len(detecciones)} objetos detectados",
        )

        if tecla == 27:
            break

    # Limpieza
    guia_sonido.detener()
    camara.detener()
    vista_maestro.destruir()
    voz_salida.detener()

    print("  [OK] Prueba completada.")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
