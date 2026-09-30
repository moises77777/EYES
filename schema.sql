-- =============================================================
-- EYES - Esquema de base de datos
-- Usar para crear las tablas en MySQL (Hostinger) y en SQLite.
-- Las diferencias entre MySQL y SQLite se indican con comentarios.
-- =============================================================

-- Tabla de usuario
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,  -- SQLite: sin AUTO_INCREMENT, usa AUTOINCREMENT
    nombre VARCHAR(100) NOT NULL,
    velocidad_voz INTEGER NOT NULL DEFAULT 175,
    volumen FLOAT NOT NULL DEFAULT 1.0,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    primer_uso_completado BOOLEAN NOT NULL DEFAULT 0,
    id_dispositivo VARCHAR(100)
);

-- Catálogo de objetos conocidos (clases COCO + futuras clases propias)
CREATE TABLE IF NOT EXISTS objetos_catalogo (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    clase_modelo VARCHAR(80) NOT NULL UNIQUE,     -- Nombre exacto de la clase en el modelo
    nombre_es VARCHAR(100) NOT NULL,              -- Nombre en español para decir en voz alta
    sinonimos TEXT,                                -- Sinónimos separados por coma para búsqueda por voz
    categoria VARCHAR(30) NOT NULL DEFAULT 'otro', -- alimento, limpieza, higiene, medicina, otro
    advertencia TEXT,                              -- Advertencia especial (productos tóxicos, medicinas)
    activo BOOLEAN NOT NULL DEFAULT 1
);

-- Objetos personales del usuario ("mi medicina de la presión")
CREATE TABLE IF NOT EXISTS objetos_personales (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    id_usuario INTEGER NOT NULL,
    nombre_personal VARCHAR(200) NOT NULL,
    descripcion TEXT,
    clase_modelo VARCHAR(80),                      -- Clase del modelo asociada
    categoria VARCHAR(30) NOT NULL DEFAULT 'otro',
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sincronizado BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id)
);

-- Historial de uso
CREATE TABLE IF NOT EXISTS historial (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    id_usuario INTEGER NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modo VARCHAR(30) NOT NULL,                     -- leer, identificar, buscar, resumen, pregunta
    resultado TEXT,
    confianza FLOAT,
    uso_ia_nube BOOLEAN NOT NULL DEFAULT 0,
    sincronizado BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id)
);

-- Configuración flexible clave-valor
CREATE TABLE IF NOT EXISTS configuracion (
    id_usuario INTEGER NOT NULL,
    clave VARCHAR(80) NOT NULL,
    valor TEXT,
    sincronizado BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (id_usuario, clave),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id)
);
