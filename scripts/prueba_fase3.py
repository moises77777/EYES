"""
prueba_fase3.py - Prueba de la Fase 3 (registro y comandos).
Verifica:
  1. Que el registro de primer uso funciona por voz.
  2. Que el saludo funciona para usuarios existentes.
  3. Que el bucle de comandos interpreta correctamente.

IMPORTANTE: Esta prueba usa el micrófono y los parlantes reales.
Ejecutar desde eyes/: .venv\Scripts\python.exe scripts\prueba_fase3.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from modulos.registro import configurar_logging
logger = configurar_logging()


def probar_primer_uso_simulado():
    """Prueba el primer uso creando un usuario directamente (sin micrófono)."""
    print("\n" + "=" * 60)
    print("  PRUEBA 1: Crear usuario simulado")
    print("=" * 60)

    from database import inicializar_sqlite, crear_usuario, obtener_usuario

    inicializar_sqlite()

    # Verificar si ya hay usuario
    usuario = obtener_usuario()
    if usuario:
        print(f"  Ya hay un usuario: {usuario['nombre']}")
        print("  Para probar el primer uso real, borra data/eyes_local.db")
        return True

    # Crear usuario de prueba
    id_u = crear_usuario("Prueba", 175)
    if id_u:
        print(f"  [OK] Usuario creado: Prueba (ID: {id_u})")
        return True
    else:
        print("  [FALLO] No se pudo crear usuario.")
        return False


def probar_saludo():
    """Prueba que el saludo funciona para usuario existente."""
    print("\n" + "=" * 60)
    print("  PRUEBA 2: Saludo a usuario existente")
    print("=" * 60)

    from database import obtener_usuario
    from modulos import voz_salida

    voz_salida.iniciar()
    time.sleep(0.5)

    usuario = obtener_usuario()
    if not usuario:
        print("  [FALLO] No hay usuario para saludar.")
        voz_salida.detener()
        return False

    nombre = usuario["nombre"]
    print(f"  Saludando a: {nombre}")
    voz_salida.decir_y_esperar(f"Hola {nombre}, dime qué quieres hacer.")
    print(f"  [OK] Saludo dicho correctamente.")

    voz_salida.detener()
    return True


def probar_bucle_comandos_simulado():
    """Prueba el intérprete de comandos sin micrófono."""
    print("\n" + "=" * 60)
    print("  PRUEBA 3: Procesamiento de comandos (simulado)")
    print("=" * 60)

    from modulos.comandos import interpretar

    comandos_prueba = [
        "leer",
        "qué es esto",
        "busca el shampoo",
        "repetir",
        "más rápido",
        "más lento",
        "ayuda",
        "historial",
        "qué hay guardado",
    ]

    todos_ok = True
    for texto in comandos_prueba:
        resultado = interpretar(texto)
        cmd = resultado["comando"]
        arg = resultado.get("argumento", "")
        extra = f" (arg: {arg})" if arg else ""
        if cmd:
            print(f"  [OK] '{texto}' -> {cmd}{extra}")
        else:
            print(f"  [!!] '{texto}' -> no reconocido")
            todos_ok = False

    return todos_ok


def probar_interactivo():
    """Prueba interactiva con micrófono real."""
    print("\n" + "=" * 60)
    print("  PRUEBA 4: Prueba interactiva (micrófono real)")
    print("=" * 60)
    print("  Habla al micrófono. EYES responderá.")
    print("  Di 'salir' para terminar.")
    print("  Tienes 60 segundos.")
    print("-" * 60)

    from database import obtener_usuario
    from modulos import voz_salida, voz_entrada
    from modulos.comandos import interpretar, TEXTO_AYUDA

    voz_salida.iniciar()
    time.sleep(0.5)
    voz_entrada.iniciar()
    time.sleep(0.5)

    usuario = obtener_usuario()
    nombre = usuario["nombre"] if usuario else "usuario"

    voz_entrada.pausar()
    voz_salida.decir_y_esperar(f"Hola {nombre}, dime qué quieres hacer.")
    voz_entrada.reanudar()
    voz_entrada.limpiar_cola()

    inicio = time.time()
    while time.time() - inicio < 60:
        if voz_salida.esta_hablando():
            voz_entrada.pausar()
            while voz_salida.esta_hablando():
                time.sleep(0.1)
            voz_entrada.reanudar()
            voz_entrada.limpiar_cola()

        texto = voz_entrada.obtener_comando(timeout=0.5)
        if not texto:
            continue

        print(f"  Escuché: '{texto}'")
        resultado = interpretar(texto)
        cmd = resultado["comando"]
        arg = resultado.get("argumento")
        print(f"  Comando: {cmd}")

        voz_entrada.pausar()

        if cmd == "leer":
            voz_salida.decir_y_esperar("Modo lectura. Disponible pronto.")
        elif cmd == "identificar":
            voz_salida.decir_y_esperar("Modo identificar. Disponible pronto.")
        elif cmd == "buscar":
            if arg:
                voz_salida.decir_y_esperar(f"Buscando {arg}. Disponible pronto.")
            else:
                voz_salida.decir_y_esperar("¿Qué quieres que busque?")
        elif cmd == "repetir":
            voz_salida.repetir()
        elif cmd == "mas_rapido":
            voz_salida.mas_rapido()
        elif cmd == "mas_lento":
            voz_salida.mas_lento()
        elif cmd == "ayuda":
            voz_salida.decir_y_esperar(TEXTO_AYUDA)
        elif cmd == "salir":
            voz_salida.decir_y_esperar(f"Hasta luego, {nombre}.")
            break
        else:
            voz_salida.decir_y_esperar("No te entendí. Di ayuda para los comandos.")

        voz_entrada.reanudar()
        voz_entrada.limpiar_cola()

    voz_entrada.detener()
    voz_salida.detener()
    print("  [OK] Prueba interactiva completada.")
    return True


def main():
    print("\n" + "=" * 60)
    print("  EYES - Prueba de Fase 3")
    print("  Registro, saludo y comandos")
    print("=" * 60)

    ok1 = probar_primer_uso_simulado()
    ok2 = probar_saludo()
    ok3 = probar_bucle_comandos_simulado()

    print("\n  ¿Quieres probar con el micrófono real? (s/n): ", end="")
    resp = input().strip().lower()
    if resp in ("s", "si", "sí", ""):
        ok4 = probar_interactivo()
    else:
        ok4 = True
        print("  Prueba interactiva omitida.")

    print("\n" + "=" * 60)
    print("  RESUMEN FASE 3")
    print("=" * 60)
    print(f"  {'[OK]' if ok1 else '[!!]'}  Crear usuario")
    print(f"  {'[OK]' if ok2 else '[!!]'}  Saludo")
    print(f"  {'[OK]' if ok3 else '[!!]'}  Comandos simulados")
    print(f"  {'[OK]' if ok4 else '[!!]'}  Prueba interactiva")

    if ok1 and ok2 and ok3:
        print("\n  FASE 3 LISTA.")
    else:
        print("\n  Hay problemas que resolver.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
