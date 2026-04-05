import tkinter as tk
from tkinter import ttk
import math
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ============================
# SERIAL
# ============================
try:
    import serial
    import serial.tools.list_ports
except Exception:
    serial = None

# ============================
# CALIBRACIÓN ESPESOR RELATIVA (FR4)
# ============================

FASE_S11 = {
    0.0:  [0.0],
    0.5:  [20.8],
    1.0:  [29.1],
    1.5:  [36.0],
    2.0:  [37.9]
}

# ============================
# FUNCIONES DE ESPESOR
# ============================
def build_phase_thresholds(fase_dict):
    sorted_items = sorted(fase_dict.items())
    thresholds = []
    for i in range(len(sorted_items)-1):
        thk_current, ph_current = sorted_items[i]
        thk_next, ph_next = sorted_items[i+1]
        midpoint = (ph_current + ph_next)/2
        thresholds.append((thk_current, midpoint))
    return thresholds

def estimate_thickness(phase, thresholds):
    for thk, limit in thresholds:
        if phase < limit:
            return f"{thk:.1f} mm"
        elif (phase > 340.0):
            return "0.0 mm"
    return "2.0 mm o más"

#crea los thresholds con los datos de FASE_S11
PHASE_THRESHOLDS = build_phase_thresholds({k: sum(v)/len(v) for k,v in FASE_S11.items()})

# ============================
# APP
# ============================
class VNAApp(tk.Tk):
    TARGET_FREQ = 2_000_000_000 

    def __init__(self):
        super().__init__()
        self.title("NanoVNA – Espesor FR4")
        self.geometry("900x400")

        self.ser = None
        self.freq = deque(maxlen=4096)
        self.phase = deque(maxlen=4096)
        self.marker_freq = None

        self._build_ui()
        self.after(200, self._tick)

        self.phase_ref = None

    def _build_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        # --- controles izquierda ---
        left_frame = ttk.Frame(main_frame, padding=8)
        left_frame.pack(side="left", fill="y")

        ttk.Label(left_frame, text="Puerto").pack()
        self.port = tk.StringVar()
        self.cb = ttk.Combobox(left_frame, textvariable=self.port,
                               values=self._list_ports(), width=14)
        self.cb.pack(pady=2)

        ttk.Button(left_frame, text="Refrescar", command=self._refresh_ports).pack(fill="x", pady=2)
        ttk.Button(left_frame, text="Conectar", command=self._connect).pack(fill="x", pady=2)
        ttk.Button(left_frame, text="Desconectar", command=self._disconnect).pack(fill="x", pady=2)

        cal = ttk.Labelframe(left_frame, text="Calibración SOL (S11)", padding=4)
        cal.pack(fill="x", pady=5)
        ttk.Button(cal, text="Reset CAL", command=lambda: self._send("cal reset")).pack(fill="x", pady=1)
        ttk.Button(cal, text="Cal SHORT", command=lambda: self._send("cal short")).pack(fill="x", pady=1)
        ttk.Button(cal, text="Cal OPEN",  command=lambda: self._send("cal open")).pack(fill="x", pady=1)
        ttk.Button(cal, text="Cal LOAD",  command=lambda: self._send("cal load")).pack(fill="x", pady=1)
        ttk.Button(cal, text="Finalizar CAL", command=lambda: self._send("cal done")).pack(fill="x", pady=1)
        ttk.Button(cal, text="Activar CAL", command=lambda: self._send("cal on")).pack(fill="x", pady=1)
        
        ttk.Button(left_frame, text="Refrescar VNA", command=self._measure).pack(fill="x", pady=10)
        ttk.Button(left_frame, text="Espesor 0 mm", command=self._save_zero).pack(fill="x", pady=4)

        # Label grande con la fase y espesor
        self.thk_var = tk.StringVar(value="Espesor: — \n Fase: —°")
        ttk.Label(left_frame, textvariable=self.thk_var, font=("Segoe UI", 18, "bold"), foreground="blue").pack(pady=20)

        # --- gráfica pequeña a la derecha ---
        right_frame = ttk.Frame(main_frame, padding=8)
        right_frame.pack(side="right", fill="both", expand=True)

        fig, self.ax = plt.subplots(figsize=(4,3))
        self.line, = self.ax.plot([], [], '-o', markersize=4, color='orange')
        self.ax.set_xlabel("Frecuencia [GHz]")
        self.ax.set_ylabel("Fase S11 [deg]")
        self.ax.set_xlim(1.95, 2.05)
        #all_phases = [sum(v)/len(v) for v in FASE_S11.values()]
        #self.ax.set_ylim(min(all_phases)-5, max(all_phases)+5)
        self.ax.grid(True, alpha=0.3)

        self.canvas = FigureCanvasTkAgg(fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.log = tk.Text(right_frame, height=6)
        self.log.pack(fill="x", pady=4)

    # ---------------- FUNCIONALIDAD ----------------
    def _measure(self):
        if not self.ser:
            return
        self.freq.clear()
        self.phase.clear()
        self.marker_freq = None
        self._send("scan 1950000000 2050000000 11 3") #11 puntos
        self.after(300, lambda: self._send("marker 1")) #espera 300ms antes de medir

    def _send(self, cmd):
        try:
            self.ser.write((cmd+"\r\n").encode())
            self._log(f">> {cmd}")
        except Exception as e:
            self._log(f"ERROR: {e}")

    def _poll(self):
        if not self.ser:
            return
        try:
            data = self.ser.read(4096)
            if not data:
                return
            for line in data.decode(errors="ignore").splitlines():
                self._log(f"<< {line}")
                p = line.split()
                if len(p) == 3 and all(x.isdigit() for x in p):
                    self.marker_freq = float(p[2])
                elif len(p) >= 3:
                    try:
                        f = float(p[0])
                        re = float(p[1])
                        im = float(p[2])
                        self.freq.append(f)
                        ph = math.degrees(math.atan2(im, re))
                        if ph < 0:  #para que la fase siempre sea positiva
                            ph += 360
                        self.phase.append(ph)
                    except:
                        pass
        except:
            pass

    def _save_zero(self):
        if self.freq and self.phase:
            idx = min(range(len(self.freq)),
                    key=lambda i: abs(self.freq[i]-self.TARGET_FREQ))
            self.phase_ref = self.phase[idx]
            self._log(f"Referencia guardada: {self.phase_ref:.2f}°")
        else:
            self._log("No hay datos para guardar referencia")

    # ---------------- SERIAL ----------------
    def _list_ports(self):
        return [] if not serial else [p.device for p in serial.tools.list_ports.comports()]

    def _refresh_ports(self):
        self.cb["values"] = self._list_ports()

    def _connect(self):
        try:
            self.ser = serial.Serial(self.port.get(), 115200, timeout=0)
            self._log("Conectado")
        except Exception as e:
            self._log(str(e))

    def _disconnect(self):
        if self.ser:
            self.ser.close()
            self.ser = None
            self._log("Desconectado")

    # ---------------- LOOP ----------------
    def _tick(self):
        self._poll()
        if self.freq:
            x = [f/1e9 for f in self.freq]
            self.line.set_data(x, list(self.phase))
            self.ax.relim()
            self.ax.autoscale_view()

        if self.freq and self.phase:
            # tomar fase del punto más cercano a 2GHz
            idx = min(range(len(self.freq)),
                      key=lambda i: abs(self.freq[i]-self.TARGET_FREQ))
            ph = self.phase[idx]

            if self.phase_ref is not None:
                delta_ph = self.phase_ref - ph
                if delta_ph < 0:
                    delta_ph += 360  # por si hay salto de fase
                thk = estimate_thickness(delta_ph, PHASE_THRESHOLDS)
                self.thk_var.set(
                    f"Espesor FR4: {thk}\n"
                    f"ΔFase: {delta_ph:.1f}°\n"
                    f"Fase medida: {ph:.1f}°"
                )
            else:
                self.thk_var.set(
                    f"Sin referencia 0\n"
                    f"Fase medida: {ph:.1f}°"
                )

        self.canvas.draw_idle()
        self.after(200, self._tick)

    def _log(self, s):
        self.log.insert("end", s+"\n")
        self.log.see("end")

# ============================
# MAIN
# ============================
if __name__ == "__main__":
    VNAApp().mainloop()
