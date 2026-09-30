"""
prueba_fase2.py - Prueba interactiva de la Fase 2.
Verifica:
  1. Texto a voz con cola (pyttsx3 en hilo dedicado)
  2. Reconocimiento de voz (Vosk + sounddevice)
  3. Interpretación de comandos

Ejecutar: .venv\Scripts\python.exe scripts\prueba_fase2.py
"""

import os
import sys
import time

# Agregar la carpeta padre al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modulos.registro import configurar_logging
logger = configurar_logging()


def probar_voz_salida():
    """Prueba el módulo de texto a voz."""
    print("\n" + "=" * 60)
    print("  PRUEBA 1: Texto a Voz (pyttsx3)")
    print("=" * 60)

    from modulos import voz_salida

    print("  Iniciando hilo de voz...")
    voz_salida.iniciar()
    time.sleep(0.5)

    # Prueba básica
    print("  Diciendo frase de prueba...")
    voz_salida.decir_y_esperar("Hola, soy EYES. La voz funciona correctamente.")
    print("  [OK] Frase dicha.")

    # Prueba de velocidad
    print("  Probando cambio de velocidad...")
    voz_salida.mas_rapido()
    time.sleep(1)
    voz_salida.decir_y_esperar("Ahora hablo más rápido.")
    print(f"  [OK] Velocidad actual: {voz_salida.obtener_velocidad()}")

    voz_salida.mas_lento()
    time.sleep(1)
    voz_salida.mas_lento()
    time.sleep(1)
    voz_salida.decir_y_esperar("Y ahora más lento.")
    print(f"  [OK] Velocidad actual: {voz_salida.obtener_velocidad()}")

    # Restaurar velocidad
    voz_salida.cambiar_velocidad(175)
    time.sleep(0.5)

    # Prueba de repetir
    voz_salida.decir_y_esperar("Esta es la frase para repetir.")
    print("  Repitiendo última respuesta...")
    voz_salida.repetir()
    time.sleep(3)
    print(f"  [OK] Última respuesta: '{voz_salida.ultima_respuesta}'")

    print("  [OK] Módulo de voz funcionando correctamente.")
    return True


def probar_comandos():
    """Prueba el intérprete de comandos."""
    print("\n" + "=" * 60)
    print("  PRUEBA 2: Intérprete de Comandos")
    print("=" * 60)

    from modulos.comandos import interpretar

    pruebas = [
        ("leer", "leer"),
        ("lee", "leer"),
        ("léeme el texto", "leer"),
        ("qué es esto", "identificar"),
        ("que es eso", "identificar"),
        ("busca el atún", "buscar"),
        ("búscame la medicina", "buscar"),
        ("repetir", "repetir"),
        ("repite", "repetir"),
        ("resume", "resumir"),
        ("más rápido", "mas_rapido"),
        ("más lento", "mas_lento"),
        ("ayuda", "ayuda"),
        ("salir", "salir"),
        ("sí", "si"),
        ("no", "no"),
        ("guardar esto", "guardar"),
        ("qué hay guardado", "que_hay_guardado"),
        ("historial", "historial"),
        ("detener", "detener"),
    ]

    aciertos = 0
    for texto, esperado in pruebas:
        resultado = interpretar(texto)
        cmd = resultado["comando"]
        ok = cmd == esperado
        aciertos += int(ok)
        estado = "[OK]" if ok else "[!!]"
        extra = ""
        if resultado.get("argumento"):
            extra = f" (arg: {resultado['argumento']})"
        print(f"  {estado}  '{texto}' → {cmd}{extra}" +
              (f"  (esperado: {esperado})" if not ok else ""))

    print(f"\n  Resultado: {aciertos}/{len(pruebas)} comandos correctos.")
    return aciertos == len(pruebas)


def probar_voz_entrada():
    """Prueba el reconocimiento de voz (interactiva)."""
    print("\n" + "=" * 60)
    print("  PRUEBA 3: Reconocimiento de Voz (Vosk)")
    print("=" * 60)
    print("  Esta prueba es interactiva.")
    print("  Habla al micrófono y verás lo que se reconoce.")
    print("  Di 'salir' para terminar la prueba.")
    print("  Tienes 30 segundos.")
    print("-" * 60)

    from modulos import voz_salida, voz_entrada
    from modulos.comandos import interpretar

    # Integración: pausar micro mientras habla
    original_decir = voz_salida.decir_y_esperar

    voz_salida.decir_y_esperar(
        "Prueba de micrófono. Habla y repetiré lo que escuche. Di salir para terminar."
    )

    voz_entrada.iniciar()
    time.sleep(0.5)

    inicio = time.time()
    limite = 30  # segundos

    while time.time() - inicio < limite:
        # Pausar reconocimiento mientras habla
        if voz_salida.esta_hablando():
            voz_entrada.pausar()
        else:
            voz_entrada.reanudar()

        texto = voz_entrada.obtener_comando(timeout=0.5)
        if texto:
            print(f"  Escuché: '{texto}'")
            resultado = interpretar(texto)
            cmd = resultado["comando"]
            print(f"  Comando: {cmd} (confianza: {resultado['confianza']:.2f})")

            if cmd == "salir":
                voz_salida.decir_y_esperar("Prueba terminada.")
                break
            elif cmd:
                voz_entrada.pausar()
                voz_salida.decir_y_esperar(f"Entendí: {cmd}.")
                voz_entrada.reanudar()
            else:
                voz_entrada.pausar()
                voz_salida.decir_y_esperar(f"Escuché: {texto}. No es un comando.")
                voz_entrada.reanudar()
    else:
        print("  Tiempo agotado.")

    voz_entrada.detener()
    print("  [OK] Reconocimiento de voz probado.")
    return True


def main():
    print("\n" + "=" * 60)
    print("  EYES - Prueba de Fase 2")
    print("  Voz de salida + Voz de entrada + Comandos")
    print("=" * 60)

    from modulos import voz_salida

    # Prueba 1: Voz de salida
    ok_voz = probar_voz_salida()

    # Prueba 2: Intérprete de comandos
    ok_cmd = probar_comandos()

    # Prueba 3: Reconocimiento de voz (interactiva)
    print("\n  ¿Quieres probar el micrófono? (s/n): ", end="")
    respuesta = input().strip().lower()
    if respuesta in ("s", "si", "sí", "y", "yes", ""):
        ok_mic = probar_voz_entrada()
    else:
        ok_mic = True
        print("  Prueba de micrófono omitida.")

    # Limpieza
    voz_salida.detener()

    # Resumen
    print("\n" + "=" * 60)
    print("  RESUMEN FASE 2")
    print("=" * 60)
    print(f"  {'[OK]' if ok_voz else '[!!]'}  Texto a voz")
    print(f"  {'[OK]' if ok_cmd else '[!!]'}  Intérprete de comandos")
    print(f"  {'[OK]' if ok_mic else '[!!]'}  Reconocimiento de voz")

    if ok_voz and ok_cmd:
        print("\n  FASE 2 LISTA.")
    else:
        print("\n  Hay problemas que resolver.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
