# comandos.py - Interprete de comandos de voz

import logging
import unicodedata

logger = logging.getLogger("eyes")


def _normalizar(texto):
    texto = texto.lower().strip()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    texto = "".join(c if c.isalnum() or c.isspace() else " " for c in texto)
    return " ".join(texto.split())


COMANDOS = {
    "identificar": {
        "variaciones": [
            "que es esto", "que es eso", "que es", "identificar",
            "identifica", "que hay", "que tengo", "dime que es",
            "es esto",
        ],
        "con_argumento": False,
    },
    "repetir": {
        "variaciones": [
            "repetir", "repite", "otra vez", "de nuevo",
            "que dijiste", "no escuche",
        ],
        "con_argumento": False,
    },
    "historial": {
        "variaciones": [
            "historial", "que identifique", "ultimas cosas", "que he visto",
        ],
        "con_argumento": False,
    },
    "guardar": {
        "variaciones": [
            "guardar esto", "guardar", "guardalo", "guarda esto",
            "recuerda esto",
        ],
        "con_argumento": False,
    },
    "que_hay_guardado": {
        "variaciones": [
            "que hay guardado", "que tengo guardado", "mis objetos",
            "objetos guardados",
        ],
        "con_argumento": False,
    },
    "mas_rapido": {
        "variaciones": [
            "mas rapido", "rapido", "acelera", "habla mas rapido",
        ],
        "con_argumento": False,
    },
    "mas_lento": {
        "variaciones": [
            "mas lento", "lento", "mas despacio", "despacio",
            "habla mas lento",
        ],
        "con_argumento": False,
    },
    "ayuda": {
        "variaciones": [
            "ayuda", "ayudame", "comandos", "que puedo decir",
        ],
        "con_argumento": False,
    },
    "detener": {
        "variaciones": [
            "detener", "deten", "detente", "para", "parar",
            "cancelar", "stop", "alto",
        ],
        "con_argumento": False,
    },
    "salir": {
        "variaciones": [
            "salir", "cerrar", "apagar", "adios", "terminar",
        ],
        "con_argumento": False,
    },
    "si": {
        "variaciones": [
            "si", "correcto", "claro", "dale", "ok", "esta bien",
        ],
        "con_argumento": False,
    },
    "no": {
        "variaciones": [
            "no", "negativo", "no gracias",
        ],
        "con_argumento": False,
    },
}

TEXTO_AYUDA = (
    "Di que es esto para identificar un objeto. "
    "Di guardar esto para recordar un objeto. "
    "Di que hay guardado para tus objetos. "
    "Di historial para las ultimas identificaciones. "
    "Di mas rapido o mas lento para la velocidad. "
    "Di detener para salir del modo actual. "
    "Di salir para cerrar."
)


def interpretar(texto):
    texto_norm = _normalizar(texto)
    if not texto_norm:
        return {"comando": None, "argumento": None, "texto_original": texto, "confianza": 0.0}

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
                if datos["con_argumento"]:
                    mejor_argumento = _extraer_argumento(texto_norm, variacion_norm)

    if mejor_confianza < 0.5:
        return {"comando": None, "argumento": None, "texto_original": texto, "confianza": mejor_confianza}

    return {"comando": mejor_comando, "argumento": mejor_argumento,
            "texto_original": texto, "confianza": mejor_confianza}


def _calcular_coincidencia(texto, variacion):
    if texto == variacion:
        return 1.0
    if texto.startswith(variacion + " ") or texto.startswith(variacion):
        return max(0.7, len(variacion) / max(len(texto), 1))
    if variacion in texto:
        return max(0.5, (len(variacion) / max(len(texto), 1)) * 0.8)
    if texto in variacion:
        return max(0.5, (len(texto) / max(len(variacion), 1)) * 0.8)
    palabras_texto = set(texto.split())
    palabras_var = set(variacion.split())
    if palabras_var and palabras_var.issubset(palabras_texto):
        return 0.7
    if palabras_texto and palabras_texto.issubset(palabras_var):
        return 0.6
    if palabras_texto and palabras_var:
        comunes = palabras_texto & palabras_var
        if comunes:
            return (len(comunes) / max(len(palabras_var), 1)) * 0.6
    return 0.0


def _extraer_argumento(texto, variacion):
    if texto.startswith(variacion):
        resto = texto[len(variacion):].strip()
    elif variacion in texto:
        idx = texto.index(variacion)
        resto = texto[idx + len(variacion):].strip()
    else:
        primera = variacion.split()[0] if variacion.split() else ""
        if primera and primera in texto:
            palabras = texto[texto.index(primera):].split()
            resto = " ".join(palabras[1:]) if len(palabras) > 1 else ""
        else:
            resto = texto
    palabras_ruido = {"el", "la", "los", "las", "un", "una", "del", "de", "al", "a", "mi", "me"}
    palabras = resto.split()
    while palabras and palabras[0] in palabras_ruido:
        palabras.pop(0)
    argumento = " ".join(palabras).strip()
    return argumento if argumento else None
