# app/ui/apps/settings/settings_screen.py

"""
@file settings_screen.py
@brief Panel de control y ajustes del sistema para la Raspberry Pi.
@details Clase QWidget que permite gestionar hardware (Audio, Bluetooth, Wi-Fi),
monitorizar el estado del sistema (CPU, RAM, Temperatura) y ejecutar tareas 
de mantenimiento (reinicio, apagado, limpieza de archivos).
"""

import subprocess
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QProgressBar, QScrollArea,
    QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, QTime, QDate, pyqtSignal
from PyQt5.QtGui import QFont
from app.core.logger import logger


STYLE = """
QWidget#settings_root {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0.00 #fdf6ee,
        stop: 0.50 #fbeede,
        stop: 1.00 #fdf0d8
    );
    font-family: "Segoe UI", "Nunito", sans-serif;
}

QPushButton#btn_back {
    background-color: #e8c060;
    border: none;
    border-radius: 20px;
    color: #4a2800;
    font-size: 22px;
    font-weight: 800;
    min-width: 160px;
    min-height: 58px;
    padding: 0 20px;
}
QPushButton#btn_back:pressed { background-color: #c09030; }

QLabel#section_title {
    color: #5a3300;
    font-size: 20px;
    font-weight: 800;
    background: transparent;
}

QLabel#value_label {
    color: #3a1f00;
    font-size: 34px;
    font-weight: 900;
    background: transparent;
}

QLabel#info_text {
    color: #7a5230;
    font-size: 18px;
    font-weight: 600;
    background: transparent;
}

/* Toggle ON */
QPushButton#btn_toggle_on {
    background-color: #86efac;
    border: none;
    border-radius: 18px;
    color: #14532d;
    font-size: 20px;
    font-weight: 900;
    min-width: 130px;
    min-height: 56px;
}
QPushButton#btn_toggle_on:pressed { background-color: #4ade80; }

/* Toggle OFF */
QPushButton#btn_toggle_off {
    background-color: #fda4af;
    border: none;
    border-radius: 18px;
    color: #6b0018;
    font-size: 20px;
    font-weight: 900;
    min-width: 130px;
    min-height: 56px;
}
QPushButton#btn_toggle_off:pressed { background-color: #f97395; }

/* Botones secundarios (escanear, limpiar...) */
QPushButton#btn_action {
    background-color: #c4b5fd;
    border: none;
    border-radius: 18px;
    color: #2e1065;
    font-size: 19px;
    font-weight: 800;
    min-height: 52px;
    padding: 0 18px;
}
QPushButton#btn_action:pressed { background-color: #a78bfa; }
QPushButton#btn_action:disabled {
    background-color: #e9e4f5;
    color: #9d8ec4;
}

QPushButton#btn_minus {
    background-color: #fda4af;
    border: none;
    border-radius: 18px;
    color: #6b0018;
    font-size: 32px;
    font-weight: 900;
    min-width: 76px;
    min-height: 64px;
}
QPushButton#btn_minus:pressed { background-color: #f97395; }

QPushButton#btn_plus {
    background-color: #86efac;
    border: none;
    border-radius: 18px;
    color: #14532d;
    font-size: 32px;
    font-weight: 900;
    min-width: 76px;
    min-height: 64px;
}
QPushButton#btn_plus:pressed { background-color: #4ade80; }

QPushButton#btn_restart {
    background-color: #7dd3fc;
    border: none;
    border-radius: 20px;
    color: #0c3253;
    font-size: 21px;
    font-weight: 900;
    min-height: 70px;
}
QPushButton#btn_restart:pressed { background-color: #38bdf8; }

QPushButton#btn_poweroff {
    background-color: #fda4af;
    border: none;
    border-radius: 20px;
    color: #6b0018;
    font-size: 21px;
    font-weight: 900;
    min-height: 70px;
}
QPushButton#btn_poweroff:pressed { background-color: #f97395; }

QProgressBar {
    border: none;
    border-radius: 8px;
    background-color: #f1e8d8;
    max-height: 16px;
    color: transparent;
}

QListWidget {
    background: #fdf6ee;
    border: 2px solid #e8d8b8;
    border-radius: 14px;
    font-size: 18px;
    color: #3a1f00;
    padding: 4px;
}
QListWidget::item { padding: 8px 12px; border-radius: 8px; }
QListWidget::item:selected { background: #c4b5fd; color: #2e1065; }

QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget { background: transparent; }
QScrollBar:vertical {
    width: 6px; background: transparent; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: rgba(200,160,100,0.4); border-radius: 3px; min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
"""


def _card(border_color: str) -> QWidget:
    """@brief Crea un contenedor estilizado (tarjeta) con borde de color."""
    w = QWidget()
    w.setObjectName("card")
    w.setStyleSheet(
        f"QWidget#card {{ background: white; border-radius: 28px; border: 3px solid {border_color}; }}"
    )
    return w


class SettingsScreen(QWidget):
    
    """
    @brief Pantalla principal de ajustes.
    @details Conecta señales asíncronas para actualizar la UI desde hilos de hardware.
    """

    # Señales para actualizar UI desde hilos
    _bt_scan_done  = pyqtSignal(list)
    _wifi_info_done = pyqtSignal(str, str)   # (estado, red)

    def __init__(self, controller):
        
        """@brief Inicializa los componentes y configura los timers de monitoreo."""
        
        super().__init__()
        self.controller = controller

        self.setObjectName("settings_root")
        self.setStyleSheet(STYLE)

        self._bt_scan_done.connect(self._on_bt_scan_done)
        self._wifi_info_done.connect(self._on_wifi_info_done)

        root = QVBoxLayout()
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(18)
        self.setLayout(root)

        # ── HEADER ──────────────────────────────────────────────────────────
        header = QHBoxLayout()
        self.btn_back = QPushButton("Volver")
        self.btn_back.setObjectName("btn_back")
        self.btn_back.clicked.connect(self._go_back)
        header.addWidget(self.btn_back)
        header.addStretch()
        title = QLabel("Ajustes del Aparato")
        title.setFont(QFont("Segoe UI", 28, QFont.Black))
        title.setStyleSheet("color: #5a3300; background: transparent;")
        header.addWidget(title)
        header.addStretch()
        header.addSpacing(160)
        root.addLayout(header)

        # ── SCROLL ───────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content)
        cl.setSpacing(16)
        cl.setContentsMargins(0, 0, 8, 0)

        # ── 1. FECHA Y HORA ──────────────────────────────────────────────────
        dt_card = _card("#f0c878")
        dt_lay = QHBoxLayout(dt_card)
        dt_lay.setContentsMargins(24, 16, 24, 16)
        self.lbl_date = QLabel("—")
        self.lbl_date.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.lbl_date.setStyleSheet("color: #5a3300; background: transparent;")
        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setFont(QFont("Segoe UI", 34, QFont.Black))
        self.lbl_time.setStyleSheet("color: #3a1f00; background: transparent;")
        self.lbl_uptime = QLabel("Activo desde: —")
        self.lbl_uptime.setFont(QFont("Segoe UI", 17))
        self.lbl_uptime.setStyleSheet("color: #a06020; background: transparent;")
        dt_left = QVBoxLayout()
        dt_left.addWidget(self.lbl_date)
        dt_left.addWidget(self.lbl_uptime)
        dt_lay.addLayout(dt_left)
        dt_lay.addStretch()
        dt_lay.addWidget(self.lbl_time)
        cl.addWidget(dt_card)

        # ── 2. VOLUMEN ───────────────────────────────────────────────────────
        vol_card = _card("#c4b5fd")
        vol_lay = QVBoxLayout(vol_card)
        vol_lay.setContentsMargins(24, 16, 24, 16)
        vol_lay.setSpacing(10)
        lbl_vt = QLabel("VOL  Volumen")
        lbl_vt.setObjectName("section_title")
        vol_lay.addWidget(lbl_vt)
        vol_row = QHBoxLayout()
        self.btn_vol_down = QPushButton("−")
        self.btn_vol_down.setObjectName("btn_minus")
        self.btn_vol_down.clicked.connect(lambda: self._change_volume(-10))
        self.lbl_vol = QLabel("—")
        self.lbl_vol.setObjectName("value_label")
        self.lbl_vol.setAlignment(Qt.AlignCenter)
        self.lbl_vol.setMinimumWidth(110)
        self.btn_vol_up = QPushButton("+")
        self.btn_vol_up.setObjectName("btn_plus")
        self.btn_vol_up.clicked.connect(lambda: self._change_volume(10))
        vol_row.addWidget(self.btn_vol_down)
        vol_row.addStretch()
        vol_row.addWidget(self.lbl_vol)
        vol_row.addStretch()
        vol_row.addWidget(self.btn_vol_up)
        vol_lay.addLayout(vol_row)
        self.bar_vol = QProgressBar()
        self.bar_vol.setStyleSheet(
            "QProgressBar { border:none; border-radius:8px; background:#f1e8d8; max-height:16px; color:transparent; }"
            "QProgressBar::chunk { background:#c4b5fd; border-radius:8px; }"
        )
        vol_lay.addWidget(self.bar_vol)
        cl.addWidget(vol_card)

        # ── 3. BLUETOOTH ─────────────────────────────────────────────────────
        bt_card = _card("#a5f3fc")
        bt_lay = QVBoxLayout(bt_card)
        bt_lay.setContentsMargins(24, 16, 24, 16)
        bt_lay.setSpacing(10)

        bt_header = QHBoxLayout()
        lbl_btt = QLabel("Bluetooth")
        lbl_btt.setObjectName("section_title")
        bt_header.addWidget(lbl_btt)
        bt_header.addStretch()
        self.lbl_bt_state = QLabel("Comprobando…")
        self.lbl_bt_state.setFont(QFont("Segoe UI", 17, QFont.Bold))
        self.lbl_bt_state.setStyleSheet("color: #7a5230; background: transparent;")
        bt_header.addWidget(self.lbl_bt_state)
        bt_lay.addLayout(bt_header)

        bt_row = QHBoxLayout()
        bt_row.setSpacing(12)
        self.btn_bt_on = QPushButton("Encender")
        self.btn_bt_on.setObjectName("btn_toggle_on")
        self.btn_bt_on.clicked.connect(self._bt_enable)
        self.btn_bt_off = QPushButton("Apagar")
        self.btn_bt_off.setObjectName("btn_toggle_off")
        self.btn_bt_off.clicked.connect(self._bt_disable)
        self.btn_bt_scan = QPushButton("Buscar dispositivos")
        self.btn_bt_scan.setObjectName("btn_action")
        self.btn_bt_scan.clicked.connect(self._bt_scan)
        bt_row.addWidget(self.btn_bt_on)
        bt_row.addWidget(self.btn_bt_off)
        bt_row.addStretch()
        bt_row.addWidget(self.btn_bt_scan)
        bt_lay.addLayout(bt_row)

        self.list_bt = QListWidget()
        self.list_bt.setMaximumHeight(140)
        self.list_bt.hide()
        bt_lay.addWidget(self.list_bt)

        cl.addWidget(bt_card)

        # ── 4. WI-FI ─────────────────────────────────────────────────────────
        wifi_card = _card("#86efac")
        wifi_lay = QVBoxLayout(wifi_card)
        wifi_lay.setContentsMargins(24, 16, 24, 16)
        wifi_lay.setSpacing(10)

        wifi_header = QHBoxLayout()
        lbl_wt = QLabel("Wi-Fi")
        lbl_wt.setObjectName("section_title")
        wifi_header.addWidget(lbl_wt)
        wifi_header.addStretch()
        self.lbl_wifi_net = QLabel("Comprobando…")
        self.lbl_wifi_net.setFont(QFont("Segoe UI", 17, QFont.Bold))
        self.lbl_wifi_net.setStyleSheet("color: #14532d; background: transparent;")
        wifi_header.addWidget(self.lbl_wifi_net)
        wifi_lay.addLayout(wifi_header)

        wifi_row = QHBoxLayout()
        wifi_row.setSpacing(12)
        self.btn_wifi_on = QPushButton("Encender")
        self.btn_wifi_on.setObjectName("btn_toggle_on")
        self.btn_wifi_on.clicked.connect(self._wifi_enable)
        self.btn_wifi_off = QPushButton("Apagar")
        self.btn_wifi_off.setObjectName("btn_toggle_off")
        self.btn_wifi_off.clicked.connect(self._wifi_disable)
        self.btn_wifi_refresh = QPushButton("Actualizar")
        self.btn_wifi_refresh.setObjectName("btn_action")
        self.btn_wifi_refresh.clicked.connect(self._wifi_refresh)
        wifi_row.addWidget(self.btn_wifi_on)
        wifi_row.addWidget(self.btn_wifi_off)
        wifi_row.addStretch()
        wifi_row.addWidget(self.btn_wifi_refresh)
        wifi_lay.addLayout(wifi_row)

        self.lbl_wifi_ip = QLabel("")
        self.lbl_wifi_ip.setFont(QFont("Segoe UI", 16))
        self.lbl_wifi_ip.setStyleSheet("color: #7a5230; background: transparent;")
        wifi_lay.addWidget(self.lbl_wifi_ip)

        cl.addWidget(wifi_card)

        # ── 5. ESTADO DEL SISTEMA ────────────────────────────────────────────
        sys_card = _card("#fde68a")
        sys_lay = QVBoxLayout(sys_card)
        sys_lay.setContentsMargins(24, 16, 24, 16)
        sys_lay.setSpacing(12)
        lbl_st = QLabel("Estado del sistema")
        lbl_st.setObjectName("section_title")
        sys_lay.addWidget(lbl_st)

        grid = QGridLayout()
        grid.setSpacing(14)

        self.lbl_cpu, self.bar_cpu = self._make_stat("CPU", "#86efac")
        grid.addWidget(self._wrap_stat(self.lbl_cpu, self.bar_cpu), 0, 0)

        self.lbl_ram, self.bar_ram = self._make_stat("RAM", "#7dd3fc")
        grid.addWidget(self._wrap_stat(self.lbl_ram, self.bar_ram), 0, 1)

        self.lbl_disk, self.bar_disk = self._make_stat("Disco libre", "#fda4af")
        grid.addWidget(self._wrap_stat(self.lbl_disk, self.bar_disk), 1, 0)

        self.lbl_temp = QLabel("Temp: —")
        self.lbl_temp.setObjectName("info_text")
        self.lbl_temp.setFont(QFont("Segoe UI", 19, QFont.Bold))
        self.lbl_temp.setStyleSheet("color: #7a5230; background: transparent;")
        grid.addWidget(self.lbl_temp, 1, 1)

        sys_lay.addLayout(grid)
        cl.addWidget(sys_card)

        # ── 6. MANTENIMIENTO ─────────────────────────────────────────────────
        maint_card = _card("#fda4af")
        maint_lay = QVBoxLayout(maint_card)
        maint_lay.setContentsMargins(24, 16, 24, 16)
        maint_lay.setSpacing(10)
        lbl_mt = QLabel("Mantenimiento")
        lbl_mt.setObjectName("section_title")
        maint_lay.addWidget(lbl_mt)

        maint_row = QHBoxLayout()
        maint_row.setSpacing(12)

        self.btn_clean_tmp = QPushButton("Limpiar temporales")
        self.btn_clean_tmp.setObjectName("btn_action")
        self.btn_clean_tmp.clicked.connect(self._clean_tmp)

        self.btn_clean_logs = QPushButton("Limpiar logs")
        self.btn_clean_logs.setObjectName("btn_action")
        self.btn_clean_logs.clicked.connect(self._clean_logs)

        self.lbl_maint_status = QLabel("")
        self.lbl_maint_status.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.lbl_maint_status.setStyleSheet("color: #14532d; background: transparent;")

        maint_row.addWidget(self.btn_clean_tmp)
        maint_row.addWidget(self.btn_clean_logs)
        maint_row.addStretch()
        maint_row.addWidget(self.lbl_maint_status)
        maint_lay.addLayout(maint_row)
        cl.addWidget(maint_card)

        # ── 7. APAGADO / REINICIO ────────────────────────────────────────────
        action_row = QHBoxLayout()
        action_row.setSpacing(16)
        self.btn_restart = QPushButton("Reiniciar")
        self.btn_restart.setObjectName("btn_restart")
        self.btn_restart.clicked.connect(self._safe_restart)
        self.btn_poweroff = QPushButton("Apagar")
        self.btn_poweroff.setObjectName("btn_poweroff")
        self.btn_poweroff.clicked.connect(self._safe_poweroff)
        action_row.addWidget(self.btn_restart)
        action_row.addWidget(self.btn_poweroff)
        cl.addLayout(action_row)

        scroll.setWidget(content)
        root.addWidget(scroll)

        # ── Timers ───────────────────────────────────────────────────────────
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._update_clock)

        self._sys_timer = QTimer(self)
        self._sys_timer.setInterval(6000)
        self._sys_timer.timeout.connect(self._update_system)

        # Timer para limpiar mensaje de mantenimiento
        self._maint_clear_timer = QTimer(self)
        self._maint_clear_timer.setSingleShot(True)
        self._maint_clear_timer.setInterval(4000)
        self._maint_clear_timer.timeout.connect(lambda: self.lbl_maint_status.setText(""))

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _make_stat(self, label: str, color: str):
        """@brief Crea un widget de barra de progreso para estadísticas del sistema."""
        lbl = QLabel(f"{label}: —")
        lbl.setObjectName("info_text")
        lbl.setFont(QFont("Segoe UI", 17, QFont.Bold))
        lbl.setStyleSheet("color: #5a3300; background: transparent;")
        bar = QProgressBar()
        bar.setStyleSheet(
            f"QProgressBar {{ border:none; border-radius:8px; background:#f1e8d8; max-height:16px; color:transparent; }}"
            f"QProgressBar::chunk {{ background:{color}; border-radius:8px; }}"
        )
        bar.setValue(0)
        return lbl, bar

    def _wrap_stat(self, lbl, bar):
        
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        lay.addWidget(lbl)
        lay.addWidget(bar)
        return w

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    def showEvent(self, event):
        """@brief Inicia los timers al mostrar la pantalla."""
        super().showEvent(event)
        self._update_clock()
        self._update_volume()
        self._update_system()
        self._bt_refresh_state()
        self._wifi_refresh()
        self._clock_timer.start()
        self._sys_timer.start()

    def hideEvent(self, event):
        """@brief Detiene los procesos en segundo plano al cerrar."""
        self._clock_timer.stop()
        self._sys_timer.stop()
        super().hideEvent(event)

    # ── Reloj y uptime ───────────────────────────────────────────────────────

    def _update_clock(self):
        """@brief Actualiza el reloj, fecha y tiempo de actividad (uptime)."""
        self.lbl_time.setText(QTime.currentTime().toString("HH:mm:ss"))
        self.lbl_date.setText(QDate.currentDate().toString("dddd, d 'de' MMMM 'de' yyyy"))
        try:
            out = subprocess.check_output(["uptime", "-p"]).decode().strip()
            self.lbl_uptime.setText(f"Activo: {out.replace('up ', 'Encendido hace ')}")
        except Exception:
            pass

    # ── Volumen ───────────────────────────────────────────────────────────────

    def _change_volume(self, delta: int):
        """@brief Cambia el nivel de volumen actual vía amixer."""
        try:
            sign = "+" if delta > 0 else "-"
            subprocess.run(
                ["amixer", "set", "Master", f"{abs(delta)}%{sign}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self._update_volume()
        except Exception as e:
            logger.error(f"[SETTINGS] Volumen: {e}")

    def _update_volume(self):
        """@brief Lee el nivel de volumen actual vía amixer."""
        try:
            out = subprocess.check_output(["amixer", "get", "Master"]).decode()
            if "[" in out and "%]" in out:
                val = int(out.split("[")[1].split("%]")[0])
                self.lbl_vol.setText(f"{val}%")
                self.bar_vol.setValue(val)
        except Exception:
            self.lbl_vol.setText("—")

    # ── Bluetooth ────────────────────────────────────────────────────────────

    def _run_cmd(self, cmd: list) -> str:
        """@brief Lanza comando de aplicaciones internas"""
        try:
            return subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            return ""

    def _bt_refresh_state(self):
        """@brief Recarga el estado de bluetooth."""
        out = self._run_cmd(["bluetoothctl", "show"])
        if "Powered: yes" in out:
            self.lbl_bt_state.setText("Encendido")
            self.lbl_bt_state.setStyleSheet("color: #14532d; background: transparent; font-weight: 800;")
        else:
            self.lbl_bt_state.setText("Apagado")
            self.lbl_bt_state.setStyleSheet("color: #b91c1c; background: transparent; font-weight: 800;")

    def _bt_enable(self):
        """@brief Habilitar bluetooth."""
        subprocess.run(["bluetoothctl", "power", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._bt_refresh_state()

    def _bt_disable(self):
        """@brief Deshabilitar bluetooth."""
        subprocess.run(["bluetoothctl", "power", "off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.list_bt.hide()
        self._bt_refresh_state()

    def _bt_scan(self):
        """@brief Inicia el escaneo de dispositivos Bluetooth en un hilo separado."""
        self.btn_bt_scan.setText("Buscando…")
        self.btn_bt_scan.setEnabled(False)
        self.list_bt.clear()
        threading.Thread(target=self._bt_scan_thread, daemon=True).start()

    def _bt_scan_thread(self):
        """@brief Lógica de escaneo (ejecución síncrona en hilo)."""
        try:
            # Escanear 8 segundos
            subprocess.run(
                ["bluetoothctl", "--timeout", "8", "scan", "on"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10
            )
            out = subprocess.check_output(
                ["bluetoothctl", "devices"], stderr=subprocess.DEVNULL
            ).decode()
            devices = []
            for line in out.strip().splitlines():
                parts = line.strip().split(" ", 2)
                if len(parts) >= 3:
                    devices.append(f"Disp: {parts[2]}  ({parts[1]})")
            self._bt_scan_done.emit(devices)
        except Exception as e:
            logger.error(f"[SETTINGS] BT scan: {e}")
            self._bt_scan_done.emit([])

    def _on_bt_scan_done(self, devices: list):
        """@brief Inicia el escaneo de dispositivos."""

        self.btn_bt_scan.setText("Buscar dispositivos")
        self.btn_bt_scan.setEnabled(True)
        self.list_bt.clear()
        if devices:
            for d in devices:
                self.list_bt.addItem(QListWidgetItem(d))
            self.list_bt.show()
        else:
            item = QListWidgetItem("No se encontraron dispositivos")
            self.list_bt.addItem(item)
            self.list_bt.show()

    # ── Wi-Fi ─────────────────────────────────────────────────────────────────

    def _wifi_enable(self):
        """@brief Habilitar wifi."""
        subprocess.run(["nmcli", "radio", "wifi", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        QTimer.singleShot(1500, self._wifi_refresh)

    def _wifi_disable(self):
        """@brief Deshabilitar wifi."""
        subprocess.run(["nmcli", "radio", "wifi", "off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        QTimer.singleShot(500, self._wifi_refresh)

    def _wifi_refresh(self):
        """@brief Recargar wifi."""        
        threading.Thread(target=self._wifi_refresh_thread, daemon=True).start()

    def _wifi_refresh_thread(self):
        """@brief Recargar wifi con hilos."""        

        try:
            # Estado radio
            radio = subprocess.check_output(
                ["nmcli", "radio", "wifi"], stderr=subprocess.DEVNULL
            ).decode().strip()
            estado = "enabled" if "enabled" in radio else "disabled"

            # Red activa
            out = subprocess.check_output(
                ["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "dev", "wifi"],
                stderr=subprocess.DEVNULL
            ).decode()
            red = "Sin conexión"
            for line in out.splitlines():
                parts = line.split(":")
                if parts[0] == "yes" and len(parts) >= 2:
                    ssid = parts[1]
                    signal = parts[2] if len(parts) > 2 else "?"
                    red = f"Red: {ssid}  ({signal}%)"
                    break

            # IP local
            ip_out = subprocess.check_output(
                ["hostname", "-I"], stderr=subprocess.DEVNULL
            ).decode().strip().split()[0] if True else ""
            try:
                ip_out = subprocess.check_output(["hostname", "-I"], stderr=subprocess.DEVNULL).decode().strip().split()[0]
            except Exception:
                ip_out = ""

            self._wifi_info_done.emit(estado, red + (f"  ·  IP: {ip_out}" if ip_out else ""))
        except Exception as e:
            logger.error(f"[SETTINGS] WiFi refresh: {e}")
            self._wifi_info_done.emit("unknown", "No disponible")

    def _on_wifi_info_done(self, estado: str, red: str):
        """@brief Estado del wifi."""        
        if estado == "enabled":
            self.lbl_wifi_net.setText("Encendido")
            self.lbl_wifi_net.setStyleSheet("color: #14532d; background: transparent; font-weight: 800;")
        else:
            self.lbl_wifi_net.setText("Apagado")
            self.lbl_wifi_net.setStyleSheet("color: #b91c1c; background: transparent; font-weight: 800;")
        self.lbl_wifi_ip.setText(red)

    # ── Sistema ───────────────────────────────────────────────────────────────

    def _update_system(self):
        """@brief Lee estadísticas de CPU, RAM, Disco y Temperatura de la Pi."""
        # CPU via /proc/stat (más ligero que top)
        try:
            with open("/proc/stat") as f:
                line = f.readline()
            parts = list(map(int, line.split()[1:]))
            idle = parts[3]
            total = sum(parts)
            cpu = round((1 - idle / total) * 100) if total else 0
            self.lbl_cpu.setText(f"CPU: {cpu}%")
            self.bar_cpu.setValue(cpu)
        except Exception:
            self.lbl_cpu.setText("CPU: —")

        # RAM
        try:
            out = subprocess.check_output(["free", "-m"]).decode()
            parts = out.splitlines()[1].split()
            total_r, used_r = int(parts[1]), int(parts[2])
            pct = round(used_r / total_r * 100)
            self.lbl_ram.setText(f"RAM: {used_r}/{total_r} MB")
            self.bar_ram.setValue(pct)
        except Exception:
            self.lbl_ram.setText("RAM: —")

        # Disco
        try:
            out = subprocess.check_output(["df", "-h", "/"]).decode()
            parts = [p for p in out.splitlines()[1].split() if p]
            avail, pct_str = parts[3], parts[4]
            pct = int(pct_str.replace("%", ""))
            self.lbl_disk.setText(f"Libre: {avail} ({100 - pct}%)")
            self.bar_disk.setValue(pct)
        except Exception:
            self.lbl_disk.setText("Disco: —")

        # Temperatura Pi
        try:
            raw = open("/sys/class/thermal/thermal_zone0/temp").read().strip()
            temp = round(int(raw) / 1000, 1)
            aviso = " (!)" if temp >= 70 else ""
            self.lbl_temp.setText(f"Temp: {temp} °C{aviso}")
        except Exception:
            self.lbl_temp.setText("Temp: —")

    # ── Mantenimiento ─────────────────────────────────────────────────────────

    def _clean_tmp(self):
        """@brief Borrar /tmp."""
        try:
            subprocess.run(["find", "/tmp", "-type", "f", "-delete"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.lbl_maint_status.setText("OK: /tmp limpiado")
        except Exception as e:
            self.lbl_maint_status.setText("Error al limpiar")
            logger.error(f"[SETTINGS] clean_tmp: {e}")
        self._maint_clear_timer.start()

    def _clean_logs(self):
        """@brief Limpiar logs."""
        try:
            subprocess.run(
                ["sudo", "journalctl", "--vacuum-time=3d"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.lbl_maint_status.setText("OK: Logs limpiados")
        except Exception as e:
            self.lbl_maint_status.setText("Error al limpiar")
            logger.error(f"[SETTINGS] clean_logs: {e}")
        self._maint_clear_timer.start()

    # ── Apagado / Reinicio ────────────────────────────────────────────────────

    def _safe_poweroff(self):
        """@brief Ejecuta un comando de apagado seguro."""
        self.btn_poweroff.setText("Apagando…")
        self.btn_poweroff.setEnabled(False)
        logger.info("[SETTINGS] Apagado seguro")
        try:
            subprocess.Popen(["sudo", "poweroff"])
        except Exception as e:
            logger.error(f"[SETTINGS] poweroff: {e}")
            self.btn_poweroff.setText("Apagar")
            self.btn_poweroff.setEnabled(True)

    def _safe_restart(self):
        """@brief Ejecuta un comando de reinicio seguro."""
        self.btn_restart.setText("Reiniciando…")
        self.btn_restart.setEnabled(False)
        logger.info("[SETTINGS] Reinicio seguro")
        try:
            subprocess.Popen(["sudo", "reboot"])
        except Exception as e:
            logger.error(f"[SETTINGS] reboot: {e}")
            self.btn_restart.setText("Reiniciar")
            self.btn_restart.setEnabled(True)

    # ── Navegación ────────────────────────────────────────────────────────────

    def _go_back(self):
        """@brief Retorna al lanzador."""
        if hasattr(self.controller, "ui"):
            self.controller.ui.show_launcher()           
            
            

