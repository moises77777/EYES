"""
database.py - Gestión de base de datos para EYES.
- SQLite local: siempre disponible, copia principal de trabajo.
- MySQL en la nube: respaldo en Hostinger, sincronización automática.
Todas las consultas usan parámetros (sin concatenar strings) para seguridad.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional

import config

logger = logging.getLogger("eyes")


# =============================================================
# SQLITE LOCAL
# =============================================================

def _obtener_conexion_sqlite() -> sqlite3.Connection:
    """Crea y retorna una conexión a SQLite local."""
    Path(config.SQLITE_RUTA).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.SQLITE_RUTA)
    conn.row_factory = sqlite3.Row  # Para acceder columnas por nombre
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def inicializar_sqlite() -> bool:
    """Crea las tablas en SQLite si no existen. Retorna True si tuvo éxito."""
    # Esquema adaptado para SQLite (sin AUTO_INCREMENT, usa AUTOINCREMENT)
    esquema_sqlite = """
    CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        velocidad_voz INTEGER NOT NULL DEFAULT 175,
        volumen REAL NOT NULL DEFAULT 1.0,
        fecha_registro TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        primer_uso_completado INTEGER NOT NULL DEFAULT 0,
        id_dispositivo TEXT
    );

    CREATE TABLE IF NOT EXISTS objetos_catalogo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clase_modelo TEXT NOT NULL UNIQUE,
        nombre_es TEXT NOT NULL,
        sinonimos TEXT,
        categoria TEXT NOT NULL DEFAULT 'otro',
        advertencia TEXT,
        activo INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS objetos_personales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER NOT NULL,
        nombre_personal TEXT NOT NULL,
        descripcion TEXT,
        clase_modelo TEXT,
        categoria TEXT NOT NULL DEFAULT 'otro',
        fecha_registro TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        sincronizado INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (id_usuario) REFERENCES usuario(id)
    );

    CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER NOT NULL,
        fecha_hora TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        modo TEXT NOT NULL,
        resultado TEXT,
        confianza REAL,
        uso_ia_nube INTEGER NOT NULL DEFAULT 0,
        sincronizado INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (id_usuario) REFERENCES usuario(id)
    );

    CREATE TABLE IF NOT EXISTS configuracion (
        id_usuario INTEGER NOT NULL,
        clave TEXT NOT NULL,
        valor TEXT,
        sincronizado INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (id_usuario, clave),
        FOREIGN KEY (id_usuario) REFERENCES usuario(id)
    );
    """
    try:
        conn = _obtener_conexion_sqlite()
        conn.executescript(esquema_sqlite)
        conn.close()
        logger.info("SQLite inicializado correctamente en: %s", config.SQLITE_RUTA)
        return True
    except Exception as e:
        logger.error("Error al inicializar SQLite: %s", e)
        return False


# =============================================================
# MYSQL EN LA NUBE
# =============================================================

def _obtener_conexion_mysql():
    """
    Crea y retorna una conexión a MySQL en la nube.
    Retorna None si no hay configuración o falla la conexión.
    """
    if not all([config.MYSQL_HOST, config.MYSQL_USER, config.MYSQL_PASSWORD]):
        return None
    try:
        import pymysql
        conn = pymysql.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5,
            read_timeout=10,
            write_timeout=10,
        )
        return conn
    except Exception as e:
        logger.warning("No se pudo conectar a MySQL: %s", e)
        return None


def inicializar_mysql() -> bool:
    """Crea las tablas en MySQL si no existen. Retorna True si tuvo éxito."""
    conn = _obtener_conexion_mysql()
    if conn is None:
        logger.warning("MySQL no disponible. Se trabajará solo con SQLite local.")
        return False
    try:
        # Sentencias directas en vez de leer schema.sql (evita problemas de parseo)
        tablas = [
            """CREATE TABLE IF NOT EXISTS usuario (
                id INT PRIMARY KEY AUTO_INCREMENT,
                nombre VARCHAR(100) NOT NULL,
                velocidad_voz INT NOT NULL DEFAULT 175,
                volumen FLOAT NOT NULL DEFAULT 1.0,
                fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                primer_uso_completado TINYINT NOT NULL DEFAULT 0,
                id_dispositivo VARCHAR(100)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS objetos_catalogo (
                id INT PRIMARY KEY AUTO_INCREMENT,
                clase_modelo VARCHAR(80) NOT NULL UNIQUE,
                nombre_es VARCHAR(100) NOT NULL,
                sinonimos TEXT,
                categoria VARCHAR(30) NOT NULL DEFAULT 'otro',
                advertencia TEXT,
                activo TINYINT NOT NULL DEFAULT 1
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS objetos_personales (
                id INT PRIMARY KEY AUTO_INCREMENT,
                id_usuario INT NOT NULL,
                nombre_personal VARCHAR(200) NOT NULL,
                descripcion TEXT,
                clase_modelo VARCHAR(80),
                categoria VARCHAR(30) NOT NULL DEFAULT 'otro',
                fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                sincronizado TINYINT NOT NULL DEFAULT 0,
                FOREIGN KEY (id_usuario) REFERENCES usuario(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS historial (
                id INT PRIMARY KEY AUTO_INCREMENT,
                id_usuario INT NOT NULL,
                fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                modo VARCHAR(30) NOT NULL,
                resultado TEXT,
                confianza FLOAT,
                uso_ia_nube TINYINT NOT NULL DEFAULT 0,
                sincronizado TINYINT NOT NULL DEFAULT 0,
                FOREIGN KEY (id_usuario) REFERENCES usuario(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS configuracion (
                id_usuario INT NOT NULL,
                clave VARCHAR(80) NOT NULL,
                valor TEXT,
                sincronizado TINYINT NOT NULL DEFAULT 0,
                PRIMARY KEY (id_usuario, clave),
                FOREIGN KEY (id_usuario) REFERENCES usuario(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        ]
        cursor = conn.cursor()
        for sql in tablas:
            cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("MySQL inicializado correctamente en: %s", config.MYSQL_HOST)
        return True
    except Exception as e:
        logger.error("Error al inicializar MySQL: %s", e)
        try:
            conn.close()
        except Exception:
            pass
        return False


def probar_conexion_mysql() -> bool:
    """Prueba la conexión a MySQL. Retorna True si funciona."""
    conn = _obtener_conexion_mysql()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True
    except Exception:
        return False


# =============================================================
# FUNCIONES DE DATOS - USUARIO
# =============================================================

def obtener_usuario() -> Optional[dict]:
    """Obtiene el primer usuario registrado (solo hay uno en este prototipo)."""
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute("SELECT * FROM usuario LIMIT 1")
        fila = cursor.fetchone()
        conn.close()
        if fila:
            return dict(fila)
        return None
    except Exception as e:
        logger.error("Error al obtener usuario: %s", e)
        return None


def crear_usuario(nombre: str, velocidad_voz: int = 175) -> Optional[int]:
    """Crea un nuevo usuario y retorna su ID."""
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "INSERT INTO usuario (nombre, velocidad_voz, primer_uso_completado) VALUES (?, ?, 1)",
            (nombre, velocidad_voz),
        )
        conn.commit()
        id_usuario = cursor.lastrowid
        conn.close()
        logger.info("Usuario creado: %s (ID: %d)", nombre, id_usuario)
        return id_usuario
    except Exception as e:
        logger.error("Error al crear usuario: %s", e)
        return None


def actualizar_velocidad_voz(id_usuario: int, velocidad: int) -> bool:
    """Actualiza la velocidad de voz del usuario."""
    try:
        conn = _obtener_conexion_sqlite()
        conn.execute(
            "UPDATE usuario SET velocidad_voz = ? WHERE id = ?",
            (velocidad, id_usuario),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error("Error al actualizar velocidad de voz: %s", e)
        return False


# =============================================================
# FUNCIONES DE DATOS - CATÁLOGO
# =============================================================

def obtener_catalogo() -> list[dict]:
    """Obtiene todos los objetos activos del catálogo."""
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "SELECT * FROM objetos_catalogo WHERE activo = 1"
        )
        filas = [dict(f) for f in cursor.fetchall()]
        conn.close()
        return filas
    except Exception as e:
        logger.error("Error al obtener catálogo: %s", e)
        return []


def buscar_en_catalogo(nombre: str) -> Optional[dict]:
    """
    Busca un objeto en el catálogo por nombre en español o sinónimos.
    Coincidencia flexible (parcial, insensible a mayúsculas).
    """
    nombre_lower = nombre.lower().strip()
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "SELECT * FROM objetos_catalogo WHERE activo = 1"
        )
        filas = cursor.fetchall()
        conn.close()

        for fila in filas:
            fila_dict = dict(fila)
            # Comparar con nombre en español
            if nombre_lower in fila_dict["nombre_es"].lower():
                return fila_dict
            # Comparar con sinónimos
            if fila_dict["sinonimos"]:
                for sinonimo in fila_dict["sinonimos"].split(","):
                    if nombre_lower in sinonimo.strip().lower():
                        return fila_dict
        return None
    except Exception as e:
        logger.error("Error al buscar en catálogo: %s", e)
        return None


def obtener_nombre_es_por_clase(clase_modelo: str) -> Optional[dict]:
    """Obtiene un objeto del catálogo por su clase de modelo."""
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "SELECT * FROM objetos_catalogo WHERE clase_modelo = ? AND activo = 1",
            (clase_modelo,),
        )
        fila = cursor.fetchone()
        conn.close()
        if fila:
            return dict(fila)
        return None
    except Exception as e:
        logger.error("Error al buscar clase en catálogo: %s", e)
        return None


def obtener_objetos_por_categoria(categoria: str) -> list[dict]:
    """Obtiene objetos del catálogo por categoría."""
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "SELECT * FROM objetos_catalogo WHERE categoria = ? AND activo = 1",
            (categoria,),
        )
        filas = [dict(f) for f in cursor.fetchall()]
        conn.close()
        return filas
    except Exception as e:
        logger.error("Error al buscar por categoría: %s", e)
        return []


# =============================================================
# FUNCIONES DE DATOS - OBJETOS PERSONALES
# =============================================================

def guardar_objeto_personal(
    id_usuario: int,
    nombre_personal: str,
    clase_modelo: str,
    categoria: str = "otro",
    descripcion: str = "",
) -> Optional[int]:
    """Guarda un objeto personal y retorna su ID."""
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            """INSERT INTO objetos_personales
               (id_usuario, nombre_personal, descripcion, clase_modelo, categoria, sincronizado)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (id_usuario, nombre_personal, descripcion, clase_modelo, categoria),
        )
        conn.commit()
        id_obj = cursor.lastrowid
        conn.close()
        logger.info("Objeto personal guardado: '%s' (ID: %d)", nombre_personal, id_obj)
        return id_obj
    except Exception as e:
        logger.error("Error al guardar objeto personal: %s", e)
        return None


def obtener_objetos_personales(id_usuario: int) -> list[dict]:
    """Obtiene todos los objetos personales del usuario."""
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "SELECT * FROM objetos_personales WHERE id_usuario = ?",
            (id_usuario,),
        )
        filas = [dict(f) for f in cursor.fetchall()]
        conn.close()
        return filas
    except Exception as e:
        logger.error("Error al obtener objetos personales: %s", e)
        return []


def buscar_objeto_personal(id_usuario: int, nombre: str) -> Optional[dict]:
    """Busca un objeto personal por nombre (coincidencia parcial)."""
    nombre_lower = nombre.lower().strip()
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "SELECT * FROM objetos_personales WHERE id_usuario = ?",
            (id_usuario,),
        )
        filas = cursor.fetchall()
        conn.close()

        for fila in filas:
            fila_dict = dict(fila)
            if nombre_lower in fila_dict["nombre_personal"].lower():
                return fila_dict
        return None
    except Exception as e:
        logger.error("Error al buscar objeto personal: %s", e)
        return None


# =============================================================
# FUNCIONES DE DATOS - HISTORIAL
# =============================================================

def guardar_historial(
    id_usuario: int,
    modo: str,
    resultado: str,
    confianza: float = 0.0,
    uso_ia_nube: bool = False,
) -> Optional[int]:
    """Guarda una entrada en el historial."""
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            """INSERT INTO historial
               (id_usuario, modo, resultado, confianza, uso_ia_nube, sincronizado)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (id_usuario, modo, resultado, confianza, 1 if uso_ia_nube else 0),
        )
        conn.commit()
        id_hist = cursor.lastrowid
        conn.close()
        return id_hist
    except Exception as e:
        logger.error("Error al guardar historial: %s", e)
        return None


def obtener_historial_reciente(id_usuario: int, limite: int = 5) -> list[dict]:
    """Obtiene las últimas N entradas del historial."""
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "SELECT * FROM historial WHERE id_usuario = ? ORDER BY fecha_hora DESC LIMIT ?",
            (id_usuario, limite),
        )
        filas = [dict(f) for f in cursor.fetchall()]
        conn.close()
        return filas
    except Exception as e:
        logger.error("Error al obtener historial: %s", e)
        return []


# =============================================================
# FUNCIONES DE DATOS - CONFIGURACIÓN
# =============================================================

def guardar_configuracion(id_usuario: int, clave: str, valor: str) -> bool:
    """Guarda o actualiza una clave de configuración."""
    try:
        conn = _obtener_conexion_sqlite()
        conn.execute(
            """INSERT INTO configuracion (id_usuario, clave, valor, sincronizado)
               VALUES (?, ?, ?, 0)
               ON CONFLICT(id_usuario, clave)
               DO UPDATE SET valor = excluded.valor, sincronizado = 0""",
            (id_usuario, clave, valor),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error("Error al guardar configuración: %s", e)
        return False


def obtener_configuracion(id_usuario: int, clave: str) -> Optional[str]:
    """Obtiene el valor de una clave de configuración."""
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "SELECT valor FROM configuracion WHERE id_usuario = ? AND clave = ?",
            (id_usuario, clave),
        )
        fila = cursor.fetchone()
        conn.close()
        if fila:
            return fila["valor"]
        return None
    except Exception as e:
        logger.error("Error al obtener configuración: %s", e)
        return None
