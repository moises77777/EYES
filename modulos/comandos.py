"""
comandos.py - Interpreta los comandos de voz del usuario.
Compara el texto reconocido con los comandos conocidos usando
coincidencia flexible (parcial, sin acentos, variaciones comunes).
"""

import logging
import unicodedata
from typing import Optional

logger = logging.getLogger("eyes")


def _normalizar(texto: str) -> str:
    """
    Normaliza texto para comparación flexible:
    - Minúsculas
    - Sin acentos
    - Sin signos de puntuación
    - Espacios simples
    """
    texto = texto.lower().strip()
    # Quitar acentos
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    # Quitar signos de puntuación
    texto = "".join(c if c.isalnum() or c.isspace() else " " for c in texto)
    # Espacios simples
    texto = " ".join(texto.split())
    return texto


# =============================================================
# DEFINICIÓN DE COMANDOS
# Cada comando tiene: nombre interno, variaciones aceptadas,
# y si espera un argumento después (como "busca [objeto]")
# =============================================================
COMANDOS = {
    "leer": {
        "variaciones": [
            "leer", "lee", "lees", "leeme", "lee me", "leelo", "lee lo",
            "leer texto", "lee el texto", "que dice", "que dice ahi",
            "que dice aqui", "dime que dice",
        ],
        "con_argumento": False,
    },
    "identificar": {
        "variaciones": [
            "que es esto", "que es eso", "que es", "identificar",
            "identifica", "que hay", "que veo", "que tengo",
            "que hay aqui", "que hay ahi", "dime que es",
            "que objeto es", "que cosa es",
        ],
        "con_argumento": False,
    },
    "buscar": {
        "variaciones": [
            "busca", "buscar", "buscame", "busca me", "encuentra",
            "encontrar", "donde esta", "donde esta el", "donde esta la",
        ],
        "con_argumento": True,
    },
    "repetir": {
        "variaciones": [
            "repetir", "repite", "repitelo", "otra vez", "de nuevo",
            "dilo otra vez", "que dijiste", "no escuche", "no te escuche",
        ],
        "con_argumento": False,
    },
    "resumir": {
        "variaciones": [
            "resume", "resumir", "resumelo", "resumen", "hazme un resumen",
            "dime el resumen",
        ],
        "con_argumento": False,
    },
    "pregunta": {
        "variaciones": [
            "pregunta", "preguntar",
        ],
        "con_argumento": True,
    },
    "historial": {
        "variaciones": [
            "historial", "que lei", "que he leido", "que identifique",
            "que he identificado", "ultimas cosas", "que he visto",
        ],
        "con_argumento": False,
    },
    "guardar": {
        "variaciones": [
            "guardar esto", "guardar", "guardalo", "guarda esto",
            "recuerda esto", "memorizar",
        ],
        "con_argumento": False,
    },
    "que_hay_guardado": {
        "variaciones": [
            "que hay guardado", "que tengo guardado", "mis objetos",
            "objetos guardados", "objetos personales", "que guarde",
            "que he guardado",
        ],
        "con_argumento": False,
    },
    "mas_rapido": {
        "variaciones": [
            "mas rapido", "mas rápido", "rapido", "acelera",
            "habla mas rapido", "mas veloz", "sube la velocidad",
        ],
        "con_argumento": False,
    },
    "mas_lento": {
        "variaciones": [
            "mas lento", "lento", "mas despacio", "despacio",
            "habla mas lento", "baja la velocidad", "mas pausado",
        ],
        "con_argumento": False,
    },
    "ayuda": {
        "variaciones": [
            "ayuda", "ayudame", "comandos", "que puedo decir",
            "que haces", "instrucciones", "como funciona",
            "que comandos hay",
        ],
        "con_argumento": False,
    },
    "detener": {
        "variaciones": [
            "detener", "deten", "detente", "para", "parar",
            "cancelar", "cancela", "stop", "alto",
        ],
        "con_argumento": False,
    },
    "salir": {
        "variaciones": [
            "salir", "cerrar", "apagar", "adios", "chao",
            "terminar", "bye", "hasta luego",
        ],
        "con_argumento": False,
    },
    "si": {
        "variaciones": [
            "si", "sí", "afirmativo", "correcto", "claro",
            "por supuesto", "dale", "ok", "okey", "esta bien",
            "asi es", "eso es",
        ],
        "con_argumento": False,
    },
    "no": {
        "variaciones": [
            "no", "negativo", "nel", "para nada", "no gracias",
            "nop", "nope",
        ],
        "con_argumento": False,
    },
}

# Texto de ayuda que se dice al usuario
TEXTO_AYUDA = (
    "Estos son los comandos que puedo entender. "
    "Di leer para que lea un texto frente a la cámara. "
    "Di qué es esto para identificar un objeto. "
    "Di busca y el nombre del objeto para buscarlo con la cámara. "
    "Di repetir para escuchar la última respuesta. "
    "Di resume para resumir lo último leído. "
    "Di pregunta y tu pregunta, para preguntar sobre lo que leí. "
    "Di historial para escuchar las últimas cosas que leí o identifiqué. "
    "Di guardar esto para recordar un objeto con tu nombre personal. "
    "Di qué hay guardado para escuchar tus objetos guardados. "
    "Di más rápido o más lento para ajustar mi velocidad. "
    "Di detener para salir del modo actual. "
    "Di salir para cerrar la aplicación."
)


def interpretar(texto: str) -> dict:
    """
    Interpreta un texto de voz y retorna un diccionario con:
    - "comando": nombre interno del comando (o None si no se reconoció)
    - "argumento": argumento extraído (para buscar, pregunta, etc.)
    - "texto_original": el texto tal como llegó
    - "confianza": qué tan segura es la coincidencia (0.0 a 1.0)
    """
    texto_original = texto
    texto_norm = _normalizar(texto)

    if not texto_norm:
        return {
            "comando": None,
            "argumento": None,
            "texto_original": texto_original,
            "confianza": 0.0,
        }

    mejor_comando = None
    mejor_confianza = 0.0
    mejor_argumento = None

    for nombre_cmd, datos in COMANDOS.items():
        for variacion in datos["variaciones"]:
            variacion_norm = _normalizar(variacion)
            confianza = _calcular_coincidencia(texto_norm, variacion_norm)

            if confianza > mejor_confianza:
                mejor_confianza = confianza
                mejor_comando = nombre_cmd

                # Extraer argumento si el comando lo espera
                if datos["con_argumento"]:
                    mejor_argumento = _extraer_argumento(
                        texto_norm, variacion_norm
                    )

    # Umbral mínimo de confianza para aceptar un comando
    if mejor_confianza < 0.5:
        return {
            "comando": None,
            "argumento": None,
            "texto_original": texto_original,
            "confianza": mejor_confianza,
        }

    resultado = {
        "comando": mejor_comando,
        "argumento": mejor_argumento,
        "texto_original": texto_original,
        "confianza": mejor_confianza,
    }
    logger.debug(
        "Comando interpretado: %s (confianza: %.2f, arg: %s)",
        mejor_comando, mejor_confianza, mejor_argumento,
    )
    return resultado


def _calcular_coincidencia(texto: str, variacion: str) -> float:
    """
    Calcula qué tan bien coincide el texto con una variación.
    Retorna un valor entre 0.0 y 1.0.
    """
    # Coincidencia exacta
    if texto == variacion:
        return 1.0

    # El texto empieza con la variación (ej: "busca el atún" empieza con "busca")
    if texto.startswith(variacion + " ") or texto.startswith(variacion):
        # Más confianza si la variación es más larga (más específica)
        ratio = len(variacion) / max(len(texto), 1)
        return max(0.7, ratio)

    # La variación está contenida en el texto
    if variacion in texto:
        ratio = len(variacion) / max(len(texto), 1)
        return max(0.5, ratio * 0.8)

    # El texto está contenido en la variación
    if texto in variacion:
        ratio = len(texto) / max(len(variacion), 1)
        return max(0.5, ratio * 0.8)

    # Comparar palabras individuales
    palabras_texto = set(texto.split())
    palabras_var = set(variacion.split())
    if palabras_var and palabras_var.issubset(palabras_texto):
        return 0.7
    if palabras_texto and palabras_texto.issubset(palabras_var):
        return 0.6

    # Coincidencia parcial de palabras
    if palabras_texto and palabras_var:
        comunes = palabras_texto & palabras_var
        if comunes:
            ratio = len(comunes) / max(len(palabras_var), 1)
            return ratio * 0.6

    return 0.0


def _extraer_argumento(texto: str, variacion: str) -> Optional[str]:
    """
    Extrae el argumento de un comando (ej: "busca el atún" → "atún").
    Quita artículos y preposiciones comunes.
    """
    # Quitar la variación del texto
    if texto.startswith(variacion):
        resto = texto[len(variacion):].strip()
    elif variacion in texto:
        idx = texto.index(variacion)
        resto = texto[idx + len(variacion):].strip()
    else:
        # Buscar la primera palabra de la variación y tomar lo que sigue
        primera = variacion.split()[0] if variacion.split() else ""
        if primera and primera in texto:
            idx = texto.index(primera)
            # Tomar desde después de la primera palabra
            palabras = texto[idx:].split()
            resto = " ".join(palabras[1:]) if len(palabras) > 1 else ""
        else:
            resto = texto

    # Quitar artículos, preposiciones y pronombres iniciales
    palabras_ruido = {"el", "la", "los", "las", "un", "una", "unos", "unas",
                      "del", "de", "al", "a", "mi", "mis", "me", "te", "se",
                      "lo", "le", "nos", "que", "como", "donde"}
    palabras = resto.split()
    while palabras and palabras[0] in palabras_ruido:
        palabras.pop(0)

    argumento = " ".join(palabras).strip()
    return argumento if argumento else None
