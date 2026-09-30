"""
prueba_fase4.py - Prueba de la Fase 4.
Verifica:
  1. Cámara en tiempo real
  2. Vista del maestro con overlays
  3. Guía por sonido (pitidos)
  4. Todo integrado con voz

Ejecutar desde eyes/: .venv\Scripts\python.exe scripts\prueba_fase4.py
Presiona ESC para cerrar.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from modulos.registro import configurar_logging
logger = configurar_logging()


def probar_camara_y_vista():
    """Prueba la cámara con la vista del maestro."""
    print("\n" + "=" * 60)
    print("  PRUEBA: Cámara + Vista del Maestro + Guía por Sonido")
    print("=" * 60)
    print("  Se abrirá la ventana de video con la cámara.")
    print("  Verás: modo actual, FPS, estado de conexión,")
    print("  marca en el centro y barras de información.")
    print("  Presiona ESC para cerrar.")
    print("  Presiona 'g' para activar/desactivar la guía por sonido.")
    print("  Presiona '1' para modo LEER.")
    print("  Presiona '2' para modo IDENTIFICAR.")
    print("  Presiona '3' para modo BUSCAR.")
    print("  Presiona '0' para modo ESPERANDO.")
    print("-" * 60)

    import cv2
    from modulos import camara, guia_sonido, vista_maestro, voz_salida

    # Iniciar voz
    voz_salida.iniciar()
    time.sleep(0.5)

    # Iniciar cámara
    if not camara.iniciar():
        print("  [FALLO] No se pudo abrir la cámara.")
        voz_salida.detener()
        return False

    print("  [OK] Cámara abierta.")

    # Iniciar guía por sonido
    guia_sonido.iniciar()
    print("  [OK] Guía por sonido lista (presiona 'g' para activar).")

    # Inicializar ventana
    vista_maestro.inicializar()
    print("  [OK] Ventana del maestro abierta.")

    voz_salida.decir_y_esperar("Prueba de cámara iniciada. Presiona escape para cerrar.")

    modo = "ESPERANDO"
    ultimo_cmd = "(demo)"
    ultima_resp = "Prueba de Fase 4"
    guia_activa = False

    modos_tecla = {
        ord("1"): "LEER",
        ord("2"): "IDENTIFICAR",
        ord("3"): "BUSCAR",
        ord("0"): "ESPERANDO",
    }

    while True:
        frame = camara.leer_frame()
        if frame is None:
            print("  [AVISO] Frame vacío.")
            time.sleep(0.1)
            continue

        # Dibujar una detección de ejemplo (recuadro simulado)
        alto, ancho = frame.shape[:2]
        if modo != "ESPERANDO":
            # Recuadro de ejemplo en el centro
            cx, cy = ancho // 2, alto // 2
            x1, y1 = cx - 80, cy - 60
            x2, y2 = cx + 80, cy + 60
            vista_maestro.dibujar_deteccion(frame, (x1, y1, x2, y2), "ejemplo", 0.85)

            # Calcular posición para la guía
            pos = camara.calcular_posicion_objeto(frame, (x1, y1, x2, y2))
            if guia_activa:
                guia_sonido.actualizar_distancia(pos["distancia_relativa"])
                guia_sonido.marcar_centrado(pos["centrado"])

        tecla = vista_maestro.mostrar(
            frame,
            modo=modo,
            ultimo_comando=ultimo_cmd,
            ultima_respuesta=ultima_resp,
            pendientes=0,
        )

        # Procesar teclas
        if tecla == 27:  # ESC
            break
        elif tecla in modos_tecla:
            modo = modos_tecla[tecla]
            ultimo_cmd = f"Modo: {modo}"
            print(f"  Modo cambiado a: {modo}")
        elif tecla == ord("g"):
            guia_activa = not guia_activa
            if guia_activa:
                guia_sonido.activar()
                ultima_resp = "Guía por sonido activada"
                print("  Guía por sonido: ACTIVADA")
            else:
                guia_sonido.desactivar()
                ultima_resp = "Guía por sonido desactivada"
                print("  Guía por sonido: DESACTIVADA")

    # Limpieza
    guia_sonido.detener()
    camara.detener()
    vista_maestro.destruir()
    voz_salida.detener()

    print("  [OK] Prueba completada.")
    return True


def main():
    print("\n" + "=" * 60)
    print("  EYES - Prueba de Fase 4")
    print("  Cámara + Vista del Maestro + Guía por Sonido")
    print("=" * 60)

    ok = probar_camara_y_vista()

    print("\n" + "=" * 60)
    print("  RESUMEN FASE 4")
    print("=" * 60)
    print(f"  {'[OK]' if ok else '[!!]'}  Cámara + Vista + Sonido")

    if ok:
        print("\n  FASE 4 LISTA.")
    else:
        print("\n  Hay problemas que resolver.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
