# database.py - Base de datos SQLite y MySQL

import logging
import sqlite3
from pathlib import Path
from typing import Optional

import config

logger = logging.getLogger("eyes")


def _obtener_conexion_sqlite():
    Path(config.SQLITE_RUTA).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.SQLITE_RUTA)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def inicializar_sqlite():
    esquema = """
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
        conn.executescript(esquema)
        conn.close()
        logger.info("SQLite inicializado correctamente en: %s", config.SQLITE_RUTA)
        return True
    except Exception as e:
        logger.error("Error al inicializar SQLite: %s", e)
        return False


def _obtener_conexion_mysql():
    if not config.MYSQL_HOST:
        return None
    try:
        import pymysql
        conn = pymysql.connect(
            host=config.MYSQL_HOST, port=config.MYSQL_PORT,
            user=config.MYSQL_USER, password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE, charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5, read_timeout=10, write_timeout=10,
        )
        return conn
    except Exception as e:
        logger.warning("No se pudo conectar a MySQL: %s", e)
        return None


def inicializar_mysql():
    conn = _obtener_conexion_mysql()
    if conn is None:
        return False
    try:
        tablas = [
            """CREATE TABLE IF NOT EXISTS usuario (
                id INT PRIMARY KEY AUTO_INCREMENT, nombre VARCHAR(100) NOT NULL,
                velocidad_voz INT NOT NULL DEFAULT 175, volumen FLOAT NOT NULL DEFAULT 1.0,
                fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                primer_uso_completado TINYINT NOT NULL DEFAULT 0, id_dispositivo VARCHAR(100)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS objetos_catalogo (
                id INT PRIMARY KEY AUTO_INCREMENT, clase_modelo VARCHAR(80) NOT NULL UNIQUE,
                nombre_es VARCHAR(100) NOT NULL, sinonimos TEXT,
                categoria VARCHAR(30) NOT NULL DEFAULT 'otro', advertencia TEXT,
                activo TINYINT NOT NULL DEFAULT 1
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS objetos_personales (
                id INT PRIMARY KEY AUTO_INCREMENT, id_usuario INT NOT NULL,
                nombre_personal VARCHAR(200) NOT NULL, descripcion TEXT,
                clase_modelo VARCHAR(80), categoria VARCHAR(30) NOT NULL DEFAULT 'otro',
                fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                sincronizado TINYINT NOT NULL DEFAULT 0,
                FOREIGN KEY (id_usuario) REFERENCES usuario(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS historial (
                id INT PRIMARY KEY AUTO_INCREMENT, id_usuario INT NOT NULL,
                fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                modo VARCHAR(30) NOT NULL, resultado TEXT, confianza FLOAT,
                uso_ia_nube TINYINT NOT NULL DEFAULT 0, sincronizado TINYINT NOT NULL DEFAULT 0,
                FOREIGN KEY (id_usuario) REFERENCES usuario(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS configuracion (
                id_usuario INT NOT NULL, clave VARCHAR(80) NOT NULL, valor TEXT,
                sincronizado TINYINT NOT NULL DEFAULT 0,
                PRIMARY KEY (id_usuario, clave), FOREIGN KEY (id_usuario) REFERENCES usuario(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        ]
        cursor = conn.cursor()
        for sql in tablas:
            cursor.execute(sql)
        conn.commit(); cursor.close(); conn.close()
        return True
    except Exception as e:
        logger.error("Error al inicializar MySQL: %s", e)
        try: conn.close()
        except: pass
        return False


def probar_conexion_mysql():
    conn = _obtener_conexion_mysql()
    if conn is None:
        return False
    try:
        conn.cursor().execute("SELECT 1"); conn.close()
        return True
    except:
        return False


# --- Usuario ---

def obtener_usuario():
    try:
        conn = _obtener_conexion_sqlite()
        fila = conn.execute("SELECT * FROM usuario LIMIT 1").fetchone()
        conn.close()
        return dict(fila) if fila else None
    except Exception as e:
        logger.error("Error al obtener usuario: %s", e)
        return None


def crear_usuario(nombre, velocidad_voz=175):
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "INSERT INTO usuario (nombre, velocidad_voz, primer_uso_completado) VALUES (?, ?, 1)",
            (nombre, velocidad_voz))
        conn.commit()
        id_usuario = cursor.lastrowid
        conn.close()
        logger.info("Usuario creado: %s (ID: %d)", nombre, id_usuario)
        return id_usuario
    except Exception as e:
        logger.error("Error al crear usuario: %s", e)
        return None


def actualizar_velocidad_voz(id_usuario, velocidad):
    try:
        conn = _obtener_conexion_sqlite()
        conn.execute("UPDATE usuario SET velocidad_voz = ? WHERE id = ?", (velocidad, id_usuario))
        conn.commit(); conn.close()
        return True
    except Exception as e:
        logger.error("Error al actualizar velocidad: %s", e)
        return False


# --- Catalogo ---

def obtener_catalogo():
    try:
        conn = _obtener_conexion_sqlite()
        filas = [dict(f) for f in conn.execute("SELECT * FROM objetos_catalogo WHERE activo = 1").fetchall()]
        conn.close()
        return filas
    except Exception as e:
        logger.error("Error al obtener catalogo: %s", e)
        return []


def buscar_en_catalogo(nombre):
    nombre_lower = nombre.lower().strip()
    try:
        conn = _obtener_conexion_sqlite()
        filas = conn.execute("SELECT * FROM objetos_catalogo WHERE activo = 1").fetchall()
        conn.close()
        for fila in filas:
            f = dict(fila)
            if nombre_lower in f["nombre_es"].lower():
                return f
            if f["sinonimos"]:
                for s in f["sinonimos"].split(","):
                    if nombre_lower in s.strip().lower():
                        return f
        return None
    except Exception as e:
        logger.error("Error al buscar en catalogo: %s", e)
        return None


def obtener_nombre_es_por_clase(clase_modelo):
    try:
        conn = _obtener_conexion_sqlite()
        fila = conn.execute(
            "SELECT * FROM objetos_catalogo WHERE clase_modelo = ? AND activo = 1",
            (clase_modelo,)).fetchone()
        conn.close()
        return dict(fila) if fila else None
    except Exception as e:
        logger.error("Error al buscar clase: %s", e)
        return None


def obtener_objetos_por_categoria(categoria):
    try:
        conn = _obtener_conexion_sqlite()
        filas = [dict(f) for f in conn.execute(
            "SELECT * FROM objetos_catalogo WHERE categoria = ? AND activo = 1",
            (categoria,)).fetchall()]
        conn.close()
        return filas
    except Exception as e:
        logger.error("Error al buscar por categoria: %s", e)
        return []


# --- Objetos personales ---

def guardar_objeto_personal(id_usuario, nombre_personal, clase_modelo, categoria="otro", descripcion=""):
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "INSERT INTO objetos_personales (id_usuario, nombre_personal, descripcion, clase_modelo, categoria, sincronizado) VALUES (?, ?, ?, ?, ?, 0)",
            (id_usuario, nombre_personal, descripcion, clase_modelo, categoria))
        conn.commit()
        id_obj = cursor.lastrowid
        conn.close()
        logger.info("Objeto personal guardado: '%s' (ID: %d)", nombre_personal, id_obj)
        return id_obj
    except Exception as e:
        logger.error("Error al guardar objeto personal: %s", e)
        return None


def obtener_objetos_personales(id_usuario):
    try:
        conn = _obtener_conexion_sqlite()
        filas = [dict(f) for f in conn.execute(
            "SELECT * FROM objetos_personales WHERE id_usuario = ?", (id_usuario,)).fetchall()]
        conn.close()
        return filas
    except Exception as e:
        logger.error("Error al obtener objetos personales: %s", e)
        return []


def buscar_objeto_personal(id_usuario, nombre):
    nombre_lower = nombre.lower().strip()
    try:
        conn = _obtener_conexion_sqlite()
        filas = conn.execute(
            "SELECT * FROM objetos_personales WHERE id_usuario = ?", (id_usuario,)).fetchall()
        conn.close()
        for fila in filas:
            f = dict(fila)
            if nombre_lower in f["nombre_personal"].lower():
                return f
        return None
    except Exception as e:
        logger.error("Error al buscar objeto personal: %s", e)
        return None


# --- Historial ---

def guardar_historial(id_usuario, modo, resultado, confianza=0.0, uso_ia_nube=False):
    try:
        conn = _obtener_conexion_sqlite()
        cursor = conn.execute(
            "INSERT INTO historial (id_usuario, modo, resultado, confianza, uso_ia_nube, sincronizado) VALUES (?, ?, ?, ?, ?, 0)",
            (id_usuario, modo, resultado, confianza, 1 if uso_ia_nube else 0))
        conn.commit()
        id_hist = cursor.lastrowid
        conn.close()
        return id_hist
    except Exception as e:
        logger.error("Error al guardar historial: %s", e)
        return None


def obtener_historial_reciente(id_usuario, limite=5):
    try:
        conn = _obtener_conexion_sqlite()
        filas = [dict(f) for f in conn.execute(
            "SELECT * FROM historial WHERE id_usuario = ? ORDER BY fecha_hora DESC LIMIT ?",
            (id_usuario, limite)).fetchall()]
        conn.close()
        return filas
    except Exception as e:
        logger.error("Error al obtener historial: %s", e)
        return []


# --- Configuracion ---

def guardar_configuracion(id_usuario, clave, valor):
    try:
        conn = _obtener_conexion_sqlite()
        conn.execute(
            "INSERT INTO configuracion (id_usuario, clave, valor, sincronizado) VALUES (?, ?, ?, 0) ON CONFLICT(id_usuario, clave) DO UPDATE SET valor = excluded.valor, sincronizado = 0",
            (id_usuario, clave, valor))
        conn.commit(); conn.close()
        return True
    except Exception as e:
        logger.error("Error al guardar configuracion: %s", e)
        return False


def obtener_configuracion(id_usuario, clave):
    try:
        conn = _obtener_conexion_sqlite()
        fila = conn.execute(
            "SELECT valor FROM configuracion WHERE id_usuario = ? AND clave = ?",
            (id_usuario, clave)).fetchone()
        conn.close()
        return fila["valor"] if fila else None
    except Exception as e:
        logger.error("Error al obtener configuracion: %s", e)
        return None
