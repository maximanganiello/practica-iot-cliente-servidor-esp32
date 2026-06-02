"""
Nombre del proyecto: Cliente IoT para monitoreo y control remoto mediante ESP32
Autor: Manganiello Maximiliano
Fecha: 31/05/2026

Descripción:
Este programa implementa una aplicación cliente de escritorio desarrollada en 
Python para interactuar con un dispositivo IoT basado en una placa NodeMCU-32S (ESP32).

La aplicación establece una conexión TCP/IP con el servidor ejecutado en la ESP32, 
permitiendo enviar comandos para la lectura de sensores y el control de actuadores 
conectados al dispositivo.
La interfaz gráfica fue desarrollada utilizando la biblioteca Tkinter e incorpora 
herramientas para la gestión de la conexión, el envío de comandos y la visualización 
de respuestas recibidas desde el servidor en tiempo real.
"""

import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, font
import time

class ClienteIoT:

    def __init__(self, root):
        self.root = root
        self.root.title("Cliente IoT — ESP32")
        self.root.geometry("680x620")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d1117")

        self.sock      = None
        self.conectado = False

        self._configurar_fuentes()
        self._configurar_colores()

        self.crear_header()
        self.crear_panel_conexion()
        self.crear_panel_comandos()
        self.crear_consola()

        self._escribir_info("Sistema listo. Ingresá una IP y puerto para conectarte.")

    # CONFIGURACIÓN

    def _configurar_fuentes(self):
        self.fnt_mono   = font.Font(family="Courier New", size=10)
        self.fnt_mono_b = font.Font(family="Courier New", size=10, weight="bold")
        self.fnt_title  = font.Font(family="Courier New", size=13, weight="bold")
        self.fnt_small  = font.Font(family="Courier New", size=9)
        self.fnt_status = font.Font(family="Courier New", size=10, weight="bold")

    def _configurar_colores(self):
        self.C = {
            "bg":         "#0d1117",
            "panel":      "#161b22",
            "border":     "#30363d",
            "green":      "#3fb950",
            "green_dk":   "#238636",
            "green_hover":"#2ea043",
            "cyan":       "#58a6ff",
            "cyan_hover": "#79c0ff",
            "red":        "#f85149",
            "red_dark":   "#6e3f3f",
            "red_hover":  "#a1403a",
            "amber":      "#d29922",
            "text":       "#e6edf3",
            "muted":      "#8b949e",
            "input_bg":   "#0d1117",
            "btn_bg":     "#21262d",
            "btn_hover":  "#30363d",
        }

    # CONSTRUCCIÓN DE LA INTERFAZ

    def crear_header(self):
        C = self.C

        hdr = tk.Frame(self.root, bg=C["panel"], bd=0)
        hdr.pack(fill="x", padx=0, pady=0)

        tk.Frame(hdr, bg=C["border"], height=1).pack(fill="x", side="bottom")

        title_row = tk.Frame(hdr, bg=C["panel"])
        title_row.pack(fill="x", padx=20, pady=(14, 10))

        tk.Label(
            title_row,
            text="◈  ESP32 IoT Client",
            font=self.fnt_title,
            bg=C["panel"],
            fg=C["green"],
        ).pack(side="left")

        self.clock_lbl = tk.Label(
            title_row,
            text="",
            font=self.fnt_small,
            bg=C["panel"],
            fg=C["muted"],
        )
        self.clock_lbl.pack(side="right")
        self._tick_clock()

    def crear_panel_conexion(self):
        C = self.C

        conn_outer = tk.Frame(self.root, bg=C["bg"])
        conn_outer.pack(fill="x", padx=18, pady=(14, 0))

        conn = tk.Frame(conn_outer, bg=C["panel"], bd=0, relief="flat")
        conn.pack(fill="x")
        self._border_frame(conn)

        conn_inner = tk.Frame(conn, bg=C["panel"])
        conn_inner.pack(fill="x", padx=16, pady=12)

        # Sección label
        tk.Label(
            conn_inner,
            text="CONNECTION",
            font=self.fnt_small,
            bg=C["panel"],
            fg=C["muted"],
        ).grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 8))

        # IP
        tk.Label(
            conn_inner, text="HOST", font=self.fnt_small,
            bg=C["panel"], fg=C["muted"]
        ).grid(row=1, column=0, sticky="w", padx=(0, 6))

        self.ip_entry = self._entry(conn_inner, width=22)
        self.ip_entry.insert(0, "192.168.100.200")
        self.ip_entry.grid(row=1, column=1, padx=(0, 16))

        # Puerto
        tk.Label(
            conn_inner, text="PORT", font=self.fnt_small,
            bg=C["panel"], fg=C["muted"]
        ).grid(row=1, column=2, sticky="w", padx=(0, 6))

        self.port_entry = self._entry(conn_inner, width=8)
        self.port_entry.insert(0, "80")
        self.port_entry.grid(row=1, column=3, padx=(0, 16))

        # Botón conectar
        self.btn_conectar = tk.Button(
            conn_inner,
            text="CONNECT",
            font=self.fnt_mono_b,
            bg=C["green_dk"],
            fg=C["text"],
            activebackground=C["green_hover"],
            activeforeground=C["text"],
            relief="flat",
            bd=0,
            padx=14,
            pady=5,
            cursor="hand2",
            command=self.conectar,
        )
        self.btn_conectar.grid(row=1, column=4)

        # Indicador de estado
        status_row = tk.Frame(conn_inner, bg=C["panel"])
        status_row.grid(row=2, column=0, columnspan=5, sticky="w", pady=(10, 0))

        self.dot = tk.Label(
            status_row, text="●", font=self.fnt_status,
            bg=C["panel"], fg=C["red"]
        )
        self.dot.pack(side="left")

        self.estado = tk.Label(
            status_row,
            text="DISCONNECTED",
            font=self.fnt_status,
            bg=C["panel"],
            fg=C["red"],
        )
        self.estado.pack(side="left", padx=(6, 0))

    def crear_panel_comandos(self):
        C = self.C

        cmd_outer = tk.Frame(self.root, bg=C["bg"])
        cmd_outer.pack(fill="x", padx=18, pady=(10, 0))

        cmd = tk.Frame(cmd_outer, bg=C["panel"])
        cmd.pack(fill="x")
        self._border_frame(cmd)

        cmd_inner = tk.Frame(cmd, bg=C["panel"])
        cmd_inner.pack(fill="x", padx=16, pady=12)

        tk.Label(
            cmd_inner,
            text="COMMAND",
            font=self.fnt_small,
            bg=C["panel"],
            fg=C["muted"],
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        # Prompt símbolo
        tk.Label(
            cmd_inner, text="›_",
            font=self.fnt_mono_b,
            bg=C["panel"], fg=C["green"]
        ).grid(row=1, column=0, padx=(0, 8))

        self.cmd_entry = self._entry(cmd_inner, width=40)
        self.cmd_entry.grid(row=1, column=1, padx=(0, 10), sticky="ew")
        cmd_inner.columnconfigure(1, weight=1)
        self.cmd_entry.bind("<Return>", lambda e: self.enviar_comando())

        self.btn_enviar = tk.Button(
            cmd_inner,
            text="SEND",
            font=self.fnt_mono_b,
            bg=C["cyan"],
            fg=C["bg"],
            activebackground=C["cyan_hover"],
            activeforeground=C["bg"],
            relief="flat",
            bd=0,
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.enviar_comando,
        )
        self.btn_enviar.grid(row=1, column=2, padx=(0, 8))

        self.btn_help = tk.Button(
            cmd_inner,
            text="? HELP",
            font=self.fnt_mono_b,
            bg=C["btn_bg"],
            fg=C["muted"],
            activebackground=C["btn_hover"],
            activeforeground=C["text"],
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=lambda: self.enviar_comando("HELP"),
        )
        self.btn_help.grid(row=1, column=3)

    def crear_consola(self):
        C = self.C

        cons_outer = tk.Frame(self.root, bg=C["bg"])
        cons_outer.pack(fill="both", expand=True, padx=18, pady=(10, 18))

        cons_hdr = tk.Frame(cons_outer, bg=C["panel"])
        cons_hdr.pack(fill="x")

        tk.Frame(cons_hdr, bg=C["border"], height=1).pack(fill="x", side="bottom")

        cons_hdr_inner = tk.Frame(cons_hdr, bg=C["panel"])
        cons_hdr_inner.pack(fill="x", padx=16, pady=6)

        tk.Label(
            cons_hdr_inner, text="OUTPUT",
            font=self.fnt_small, bg=C["panel"], fg=C["muted"]
        ).pack(side="left")

        self.btn_clear = tk.Button(
            cons_hdr_inner,
            text="CLEAR",
            font=self.fnt_small,
            bg=C["panel"],
            fg=C["muted"],
            activebackground=C["btn_hover"],
            activeforeground=C["text"],
            relief="flat",
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self._clear_console,
        )
        self.btn_clear.pack(side="right")

        self.consola = scrolledtext.ScrolledText(
            cons_outer,
            font=self.fnt_mono,
            bg=C["input_bg"],
            fg=C["text"],
            insertbackground=C["green"],
            selectbackground=C["green_dk"],
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            state="disabled",
            wrap="word",
        )
        self.consola.pack(fill="both", expand=True)

        # Tags de color para la consola
        self.consola.tag_config("prompt",   foreground=C["green"])
        self.consola.tag_config("response", foreground=C["text"])
        self.consola.tag_config("info",     foreground=C["cyan"])
        self.consola.tag_config("error",    foreground=C["red"])
        self.consola.tag_config("muted",    foreground=C["muted"])

        # Borde inferior de la consola
        tk.Frame(cons_outer, bg=C["border"], height=1).pack(fill="x")

    # HELPERS UI

    def _entry(self, parent, width=20):
        C = self.C
        e = tk.Entry(
            parent,
            font=self.fnt_mono,
            bg=C["input_bg"],
            fg=C["text"],
            insertbackground=C["green"],
            selectbackground=C["green_dk"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=C["border"],
            highlightcolor=C["cyan"],
            width=width,
        )
        return e

    def _border_frame(self, widget):
        widget.configure(
            highlightthickness=1,
            highlightbackground=self.C["border"],
            highlightcolor=self.C["cyan"],
        )

    def _clear_console(self):
        self.consola.configure(state="normal")
        self.consola.delete("1.0", tk.END)
        self.consola.configure(state="disabled")
        self._escribir_info("Consola limpiada.")

    def _tick_clock(self):
        t = time.strftime("%Y-%m-%d  %H:%M:%S")
        self.clock_lbl.configure(text=t)
        self.root.after(1000, self._tick_clock)

    def _hora(self):
        return time.strftime("%H:%M:%S")

    # CONSOLA

    def _escribir_raw(self, texto, tag="response"):
        self.consola.configure(state="normal")
        self.consola.insert(tk.END, texto, tag)
        self.consola.see(tk.END)
        self.consola.configure(state="disabled")

    def _escribir_info(self, texto):
        self._escribir_raw(f"[{self._hora()}] ", "muted")
        self._escribir_raw(texto + "\n", "info")

    def escribir(self, comando, respuesta):
        self._escribir_raw(f"\n[{self._hora()}] ", "muted")
        self._escribir_raw(f"› {comando}\n", "prompt")
        self._escribir_raw(respuesta + "\n", "response")

    def escribir_error(self, texto):
        self._escribir_raw(f"[{self._hora()}] ", "muted")
        self._escribir_raw(f"ERROR: {texto}\n", "error")

    # RED

    def conectar(self):
        if self.conectado:
            self._desconectar()
            return
        try:
            host   = self.ip_entry.get().strip()
            puerto = int(self.port_entry.get().strip())

            ip = socket.gethostbyname(host)

            self.sock    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, puerto))
            self.archivo = self.sock.makefile("r")

            self.conectado = True
            self.estado.configure(text="CONNECTED", fg=self.C["green"])
            self.dot.configure(fg=self.C["green"])
            self.btn_conectar.configure(
                text="DISCONNECT",
                bg=self.C["red_dark"],
                activebackground=self.C["red_hover"],
            )
            sufijo = f" ({ip})" if ip != host else ""
            self._escribir_info(f"Conectado a {host}:{puerto}{sufijo}")

        except Exception as e:
            messagebox.showerror("Error de conexión", str(e))

    def _desconectar(self):
        try:
            self.sock.close()
        except Exception:
            pass
        self.sock      = None
        self.conectado = False
        self.estado.configure(text="DISCONNECTED", fg=self.C["red"])
        self.dot.configure(fg=self.C["red"])
        self.btn_conectar.configure(
            text="CONNECT",
            bg=self.C["green_dk"],
            activebackground=self.C["green_hover"],
        )
        self._escribir_info("Desconectado.")

    def enviar_comando(self, comando=None):
        if not self.conectado:
            messagebox.showwarning("Sin conexión", "Primero conectate al servidor.")
            return

        if comando is None:
            comando = self.cmd_entry.get().strip()

        if not comando:
            return

        threading.Thread(
            target=self._enviar_y_recibir,
            args=(comando,),
            daemon=True,
        ).start()

        self.cmd_entry.delete(0, tk.END)

    def _enviar_y_recibir(self, comando):
        try:
            self.sock.sendall((comando + "\n").encode())

            lineas = []
            while True:
                linea = self.archivo.readline()
                if not linea:
                    break
                linea = linea.strip()
                if linea == "END":
                    break
                lineas.append(linea)

            texto = "\n".join(lineas)
            self.root.after(
                0, lambda: self.escribir(comando, texto)
            )

        except Exception as e:
            self.root.after(
                0, lambda: self.escribir_error(str(e))
            )

# Entry point
if __name__ == "__main__":
    root = tk.Tk()
    app  = ClienteIoT(root)
    root.mainloop()