"""
interfaz.py - Interfaz gráfica de EYES con tkinter.
Pantalla de inicio con dos roles: Administrador y Usuario.
- Usuario: inicia la app de voz + cámara (registro por voz si es primera vez).
- Admin: panel de gestión con CRUD (usuarios, historial, objetos, config, estado).
"""

import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Asegurar que estamos en el directorio correcto
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from modulos.registro import configurar_logging

logger = configurar_logging()


# =============================================================
# COLORES Y ESTILOS
# =============================================================
COLOR_FONDO = "#1a1a2e"
COLOR_PANEL = "#16213e"
COLOR_ACENTO = "#0f3460"
COLOR_BOTON = "#e94560"
COLOR_TEXTO = "#ffffff"
COLOR_TEXTO_SEC = "#a0a0b0"
COLOR_VERDE = "#00d474"
COLOR_AMARILLO = "#ffd93d"
COLOR_ROJO = "#e94560"


def _conn_sqlite():
    """Conexión rápida a SQLite."""
    conn = sqlite3.connect(config.SQLITE_RUTA)
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================
# PANTALLA DE INICIO
# =============================================================
class PantallaInicio(tk.Tk):
    """Ventana principal de inicio de EYES."""

    def __init__(self):
        super().__init__()
        self.title("EYES - Asistente Visual")
        self.geometry("500x600")
        self.resizable(False, False)
        self.configure(bg=COLOR_FONDO)
        self._centrar()
        self._crear_widgets()

    def _centrar(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 250
        y = (self.winfo_screenheight() // 2) - 300
        self.geometry(f"500x600+{x}+{y}")

    def _crear_widgets(self):
        # Título
        tk.Label(
            self, text="EYES",
            font=("Segoe UI", 48, "bold"), fg=COLOR_BOTON, bg=COLOR_FONDO,
        ).pack(pady=(40, 5))

        tk.Label(
            self, text="Asistente Visual por Voz",
            font=("Segoe UI", 14), fg=COLOR_TEXTO_SEC, bg=COLOR_FONDO,
        ).pack()

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=40, pady=20)

        tk.Label(
            self,
            text="Sistema de ayuda visual para personas\ncon discapacidad visual",
            font=("Segoe UI", 11), fg=COLOR_TEXTO_SEC, bg=COLOR_FONDO,
            justify="center",
        ).pack(pady=(0, 30))

        # Botón Usuario
        btn_u = tk.Button(
            self, text="Iniciar como Usuario",
            font=("Segoe UI", 16, "bold"),
            fg=COLOR_TEXTO, bg=COLOR_VERDE,
            activebackground="#00b863", activeforeground=COLOR_TEXTO,
            relief="flat", cursor="hand2", width=22, height=2,
            command=self._iniciar_usuario,
        )
        btn_u.pack(pady=(0, 5))
        btn_u.bind("<Enter>", lambda e: btn_u.config(bg="#00b863"))
        btn_u.bind("<Leave>", lambda e: btn_u.config(bg=COLOR_VERDE))

        tk.Label(
            self, text="Controla EYES solo con tu voz",
            font=("Segoe UI", 10), fg=COLOR_TEXTO_SEC, bg=COLOR_FONDO,
        ).pack(pady=(0, 25))

        # Botón Admin
        btn_a = tk.Button(
            self, text="Administrador",
            font=("Segoe UI", 14),
            fg=COLOR_TEXTO, bg=COLOR_ACENTO,
            activebackground="#1a4a80", activeforeground=COLOR_TEXTO,
            relief="flat", cursor="hand2", width=22, height=2,
            command=self._iniciar_admin,
        )
        btn_a.pack(pady=(0, 5))
        btn_a.bind("<Enter>", lambda e: btn_a.config(bg="#1a4a80"))
        btn_a.bind("<Leave>", lambda e: btn_a.config(bg=COLOR_ACENTO))

        tk.Label(
            self, text="Configurar y gestionar el sistema",
            font=("Segoe UI", 10), fg=COLOR_TEXTO_SEC, bg=COLOR_FONDO,
        ).pack()

        tk.Label(
            self, text="Prototipo Escolar - 2026",
            font=("Segoe UI", 9), fg="#555570", bg=COLOR_FONDO,
        ).pack(side="bottom", pady=15)

    def _iniciar_usuario(self):
        self.destroy()
        _iniciar_app_voz()

    def _iniciar_admin(self):
        pwd = simpledialog.askstring(
            "Administrador", "Contraseña de administrador:",
            show="*", parent=self,
        )
        if pwd is None:
            return
        if pwd == config.ADMIN_PASSWORD:
            self.destroy()
            PanelAdmin().mainloop()
        else:
            messagebox.showerror("Error", "Contraseña incorrecta.", parent=self)


# =============================================================
# PANEL DE ADMINISTRADOR
# =============================================================
class PanelAdmin(tk.Tk):
    """Panel de administración con CRUD completo."""

    def __init__(self):
        super().__init__()
        self.title("EYES - Panel de Administración")
        self.geometry("850x620")
        self.configure(bg=COLOR_FONDO)
        self.minsize(750, 550)
        self._centrar()

        from database import inicializar_sqlite
        inicializar_sqlite()

        self._crear_widgets()
        self._cargar_todo()

    def _centrar(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 425
        y = (self.winfo_screenheight() // 2) - 310
        self.geometry(f"850x620+{x}+{y}")

    def _crear_widgets(self):
        # Barra superior
        barra = tk.Frame(self, bg=COLOR_PANEL, height=50)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(
            barra, text="EYES - Administración",
            font=("Segoe UI", 16, "bold"), fg=COLOR_BOTON, bg=COLOR_PANEL,
        ).pack(side="left", padx=15, pady=10)

        tk.Button(
            barra, text="Volver al Inicio",
            font=("Segoe UI", 10), fg=COLOR_TEXTO, bg=COLOR_ACENTO,
            relief="flat", cursor="hand2", command=self._volver,
        ).pack(side="right", padx=15, pady=10)

        # Notebook (tabs)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=COLOR_FONDO, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=COLOR_PANEL, foreground=COLOR_TEXTO,
                        padding=[15, 8], font=("Segoe UI", 11))
        style.map("TNotebook.Tab",
                  background=[("selected", COLOR_ACENTO)],
                  foreground=[("selected", COLOR_TEXTO)])
        style.configure("Treeview",
                        background=COLOR_PANEL, foreground=COLOR_TEXTO,
                        fieldbackground=COLOR_PANEL, font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=COLOR_ACENTO, foreground=COLOR_TEXTO,
                        font=("Segoe UI", 10, "bold"))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabs
        self.tab_estado = tk.Frame(nb, bg=COLOR_FONDO)
        nb.add(self.tab_estado, text="  Estado  ")
        self._crear_tab_estado()

        self.tab_usuarios = tk.Frame(nb, bg=COLOR_FONDO)
        nb.add(self.tab_usuarios, text="  Usuarios  ")
        self._crear_tab_usuarios()

        self.tab_historial = tk.Frame(nb, bg=COLOR_FONDO)
        nb.add(self.tab_historial, text="  Historial  ")
        self._crear_tab_historial()

        self.tab_objetos = tk.Frame(nb, bg=COLOR_FONDO)
        nb.add(self.tab_objetos, text="  Objetos  ")
        self._crear_tab_objetos()

        self.tab_config = tk.Frame(nb, bg=COLOR_FONDO)
        nb.add(self.tab_config, text="  Configuración  ")
        self._crear_tab_config()

    # ---------- TAB ESTADO ----------
    def _crear_tab_estado(self):
        frame = tk.Frame(self.tab_estado, bg=COLOR_FONDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="Estado del Sistema",
                 font=("Segoe UI", 18, "bold"), fg=COLOR_TEXTO, bg=COLOR_FONDO,
                 ).pack(anchor="w", pady=(0, 15))

        self.labels_estado = {}
        componentes = ["Python", "SQLite", "MySQL", "Internet",
                       "Gemini", "Vosk", "YOLO", "Cámara", "Catálogo"]
        for nombre in componentes:
            row = tk.Frame(frame, bg=COLOR_PANEL, pady=5, padx=10)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=nombre, font=("Segoe UI", 12, "bold"),
                     fg=COLOR_TEXTO, bg=COLOR_PANEL, width=12, anchor="w").pack(side="left")
            lbl = tk.Label(row, text="...", font=("Segoe UI", 11),
                           fg=COLOR_TEXTO_SEC, bg=COLOR_PANEL)
            lbl.pack(side="left", padx=10)
            self.labels_estado[nombre] = lbl

        tk.Button(frame, text="Refrescar", font=("Segoe UI", 11),
                  fg=COLOR_TEXTO, bg=COLOR_ACENTO, relief="flat", cursor="hand2",
                  command=self._verificar_estado).pack(pady=15)

    # ---------- TAB USUARIO ----------
    def _crear_tab_usuarios(self):
        frame = tk.Frame(self.tab_usuarios, bg=COLOR_FONDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="Usuario Registrado",
                 font=("Segoe UI", 18, "bold"), fg=COLOR_TEXTO, bg=COLOR_FONDO,
                 ).pack(anchor="w", pady=(0, 5))

        tk.Label(frame,
                 text="Solo se permite un usuario por dispositivo.\n"
                      "El registro se hace por voz al iniciar como Usuario.",
                 font=("Segoe UI", 10), fg=COLOR_TEXTO_SEC, bg=COLOR_FONDO,
                 justify="left").pack(anchor="w", pady=(0, 15))

        # Info del usuario (sin tabla, más limpio)
        self.frame_usuario_info = tk.Frame(frame, bg=COLOR_PANEL, padx=15, pady=15)
        self.frame_usuario_info.pack(fill="x", pady=5)

        self.lbl_usuario_nombre = tk.Label(
            self.frame_usuario_info, text="...",
            font=("Segoe UI", 16, "bold"), fg=COLOR_TEXTO, bg=COLOR_PANEL)
        self.lbl_usuario_nombre.pack(anchor="w")

        self.lbl_usuario_detalles = tk.Label(
            self.frame_usuario_info, text="...",
            font=("Segoe UI", 11), fg=COLOR_TEXTO_SEC, bg=COLOR_PANEL)
        self.lbl_usuario_detalles.pack(anchor="w", pady=(5, 0))

        btn = tk.Frame(frame, bg=COLOR_FONDO)
        btn.pack(fill="x", pady=15)

        tk.Button(btn, text="Editar nombre", font=("Segoe UI", 10),
                  fg=COLOR_TEXTO, bg=COLOR_ACENTO, relief="flat", cursor="hand2",
                  command=self._editar_usuario).pack(side="left", padx=(0, 5))
        tk.Button(btn, text="Eliminar usuario y datos", font=("Segoe UI", 10),
                  fg=COLOR_TEXTO, bg=COLOR_ROJO, relief="flat", cursor="hand2",
                  command=self._borrar_usuario).pack(side="left", padx=5)
        tk.Button(btn, text="Refrescar", font=("Segoe UI", 10),
                  fg=COLOR_TEXTO, bg=COLOR_ACENTO, relief="flat", cursor="hand2",
                  command=self._cargar_usuarios).pack(side="right")

    # ---------- TAB HISTORIAL ----------
    def _crear_tab_historial(self):
        frame = tk.Frame(self.tab_historial, bg=COLOR_FONDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="Historial de Actividad",
                 font=("Segoe UI", 18, "bold"), fg=COLOR_TEXTO, bg=COLOR_FONDO,
                 ).pack(anchor="w", pady=(0, 15))

        cols = ("ID", "Fecha", "Modo", "Resultado", "Confianza", "Sync")
        self.tree_historial = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        for c in cols:
            self.tree_historial.heading(c, text=c)
            self.tree_historial.column(c, width=100)
        self.tree_historial.column("ID", width=40)
        self.tree_historial.column("Resultado", width=200)
        self.tree_historial.column("Confianza", width=70)
        self.tree_historial.column("Sync", width=50)
        self.tree_historial.pack(fill="both", expand=True)

        btn = tk.Frame(frame, bg=COLOR_FONDO)
        btn.pack(fill="x", pady=10)
        tk.Button(btn, text="Eliminar seleccionado", font=("Segoe UI", 10),
                  fg=COLOR_TEXTO, bg=COLOR_ROJO, relief="flat", cursor="hand2",
                  command=self._eliminar_historial).pack(side="left", padx=(0, 5))
        tk.Button(btn, text="Borrar todo", font=("Segoe UI", 10),
                  fg=COLOR_TEXTO, bg=COLOR_ROJO, relief="flat", cursor="hand2",
                  command=self._borrar_historial).pack(side="left", padx=5)
        tk.Button(btn, text="Refrescar", font=("Segoe UI", 10),
                  fg=COLOR_TEXTO, bg=COLOR_ACENTO, relief="flat", cursor="hand2",
                  command=self._cargar_historial).pack(side="right")

    # ---------- TAB OBJETOS ----------
    def _crear_tab_objetos(self):
        frame = tk.Frame(self.tab_objetos, bg=COLOR_FONDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="Objetos Personales",
                 font=("Segoe UI", 18, "bold"), fg=COLOR_TEXTO, bg=COLOR_FONDO,
                 ).pack(anchor="w", pady=(0, 15))

        cols = ("ID", "Nombre", "Clase YOLO", "Categoría", "Fecha")
        self.tree_objetos = ttk.Treeview(frame, columns=cols, show="headings", height=8)
        for c in cols:
            self.tree_objetos.heading(c, text=c)
            self.tree_objetos.column(c, width=130)
        self.tree_objetos.column("ID", width=40)
        self.tree_objetos.pack(fill="both", expand=True)

        btn = tk.Frame(frame, bg=COLOR_FONDO)
        btn.pack(fill="x", pady=10)
        tk.Button(btn, text="Agregar objeto", font=("Segoe UI", 10),
                  fg=COLOR_TEXTO, bg=COLOR_VERDE, relief="flat", cursor="hand2",
                  command=self._agregar_objeto).pack(side="left", padx=(0, 5))
        tk.Button(btn, text="Editar nombre", font=("Segoe UI", 10),
                  fg=COLOR_TEXTO, bg=COLOR_ACENTO, relief="flat", cursor="hand2",
                  command=self._editar_objeto).pack(side="left", padx=5)
        tk.Button(btn, text="Eliminar seleccionado", font=("Segoe UI", 10),
                  fg=COLOR_TEXTO, bg=COLOR_ROJO, relief="flat", cursor="hand2",
                  command=self._eliminar_objeto).pack(side="left", padx=5)
        tk.Button(btn, text="Refrescar", font=("Segoe UI", 10),
                  fg=COLOR_TEXTO, bg=COLOR_ACENTO, relief="flat", cursor="hand2",
                  command=self._cargar_objetos).pack(side="right")

    # ---------- TAB CONFIG ----------
    def _crear_tab_config(self):
        frame = tk.Frame(self.tab_config, bg=COLOR_FONDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="Configuración",
                 font=("Segoe UI", 18, "bold"), fg=COLOR_TEXTO, bg=COLOR_FONDO,
                 ).pack(anchor="w", pady=(0, 15))

        configs = [
            ("Cámara", f"Índice: {config.CAMARA_INDICE}, {config.CAMARA_ANCHO}x{config.CAMARA_ALTO} @ {config.CAMARA_FPS}fps"),
            ("Voz", f"Velocidad: {config.VOZ_VELOCIDAD}, Volumen: {config.VOZ_VOLUMEN}"),
            ("YOLO", f"Modelo: {'Propio' if config.YOLO_USAR_MODELO_PROPIO else 'COCO'}, Confianza: {config.YOLO_CONFIANZA_MINIMA}"),
            ("OCR", f"Idiomas: {config.OCR_IDIOMAS}, Confianza: {config.OCR_CONFIANZA_MINIMA}"),
            ("Sonido", f"Lejos: {config.SONIDO_FRECUENCIA_LEJOS}Hz, Cerca: {config.SONIDO_FRECUENCIA_CERCA}Hz"),
            ("MySQL", f"Host: {config.MYSQL_HOST or 'No configurado'}"),
            ("Gemini", f"Modelo: {config.GEMINI_MODELO}"),
            ("Sync", f"Cada {config.SYNC_INTERVALO_SEGUNDOS}s, lote máx: {config.SYNC_LOTE_MAXIMO}"),
        ]
        for nombre, valor in configs:
            row = tk.Frame(frame, bg=COLOR_PANEL, pady=8, padx=10)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=nombre, font=("Segoe UI", 11, "bold"),
                     fg=COLOR_BOTON, bg=COLOR_PANEL, width=10, anchor="w").pack(side="left")
            tk.Label(row, text=valor, font=("Segoe UI", 10),
                     fg=COLOR_TEXTO_SEC, bg=COLOR_PANEL).pack(side="left", padx=10)

        tk.Label(frame, text="Para cambiar la configuración, edita config.py o .env",
                 font=("Segoe UI", 10, "italic"), fg=COLOR_TEXTO_SEC, bg=COLOR_FONDO).pack(pady=15)

    # ===== CARGAR DATOS =====
    def _cargar_todo(self):
        self._verificar_estado()
        self._cargar_usuarios()
        self._cargar_historial()
        self._cargar_objetos()

    def _verificar_estado(self):
        def _set(nombre, texto, color=COLOR_VERDE):
            if nombre in self.labels_estado:
                self.labels_estado[nombre].config(text=texto, fg=color)

        _set("Python", "3.11.9 OK")
        try:
            conn = sqlite3.connect(config.SQLITE_RUTA)
            conn.execute("SELECT 1"); conn.close()
            _set("SQLite", "OK")
        except Exception:
            _set("SQLite", "Error", COLOR_ROJO)
        try:
            from database import probar_conexion_mysql
            _set("MySQL", f"OK ({config.MYSQL_HOST})" if probar_conexion_mysql() else "No disponible", COLOR_VERDE if probar_conexion_mysql() else COLOR_AMARILLO)
        except Exception:
            _set("MySQL", "Error", COLOR_ROJO)
        try:
            from modulos.conexion import hay_internet
            _set("Internet", "Conectado" if hay_internet() else "Sin conexión", COLOR_VERDE if hay_internet() else COLOR_AMARILLO)
        except Exception:
            _set("Internet", "Error", COLOR_ROJO)

        _set("Gemini", f"Configurado ({config.GEMINI_MODELO})" if config.GEMINI_API_KEY else "No configurado",
             COLOR_VERDE if config.GEMINI_API_KEY else COLOR_AMARILLO)
        _set("Vosk", "Modelo instalado" if os.path.isdir(config.VOSK_MODELO_RUTA) else "No encontrado",
             COLOR_VERDE if os.path.isdir(config.VOSK_MODELO_RUTA) else COLOR_ROJO)
        _set("YOLO", "Modelo disponible (80 clases)" if os.path.isfile(config.YOLO_MODELO_RUTA) else "No encontrado",
             COLOR_VERDE if os.path.isfile(config.YOLO_MODELO_RUTA) else COLOR_ROJO)
        try:
            import cv2
            cap = cv2.VideoCapture(config.CAMARA_INDICE)
            ok = cap.isOpened(); cap.release()
            _set("Cámara", f"OK ({config.CAMARA_ANCHO}x{config.CAMARA_ALTO})" if ok else "No disponible",
                 COLOR_VERDE if ok else COLOR_ROJO)
        except Exception:
            _set("Cámara", "Error", COLOR_ROJO)
        try:
            from database import obtener_catalogo
            _set("Catálogo", f"{len(obtener_catalogo())} objetos")
        except Exception:
            _set("Catálogo", "Error", COLOR_ROJO)

    def _cargar_usuarios(self):
        try:
            conn = _conn_sqlite()
            fila = conn.execute("SELECT * FROM usuario LIMIT 1").fetchone()
            conn.close()
            if fila:
                f = dict(fila)
                self.lbl_usuario_nombre.config(text=f["nombre"], fg=COLOR_VERDE)
                detalles = (
                    f"Velocidad de voz: {f['velocidad_voz']}  |  "
                    f"Registro: {f.get('fecha_registro', 'N/A')}  |  "
                    f"Primer uso: {'Completado' if f.get('primer_uso_completado') else 'Pendiente'}"
                )
                self.lbl_usuario_detalles.config(text=detalles)
                self._usuario_actual = f
            else:
                self.lbl_usuario_nombre.config(
                    text="No hay usuario registrado", fg=COLOR_AMARILLO)
                self.lbl_usuario_detalles.config(
                    text="Al iniciar como Usuario, EYES pedirá el nombre por voz.")
                self._usuario_actual = None
        except Exception as e:
            logger.error("Error cargando usuario: %s", e)
            self._usuario_actual = None

    def _cargar_historial(self):
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)
        try:
            conn = _conn_sqlite()
            for f in [dict(r) for r in conn.execute("SELECT * FROM historial ORDER BY fecha_hora DESC LIMIT 50").fetchall()]:
                res = f.get("resultado", "") or ""
                if len(res) > 40:
                    res = res[:40] + "..."
                self.tree_historial.insert("", "end", values=(
                    f["id"], f.get("fecha_hora", ""), f.get("modo", ""),
                    res, f"{f.get('confianza', 0):.0%}",
                    "Sí" if f.get("sincronizado") else "No",
                ))
            conn.close()
        except Exception as e:
            logger.error("Error cargando historial: %s", e)

    def _cargar_objetos(self):
        for item in self.tree_objetos.get_children():
            self.tree_objetos.delete(item)
        try:
            conn = _conn_sqlite()
            for f in [dict(r) for r in conn.execute("SELECT * FROM objetos_personales").fetchall()]:
                self.tree_objetos.insert("", "end", values=(
                    f["id"], f.get("nombre_personal", ""),
                    f.get("clase_modelo", ""), f.get("categoria", ""),
                    f.get("fecha_registro", ""),
                ))
            conn.close()
        except Exception as e:
            logger.error("Error cargando objetos: %s", e)

    # ===== USUARIO (solo uno) =====
    def _editar_usuario(self):
        if not self._usuario_actual:
            messagebox.showinfo("Aviso",
                "No hay usuario registrado.\nInicia como Usuario para registrarte por voz.",
                parent=self)
            return
        uid = self._usuario_actual["id"]
        nombre_actual = self._usuario_actual["nombre"]
        nuevo = simpledialog.askstring("Editar usuario", "Nuevo nombre:",
                                       initialvalue=nombre_actual, parent=self)
        if not nuevo or not nuevo.strip():
            return
        try:
            conn = _conn_sqlite()
            conn.execute("UPDATE usuario SET nombre = ? WHERE id = ?", (nuevo.strip(), uid))
            conn.commit(); conn.close()
            self._cargar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _borrar_usuario(self):
        if not self._usuario_actual:
            messagebox.showinfo("Aviso", "No hay usuario para eliminar.", parent=self)
            return
        nombre = self._usuario_actual["nombre"]
        uid = self._usuario_actual["id"]
        if not messagebox.askyesno("Confirmar",
                f"¿Eliminar a '{nombre}' y todo su historial y objetos?\n\n"
                f"La próxima vez que inicie como Usuario,\n"
                f"EYES pedirá registrarse por voz.", parent=self):
            return
        try:
            conn = _conn_sqlite()
            conn.execute("DELETE FROM historial WHERE id_usuario = ?", (uid,))
            conn.execute("DELETE FROM objetos_personales WHERE id_usuario = ?", (uid,))
            conn.execute("DELETE FROM configuracion WHERE id_usuario = ?", (uid,))
            conn.execute("DELETE FROM usuario WHERE id = ?", (uid,))
            conn.commit(); conn.close()
            self._cargar_todo()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    # ===== CRUD HISTORIAL =====
    def _eliminar_historial(self):
        sel = self.tree_historial.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una entrada.", parent=self)
            return
        hid = self.tree_historial.item(sel[0])["values"][0]
        try:
            conn = _conn_sqlite()
            conn.execute("DELETE FROM historial WHERE id = ?", (hid,))
            conn.commit(); conn.close()
            self._cargar_historial()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _borrar_historial(self):
        if not messagebox.askyesno("Confirmar", "¿Borrar TODO el historial?", parent=self):
            return
        try:
            conn = _conn_sqlite()
            conn.execute("DELETE FROM historial")
            conn.commit(); conn.close()
            self._cargar_historial()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    # ===== CRUD OBJETOS =====
    def _agregar_objeto(self):
        nombre = simpledialog.askstring("Nuevo objeto", "Nombre del objeto personal:", parent=self)
        if not nombre or not nombre.strip():
            return
        clase = simpledialog.askstring("Clase YOLO", "Clase del modelo (ej: bottle, cup):", parent=self)
        if not clase:
            clase = ""
        try:
            conn = _conn_sqlite()
            # Obtener primer usuario
            u = conn.execute("SELECT id FROM usuario LIMIT 1").fetchone()
            uid = u["id"] if u else 1
            conn.execute(
                "INSERT INTO objetos_personales (id_usuario, nombre_personal, clase_modelo, categoria, sincronizado) VALUES (?, ?, ?, 'otro', 0)",
                (uid, nombre.strip(), clase.strip()),
            )
            conn.commit(); conn.close()
            self._cargar_objetos()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _editar_objeto(self):
        sel = self.tree_objetos.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un objeto.", parent=self)
            return
        vals = self.tree_objetos.item(sel[0])["values"]
        oid, nombre_actual = vals[0], vals[1]
        nuevo = simpledialog.askstring("Editar objeto", "Nuevo nombre:", initialvalue=nombre_actual, parent=self)
        if not nuevo or not nuevo.strip():
            return
        try:
            conn = _conn_sqlite()
            conn.execute("UPDATE objetos_personales SET nombre_personal = ?, sincronizado = 0 WHERE id = ?",
                         (nuevo.strip(), oid))
            conn.commit(); conn.close()
            self._cargar_objetos()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _eliminar_objeto(self):
        sel = self.tree_objetos.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un objeto.", parent=self)
            return
        vals = self.tree_objetos.item(sel[0])["values"]
        oid, nombre = vals[0], vals[1]
        if not messagebox.askyesno("Confirmar", f"¿Eliminar '{nombre}'?", parent=self):
            return
        try:
            conn = _conn_sqlite()
            conn.execute("DELETE FROM objetos_personales WHERE id = ?", (oid,))
            conn.commit(); conn.close()
            self._cargar_objetos()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _volver(self):
        self.destroy()
        PantallaInicio().mainloop()


# =============================================================
# INICIAR APP DE VOZ
# =============================================================
def _iniciar_app_voz():
    """Inicia EYES en modo usuario (voz + cámara)."""
    import main
    main.main()


# =============================================================
# PUNTO DE ENTRADA
# =============================================================
if __name__ == "__main__":
    app = PantallaInicio()
    app.mainloop()
