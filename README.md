# EYES - Asistente Visual por Voz

Prototipo de aplicación para ayudar a personas con discapacidad visual. Identifica objetos del hogar usando la cámara y le dice al usuario qué tiene enfrente, todo controlado por voz en español.

## Qué hace

- **Reconoce tu voz** - Dices comandos en español y EYES responde hablando.
- **Identifica objetos** - Apuntas algo a la cámara y dice "Es una botella", "Es un celular", etc.
- **Guía por sonido** - Pitidos que te ayudan a centrar el objeto (como sensor de reversa).
- **Advierte de peligro** - Si detecta un cuchillo o tijeras, dice "Cuidado: objeto cortante".
- **Guarda objetos personales** - Dices "guardar esto" y le pones nombre: "mi medicina".
- **Registro por voz** - La primera vez, EYES pregunta tu nombre hablando.
- **Funciona sin internet** - Todo corre local. Si hay internet, sincroniza con MySQL en la nube.

## Comandos de voz

| Comando | Qué hace |
|---------|----------|
| "qué es esto" | Activa la cámara para identificar objetos |
| "detener" | Deja de identificar |
| "guardar esto" | Guarda el objeto actual con un nombre personal |
| "qué hay guardado" | Lista tus objetos personales |
| "repetir" | Repite la última respuesta |
| "más rápido" | Aumenta la velocidad de la voz |
| "más lento" | Reduce la velocidad de la voz |
| "ayuda" | Lista todos los comandos disponibles |
| "historial" | Lee las últimas identificaciones |
| "salir" | Cierra la aplicación |

---

## Instalación local (paso a paso)

### 1. Requisitos

- **Windows 10/11**
- **Python 3.11** (descargar de https://www.python.org/downloads/release/python-3119/)
  - Al instalar, marcar "Add Python to PATH"
- **Cámara web** (integrada o USB)
- **Micrófono**
- **Bocinas o audífonos**

### 2. Clonar el repositorio

```
git clone https://github.com/moises77777/EYES.git
cd EYES
```

### 3. Crear entorno virtual

```
python -m venv .venv
```

### 4. Activar entorno virtual

```
.venv\Scripts\activate
```

### 5. Instalar dependencias

```
pip install -r requirements.txt
```

Esto instala: OpenCV, YOLO (ultralytics), PyTorch, Vosk, pyttsx3, EasyOCR, PyMySQL, etc.

### 6. Descargar modelo de voz (Vosk)

```
mkdir modelos
```

Descargar el modelo de https://alphacephei.com/vosk/models

Buscar: **vosk-model-small-es-0.42** (español, ~40MB)

Descomprimir y poner la carpeta en:
```
modelos/vosk-model-small-es-0.42/
```

Dentro debe quedar algo así:
```
modelos/vosk-model-small-es-0.42/
    am/
    conf/
    graph/
    ivector/
    README
```

### 7. Modelo YOLO

Se descarga automáticamente la primera vez que se ejecuta (~6MB). Se guarda en `modelos/yolov8n.pt`. Si quieres descargarlo manualmente:

```
.venv\Scripts\python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
move yolov8n.pt modelos\
```

### 8. Configurar variables de entorno (OPCIONAL)

Solo necesario si quieres sincronización con MySQL en la nube o usar Gemini:

```
copy .env.example .env
```

Editar `.env` con tus datos:
```
MYSQL_HOST=tu_host
MYSQL_USER=tu_usuario
MYSQL_PASSWORD=tu_contraseña
MYSQL_DATABASE=tu_base_de_datos

GEMINI_API_KEY=tu_clave_api

ADMIN_PASSWORD=tu_contraseña_admin
```

**Sin .env la aplicación funciona normalmente en modo local.**

### 9. Ejecutar

```
.venv\Scripts\python interfaz.py
```

O doble clic en `iniciar.bat`.

Se abre una ventana con dos opciones:
- **Iniciar como Usuario** - Abre la app de voz + cámara
- **Administrador** - Panel de gestión (contraseña: `admin123`)

---

## Estructura del proyecto

```
EYES/
├── interfaz.py              # Interfaz gráfica (tkinter) - punto de entrada
├── main.py                  # App principal: voz + cámara + YOLO
├── config.py                # Toda la configuración centralizada
├── database.py              # Base de datos SQLite (crear tablas, consultas)
├── sincronizacion.py        # Sincronización SQLite local <-> MySQL nube
├── seed.py                  # Catálogo de 46 objetos en español
├── schema.sql               # Esquema SQL de las tablas
├── requirements.txt         # Dependencias de Python
├── iniciar.bat              # Ejecutar con doble clic en Windows
├── .env.example             # Plantilla de variables de entorno
├── .gitignore               # Archivos excluidos de git
│
├── modulos/                 # Módulos de la aplicación
│   ├── voz_salida.py        # Habla con pyttsx3 (hilo dedicado)
│   ├── voz_entrada.py       # Escucha con Vosk (hilo dedicado)
│   ├── comandos.py          # Intérprete de comandos de voz
│   ├── camara.py            # Captura de video con OpenCV
│   ├── detector_objetos.py  # Detección con YOLO + traducción al español
│   ├── guia_sonido.py       # Pitidos de guía (hilo dedicado)
│   ├── vista_maestro.py     # Ventana OpenCV con overlays
│   ├── conexion.py          # Verificar si hay internet
│   └── registro.py          # Configurar logging
│
├── scripts/                 # Pruebas por fase
│   ├── prueba_sistema.py    # Verifica que todo esté instalado
│   ├── prueba_fase2.py      # Prueba de voz
│   ├── prueba_fase3.py      # Prueba de registro
│   ├── prueba_fase4.py      # Prueba de cámara
│   └── prueba_fase5.py      # Prueba de YOLO
│
├── modelos/                 # (no se sube a git)
│   ├── vosk-model-small-es-0.42/  # Modelo de voz español
│   └── yolov8n.pt                 # Modelo YOLO
│
├── data/                    # (no se sube a git)
│   └── eyes_local.db        # Base de datos SQLite
│
└── logs/                    # (no se sube a git)
    └── eyes.log             # Registro de actividad
```

---

## Explicación del código

### `interfaz.py` - Punto de entrada

Es la interfaz gráfica hecha con **tkinter**. Al ejecutar `python interfaz.py` se abre una ventana con:

- **Botón "Iniciar como Usuario"**: cierra la ventana y llama a `main.main()` que arranca toda la app de voz.
- **Botón "Administrador"**: pide contraseña y abre un panel con 5 tabs (Estado, Usuario, Historial, Objetos, Configuración).

El panel de admin permite ver el estado de todos los componentes (SQLite, MySQL, YOLO, Vosk, cámara), editar/eliminar el usuario, borrar historial y gestionar objetos personales.

---

### `main.py` - Cerebro de la aplicación

Este es el archivo más importante. Controla todo el flujo:

1. **Inicializa** la base de datos, el catálogo y la sincronización.
2. **Arranca la voz**: pyttsx3 en un hilo y Vosk en otro hilo.
3. **Primer uso**: si no hay usuario, pregunta el nombre por voz, lo confirma y registra.
4. **Bucle principal**: un loop infinito que al mismo tiempo:
   - Lee frames de la cámara (hilo principal, requisito de OpenCV en Windows).
   - Escucha comandos de voz (no bloqueante, timeout de 30ms).
   - Corre YOLO en un **hilo separado** para no trabar la cámara.
   - Muestra la ventana del maestro con overlays.
   - Controla la guía por sonido.

**Clase `EstadoApp`**: almacena el estado global (usuario activo, modo actual, último objeto detectado, etc.).

**`procesar_comando(texto)`**: recibe lo que Vosk reconoció, lo pasa al intérprete de comandos, y ejecuta la acción correspondiente (cambiar modo, ajustar voz, guardar objeto, etc.).

**Hilo YOLO**: YOLO corre en CPU y tarda ~1 segundo por frame. Si corriera en el hilo principal, la cámara se trabaría. Por eso está en un hilo separado que:
- Toma el frame más reciente.
- Detecta objetos.
- Publica los resultados en una variable compartida con lock.
- El hilo principal lee los resultados sin bloquearse.

---

### `config.py` - Configuración centralizada

Todos los parámetros ajustables están aquí en un solo lugar:
- **Cámara**: índice, resolución, FPS.
- **Voz**: velocidad, volumen, límites.
- **Vosk**: ruta del modelo, frecuencia de muestreo.
- **YOLO**: ruta del modelo, confianza mínima, dispositivo (cpu/cuda).
- **OCR**: idiomas, confianza mínima.
- **Sonido**: frecuencias de los pitidos, duración, volumen.
- **Base de datos**: ruta SQLite, credenciales MySQL (desde .env).
- **Gemini**: API key (desde .env), modelo, timeout.
- **Sincronización**: intervalo, tamaño de lote.

Lee las variables sensibles (contraseñas, API keys) desde el archivo `.env` usando `python-dotenv`.

---

### `database.py` - Base de datos SQLite

Maneja toda la persistencia local:

- **`inicializar_sqlite()`**: crea las tablas si no existen (usuario, objetos_catalogo, objetos_personales, historial, configuracion).
- **`crear_usuario(nombre)`**: inserta un usuario nuevo.
- **`obtener_usuario()`**: retorna el usuario registrado.
- **`obtener_catalogo()`**: retorna los 46 objetos del catálogo con traducción al español.
- **`guardar_historial()`**: guarda cada identificación (fecha, modo, resultado, confianza).
- **`guardar_objeto_personal()`**: guarda un objeto con nombre personalizado.

Cada tabla tiene un campo `sincronizado` (0 o 1) para saber qué registros faltan por subir a MySQL.

---

### `sincronizacion.py` - Sincronización local/nube

Funciona en un **hilo aparte** que cada 30 segundos:
1. Verifica si hay internet.
2. Sube el usuario a MySQL (necesario antes que las demás tablas por las foreign keys).
3. Sube historial, objetos personales y configuración pendientes.
4. Marca los registros como sincronizados en SQLite.

Al iniciar la app, descarga datos de la nube (usuario, catálogo, objetos personales) si hay internet.

**Si no hay internet, la app funciona normal con datos locales.**

---

### `seed.py` - Catálogo de objetos

Contiene los 46 objetos que YOLO puede detectar, traducidos al español:

```
person -> persona
bottle -> botella
cup -> taza
cell phone -> celular
knife -> cuchillo [advertencia: objeto cortante]
scissors -> tijeras [advertencia: objeto cortante]
cat -> gato
dog -> perro
remote -> control remoto
...
```

Se ejecuta automáticamente al iniciar si el catálogo está vacío.

---

### `modulos/voz_salida.py` - Hablar

Usa **pyttsx3** para convertir texto a voz. pyttsx3 NO es thread-safe, así que corre en un **hilo dedicado** con una cola de mensajes:

- `decir("hola")` - Encola el mensaje (no bloquea).
- `decir_y_esperar("hola")` - Encola y espera a que termine de hablar.
- `esta_hablando()` - Retorna True si está hablando (para pausar el micrófono).
- `cambiar_velocidad(200)` - Ajusta la velocidad.
- `repetir()` - Repite la última respuesta.

---

### `modulos/voz_entrada.py` - Escuchar

Usa **Vosk** (reconocimiento de voz offline) + **sounddevice** (captura de audio del micrófono). Corre en otro **hilo dedicado**:

- Captura audio del micrófono en bloques.
- Vosk lo convierte a texto en español.
- El texto se pone en una cola.
- `obtener_comando(timeout=0.03)` - El bucle principal consulta si hay algo reconocido (no bloquea).
- `pausar()` / `reanudar()` - Se pausa mientras EYES habla para que no se escuche a sí misma.

---

### `modulos/comandos.py` - Intérprete de comandos

Recibe un texto (lo que dijo el usuario) y busca qué comando corresponde. Es flexible:

- "qué es esto", "es esto", "identifica" -> comando `identificar`
- "busca el control", "búscame la medicina" -> comando `buscar`, argumento: "control" o "medicina"
- "más rápido", "sube la velocidad" -> comando `mas_rapido`

Usa coincidencia parcial sin acentos para tolerar errores de Vosk.

---

### `modulos/camara.py` - Cámara

Abre la cámara con **OpenCV** y captura frames:

- `iniciar()` - Abre la cámara en 640x480.
- `leer_frame()` - Retorna el frame actual.
- `frame_estable(anterior, actual)` - Compara dos frames para saber si el objeto se movió.
- `calcular_posicion_objeto(frame, bbox)` - Calcula si el objeto está centrado, a qué distancia y en qué dirección moverlo.

---

### `modulos/detector_objetos.py` - Detección YOLO

Carga el modelo **YOLOv8n** (nano, optimizado para CPU) y detecta objetos:

- `inicializar()` - Carga el modelo una sola vez.
- `detectar(frame)` - Reduce el frame a 320x240, corre YOLO, escala las coordenadas de vuelta. Retorna lista de detecciones con: clase, nombre en español, confianza, bounding box, categoría, advertencia.
- `ya_fue_dicho(clase)` - Evita repetir "es una botella" cada segundo.
- `buscar_objeto_personal_en_detecciones()` - Si guardaste "mi medicina" como una botella, la próxima vez que detecte una botella, dice "es mi medicina" en vez de "es una botella".

---

### `modulos/guia_sonido.py` - Pitidos de guía

Genera pitidos con **sounddevice** en un **hilo dedicado**:

- Cuando el objeto está **lejos** del centro: pitidos lentos (800 Hz).
- Cuando está **cerca**: pitidos rápidos (1200 Hz).
- Cuando está **centrado**: tono de "listo" (1800 Hz).

Funciona como un sensor de reversa de un carro.

---

### `modulos/vista_maestro.py` - Ventana del maestro

Dibuja overlays en el frame de la cámara usando **OpenCV**:

- Barra superior: modo actual, FPS, estado de conexión.
- Cruz verde en el centro (zona de tolerancia).
- Recuadros verdes alrededor de objetos detectados con nombre y %.
- Barra inferior: último comando y última respuesta.

Esta ventana es para demostración/presentación. El usuario ciego no la necesita.

---

### `modulos/conexion.py` - Verificar internet

Una función simple que intenta conectar a Google (puerto 443, timeout 3s). Retorna True o False. Se usa para decidir si sincronizar con MySQL o no.

---

### `modulos/registro.py` - Logging

Configura el sistema de logs para que se escriban en `logs/eyes.log` y también se muestren en la terminal. Cada línea tiene: fecha, nivel, módulo, mensaje.

---

## Tecnologías usadas

| Tecnología | Para qué |
|-----------|----------|
| Python 3.11 | Lenguaje principal |
| OpenCV | Captura de cámara y dibujar en frames |
| YOLOv8 (ultralytics) | Detección de objetos en tiempo real |
| PyTorch | Motor de YOLO (en CPU) |
| Vosk | Reconocimiento de voz offline en español |
| pyttsx3 | Síntesis de voz (texto a habla) |
| sounddevice | Captura de audio del micrófono y pitidos |
| SQLite | Base de datos local |
| PyMySQL | Sincronización con MySQL en la nube |
| tkinter | Interfaz gráfica |
| python-dotenv | Variables de entorno |
| NumPy | Operaciones con arrays de imágenes |

---

## Arquitectura de hilos

La app usa varios hilos para que nada se trabe:

```
Hilo principal (main thread)
├── Cámara (OpenCV) - lee frames
├── Ventana del maestro - muestra video
└── Comandos de voz - revisa la cola cada 30ms

Hilo de voz salida (pyttsx3)
└── Cola de mensajes -> habla uno a la vez

Hilo de voz entrada (Vosk)
└── Micrófono -> reconocimiento -> cola de texto

Hilo YOLO (detección)
└── Toma frame -> detecta -> publica resultados

Hilo guía sonido (pitidos)
└── Genera pitidos según la distancia al centro

Hilo sincronización (MySQL)
└── Cada 30s sube datos locales a la nube
```

---

## Licencia

Proyecto escolar - Prototipo 2026.
