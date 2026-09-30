"""
seed.py - Llena la tabla objetos_catalogo con las clases de COCO
útiles en el hogar, traducidas al español, con sinónimos,
categoría y advertencias.

Ejecutar: python seed.py
"""

import logging
import sqlite3
from pathlib import Path

import config

logger = logging.getLogger("eyes")

# =============================================================
# CATÁLOGO DE OBJETOS
# Formato: (clase_modelo, nombre_es, sinonimos, categoria, advertencia)
# clase_modelo = nombre exacto en el modelo YOLO (COCO)
# =============================================================
CATALOGO = [
    # --- Personas ---
    ("person", "persona", "persona,gente,alguien,humano", "otro", None),

    # --- Alimentos ---
    ("bottle", "botella", "botella,frasco,envase,agua,refresco,jugo", "alimento", None),
    ("wine glass", "copa de vino", "copa,vaso de vino", "alimento", None),
    ("cup", "taza", "taza,vaso,pocillo", "alimento", None),
    ("fork", "tenedor", "tenedor,cubierto", "otro", None),
    ("knife", "cuchillo", "cuchillo,navaja", "otro", "Cuidado: objeto cortante."),
    ("spoon", "cuchara", "cuchara,cucharón", "otro", None),
    ("bowl", "tazón", "tazón,plato hondo,bowl,cuenco", "alimento", None),
    ("banana", "plátano", "plátano,banana,guineo", "alimento", None),
    ("apple", "manzana", "manzana", "alimento", None),
    ("sandwich", "sándwich", "sándwich,torta,emparedado", "alimento", None),
    ("orange", "naranja", "naranja,mandarina", "alimento", None),
    ("broccoli", "brócoli", "brócoli,brocolí", "alimento", None),
    ("carrot", "zanahoria", "zanahoria", "alimento", None),
    ("hot dog", "hot dog", "hot dog,salchicha", "alimento", None),
    ("pizza", "pizza", "pizza,rebanada", "alimento", None),
    ("donut", "dona", "dona,rosquilla,donut", "alimento", None),
    ("cake", "pastel", "pastel,torta,cake", "alimento", None),

    # --- Bebidas y recipientes ---
    ("dining table", "mesa", "mesa,mesa de comedor", "otro", None),

    # --- Higiene y hogar ---
    ("toothbrush", "cepillo de dientes", "cepillo,cepillo de dientes,cepillo dental", "higiene", None),
    ("scissors", "tijeras", "tijeras", "otro", "Cuidado: objeto cortante."),
    ("hair drier", "secadora de pelo", "secadora,secador,pistola de pelo", "higiene", None),
    ("vase", "florero", "florero,jarrón,vaso decorativo", "otro", None),

    # --- Electrónicos y tecnología ---
    ("tv", "televisión", "tele,televisión,televisor,pantalla,monitor", "otro", None),
    ("laptop", "laptop", "laptop,computadora,portátil,notebook", "otro", None),
    ("mouse", "ratón", "ratón,mouse,apuntador", "otro", None),
    ("remote", "control remoto", "control,control remoto,mando", "otro", None),
    ("keyboard", "teclado", "teclado", "otro", None),
    ("cell phone", "celular", "celular,teléfono,móvil,smartphone", "otro", None),
    ("microwave", "microondas", "microondas,horno de microondas", "otro", None),
    ("oven", "horno", "horno,estufa,cocina", "otro", None),
    ("toaster", "tostadora", "tostadora,tostador", "otro", None),
    ("sink", "lavabo", "lavabo,fregadero,lavaplatos,tarja", "otro", None),
    ("refrigerator", "refrigerador", "refrigerador,refri,nevera,frigorífico", "otro", None),

    # --- Muebles y accesorios ---
    ("chair", "silla", "silla,banco,asiento", "otro", None),
    ("couch", "sofá", "sofá,sillón,sala", "otro", None),
    ("bed", "cama", "cama,cama individual,cama matrimonial", "otro", None),
    ("potted plant", "planta", "planta,maceta,planta en maceta", "otro", None),
    ("book", "libro", "libro,cuaderno,revista,libreta", "otro", None),
    ("clock", "reloj", "reloj,reloj de pared", "otro", None),

    # --- Objetos personales ---
    ("backpack", "mochila", "mochila,bolsa,maleta", "otro", None),
    ("umbrella", "paraguas", "paraguas,sombrilla", "otro", None),
    ("handbag", "bolsa", "bolsa,bolso,cartera,monedero", "otro", None),
    ("suitcase", "maleta", "maleta,equipaje,petaca", "otro", None),

    # --- Mascotas ---
    ("cat", "gato", "gato,gatito,minino", "otro", None),
    ("dog", "perro", "perro,perrito,can,mascota", "otro", None),

    # --- Nota para clases propias futuras ---
    # Al entrenar un modelo propio, agregar aquí las clases nuevas.
    # Ejemplo para productos específicos del hogar:
    # ("shampoo", "shampoo", "shampoo,champú", "higiene", None),
    # ("cloro", "cloro", "cloro,blanqueador,lejía", "limpieza",
    #  "Advertencia: producto tóxico. No ingerir ni mezclar con otros químicos."),
    # ("pasta_dental", "pasta de dientes", "pasta,crema dental", "higiene", None),
    # ("medicina_caja", "caja de medicina", "medicina,medicamento,pastillas", "medicina",
    #  "Advertencia: este es un medicamento. Confirma la dosis con tu médico o farmacéutico."),
]


def poblar_catalogo():
    """Inserta o actualiza el catálogo de objetos en SQLite."""
    try:
        conn = sqlite3.connect(config.SQLITE_RUTA)
        cursor = conn.cursor()

        insertados = 0
        actualizados = 0

        for clase, nombre_es, sinonimos, categoria, advertencia in CATALOGO:
            cursor.execute(
                "SELECT id FROM objetos_catalogo WHERE clase_modelo = ?",
                (clase,),
            )
            existente = cursor.fetchone()

            if existente:
                cursor.execute(
                    """UPDATE objetos_catalogo SET
                       nombre_es = ?, sinonimos = ?, categoria = ?,
                       advertencia = ?, activo = 1
                       WHERE clase_modelo = ?""",
                    (nombre_es, sinonimos, categoria, advertencia, clase),
                )
                actualizados += 1
            else:
                cursor.execute(
                    """INSERT INTO objetos_catalogo
                       (clase_modelo, nombre_es, sinonimos, categoria, advertencia, activo)
                       VALUES (?, ?, ?, ?, ?, 1)""",
                    (clase, nombre_es, sinonimos, categoria, advertencia),
                )
                insertados += 1

        conn.commit()
        conn.close()
        print(f"Catálogo poblado: {insertados} insertados, {actualizados} actualizados.")
        print(f"Total de objetos en catálogo: {insertados + actualizados}")
        return True

    except Exception as e:
        print(f"Error al poblar catálogo: {e}")
        return False


def poblar_catalogo_mysql():
    """Inserta el catálogo también en MySQL (si hay conexión)."""
    try:
        import pymysql
        if not all([config.MYSQL_HOST, config.MYSQL_USER, config.MYSQL_PASSWORD]):
            print("MySQL no configurado. Solo se pobló SQLite.")
            return False

        conn = pymysql.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        cursor = conn.cursor()

        for clase, nombre_es, sinonimos, categoria, advertencia in CATALOGO:
            cursor.execute(
                """INSERT INTO objetos_catalogo
                   (clase_modelo, nombre_es, sinonimos, categoria, advertencia, activo)
                   VALUES (%s, %s, %s, %s, %s, 1)
                   ON DUPLICATE KEY UPDATE
                   nombre_es = VALUES(nombre_es),
                   sinonimos = VALUES(sinonimos),
                   categoria = VALUES(categoria),
                   advertencia = VALUES(advertencia),
                   activo = 1""",
                (clase, nombre_es, sinonimos, categoria, advertencia),
            )

        conn.commit()
        cursor.close()
        conn.close()
        print("Catálogo poblado también en MySQL.")
        return True

    except Exception as e:
        print(f"No se pudo poblar MySQL (no crítico): {e}")
        return False


if __name__ == "__main__":
    # Primero inicializar las tablas
    from database import inicializar_sqlite
    if inicializar_sqlite():
        poblar_catalogo()
        poblar_catalogo_mysql()
    else:
        print("Error: no se pudo inicializar SQLite.")
