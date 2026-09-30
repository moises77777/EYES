"""
sincronizacion.py - Sincronización entre SQLite local y MySQL en la nube.
Todo se guarda primero en local. Un hilo aparte sube registros pendientes
cuando hay internet. Sin internet, la app sigue normal y sincroniza después.
"""

import logging
import sqlite3
import threading
import time
from typing import Optional

import config
from modulos.conexion import hay_internet

logger = logging.getLogger("eyes")

# Bandera para detener el hilo de sincronización
_detener = threading.Event()


def _obtener_conexion_sqlite() -> sqlite3.Connection:
    """Conexión a SQLite para el hilo de sincronización."""
    conn = sqlite3.connect(config.SQLITE_RUTA)
    conn.row_factory = sqlite3.Row
    return conn


def _obtener_conexion_mysql():
    """Conexión a MySQL. Retorna None si no hay configuración o falla."""
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
        logger.warning("Sincronización: no se pudo conectar a MySQL: %s", e)
        return None


def _sincronizar_tabla(tabla: str, columnas: list[str], tiene_sincronizado: bool = True):
    """
    Sincroniza una tabla de SQLite a MySQL.
    Solo sube registros donde sincronizado = 0.
    """
    if not tiene_sincronizado:
        return

    sqlite_conn = None
    mysql_conn = None
    try:
        sqlite_conn = _obtener_conexion_sqlite()
        mysql_conn = _obtener_conexion_mysql()
        if mysql_conn is None:
            return

        # Obtener registros pendientes de sincronizar
        cursor_sqlite = sqlite_conn.execute(
            f"SELECT * FROM {tabla} WHERE sincronizado = 0 LIMIT ?",
            (config.SYNC_LOTE_MAXIMO,),
        )
        filas = cursor_sqlite.fetchall()

        if not filas:
            return

        cursor_mysql = mysql_conn.cursor()
        ids_sincronizados = []

        for fila in filas:
            fila_dict = dict(fila)
            fila_id = fila_dict.get("id") or fila_dict.get("id_usuario")

            # Construir la sentencia INSERT ... ON DUPLICATE KEY UPDATE
            cols = [c for c in columnas if c in fila_dict]
            valores = [fila_dict[c] for c in cols]
            placeholders = ", ".join(["%s"] * len(cols))
            cols_str = ", ".join(cols)
            update_str = ", ".join([f"{c} = VALUES({c})" for c in cols if c != "id"])

            sql = f"""INSERT INTO {tabla} ({cols_str}) VALUES ({placeholders})
                      ON DUPLICATE KEY UPDATE {update_str}"""

            try:
                cursor_mysql.execute(sql, valores)
                ids_sincronizados.append(fila_id)
            except Exception as e:
                logger.warning("Error sincronizando fila %s de %s: %s", fila_id, tabla, e)

        mysql_conn.commit()
        cursor_mysql.close()

        # Marcar como sincronizados en SQLite
        if ids_sincronizados:
            # Para tablas con clave compuesta (configuracion), manejar diferente
            if tabla == "configuracion":
                for fila in filas:
                    fila_dict = dict(fila)
                    sqlite_conn.execute(
                        "UPDATE configuracion SET sincronizado = 1 WHERE id_usuario = ? AND clave = ?",
                        (fila_dict["id_usuario"], fila_dict["clave"]),
                    )
            else:
                placeholders_ids = ", ".join(["?"] * len(ids_sincronizados))
                sqlite_conn.execute(
                    f"UPDATE {tabla} SET sincronizado = 1 WHERE id IN ({placeholders_ids})",
                    ids_sincronizados,
                )
            sqlite_conn.commit()
            logger.debug("Sincronizados %d registros de %s", len(ids_sincronizados), tabla)

    except Exception as e:
        logger.warning("Error en sincronización de %s: %s", tabla, e)
    finally:
        if sqlite_conn:
            try:
                sqlite_conn.close()
            except Exception:
                pass
        if mysql_conn:
            try:
                mysql_conn.close()
            except Exception:
                pass


def _descargar_catalogo_desde_nube():
    """
    Descarga el catálogo de objetos desde MySQL a SQLite.
    Se ejecuta al inicio si hay internet para tener el catálogo actualizado.
    """
    mysql_conn = None
    sqlite_conn = None
    try:
        mysql_conn = _obtener_conexion_mysql()
        if mysql_conn is None:
            return

        cursor_mysql = mysql_conn.cursor()
        cursor_mysql.execute("SELECT * FROM objetos_catalogo WHERE activo = 1")
        filas = cursor_mysql.fetchall()
        cursor_mysql.close()

        if not filas:
            return

        sqlite_conn = _obtener_conexion_sqlite()
        for fila in filas:
            sqlite_conn.execute(
                """INSERT INTO objetos_catalogo
                   (id, clase_modelo, nombre_es, sinonimos, categoria, advertencia, activo)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(clase_modelo) DO UPDATE SET
                   nombre_es = excluded.nombre_es,
                   sinonimos = excluded.sinonimos,
                   categoria = excluded.categoria,
                   advertencia = excluded.advertencia,
                   activo = excluded.activo""",
                (
                    fila["id"], fila["clase_modelo"], fila["nombre_es"],
                    fila["sinonimos"], fila["categoria"],
                    fila["advertencia"], fila["activo"],
                ),
            )
        sqlite_conn.commit()
        logger.info("Catálogo descargado de la nube: %d objetos", len(filas))

    except Exception as e:
        logger.warning("Error al descargar catálogo desde la nube: %s", e)
    finally:
        if mysql_conn:
            try:
                mysql_conn.close()
            except Exception:
                pass
        if sqlite_conn:
            try:
                sqlite_conn.close()
            except Exception:
                pass


def _descargar_usuario_desde_nube():
    """Descarga usuario y configuración desde MySQL si existen."""
    mysql_conn = None
    sqlite_conn = None
    try:
        mysql_conn = _obtener_conexion_mysql()
        if mysql_conn is None:
            return

        cursor_mysql = mysql_conn.cursor()

        # Descargar usuario
        cursor_mysql.execute("SELECT * FROM usuario LIMIT 1")
        usuario = cursor_mysql.fetchone()
        if usuario:
            sqlite_conn = _obtener_conexion_sqlite()
            sqlite_conn.execute(
                """INSERT INTO usuario (id, nombre, velocidad_voz, volumen,
                   fecha_registro, primer_uso_completado, id_dispositivo)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                   nombre = excluded.nombre,
                   velocidad_voz = excluded.velocidad_voz,
                   volumen = excluded.volumen""",
                (
                    usuario["id"], usuario["nombre"], usuario["velocidad_voz"],
                    usuario["volumen"], usuario["fecha_registro"],
                    usuario["primer_uso_completado"], usuario["id_dispositivo"],
                ),
            )
            sqlite_conn.commit()
            logger.info("Usuario descargado de la nube: %s", usuario["nombre"])

            # Descargar configuración
            cursor_mysql.execute(
                "SELECT * FROM configuracion WHERE id_usuario = %s",
                (usuario["id"],),
            )
            configs = cursor_mysql.fetchall()
            for cfg in configs:
                sqlite_conn.execute(
                    """INSERT INTO configuracion (id_usuario, clave, valor, sincronizado)
                       VALUES (?, ?, ?, 1)
                       ON CONFLICT(id_usuario, clave)
                       DO UPDATE SET valor = excluded.valor, sincronizado = 1""",
                    (cfg["id_usuario"], cfg["clave"], cfg["valor"]),
                )
            sqlite_conn.commit()

            # Descargar objetos personales
            cursor_mysql.execute(
                "SELECT * FROM objetos_personales WHERE id_usuario = %s",
                (usuario["id"],),
            )
            personales = cursor_mysql.fetchall()
            for obj in personales:
                sqlite_conn.execute(
                    """INSERT INTO objetos_personales
                       (id, id_usuario, nombre_personal, descripcion, clase_modelo,
                        categoria, fecha_registro, sincronizado)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                       ON CONFLICT(id) DO UPDATE SET
                       nombre_personal = excluded.nombre_personal,
                       descripcion = excluded.descripcion,
                       sincronizado = 1""",
                    (
                        obj["id"], obj["id_usuario"], obj["nombre_personal"],
                        obj["descripcion"], obj["clase_modelo"],
                        obj["categoria"], obj["fecha_registro"],
                    ),
                )
            sqlite_conn.commit()
            logger.info("Objetos personales descargados: %d", len(personales))

        cursor_mysql.close()

    except Exception as e:
        logger.warning("Error al descargar usuario desde la nube: %s", e)
    finally:
        if mysql_conn:
            try:
                mysql_conn.close()
            except Exception:
                pass
        if sqlite_conn:
            try:
                sqlite_conn.close()
            except Exception:
                pass


def _sincronizar_usuario():
    """Sube el usuario local a MySQL (necesario antes de historial y demás FK)."""
    sqlite_conn = None
    mysql_conn = None
    try:
        sqlite_conn = _obtener_conexion_sqlite()
        cursor = sqlite_conn.execute("SELECT * FROM usuario LIMIT 1")
        usuario = cursor.fetchone()
        if not usuario:
            return

        mysql_conn = _obtener_conexion_mysql()
        if mysql_conn is None:
            return

        u = dict(usuario)
        cursor_mysql = mysql_conn.cursor()
        cursor_mysql.execute(
            """INSERT INTO usuario (id, nombre, velocidad_voz, volumen,
               fecha_registro, primer_uso_completado, id_dispositivo)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
               nombre = VALUES(nombre),
               velocidad_voz = VALUES(velocidad_voz),
               volumen = VALUES(volumen)""",
            (u["id"], u["nombre"], u["velocidad_voz"], u["volumen"],
             u["fecha_registro"], u["primer_uso_completado"], u.get("id_dispositivo")),
        )
        mysql_conn.commit()
        cursor_mysql.close()
        logger.debug("Usuario sincronizado a la nube: %s", u["nombre"])
    except Exception as e:
        logger.warning("Error al sincronizar usuario: %s", e)
    finally:
        if sqlite_conn:
            try:
                sqlite_conn.close()
            except Exception:
                pass
        if mysql_conn:
            try:
                mysql_conn.close()
            except Exception:
                pass


def sincronizar_al_inicio():
    """
    Sincronización al arrancar la app:
    - Si hay internet, descarga datos de la nube al local.
    """
    if not hay_internet():
        logger.info("Sin internet al iniciar. Se trabajará solo con datos locales.")
        return

    logger.info("Internet disponible. Descargando datos de la nube...")
    _descargar_usuario_desde_nube()
    _descargar_catalogo_desde_nube()


def _hilo_sincronizacion():
    """Hilo que sincroniza periódicamente datos locales a la nube."""
    logger.info("Hilo de sincronización iniciado.")
    while not _detener.is_set():
        # Esperar el intervalo configurado
        _detener.wait(config.SYNC_INTERVALO_SEGUNDOS)
        if _detener.is_set():
            break

        if not hay_internet():
            continue

        # Sincronizar usuario PRIMERO (las demás tablas tienen FK a usuario)
        _sincronizar_usuario()

        # Sincronizar tablas que tienen campo "sincronizado"
        _sincronizar_tabla(
            "historial",
            ["id", "id_usuario", "fecha_hora", "modo", "resultado",
             "confianza", "uso_ia_nube", "sincronizado"],
        )
        _sincronizar_tabla(
            "objetos_personales",
            ["id", "id_usuario", "nombre_personal", "descripcion",
             "clase_modelo", "categoria", "fecha_registro", "sincronizado"],
        )
        _sincronizar_tabla(
            "configuracion",
            ["id_usuario", "clave", "valor", "sincronizado"],
        )

    logger.info("Hilo de sincronización detenido.")


def iniciar_sincronizacion() -> Optional[threading.Thread]:
    """Inicia el hilo de sincronización en segundo plano."""
    _detener.clear()
    hilo = threading.Thread(target=_hilo_sincronizacion, daemon=True, name="sync")
    hilo.start()
    return hilo


def detener_sincronizacion():
    """Detiene el hilo de sincronización."""
    _detener.set()
    logger.info("Señal de detención enviada al hilo de sincronización.")


def pendientes_por_sincronizar() -> int:
    """Cuenta cuántos registros locales faltan por sincronizar."""
    total = 0
    try:
        conn = _obtener_conexion_sqlite()
        for tabla in ["historial", "objetos_personales", "configuracion"]:
            cursor = conn.execute(
                f"SELECT COUNT(*) as n FROM {tabla} WHERE sincronizado = 0"
            )
            fila = cursor.fetchone()
            if fila:
                total += fila["n"]
        conn.close()
    except Exception as e:
        logger.warning("Error al contar pendientes: %s", e)
    return total
