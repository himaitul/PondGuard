
import json
import socket
import threading
import queue
import tkinter as tk
from tkinter import ttk
from datetime import datetime


SERVER = ("127.0.0.1", 9001)
REFRESH_INTERVAL = 2000

BG = "#101820"
PANEL = "#1B2836"
PANEL2 = "#243447"
TEXT = "#F1F5F9"
MUTED = "#A8B5C4"
GREEN = "#22C55E"
RED = "#EF4444"
ORANGE = "#F59E0B"
BLUE = "#38BDF8"


def tcp_request(command):
    """Send one TCP command and return the decoded server response."""
    with socket.create_connection(SERVER, timeout=2) as client:
        client.settimeout(2)
        client.sendall(command.encode("utf-8"))

        chunks = []
        while True:
            try:
                data = client.recv(4096)
            except socket.timeout:
                break

            if not data:
                break

            chunks.append(data)

    raw = b"".join(chunks).decode("utf-8")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


class PondDashboard:

    def __init__(self, root):
        self.root = root
        self.root.title("PondGuard | Agentic AI Monitoring Dashboard")
        self.root.geometry("1150x780")
        self.root.minsize(950, 650)
        self.root.configure(bg=BG)

        self.result_queue = queue.Queue()
        self.busy = False
        self.last_reading = None
        self.agent_data = {}
        self.oxygen_history = []

        self.setup_style()
        self.build_ui()

        self.root.after(300, self.refresh)
        self.root.after(200, self.process_queue)

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=PANEL,
            foreground=TEXT,
            fieldbackground=PANEL,
            rowheight=27,
            borderwidth=0
        )

        style.configure(
            "Treeview.Heading",
            background=PANEL2,
            foreground=TEXT,
            font=("Segoe UI", 9, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", "#36536D")],
            foreground=[("selected", "white")]
        )

    def label(self, parent, text, size=11, color=TEXT, bold=False):
        return tk.Label(
            parent,
            text=text,
            bg=parent.cget("bg"),
            fg=color,
            font=(
                "Segoe UI",
                size,
                "bold" if bold else "normal"
            )
        )

    def build_ui(self):

        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=22, pady=(18, 10))

        tk.Label(
            header,
            text="PONDGUARD",
            bg=BG,
            fg=BLUE,
            font=("Segoe UI", 24, "bold")
        ).pack(side="left")

        tk.Label(
            header,
            text="AGENTIC AI POND MONITORING SYSTEM",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(side="left", padx=15, pady=(12, 0))

        self.connection_label = tk.Label(
            header,
            text="● CONNECTING",
            bg=BG,
            fg=ORANGE,
            font=("Segoe UI", 10, "bold")
        )
        self.connection_label.pack(side="right", pady=12)

        self.time_label = tk.Label(
            self.root,
            text="",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9)
        )
        self.time_label.pack(anchor="e", padx=25)

        # Main sensor cards
        cards = tk.Frame(self.root, bg=BG)
        cards.pack(fill="x", padx=20, pady=12)

        self.temp_value = self.create_card(
            cards, "TEMPERATURE", "-- °C", "Water temperature"
        )

        self.ph_value = self.create_card(
            cards, "pH LEVEL", "--", "Water acidity / alkalinity"
        )

        self.oxygen_value = self.create_card(
            cards, "DISSOLVED OXYGEN", "-- mg/L", "Oxygen concentration"
        )

        # Agent status section
        status_frame = tk.Frame(self.root, bg=BG)
        status_frame.pack(fill="x", padx=20, pady=5)

        self.risk_value = self.create_status_card(
            status_frame, "AGENT RISK LEVEL", "WAITING"
        )

        self.aerator_value = self.create_status_card(
            status_frame, "VIRTUAL AERATOR", "UNKNOWN"
        )

        self.trend_value = self.create_status_card(
            status_frame, "OXYGEN TREND", "WAITING"
        )

        self.action_value = self.create_status_card(
            status_frame, "LAST AGENT ACTION", "WAITING"
        )

        # Middle section
        middle = tk.Frame(self.root, bg=BG)
        middle.pack(fill="both", expand=True, padx=20, pady=10)

        graph_panel = tk.Frame(middle, bg=PANEL)
        graph_panel.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 8)
        )

        self.label(
            graph_panel,
            "OXYGEN TREND (mg/L)",
            12,
            BLUE,
            True
        ).pack(anchor="w", padx=15, pady=12)

        self.graph = tk.Canvas(
            graph_panel,
            bg=PANEL,
            highlightthickness=0,
            height=260
        )
        self.graph.pack(fill="both", expand=True, padx=10, pady=10)
        self.graph.bind("<Configure>", lambda event: self.draw_graph())

        right_panel = tk.Frame(middle, bg=PANEL, width=330)
        right_panel.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(8, 0)
        )

        self.label(
            right_panel,
            "AGENT CONTROL",
            12,
            BLUE,
            True
        ).pack(anchor="w", padx=15, pady=12)

        self.pending_label = tk.Label(
            right_panel,
            text="No pending approval",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 10),
            wraplength=280
        )
        self.pending_label.pack(padx=15, pady=8)

        self.approve_button = tk.Button(
            right_panel,
            text="APPROVE STOP",
            command=lambda: self.send_action("APPROVE_STOP"),
            bg=GREEN,
            fg="#07130B",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=12,
            pady=10,
            state="disabled"
        )
        self.approve_button.pack(fill="x", padx=15, pady=5)

        self.reject_button = tk.Button(
            right_panel,
            text="REJECT STOP",
            command=lambda: self.send_action("REJECT_STOP"),
            bg=RED,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=12,
            pady=10,
            state="disabled"
        )
        self.reject_button.pack(fill="x", padx=15, pady=5)

        self.label(
            right_panel,
            "SYSTEM INFORMATION",
            10,
            BLUE,
            True
        ).pack(anchor="w", padx=15, pady=(18, 5))

        self.system_info = tk.Label(
            right_panel,
            text="Waiting for server...",
            bg=PANEL,
            fg=MUTED,
            justify="left",
            anchor="w",
            font=("Consolas", 9)
        )
        self.system_info.pack(fill="x", padx=15, pady=5)

        # Bottom log section: reserve a stable area so the history table remains visible.
        bottom = tk.Frame(self.root, bg=PANEL, height=190)
        bottom.pack(
            side="bottom",
            fill="x",
            expand=False,
            padx=20,
            pady=(5, 15)
        )
        bottom.pack_propagate(False)

        self.label(
            bottom,
            "AGENT ACTION HISTORY",
            12,
            BLUE,
            True
        ).pack(anchor="w", padx=15, pady=10)

        self.log_tree = ttk.Treeview(
            bottom,
            columns=("time", "event", "details"),
            show="headings",
            height=5
        )

        self.log_tree.heading("time", text="TIME")
        self.log_tree.heading("event", text="EVENT")
        self.log_tree.heading("details", text="DETAILS")

        self.log_tree.column("time", width=160, stretch=False)
        self.log_tree.column("event", width=210, stretch=False)
        self.log_tree.column("details", width=650, stretch=True)

        self.log_tree.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 12)
        )

        self.status_bar = tk.Label(
            self.root,
            text="PondGuard | Waiting for sensor data",
            bg=PANEL2,
            fg=MUTED,
            anchor="w",
            padx=15,
            pady=7,
            font=("Segoe UI", 9)
        )
        self.status_bar.pack(fill="x", side="bottom")

    def create_card(self, parent, title, value, subtitle):
        card = tk.Frame(parent, bg=PANEL, padx=15, pady=15)
        card.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(
            card,
            text=title,
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        value_label = tk.Label(
            card,
            text=value,
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 23, "bold")
        )
        value_label.pack(anchor="w", pady=8)

        tk.Label(
            card,
            text=subtitle,
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(anchor="w")

        return value_label

    def create_status_card(self, parent, title, value):
        card = tk.Frame(parent, bg=PANEL, padx=12, pady=12)
        card.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(
            card,
            text=title,
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        value_label = tk.Label(
            card,
            text=value,
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 13, "bold"),
            wraplength=190
        )
        value_label.pack(anchor="w", pady=8)

        return value_label

    def refresh(self):
        if not self.busy:
            self.busy = True
            threading.Thread(
                target=self.fetch_data,
                daemon=True
            ).start()

        self.root.after(REFRESH_INTERVAL, self.refresh)

    def fetch_data(self):
        try:
            result = {
                "last": tcp_request("LAST"),
                "stats": tcp_request("STATS"),
                "agent": tcp_request("AGENT"),
                "alerts": tcp_request("ALERTS"),
                "logs": tcp_request("LOG")
            }

            self.result_queue.put(("data", result))

        except Exception as exc:
            self.result_queue.put(("error", str(exc)))

    def update_dashboard(self, data):

        self.connection_label.config(
            text="● CONNECTED",
            fg=GREEN
        )

        self.time_label.config(
            text="Last update: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        reading = data.get("last")
        stats = data.get("stats")
        agent = data.get("agent", {})

        self.agent_data = agent

        if isinstance(reading, dict):
            self.last_reading = reading

            self.temp_value.config(
                text=f'{reading["temp"]:.1f} °C'
            )

            self.ph_value.config(
                text=f'{reading["ph"]:.2f}'
            )

            self.oxygen_value.config(
                text=f'{reading["oxygen"]:.2f} mg/L'
            )

            self.oxygen_history = agent.get("recent_oxygen", [])
            self.draw_graph()

        if isinstance(stats, dict):
            info = (
                f'Packets received: {stats.get("packets_received", 0)}\n'
                f'Average temperature: {stats.get("avg_temp", "--")} °C\n'
                f'Average pH: {stats.get("avg_ph", "--")}\n'
                f'Average oxygen: {stats.get("avg_oxygen", "--")} mg/L'
            )
        else:
            info = "Waiting for sensor readings..."

        self.system_info.config(text=info)

        risk = agent.get("risk_level", "UNKNOWN")
        aerator = agent.get("virtual_aerator", "UNKNOWN")
        trend = agent.get("oxygen_trend", "unknown")
        action = agent.get("last_action", "unknown")

        risk_colors = {
            "NORMAL": GREEN,
            "ELEVATED": ORANGE,
            "HIGH": RED,
            "CRITICAL": RED
        }

        self.risk_value.config(
            text=risk,
            fg=risk_colors.get(risk, TEXT)
        )

        self.aerator_value.config(
            text=aerator,
            fg=GREEN if aerator == "ON" else MUTED
        )

        self.trend_value.config(
            text=trend.upper(),
            fg=BLUE
        )

        self.action_value.config(
            text=action.replace("_", " "),
            fg=TEXT
        )

        pending = agent.get("pending_stop_confirmation", False)

        self.pending_label.config(
            text=(
                "Agent requests human approval to stop the aerator."
                if pending else
                "No pending approval."
            ),
            fg=ORANGE if pending else MUTED
        )

        button_state = "normal" if pending else "disabled"

        self.approve_button.config(state=button_state)
        self.reject_button.config(state=button_state)

        self.update_logs(data.get("logs", []))

        self.status_bar.config(
            text=(
                f"PondGuard | Risk: {risk} | "
                f"Aerator: {aerator} | "
                f"Packets: {stats.get('packets_received', 0) if isinstance(stats, dict) else 0}"
            )
        )

    def update_logs(self, logs):
        if not isinstance(logs, list):
            return

        existing = self.log_tree.get_children()

        for item in existing:
            self.log_tree.delete(item)

        for entry in reversed(logs[-20:]):
            timestamp = entry.get("timestamp", "")
            event = entry.get("event", "")

            details = {
                key: value
                for key, value in entry.items()
                if key not in ("timestamp", "event")
            }

            self.log_tree.insert(
                "",
                "end",
                values=(
                    timestamp,
                    event,
                    json.dumps(details, ensure_ascii=False)
                )
            )

    def draw_graph(self):
        canvas = self.graph
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width < 100 or height < 100:
            return

        left = 45
        right = width - 20
        top = 20
        bottom = height - 35

        for value in range(0, 11, 2):
            y = bottom - (value / 10) * (bottom - top)

            canvas.create_line(
                left, y, right, y,
                fill="#34495E"
            )

            canvas.create_text(
                25, y,
                text=str(value),
                fill=MUTED,
                font=("Segoe UI", 8)
            )

        canvas.create_text(
            left, height - 12,
            text="Older",
            fill=MUTED
        )

        canvas.create_text(
            right, height - 12,
            text="Latest",
            fill=MUTED
        )

        values = self.oxygen_history

        if not values:
            canvas.create_text(
                width / 2,
                height / 2,
                text="Waiting for oxygen readings...",
                fill=MUTED,
                font=("Segoe UI", 11)
            )
            return

        if len(values) == 1:
            x = (left + right) / 2
            y = bottom - (values[0] / 10) * (bottom - top)

            canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4,
                fill=BLUE,
                outline=BLUE
            )
            return

        points = []

        for index, value in enumerate(values):
            x = left + index * (right - left) / (len(values) - 1)
            y = bottom - (value / 10) * (bottom - top)
            points.extend([x, y])

        canvas.create_line(
            *points,
            fill=BLUE,
            width=3,
            smooth=True
        )

        for index in range(0, len(points), 2):
            x = points[index]
            y = points[index + 1]

            canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4,
                fill=GREEN,
                outline=GREEN
            )

    def send_action(self, command):
        self.approve_button.config(state="disabled")
        self.reject_button.config(state="disabled")

        threading.Thread(
            target=self.action_worker,
            args=(command,),
            daemon=True
        ).start()

    def action_worker(self, command):
        try:
            result = tcp_request(command)
            self.result_queue.put(("action", result))
        except Exception as exc:
            self.result_queue.put(("error", str(exc)))

    def process_queue(self):
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()

                if kind == "data":
                    self.update_dashboard(payload)

                elif kind == "action":
                    self.status_bar.config(
                        text="Agent response: " + json.dumps(payload)
                    )
                    self.refresh()

                elif kind == "error":
                    self.connection_label.config(
                        text="● SERVER OFFLINE",
                        fg=RED
                    )
                    self.status_bar.config(
                        text="Connection error: " + payload
                    )

                self.busy = False

        except queue.Empty:
            pass

        self.root.after(200, self.process_queue)


if __name__ == "__main__":
    root = tk.Tk()
    app = PondDashboard(root)
    root.mainloop()
