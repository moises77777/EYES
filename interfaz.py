# interfaz.py - Interfaz grafica de EYES (prototipo)

import os
import sys
import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from modulos.registro import configurar_logging
logger = configurar_logging()

FONDO = "#2b2b2b"
PANEL = "#3c3c3c"
VERDE = "#4CAF50"
ROJO = "#f44336"
AZUL = "#2196F3"
TEXTO = "#ffffff"
GRIS = "#aaaaaa"


def _conn():
    conn = sqlite3.connect(config.SQLITE_RUTA)
    conn.row_factory = sqlite3.Row
    return conn


def _mysql_ok():
    try:
        import pymysql
        c = pymysql.connect(
            host=config.MYSQL_HOST, port=config.MYSQL_PORT,
            user=config.MYSQL_USER, password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE, connect_timeout=3)
        c.close()
        return True
    except:
        return False


class Inicio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EYES")
        self.geometry("400x500")
        self.resizable(False, False)
        self.configure(bg=FONDO)
        self._centrar()
        self._crear()

    def _centrar(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 200
        y = (self.winfo_screenheight() // 2) - 250
        self.geometry(f"400x500+{x}+{y}")

    def _crear(self):
        tk.Label(self, text="EYES", font=("Arial", 40, "bold"),
                 fg=VERDE, bg=FONDO).pack(pady=(50, 5))
        tk.Label(self, text="Asistente Visual por Voz",
                 font=("Arial", 12), fg=GRIS, bg=FONDO).pack(pady=(0, 40))

        tk.Button(self, text="Iniciar", font=("Arial", 16, "bold"),
                  fg=TEXTO, bg=VERDE, relief="flat", width=20, height=2,
                  command=self._iniciar).pack(pady=(0, 10))
        tk.Label(self, text="Registro y control por voz",
                 font=("Arial", 9), fg=GRIS, bg=FONDO).pack(pady=(0, 30))

        tk.Button(self, text="Administrador", font=("Arial", 12),
                  fg=TEXTO, bg=AZUL, relief="flat", width=20, height=2,
                  command=self._admin).pack(pady=(0, 10))

        self.lbl_db = tk.Label(self, text="...", font=("Arial", 10), fg=GRIS, bg=FONDO)
        self.lbl_db.pack(pady=(20, 0))
        self._verificar_db()

        tk.Label(self, text="Prototipo Escolar 2026",
                 font=("Arial", 8), fg="#555555", bg=FONDO).pack(side="bottom", pady=10)

    def _verificar_db(self):
        try:
            c = sqlite3.connect(config.SQLITE_RUTA)
            c.execute("SELECT 1"); c.close()
            sql_ok = True
        except:
            sql_ok = False
        my_ok = _mysql_ok()
        if sql_ok and my_ok:
            self.lbl_db.config(text="SQLite OK  |  MySQL OK", fg=VERDE)
        elif sql_ok:
            self.lbl_db.config(text="SQLite OK  |  MySQL no disponible", fg="#FFC107")
        else:
            self.lbl_db.config(text="Error de base de datos", fg=ROJO)

    def _iniciar(self):
        self.destroy()
        import main
        main.main()

    def _admin(self):
        pwd = simpledialog.askstring("Admin", "Contrasena:", show="*", parent=self)
        if pwd is None:
            return
        if pwd == config.ADMIN_PASSWORD:
            self.destroy()
            Admin().mainloop()
        else:
            messagebox.showerror("Error", "Contrasena incorrecta.", parent=self)


class Admin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EYES - Admin")
        self.geometry("500x450")
        self.resizable(False, False)
        self.configure(bg=FONDO)
        self._centrar()
        from database import inicializar_sqlite
        inicializar_sqlite()
        self._usuario = None
        self._crear()
        self._cargar()

    def _centrar(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 250
        y = (self.winfo_screenheight() // 2) - 225
        self.geometry(f"500x450+{x}+{y}")

    def _crear(self):
        tk.Label(self, text="EYES - Admin", font=("Arial", 18, "bold"),
                 fg=AZUL, bg=FONDO).pack(pady=(20, 20))

        tk.Label(self, text="USUARIO", font=("Arial", 12, "bold"),
                 fg=TEXTO, bg=FONDO).pack(anchor="w", padx=30)
        self.frame_user = tk.Frame(self, bg=PANEL, padx=15, pady=12)
        self.frame_user.pack(fill="x", padx=30, pady=(5, 15))
        self.lbl_nombre = tk.Label(self.frame_user, text="...",
                                   font=("Arial", 14, "bold"), fg=TEXTO, bg=PANEL)
        self.lbl_nombre.pack(anchor="w")
        self.lbl_info = tk.Label(self.frame_user, text="...",
                                 font=("Arial", 10), fg=GRIS, bg=PANEL)
        self.lbl_info.pack(anchor="w", pady=(3, 0))

        btn_user = tk.Frame(self, bg=FONDO)
        btn_user.pack(fill="x", padx=30)
        tk.Button(btn_user, text="Editar nombre", font=("Arial", 10),
                  fg=TEXTO, bg=AZUL, relief="flat",
                  command=self._editar).pack(side="left", padx=(0, 5))
        tk.Button(btn_user, text="Eliminar", font=("Arial", 10),
                  fg=TEXTO, bg=ROJO, relief="flat",
                  command=self._eliminar).pack(side="left")

        tk.Label(self, text="CONEXION", font=("Arial", 12, "bold"),
                 fg=TEXTO, bg=FONDO).pack(anchor="w", padx=30, pady=(20, 0))
        self.frame_conn = tk.Frame(self, bg=PANEL, padx=15, pady=12)
        self.frame_conn.pack(fill="x", padx=30, pady=(5, 15))
        self.lbl_sqlite = tk.Label(self.frame_conn, text="SQLite: ...",
                                   font=("Arial", 11), fg=GRIS, bg=PANEL)
        self.lbl_sqlite.pack(anchor="w")
        self.lbl_mysql = tk.Label(self.frame_conn, text="MySQL: ...",
                                  font=("Arial", 11), fg=GRIS, bg=PANEL)
        self.lbl_mysql.pack(anchor="w", pady=(3, 0))
        self.lbl_mysql_host = tk.Label(self.frame_conn, text="",
                                       font=("Arial", 9), fg=GRIS, bg=PANEL)
        self.lbl_mysql_host.pack(anchor="w", pady=(3, 0))

        btn_bottom = tk.Frame(self, bg=FONDO)
        btn_bottom.pack(fill="x", padx=30, pady=(10, 0))
        tk.Button(btn_bottom, text="Refrescar", font=("Arial", 10),
                  fg=TEXTO, bg=AZUL, relief="flat",
                  command=self._cargar).pack(side="left")
        tk.Button(btn_bottom, text="Volver", font=("Arial", 10),
                  fg=TEXTO, bg="#666666", relief="flat",
                  command=self._volver).pack(side="right")

    def _cargar(self):
        try:
            conn = _conn()
            fila = conn.execute("SELECT * FROM usuario LIMIT 1").fetchone()
            conn.close()
            if fila:
                f = dict(fila)
                self._usuario = f
                self.lbl_nombre.config(text=f["nombre"], fg=VERDE)
                self.lbl_info.config(
                    text=f"Velocidad: {f['velocidad_voz']}  |  Registro: {f.get('fecha_registro', 'N/A')}")
            else:
                self._usuario = None
                self.lbl_nombre.config(text="Sin usuario registrado", fg="#FFC107")
                self.lbl_info.config(text="Se registra por voz al iniciar")
        except Exception as e:
            self._usuario = None
            self.lbl_nombre.config(text="Error", fg=ROJO)
            self.lbl_info.config(text=str(e))

        try:
            c = sqlite3.connect(config.SQLITE_RUTA)
            c.execute("SELECT 1"); c.close()
            self.lbl_sqlite.config(text="SQLite: OK", fg=VERDE)
        except:
            self.lbl_sqlite.config(text="SQLite: Error", fg=ROJO)

        if _mysql_ok():
            self.lbl_mysql.config(text="MySQL: OK", fg=VERDE)
        else:
            self.lbl_mysql.config(text="MySQL: No disponible", fg=ROJO)
        self.lbl_mysql_host.config(
            text=f"Host: {config.MYSQL_HOST}:{config.MYSQL_PORT} / {config.MYSQL_DATABASE}")

    def _editar(self):
        if not self._usuario:
            messagebox.showinfo("Aviso", "No hay usuario.", parent=self)
            return
        nuevo = simpledialog.askstring("Editar", "Nuevo nombre:",
                                       initialvalue=self._usuario["nombre"], parent=self)
        if not nuevo or not nuevo.strip():
            return
        try:
            conn = _conn()
            conn.execute("UPDATE usuario SET nombre = ? WHERE id = ?",
                         (nuevo.strip(), self._usuario["id"]))
            conn.commit(); conn.close()
            self._cargar()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _eliminar(self):
        if not self._usuario:
            messagebox.showinfo("Aviso", "No hay usuario.", parent=self)
            return
        if not messagebox.askyesno("Confirmar",
                f"Eliminar a '{self._usuario['nombre']}' y todos sus datos?", parent=self):
            return
        try:
            conn = _conn()
            uid = self._usuario["id"]
            conn.execute("DELETE FROM historial WHERE id_usuario = ?", (uid,))
            conn.execute("DELETE FROM objetos_personales WHERE id_usuario = ?", (uid,))
            conn.execute("DELETE FROM configuracion WHERE id_usuario = ?", (uid,))
            conn.execute("DELETE FROM usuario WHERE id = ?", (uid,))
            conn.commit(); conn.close()
            self._cargar()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _volver(self):
        self.destroy()
        Inicio().mainloop()


if __name__ == "__main__":
    app = Inicio()
    app.mainloop()
