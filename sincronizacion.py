# sincronizacion.py - Sincronizacion SQLite <-> MySQL

import logging
import sqlite3
import threading

import config

logger = logging.getLogger("eyes")

_detener = threading.Event()


def _obtener_conexion_sqlite():
    conn = sqlite3.connect(config.SQLITE_RUTA)
    conn.row_factory = sqlite3.Row
    return conn


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
            connect_timeout=5, read_timeout=10, write_timeout=10)
        return conn
    except Exception as e:
        logger.warning("Sync: no se pudo conectar a MySQL: %s", e)
        return None


def _mysql_disponible():
    conn = _obtener_conexion_mysql()
    if conn is None:
        return False
    try: conn.close()
    except: pass
    return True


def _sincronizar_tabla(tabla, columnas, tiene_sincronizado=True):
    if not tiene_sincronizado:
        return
    sqlite_conn = None
    mysql_conn = None
    try:
        sqlite_conn = _obtener_conexion_sqlite()
        mysql_conn = _obtener_conexion_mysql()
        if mysql_conn is None:
            return
        filas = sqlite_conn.execute(
            f"SELECT * FROM {tabla} WHERE sincronizado = 0 LIMIT ?",
            (config.SYNC_LOTE_MAXIMO,)).fetchall()
        if not filas:
            return
        cursor_mysql = mysql_conn.cursor()
        ids_ok = []
        for fila in filas:
            f = dict(fila)
            fila_id = f.get("id") or f.get("id_usuario")
            cols = [c for c in columnas if c in f]
            valores = [f[c] for c in cols]
            placeholders = ", ".join(["%s"] * len(cols))
            cols_str = ", ".join(cols)
            update_str = ", ".join([f"{c} = VALUES({c})" for c in cols if c != "id"])
            sql = f"INSERT INTO {tabla} ({cols_str}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_str}"
            try:
                cursor_mysql.execute(sql, valores)
                ids_ok.append(fila_id)
            except Exception as e:
                logger.warning("Error sync fila %s de %s: %s", fila_id, tabla, e)
        mysql_conn.commit()
        cursor_mysql.close()
        if ids_ok:
            if tabla == "configuracion":
                for fila in filas:
                    f = dict(fila)
                    sqlite_conn.execute(
                        "UPDATE configuracion SET sincronizado = 1 WHERE id_usuario = ? AND clave = ?",
                        (f["id_usuario"], f["clave"]))
            else:
                ph = ", ".join(["?"] * len(ids_ok))
                sqlite_conn.execute(f"UPDATE {tabla} SET sincronizado = 1 WHERE id IN ({ph})", ids_ok)
            sqlite_conn.commit()
    except Exception as e:
        logger.warning("Error sync %s: %s", tabla, e)
    finally:
        if sqlite_conn:
            try: sqlite_conn.close()
            except: pass
        if mysql_conn:
            try: mysql_conn.close()
            except: pass


def _sincronizar_usuario():
    sqlite_conn = None
    mysql_conn = None
    try:
        sqlite_conn = _obtener_conexion_sqlite()
        usuario = sqlite_conn.execute("SELECT * FROM usuario LIMIT 1").fetchone()
        if not usuario:
            return
        mysql_conn = _obtener_conexion_mysql()
        if mysql_conn is None:
            return
        u = dict(usuario)
        cursor = mysql_conn.cursor()
        cursor.execute(
            "INSERT INTO usuario (id, nombre, velocidad_voz, volumen, fecha_registro, primer_uso_completado, id_dispositivo) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre), velocidad_voz=VALUES(velocidad_voz), volumen=VALUES(volumen)",
            (u["id"], u["nombre"], u["velocidad_voz"], u["volumen"],
             u["fecha_registro"], u["primer_uso_completado"], u.get("id_dispositivo")))
        mysql_conn.commit()
        cursor.close()
    except Exception as e:
        logger.warning("Error sync usuario: %s", e)
    finally:
        if sqlite_conn:
            try: sqlite_conn.close()
            except: pass
        if mysql_conn:
            try: mysql_conn.close()
            except: pass


def _descargar_catalogo():
    mysql_conn = None
    sqlite_conn = None
    try:
        mysql_conn = _obtener_conexion_mysql()
        if mysql_conn is None:
            return
        cursor = mysql_conn.cursor()
        cursor.execute("SELECT * FROM objetos_catalogo WHERE activo = 1")
        filas = cursor.fetchall()
        cursor.close()
        if not filas:
            return
        sqlite_conn = _obtener_conexion_sqlite()
        for f in filas:
            sqlite_conn.execute(
                "INSERT INTO objetos_catalogo (id, clase_modelo, nombre_es, sinonimos, categoria, advertencia, activo) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(clase_modelo) DO UPDATE SET "
                "nombre_es=excluded.nombre_es, sinonimos=excluded.sinonimos, categoria=excluded.categoria, "
                "advertencia=excluded.advertencia, activo=excluded.activo",
                (f["id"], f["clase_modelo"], f["nombre_es"], f["sinonimos"],
                 f["categoria"], f["advertencia"], f["activo"]))
        sqlite_conn.commit()
        logger.info("Catalogo descargado: %d objetos", len(filas))
    except Exception as e:
        logger.warning("Error descarga catalogo: %s", e)
    finally:
        if mysql_conn:
            try: mysql_conn.close()
            except: pass
        if sqlite_conn:
            try: sqlite_conn.close()
            except: pass


def sincronizar_al_inicio():
    if not _mysql_disponible():
        logger.info("MySQL no disponible al iniciar. Se trabajara solo con datos locales.")
        return
    logger.info("MySQL disponible. Descargando datos...")
    _descargar_catalogo()


def _hilo_sincronizacion():
    logger.info("Hilo de sincronizacion iniciado.")
    while not _detener.is_set():
        _detener.wait(config.SYNC_INTERVALO_SEGUNDOS)
        if _detener.is_set():
            break
        if not _mysql_disponible():
            continue
        _sincronizar_usuario()
        _sincronizar_tabla("historial",
            ["id", "id_usuario", "fecha_hora", "modo", "resultado", "confianza", "uso_ia_nube", "sincronizado"])
        _sincronizar_tabla("objetos_personales",
            ["id", "id_usuario", "nombre_personal", "descripcion", "clase_modelo", "categoria", "fecha_registro", "sincronizado"])
        _sincronizar_tabla("configuracion",
            ["id_usuario", "clave", "valor", "sincronizado"])
    logger.info("Hilo de sincronizacion detenido.")


def iniciar_sincronizacion():
    _detener.clear()
    hilo = threading.Thread(target=_hilo_sincronizacion, daemon=True, name="sync")
    hilo.start()
    return hilo


def detener_sincronizacion():
    _detener.set()
    logger.info("Senal de detencion enviada al hilo de sincronizacion.")


def pendientes_por_sincronizar():
    total = 0
    try:
        conn = _obtener_conexion_sqlite()
        for tabla in ["historial", "objetos_personales", "configuracion"]:
            fila = conn.execute(f"SELECT COUNT(*) as n FROM {tabla} WHERE sincronizado = 0").fetchone()
            if fila:
                total += fila["n"]
        conn.close()
    except Exception as e:
        logger.warning("Error contando pendientes: %s", e)
    return total
