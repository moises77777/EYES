# config.py - Configuracion de EYES

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Rutas
BASE_DIR = Path(__file__).parent
MODELOS_DIR = BASE_DIR / "modelos"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DATASET_DIR = BASE_DIR / "dataset"

for d in [MODELOS_DIR, DATA_DIR, LOGS_DIR, DATASET_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Camara
CAMARA_INDICE = 0
CAMARA_ANCHO = 640
CAMARA_ALTO = 480
CAMARA_FPS = 30

# Voz salida
VOZ_VELOCIDAD = 175
VOZ_VOLUMEN = 1.0
VOZ_VELOCIDAD_MIN = 100
VOZ_VELOCIDAD_MAX = 300
VOZ_AJUSTE_PASO = 25

# Voz entrada (Vosk)
VOSK_MODELO_RUTA = str(MODELOS_DIR / "vosk-model-small-es-0.42")
VOSK_FRECUENCIA_MUESTREO = 16000
VOSK_BLOQUE_TAMANO = 8000

# YOLO
YOLO_MODELO_RUTA = str(MODELOS_DIR / "yolov8n.pt")
YOLO_MODELO_PROPIO_RUTA = str(MODELOS_DIR / "mejor_modelo.pt")
YOLO_USAR_MODELO_PROPIO = False
YOLO_CONFIANZA_MINIMA = 0.6
YOLO_DISPOSITIVO = "cpu"

# OCR
OCR_IDIOMAS = ["es", "en"]
OCR_CONFIANZA_MINIMA = 0.3
OCR_GPU = False

# Texto largo
TEXTO_LARGO_PALABRAS = 40

# Guia por sonido
SONIDO_FRECUENCIA_LEJOS = 800
SONIDO_FRECUENCIA_CERCA = 1200
SONIDO_FRECUENCIA_LISTO = 1800
SONIDO_DURACION = 0.08
SONIDO_VOLUMEN = 0.5

# Modo buscar
BUSCAR_TIEMPO_LIMITE = 30

# Estabilidad de deteccion
ESTABILIDAD_FRAMES = 5
ESTABILIDAD_REPETIR_SEGUNDOS = 5

# Nitidez
NITIDEZ_UMBRAL = 50.0

# SQLite
SQLITE_RUTA = str(DATA_DIR / "eyes_local.db")

# MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST", "")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "EYES")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODELO = "gemini-3.5-flash-lite"
GEMINI_TIMEOUT = 8
GEMINI_MAX_TOKENS = 200

# Sincronizacion
SYNC_INTERVALO_SEGUNDOS = 30
SYNC_LOTE_MAXIMO = 50

# Admin
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Logging
LOG_ARCHIVO = str(LOGS_DIR / "eyes.log")
LOG_NIVEL = "DEBUG"
