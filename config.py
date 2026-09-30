"""
config.py - Configuración central de EYES.
Todos los parámetros ajustables están aquí.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv(Path(__file__).parent / ".env")

# =============================================================
# RUTAS BASE
# =============================================================
BASE_DIR = Path(__file__).parent
MODELOS_DIR = BASE_DIR / "modelos"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DATASET_DIR = BASE_DIR / "dataset"

# Crear directorios si no existen
for d in [MODELOS_DIR, DATA_DIR, LOGS_DIR, DATASET_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# =============================================================
# CÁMARA
# =============================================================
CAMARA_INDICE = 0                # Índice de la cámara (0 = predeterminada)
CAMARA_ANCHO = 640               # Ancho del frame
CAMARA_ALTO = 480                # Alto del frame
CAMARA_FPS = 30                  # FPS objetivo

# =============================================================
# VOZ DE SALIDA (pyttsx3)
# =============================================================
VOZ_VELOCIDAD = 175              # Palabras por minuto (ajustable por el usuario)
VOZ_VOLUMEN = 1.0                # Volumen de 0.0 a 1.0
VOZ_VELOCIDAD_MIN = 100          # Mínimo permitido
VOZ_VELOCIDAD_MAX = 300          # Máximo permitido
VOZ_AJUSTE_PASO = 25             # Cuánto sube/baja al decir "más rápido" / "más lento"

# =============================================================
# VOZ DE ENTRADA (Vosk)
# =============================================================
VOSK_MODELO_RUTA = str(MODELOS_DIR / "vosk-model-small-es-0.42")
VOSK_FRECUENCIA_MUESTREO = 16000  # Hz
VOSK_BLOQUE_TAMANO = 8000         # Muestras por bloque

# =============================================================
# DETECCIÓN DE OBJETOS (YOLO)
# =============================================================
YOLO_MODELO_RUTA = str(MODELOS_DIR / "yolov8n.pt")  # Modelo preentrenado COCO
YOLO_MODELO_PROPIO_RUTA = str(MODELOS_DIR / "mejor_modelo.pt")  # Modelo entrenado propio
YOLO_USAR_MODELO_PROPIO = False   # Cambiar a True al tener modelo entrenado
YOLO_CONFIANZA_MINIMA = 0.6       # Umbral de confianza
YOLO_DISPOSITIVO = "cpu"          # "cpu" o "cuda" si hay GPU NVIDIA

# =============================================================
# OCR (EasyOCR)
# =============================================================
OCR_IDIOMAS = ["es", "en"]        # Idiomas para lectura
OCR_CONFIANZA_MINIMA = 0.3        # Umbral mínimo de confianza por línea
OCR_GPU = False                   # True si hay GPU NVIDIA

# =============================================================
# TEXTO LARGO (para ofrecer resumen)
# =============================================================
TEXTO_LARGO_PALABRAS = 40         # Más de N palabras = ofrecer resumen

# =============================================================
# GUÍA POR SONIDO
# =============================================================
SONIDO_FRECUENCIA_LEJOS = 800     # Hz del pitido cuando está lejos
SONIDO_FRECUENCIA_CERCA = 1200    # Hz del pitido cuando está cerca
SONIDO_FRECUENCIA_LISTO = 1800    # Hz del tono de "listo"
SONIDO_DURACION = 0.08            # Duración del pitido en segundos
SONIDO_VOLUMEN = 0.5              # Volumen de los pitidos (0.0 a 1.0)

# =============================================================
# MODO BUSCAR
# =============================================================
BUSCAR_TIEMPO_LIMITE = 30         # Segundos antes de preguntar si sigue buscando

# =============================================================
# ESTABILIDAD DE DETECCIÓN
# =============================================================
ESTABILIDAD_FRAMES = 5            # Frames consecutivos para confirmar detección
ESTABILIDAD_REPETIR_SEGUNDOS = 5  # No repetir el mismo objeto antes de N segundos

# =============================================================
# NITIDEZ (Laplaciano para verificar enfoque)
# =============================================================
NITIDEZ_UMBRAL = 50.0             # Varianza del Laplaciano mínima para considerar nítido

# =============================================================
# BASE DE DATOS - SQLite LOCAL
# =============================================================
SQLITE_RUTA = str(DATA_DIR / "eyes_local.db")

# =============================================================
# BASE DE DATOS - MySQL EN LA NUBE
# =============================================================
MYSQL_HOST = os.getenv("MYSQL_HOST", "")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "eyes_db")

# =============================================================
# IA EN LA NUBE (Gemini)
# =============================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODELO = "gemini-3.5-flash-lite"  # Modelo de Gemini a usar
GEMINI_TIMEOUT = 8                       # Segundos máximos de espera
GEMINI_MAX_TOKENS = 200                  # Máximo de tokens en respuesta

# =============================================================
# SINCRONIZACIÓN
# =============================================================
SYNC_INTERVALO_SEGUNDOS = 30      # Cada cuántos segundos intentar sincronizar
SYNC_LOTE_MAXIMO = 50             # Máximo de registros por lote de sincronización

# =============================================================
# ADMINISTRADOR
# =============================================================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# =============================================================
# LOGGING
# =============================================================
LOG_ARCHIVO = str(LOGS_DIR / "eyes.log")
LOG_NIVEL = "DEBUG"               # DEBUG, INFO, WARNING, ERROR, CRITICAL
