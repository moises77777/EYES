# EYES - Asistente Visual por Voz

Prototipo para ayudar a personas con discapacidad visual. Identifica objetos del hogar con la camara y le dice al usuario que tiene enfrente, todo controlado por voz en espanol.

## Que hace

- **Reconoce tu voz** - Dices comandos en espanol y EYES responde hablando.
- **Identifica objetos** - Apuntas algo a la camara y dice "Es una botella", "Es un celular", etc.
- **Guia por sonido** - Pitidos que te ayudan a centrar el objeto (como sensor de reversa).
- **Advierte de peligro** - Si detecta un cuchillo o tijeras, dice "Cuidado: objeto cortante".
- **Guarda objetos personales** - Dices "guardar esto" y le pones nombre: "mi medicina".
- **Registro por voz** - La primera vez, EYES pregunta tu nombre hablando.
- **Base de datos local** - SQLite siempre funciona. MySQL (XAMPP) sincroniza si esta disponible.

## Comandos de voz

| Comando | Que hace |
|---------|----------|
| "que es esto" | Identifica el objeto frente a la camara |
| "detener" | Deja de identificar |
| "guardar esto" | Guarda el objeto con un nombre personal |
| "que hay guardado" | Lista tus objetos personales |
| "repetir" | Repite la ultima respuesta |
| "mas rapido" | Aumenta la velocidad de la voz |
| "mas lento" | Reduce la velocidad de la voz |
| "ayuda" | Lista los comandos |
| "historial" | Lee las ultimas identificaciones |
| "salir" | Cierra la aplicacion |

---

## Instalacion

### Requisitos

- Windows 10/11
- Python 3.11 (https://www.python.org/downloads/release/python-3119/)
- Camara web
- Microfono
- Bocinas o audifonos
- XAMPP (opcional, para MySQL local)

### Pasos

```
git clone https://github.com/moises77777/EYES.git
cd EYES
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Modelo de voz (Vosk)

Descargar **vosk-model-small-es-0.42** (~40MB) de https://alphacephei.com/vosk/models

Descomprimir en:
```
modelos/vosk-model-small-es-0.42/
```

### Modelo YOLO

Se descarga automatico la primera vez (~6MB). Se guarda en `modelos/yolov8n.pt`.

### Configurar .env (opcional)

Solo si quieres MySQL local con XAMPP:

```
copy .env.example .env
```

Editar `.env`:
```
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=EYES

ADMIN_PASSWORD=admin123
```

Sin .env la app funciona normal con SQLite local.

### Ejecutar

```
.venv\Scripts\python interfaz.py
```

O doble clic en `iniciar.bat`.

---

## Donde esta cada cosa

```
EYES/
├── interfaz.py          # Ventana de inicio (tkinter)
├── main.py              # App principal: voz + camara + YOLO
├── config.py            # Configuracion (camara, voz, YOLO, MySQL)
├── database.py          # Base de datos SQLite y MySQL
├── sincronizacion.py    # Sincronizacion SQLite <-> MySQL
├── seed.py              # 46 objetos en espanol (catalogo)
├── requirements.txt     # Dependencias
├── iniciar.bat          # Ejecutar con doble clic
├── .env.example         # Plantilla de configuracion
│
├── modulos/
│   ├── voz_salida.py        # VOZ: habla con pyttsx3
│   ├── voz_entrada.py       # VOZ: escucha con Vosk
│   ├── comandos.py          # VOZ: interpreta comandos
│   ├── camara.py            # CAMARA: captura video con OpenCV
│   ├── detector_objetos.py  # IA: deteccion con YOLO
│   ├── guia_sonido.py       # SONIDO: pitidos de guia
│   ├── vista_maestro.py     # CAMARA: ventana de video
│   ├── conexion.py          # RED: verificar internet
│   └── registro.py          # LOGS: configurar logging
│
├── modelos/             # (no se sube a git)
│   ├── vosk-model-small-es-0.42/  # Modelo de voz
│   └── yolov8n.pt                 # Modelo YOLO
│
├── data/                # (no se sube a git)
│   └── eyes_local.db   # Base de datos SQLite
│
└── logs/                # (no se sube a git)
    └── eyes.log
```

---

## Explicacion del codigo

### interfaz.py - Ventana de inicio

Ventana con tkinter. Tiene:
- Boton "Iniciar" -> llama a `main.main()` que arranca la app de voz
- Boton "Administrador" -> pide contrasena, muestra el usuario registrado y estado de conexion

### main.py - Cerebro de la app

Controla todo:
1. Inicializa base de datos y catalogo
2. Arranca voz (pyttsx3 en un hilo, Vosk en otro)
3. Si es primera vez: pregunta nombre por voz y registra
4. Bucle principal: lee camara + escucha comandos + corre YOLO + guia por sonido

YOLO corre en un **hilo separado** porque tarda ~1 segundo por frame en CPU. Si corriera en el hilo principal, la camara se trabaria.

### config.py - Configuracion

Todo en un solo lugar: camara (640x480), voz (velocidad 175), YOLO (confianza 0.6), MySQL (desde .env), rutas de modelos.

### database.py - Base de datos

SQLite local + MySQL opcional. Tablas: usuario, objetos_catalogo, objetos_personales, historial, configuracion. Cada tabla tiene campo `sincronizado` para saber que falta subir a MySQL.

### sincronizacion.py - Sync SQLite <-> MySQL

Hilo aparte que cada 30 segundos:
1. Verifica si MySQL esta disponible
2. Sube el usuario primero (las demas tablas dependen de el)
3. Sube historial, objetos y configuracion pendientes

### seed.py - Catalogo de objetos

46 objetos que YOLO detecta, traducidos: bottle->botella, cup->taza, knife->cuchillo, cell phone->celular, etc.

### modulos/voz_salida.py - Hablar

pyttsx3 en un hilo dedicado con cola de mensajes. `decir("hola")` encola sin bloquear. `decir_y_esperar("hola")` espera a que termine.

### modulos/voz_entrada.py - Escuchar

Vosk + sounddevice en hilo dedicado. Captura audio, lo convierte a texto en espanol. Se pausa mientras EYES habla para no escucharse a si misma.

### modulos/comandos.py - Interprete

"que es esto" -> identificar, "mas rapido" -> mas_rapido, "salir" -> salir. Coincidencia flexible sin acentos.

### modulos/camara.py - Camara

OpenCV: abre webcam 640x480, lee frames, calcula si el objeto esta centrado.

### modulos/detector_objetos.py - YOLO

Carga YOLOv8n (nano, para CPU). Reduce el frame a 320x240 para ser mas rapido. Traduce clases al espanol usando el catalogo. Evita repetir el mismo objeto cada segundo.

### modulos/guia_sonido.py - Pitidos

Hilo dedicado. Objeto lejos: pitidos lentos (800Hz). Cerca: rapidos (1200Hz). Centrado: tono listo (1800Hz). Como sensor de reversa.

### modulos/vista_maestro.py - Ventana de video

Muestra la camara en una ventana de OpenCV. Solo el video, sin texto encima.

### modulos/conexion.py - Internet

Intenta conectar a 8.8.8.8. Retorna True o False.

### modulos/registro.py - Logs

Configura logs a archivo (logs/eyes.log) y consola.

---

## Hilos de la app

```
Hilo principal
├── Camara (OpenCV) - lee frames
├── Ventana de video - muestra camara
└── Comandos - revisa cola cada 30ms

Hilo voz salida (pyttsx3)
└── Cola de mensajes -> habla

Hilo voz entrada (Vosk)
└── Microfono -> texto -> cola

Hilo YOLO
└── Frame -> detecta objetos -> resultados

Hilo guia sonido
└── Pitidos segun distancia al centro

Hilo sincronizacion
└── Cada 30s sube datos a MySQL
```

---

## Tablas de la base de datos (MySQL / XAMPP)

5 tablas en la base de datos `EYES`:

### usuario
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INT AUTO_INCREMENT | Llave primaria |
| nombre | VARCHAR(100) | Nombre del usuario (se pide por voz) |
| velocidad_voz | INT (default 175) | Velocidad de pyttsx3 |
| volumen | FLOAT (default 1.0) | Volumen de la voz |
| fecha_registro | DATETIME | Cuando se registro |
| primer_uso_completado | TINYINT | 1 si ya paso el tutorial |
| id_dispositivo | VARCHAR(100) | Identificador de la PC (opcional) |

### objetos_catalogo
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INT AUTO_INCREMENT | Llave primaria |
| clase_modelo | VARCHAR(80) UNIQUE | Nombre en YOLO (ej: "bottle") |
| nombre_es | VARCHAR(100) | Nombre en espanol (ej: "botella") |
| sinonimos | TEXT | Sinonimos separados por coma |
| categoria | VARCHAR(30) | alimento, higiene, otro |
| advertencia | TEXT | Texto de advertencia (ej: "objeto cortante") |
| activo | TINYINT | 1 si esta activo |

### objetos_personales
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INT AUTO_INCREMENT | Llave primaria |
| id_usuario | INT | FK a usuario(id) |
| nombre_personal | VARCHAR(200) | Nombre que le puso el usuario |
| descripcion | TEXT | Descripcion opcional |
| clase_modelo | VARCHAR(80) | Clase YOLO asociada |
| categoria | VARCHAR(30) | Categoria del objeto |
| fecha_registro | DATETIME | Cuando se guardo |
| sincronizado | TINYINT | 0=pendiente, 1=sincronizado |

### historial
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INT AUTO_INCREMENT | Llave primaria |
| id_usuario | INT | FK a usuario(id) |
| fecha_hora | DATETIME | Cuando se identifico |
| modo | VARCHAR(30) | "identificar" |
| resultado | TEXT | Que detecto (ej: "botella") |
| confianza | FLOAT | % de confianza de YOLO |
| uso_ia_nube | TINYINT | Si uso IA en la nube |
| sincronizado | TINYINT | 0=pendiente, 1=sincronizado |

### configuracion
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_usuario | INT | FK a usuario(id) |
| clave | VARCHAR(80) | Nombre del ajuste (ej: "velocidad_voz") |
| valor | TEXT | Valor del ajuste (ej: "175") |
| sincronizado | TINYINT | 0=pendiente, 1=sincronizado |
| | | Llave primaria: (id_usuario, clave) |

### Relaciones

```
usuario (1) --- (N) objetos_personales
usuario (1) --- (N) historial
usuario (1) --- (N) configuracion
objetos_catalogo (independiente, 46 objetos precargados)
```

---

Proyecto escolar - Prototipo 2026.
