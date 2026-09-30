# seed.py - Catalogo de objetos COCO en espanol

import sqlite3
import config

CATALOGO = [
    ("person", "persona", "persona,gente,alguien,humano", "otro", None),
    ("bottle", "botella", "botella,frasco,envase,agua,refresco,jugo", "alimento", None),
    ("wine glass", "copa de vino", "copa,vaso de vino", "alimento", None),
    ("cup", "taza", "taza,vaso,pocillo", "alimento", None),
    ("fork", "tenedor", "tenedor,cubierto", "otro", None),
    ("knife", "cuchillo", "cuchillo,navaja", "otro", "Cuidado: objeto cortante."),
    ("spoon", "cuchara", "cuchara,cucharon", "otro", None),
    ("bowl", "tazon", "tazon,plato hondo,bowl,cuenco", "alimento", None),
    ("banana", "platano", "platano,banana,guineo", "alimento", None),
    ("apple", "manzana", "manzana", "alimento", None),
    ("sandwich", "sandwich", "sandwich,torta,emparedado", "alimento", None),
    ("orange", "naranja", "naranja,mandarina", "alimento", None),
    ("broccoli", "brocoli", "brocoli", "alimento", None),
    ("carrot", "zanahoria", "zanahoria", "alimento", None),
    ("hot dog", "hot dog", "hot dog,salchicha", "alimento", None),
    ("pizza", "pizza", "pizza,rebanada", "alimento", None),
    ("donut", "dona", "dona,rosquilla,donut", "alimento", None),
    ("cake", "pastel", "pastel,torta,cake", "alimento", None),
    ("dining table", "mesa", "mesa,mesa de comedor", "otro", None),
    ("toothbrush", "cepillo de dientes", "cepillo,cepillo de dientes", "higiene", None),
    ("scissors", "tijeras", "tijeras", "otro", "Cuidado: objeto cortante."),
    ("hair drier", "secadora de pelo", "secadora,secador", "higiene", None),
    ("vase", "florero", "florero,jarron", "otro", None),
    ("tv", "television", "tele,television,televisor,pantalla,monitor", "otro", None),
    ("laptop", "laptop", "laptop,computadora,portatil", "otro", None),
    ("mouse", "raton", "raton,mouse", "otro", None),
    ("remote", "control remoto", "control,control remoto,mando", "otro", None),
    ("keyboard", "teclado", "teclado", "otro", None),
    ("cell phone", "celular", "celular,telefono,movil", "otro", None),
    ("microwave", "microondas", "microondas", "otro", None),
    ("oven", "horno", "horno,estufa,cocina", "otro", None),
    ("toaster", "tostadora", "tostadora,tostador", "otro", None),
    ("sink", "lavabo", "lavabo,fregadero,tarja", "otro", None),
    ("refrigerator", "refrigerador", "refrigerador,refri,nevera", "otro", None),
    ("chair", "silla", "silla,banco,asiento", "otro", None),
    ("couch", "sofa", "sofa,sillon,sala", "otro", None),
    ("bed", "cama", "cama", "otro", None),
    ("potted plant", "planta", "planta,maceta", "otro", None),
    ("book", "libro", "libro,cuaderno,revista", "otro", None),
    ("clock", "reloj", "reloj,reloj de pared", "otro", None),
    ("backpack", "mochila", "mochila,bolsa,maleta", "otro", None),
    ("umbrella", "paraguas", "paraguas,sombrilla", "otro", None),
    ("handbag", "bolsa", "bolsa,bolso,cartera", "otro", None),
    ("suitcase", "maleta", "maleta,equipaje", "otro", None),
    ("cat", "gato", "gato,gatito,minino", "otro", None),
    ("dog", "perro", "perro,perrito,can,mascota", "otro", None),
]


def poblar_catalogo():
    try:
        conn = sqlite3.connect(config.SQLITE_RUTA)
        cursor = conn.cursor()
        insertados = 0
        for clase, nombre_es, sinonimos, categoria, advertencia in CATALOGO:
            cursor.execute("SELECT id FROM objetos_catalogo WHERE clase_modelo = ?", (clase,))
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE objetos_catalogo SET nombre_es=?, sinonimos=?, categoria=?, advertencia=?, activo=1 WHERE clase_modelo=?",
                    (nombre_es, sinonimos, categoria, advertencia, clase))
            else:
                cursor.execute(
                    "INSERT INTO objetos_catalogo (clase_modelo, nombre_es, sinonimos, categoria, advertencia, activo) VALUES (?, ?, ?, ?, ?, 1)",
                    (clase, nombre_es, sinonimos, categoria, advertencia))
                insertados += 1
        conn.commit(); conn.close()
        print(f"Catalogo: {insertados} objetos nuevos, {len(CATALOGO)} total.")
        return True
    except Exception as e:
        print(f"Error catalogo: {e}")
        return False


if __name__ == "__main__":
    from database import inicializar_sqlite
    if inicializar_sqlite():
        poblar_catalogo()
