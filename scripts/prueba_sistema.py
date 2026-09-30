"""
prueba_sistema.py - Verifica uno por uno todos los componentes de EYES.
Ejecutar desde la carpeta eyes/: python scripts/prueba_sistema.py
"""

import os
import sys
import time

# Agregar la carpeta padre al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def separador(titulo: str):
    """Imprime un separador visual."""
    print(f"\n{'=' * 60}")
    print(f"  {titulo}")
    print(f"{'=' * 60}")


def ok(msg: str):
    print(f"  [OK]    {msg}")


def fallo(msg: str):
    print(f"  [FALLO] {msg}")


def aviso(msg: str):
    print(f"  [AVISO] {msg}")


def probar_python():
    """Verifica la versión de Python."""
    separador("PYTHON")
    version = sys.version
    print(f"  Versión: {version}")
    v = sys.version_info
    if v.major == 3 and v.minor == 11:
        ok("Python 3.11 detectado.")
        return True
    else:
        aviso(f"Se recomienda Python 3.11. Tienes {v.major}.{v.minor}.{v.micro}")
        return True  # No es fallo crítico si funciona


def probar_imports():
    """Verifica que todas las dependencias se pueden importar."""
    separador("DEPENDENCIAS (imports)")
    dependencias = {
        "cv2": "opencv-python",
        "numpy": "numpy",
        "torch": "torch (PyTorch)",
        "pyttsx3": "pyttsx3",
        "sounddevice": "sounddevice",
        "PIL": "Pillow",
        "dotenv": "python-dotenv",
        "pymysql": "PyMySQL",
        "requests": "requests",
    }
    todas_ok = True
    for modulo, nombre in dependencias.items():
        try:
            __import__(modulo)
            ok(f"{nombre}")
        except ImportError as e:
            fallo(f"{nombre}: {e}")
            todas_ok = False
    return todas_ok


def probar_vosk():
    """Verifica que Vosk está instalado y el modelo existe."""
    separador("VOSK (reconocimiento de voz)")
    try:
        import vosk
        ok("vosk importado correctamente.")
    except ImportError:
        fallo("vosk no está instalado. Ejecuta: pip install vosk")
        return False

    import config
    modelo_ruta = config.VOSK_MODELO_RUTA
    if os.path.isdir(modelo_ruta):
        ok(f"Modelo Vosk encontrado en: {modelo_ruta}")
        return True
    else:
        fallo(f"Modelo Vosk NO encontrado en: {modelo_ruta}")
        print("  Descárgalo de: https://alphacephei.com/vosk/models")
        print("  Modelo recomendado: vosk-model-small-es-0.42")
        print(f"  Descomprímelo en: {modelo_ruta}")
        return False


def probar_yolo():
    """Verifica YOLO (ultralytics)."""
    separador("YOLO (detección de objetos)")
    try:
        from ultralytics import YOLO
        ok("ultralytics importado correctamente.")
    except ImportError:
        fallo("ultralytics no está instalado. Ejecuta: pip install ultralytics")
        return False

    import config
    modelo_ruta = config.YOLO_MODELO_RUTA
    if os.path.isfile(modelo_ruta):
        ok(f"Modelo YOLO encontrado en: {modelo_ruta}")
    else:
        aviso(f"Modelo YOLO no encontrado en: {modelo_ruta}")
        print("  Se descargará automáticamente la primera vez que se use.")

    # Intentar cargar el modelo
    try:
        modelo = YOLO("yolov8n.pt")
        ok(f"YOLO cargado. Clases disponibles: {len(modelo.names)}")
        return True
    except Exception as e:
        fallo(f"Error al cargar YOLO: {e}")
        return False


def probar_easyocr():
    """Verifica EasyOCR."""
    separador("EASYOCR (lectura de texto)")
    try:
        import easyocr
        ok("easyocr importado correctamente.")
    except ImportError:
        fallo("easyocr no está instalado. Ejecuta: pip install easyocr")
        return False

    try:
        print("  Cargando modelo de OCR (puede tardar la primera vez)...")
        reader = easyocr.Reader(["es", "en"], gpu=False, verbose=False)
        ok("EasyOCR inicializado con idiomas: español e inglés.")
        return True
    except Exception as e:
        fallo(f"Error al inicializar EasyOCR: {e}")
        return False


def probar_camara():
    """Verifica acceso a la cámara."""
    separador("CÁMARA")
    try:
        import cv2
    except ImportError:
        fallo("opencv-python no está instalado.")
        return False

    import config
    cap = cv2.VideoCapture(config.CAMARA_INDICE)
    if not cap.isOpened():
        fallo(f"No se pudo abrir la cámara (índice {config.CAMARA_INDICE}).")
        print("  Verifica que tu cámara esté conectada y no la use otra app.")
        print(f"  Puedes cambiar CAMARA_INDICE en config.py (actual: {config.CAMARA_INDICE})")
        return False

    ret, frame = cap.read()
    cap.release()
    if ret and frame is not None:
        ok(f"Cámara funcionando. Resolución: {frame.shape[1]}x{frame.shape[0]}")
        return True
    else:
        fallo("La cámara se abrió pero no pudo capturar un frame.")
        return False


def probar_microfono():
    """Verifica acceso al micrófono."""
    separador("MICRÓFONO")
    try:
        import sounddevice as sd
        ok("sounddevice importado correctamente.")
    except ImportError:
        fallo("sounddevice no está instalado.")
        return False

    try:
        dispositivos = sd.query_devices()
        entrada_default = sd.query_devices(kind="input")
        ok(f"Micrófono detectado: {entrada_default['name']}")
        print(f"  Frecuencia máx: {int(entrada_default['default_samplerate'])} Hz")

        # Intentar grabar un segundo
        print("  Grabando 1 segundo de prueba...")
        audio = sd.rec(int(16000), samplerate=16000, channels=1, dtype="int16")
        sd.wait()
        nivel = abs(audio).mean()
        ok(f"Audio capturado. Nivel promedio: {nivel:.0f}")
        if nivel < 10:
            aviso("El nivel es muy bajo. Verifica que el micrófono no esté en silencio.")
        return True
    except Exception as e:
        fallo(f"Error al acceder al micrófono: {e}")
        return False


def probar_voz_espanol():
    """Verifica que haya una voz en español en Windows."""
    separador("VOZ EN ESPAÑOL (pyttsx3)")
    try:
        import pyttsx3
    except ImportError:
        fallo("pyttsx3 no está instalado.")
        return False

    try:
        motor = pyttsx3.init()
        voces = motor.getProperty("voices")
        voz_es = None
        for voz in voces:
            # Buscar por idioma español
            langs = getattr(voz, "languages", [])
            nombre = voz.name.lower()
            voz_id = voz.id.lower()
            if ("spanish" in nombre or "español" in nombre or
                "es-" in voz_id or "es_" in voz_id or
                any("es" in str(l).lower() for l in langs)):
                voz_es = voz
                break

        if voz_es:
            ok(f"Voz en español encontrada: {voz_es.name}")
            motor.setProperty("voice", voz_es.id)
            motor.setProperty("rate", 175)
            motor.say("Prueba de voz en español.")
            motor.runAndWait()
            motor.stop()
            ok("Reproducción de voz exitosa.")
            return True
        else:
            aviso("No se encontró una voz en español.")
            print("  Voces disponibles:")
            for v in voces:
                print(f"    - {v.name} ({v.id})")
            print("  Instala un paquete de voz en español desde Configuración > Hora e idioma > Voz.")
            motor.stop()
            return False
    except Exception as e:
        fallo(f"Error con pyttsx3: {e}")
        return False


def probar_sqlite():
    """Verifica SQLite local."""
    separador("SQLITE (base de datos local)")
    try:
        import config
        from database import inicializar_sqlite, obtener_usuario
        if inicializar_sqlite():
            ok(f"SQLite inicializado en: {config.SQLITE_RUTA}")
            # Probar una consulta
            usuario = obtener_usuario()
            if usuario:
                ok(f"Usuario existente: {usuario['nombre']}")
            else:
                ok("Sin usuario aún (se creará en el primer uso).")
            return True
        else:
            fallo("Error al inicializar SQLite.")
            return False
    except Exception as e:
        fallo(f"Error con SQLite: {e}")
        return False


def probar_mysql():
    """Verifica conexión a MySQL en la nube."""
    separador("MYSQL (base de datos en la nube)")
    import config
    if not config.MYSQL_HOST:
        aviso("MySQL no configurado. Edita el archivo .env con los datos de Hostinger.")
        return False

    try:
        from database import probar_conexion_mysql, inicializar_mysql
        if probar_conexion_mysql():
            ok(f"Conexión a MySQL exitosa: {config.MYSQL_HOST}")
            if inicializar_mysql():
                ok("Tablas de MySQL verificadas/creadas.")
            return True
        else:
            fallo(f"No se pudo conectar a MySQL en: {config.MYSQL_HOST}")
            print("  Verifica: host, puerto, usuario, contraseña y que Remote MySQL esté habilitado.")
            return False
    except Exception as e:
        fallo(f"Error con MySQL: {e}")
        return False


def probar_internet():
    """Verifica conexión a internet."""
    separador("INTERNET")
    from modulos.conexion import hay_internet
    if hay_internet():
        ok("Conexión a internet disponible.")
        return True
    else:
        aviso("Sin conexión a internet. Las funciones de IA en la nube no estarán disponibles.")
        return False


def probar_gemini():
    """Verifica la API de Gemini."""
    separador("GEMINI (IA en la nube)")
    import config
    if not config.GEMINI_API_KEY:
        aviso("Clave de API de Gemini no configurada en .env")
        return False

    from modulos.conexion import hay_internet
    if not hay_internet():
        aviso("Sin internet. No se puede probar Gemini.")
        return False

    try:
        from google import genai
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        respuesta = client.models.generate_content(
            model=config.GEMINI_MODELO,
            contents="Di solamente: hola, funciono correctamente.",
        )
        texto = respuesta.text.strip()
        ok(f"Gemini respondió: {texto[:80]}")
        return True
    except Exception as e:
        fallo(f"Error con Gemini: {e}")
        return False


def main():
    """Ejecuta todas las pruebas del sistema."""
    print("\n" + "=" * 60)
    print("  EYES - Prueba del Sistema")
    print("  " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    resultados = {}
    pruebas = [
        ("Python", probar_python),
        ("Dependencias", probar_imports),
        ("SQLite", probar_sqlite),
        ("MySQL", probar_mysql),
        ("Internet", probar_internet),
        ("Gemini", probar_gemini),
        ("Voz español", probar_voz_espanol),
        ("Micrófono", probar_microfono),
        ("Vosk", probar_vosk),
        ("Cámara", probar_camara),
        ("YOLO", probar_yolo),
        ("EasyOCR", probar_easyocr),
    ]

    for nombre, funcion in pruebas:
        try:
            resultados[nombre] = funcion()
        except Exception as e:
            fallo(f"Error inesperado en prueba {nombre}: {e}")
            resultados[nombre] = False

    # Resumen final
    separador("RESUMEN")
    criticos = ["Python", "Dependencias", "SQLite", "Voz español", "Micrófono", "Vosk", "Cámara"]
    opcionales = ["MySQL", "Internet", "Gemini", "YOLO", "EasyOCR"]

    print("\n  Componentes críticos (deben funcionar):")
    for nombre in criticos:
        estado = "OK" if resultados.get(nombre) else "FALLO"
        simbolo = "[OK]" if resultados.get(nombre) else "[!!]"
        print(f"    {simbolo}  {nombre}")

    print("\n  Componentes opcionales (mejoran la experiencia):")
    for nombre in opcionales:
        estado = "OK" if resultados.get(nombre) else "NO DISPONIBLE"
        simbolo = "[OK]" if resultados.get(nombre) else "[--]"
        print(f"    {simbolo}  {nombre}")

    # Resultado general
    criticos_ok = all(resultados.get(n, False) for n in criticos)
    total_ok = sum(1 for v in resultados.values() if v)
    total = len(resultados)

    print(f"\n  Total: {total_ok}/{total} componentes funcionando.")
    if criticos_ok:
        print("\n  RESULTADO: Sistema listo para funcionar.")
        print("  Los componentes opcionales se pueden configurar después.")
    else:
        print("\n  RESULTADO: Faltan componentes críticos.")
        print("  Revisa los errores marcados con [!!] antes de continuar.")

    return 0 if criticos_ok else 1


if __name__ == "__main__":
    sys.exit(main())
