
import json
import math
import os
import socket
import threading
import time
import urllib.request
import urllib.error
from collections import deque
from datetime import datetime
from pathlib import Path

HOST = "127.0.0.1"
UDP_PORT = 9000
TCP_PORT = 9001

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "agent_actions.jsonl"

readings = []
lock = threading.RLock()


def now():
    return datetime.now().isoformat(timespec="seconds")


def valid_reading(r):
    if not isinstance(r, dict):
        return False

    required = ("seq", "temp", "ph", "oxygen")
    if any(key not in r for key in required):
        return False

    if isinstance(r["seq"], bool) or not isinstance(r["seq"], int):
        return False

    if r["seq"] < 1:
        return False

    for key in ("temp", "ph", "oxygen"):
        value = r[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if not math.isfinite(value):
            return False

    return True


class PondAgent:
    def __init__(self):
        self.history = deque(maxlen=5)
        self.aerator_on = False
        self.pending_stop_confirmation = False

        self.aeration_start_do = None
        self.aeration_samples = 0
        self.improvement_detected = False
        self.no_improvement_alerted = False

        self.risk_level = "NORMAL"
        self.last_action = "SYSTEM_STARTED"

        self.alerts = []
        self.logs = []
        self.active_conditions = set()

        self.lock = threading.RLock()
        self.llm_key = os.getenv("OPENAI_API_KEY", "")
        self.llm_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _record(self, event, **details):
        entry = {
            "timestamp": now(),
            "event": event,
            **details
        }

        self.logs.append(entry)

        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as exc:
            print("[AGENT] Log file error:", exc)

        print("[AGENT LOG]", entry)
        return entry

    def _alert(self, seq, message):
        alert = {
            "timestamp": now(),
            "seq": seq,
            "problem": message
        }

        self.alerts.append(alert)
        self._record("ALERT", **alert)
        print("[AGENT] ALERT:", message)

    def _llm_request(self, event, context):
        if not self.llm_key:
            return

        def worker():
            try:
                prompt = (
                    "You are the explanation component of a fish pond monitoring "
                    "system. Explain the water-quality risk and the action taken. "
                    "Use simple language for a fish farmer. Keep it under 100 words. "
                    "You must NOT change the deterministic controller decision, "
                    "issue commands, or recommend bypassing safety rules.\n\n"
                    + json.dumps(context, ensure_ascii=False)
                )

                payload = {
                    "model": self.llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Explain decisions only. Never control equipment."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 150
                }

                request = urllib.request.Request(
                    "https://api.openai.com/v1/chat/completions",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": "Bearer " + self.llm_key,
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )

                with urllib.request.urlopen(request, timeout=8) as response:
                    result = json.loads(response.read().decode("utf-8"))

                explanation = result["choices"][0]["message"]["content"]

                with self.lock:
                    self._record(
                        "LLM_EXPLANATION",
                        related_event=event,
                        explanation=explanation
                    )

                print("[LLM EXPLANATION]", explanation)

            except Exception as exc:
                print("[LLM] Explanation unavailable:", str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _start_aerator(self, reading, reason):
        self.aerator_on = True
        self.pending_stop_confirmation = False

        self.aeration_start_do = reading["oxygen"]
        self.aeration_samples = 0
        self.improvement_detected = False
        self.no_improvement_alerted = False

        self.last_action = "AERATOR_ON"

        self._record(
            "AERATOR_ON",
            seq=reading["seq"],
            oxygen=reading["oxygen"],
            reason=reason,
            aerator_state="ON"
        )

        self._alert(
            reading["seq"],
            "Low oxygen or falling oxygen trend detected. "
            "Virtual aerator switched ON. Reason: " + reason
        )

        self._llm_request(
            "AERATOR_ON",
            {
                "reading": reading,
                "reason": reason,
                "action": "Virtual aerator switched ON"
            }
        )

    def process(self, reading):
        with self.lock:
            self.history.append(reading)
            oxygen = reading["oxygen"]

            falling = (
                len(self.history) >= 3
                and self.history[-1]["oxygen"]
                < self.history[0]["oxygen"] - 0.5
            )

            low_oxygen = oxygen < 4.0

            temperature_problem = (
                reading["temp"] < 18 or reading["temp"] > 32
            )

            ph_problem = (
                reading["ph"] < 6.5 or reading["ph"] > 8.5
            )

            if oxygen < 3.0:
                self.risk_level = "CRITICAL"
            elif low_oxygen or falling or temperature_problem or ph_problem:
                self.risk_level = "HIGH"
            elif oxygen < 5.0:
                self.risk_level = "ELEVATED"
            else:
                self.risk_level = "NORMAL"

            if temperature_problem:
                if "temperature" not in self.active_conditions:
                    self._alert(
                        reading["seq"],
                        f"Temperature {reading['temp']}C outside safe range 18-32C"
                    )
                self.active_conditions.add("temperature")
            else:
                self.active_conditions.discard("temperature")

            if ph_problem:
                if "ph" not in self.active_conditions:
                    self._alert(
                        reading["seq"],
                        f"pH {reading['ph']} outside safe range 6.5-8.5"
                    )
                self.active_conditions.add("ph")
            else:
                self.active_conditions.discard("ph")

            oxygen_risk = low_oxygen or falling

            if oxygen_risk and not self.aerator_on:
                reason = (
                    "Dissolved oxygen below 4 mg/L"
                    if low_oxygen
                    else "Recent oxygen readings show a falling trend"
                )
                self._start_aerator(reading, reason)

            elif oxygen_risk and self.aerator_on:
                self.active_conditions.add("oxygen")

            else:
                self.active_conditions.discard("oxygen")

            if self.aerator_on:
                self.aeration_samples += 1

                baseline = self.aeration_start_do

                if (
                    baseline is not None
                    and oxygen >= baseline + 0.3
                    and not self.improvement_detected
                ):
                    self.improvement_detected = True

                    self._record(
                        "OXYGEN_IMPROVEMENT",
                        seq=reading["seq"],
                        initial_oxygen=baseline,
                        current_oxygen=oxygen,
                        improvement=round(oxygen - baseline, 2)
                    )

                    self._alert(
                        reading["seq"],
                        "Oxygen has improved after virtual aeration. "
                        "The agent continues monitoring."
                    )

                if (
                    self.aeration_samples >= 5
                    and not self.improvement_detected
                    and not self.no_improvement_alerted
                ):
                    self.no_improvement_alerted = True

                    self._alert(
                        reading["seq"],
                        "Oxygen has not improved after five readings. "
                        "Virtual aerator remains ON. Human inspection required."
                    )

                    self._record(
                        "NO_IMPROVEMENT_ESCALATION",
                        seq=reading["seq"],
                        oxygen=oxygen,
                        action="KEEP_AERATOR_ON"
                    )

                recent_safe = (
                    len(self.history) >= 3
                    and all(x["oxygen"] >= 5.5 for x in list(self.history)[-3:])
                )

                if recent_safe and not self.pending_stop_confirmation:
                    self.pending_stop_confirmation = True
                    self.last_action = "STOP_CONFIRMATION_REQUIRED"

                    self._record(
                        "STOP_CONFIRMATION_REQUIRED",
                        seq=reading["seq"],
                        oxygen=oxygen,
                        reason="Oxygen remained at or above 5.5 mg/L for three readings",
                        aerator_state="ON"
                    )

                    self._alert(
                        reading["seq"],
                        "Oxygen is stable and improved. The agent proposes "
                        "stopping the virtual aerator. Human confirmation required."
                    )

                    self._llm_request(
                        "STOP_CONFIRMATION_REQUIRED",
                        {
                            "reading": reading,
                            "action": "Request human approval to stop aerator",
                            "reason": "Three consecutive oxygen readings >= 5.5 mg/L"
                        }
                    )

                if self.pending_stop_confirmation and oxygen < 5.5:
                    self.pending_stop_confirmation = False

                    self._record(
                        "STOP_REQUEST_CANCELLED",
                        seq=reading["seq"],
                        oxygen=oxygen,
                        reason="Oxygen dropped below the safe stopping threshold",
                        aerator_state="ON"
                    )

            return {
                "risk_level": self.risk_level,
                "aerator_on": self.aerator_on,
                "pending_stop_confirmation": self.pending_stop_confirmation
            }

    def approve_stop(self):
        with self.lock:
            safe = (
                len(self.history) >= 3
                and all(x["oxygen"] >= 5.5 for x in list(self.history)[-3:])
            )

            if not self.pending_stop_confirmation or not safe:
                return {
                    "success": False,
                    "message": "Stop not approved: safety conditions are not satisfied."
                }

            self.aerator_on = False
            self.pending_stop_confirmation = False
            self.last_action = "AERATOR_OFF"

            self._record(
                "AERATOR_OFF",
                reason="Human approved stop after sustained oxygen improvement",
                aerator_state="OFF"
            )

            self._alert(
                self.history[-1]["seq"],
                "Human approved stopping the virtual aerator. Oxygen was stable."
            )

            self._llm_request(
                "AERATOR_OFF",
                {
                    "action": "Virtual aerator switched OFF",
                    "reason": "Human approved after stable oxygen readings"
                }
            )

            return {
                "success": True,
                "message": "Human approval accepted. Virtual aerator is OFF."
            }

    def reject_stop(self):
        with self.lock:
            if not self.pending_stop_confirmation:
                return {
                    "success": False,
                    "message": "There is no pending stop request."
                }

            self.pending_stop_confirmation = False
            self.last_action = "KEEP_AERATOR_ON"

            self._record(
                "STOP_REJECTED",
                reason="Human rejected stop request",
                aerator_state="ON"
            )

            return {
                "success": True,
                "message": "Stop rejected. Virtual aerator remains ON."
            }

    def snapshot(self):
        with self.lock:
            recent = list(self.history)

            trend = "insufficient data"
            if len(recent) >= 3:
                difference = recent[-1]["oxygen"] - recent[0]["oxygen"]
                if difference > 0.2:
                    trend = "rising"
                elif difference < -0.2:
                    trend = "falling"
                else:
                    trend = "stable"

            return {
                "risk_level": self.risk_level,
                "virtual_aerator": "ON" if self.aerator_on else "OFF",
                "pending_stop_confirmation": self.pending_stop_confirmation,
                "oxygen_trend": trend,
                "recent_oxygen": [x["oxygen"] for x in recent],
                "aeration_samples": self.aeration_samples,
                "oxygen_improvement_detected": self.improvement_detected,
                "last_action": self.last_action,
                "llm_api_configured": bool(self.llm_key),
                "llm_model": self.llm_model if self.llm_key else None
            }

    def recent_logs(self):
        with self.lock:
            return self.logs[-30:]


agent = PondAgent()
alerts = agent.alerts


def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, UDP_PORT))

    print(f"[UDP] listening on {HOST}:{UDP_PORT}", flush=True)

    last_seq = None

    while True:
        data, address = sock.recvfrom(4096)

        try:
            reading = json.loads(data.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            print("[UDP] rejected invalid JSON", flush=True)
            continue

        if not valid_reading(reading):
            print("[UDP] rejected invalid sensor data", flush=True)
            continue

        with lock:
            if last_seq is not None and reading["seq"] > last_seq + 1:
                missing = reading["seq"] - last_seq - 1
                print(
                    f"[UDP] WARNING: {missing} packet(s) may have been lost",
                    flush=True
                )

            last_seq = reading["seq"]
            readings.append(reading)
            state = agent.process(reading)

        print(f"[UDP] from {address} -> {reading}", flush=True)
        print("[AGENT STATE]", state, flush=True)


def handle_tcp_client(conn, address):
    with conn:
        try:
            command = conn.recv(4096).decode("utf-8").strip().upper()
        except (UnicodeDecodeError, OSError):
            return

        with lock:
            if command == "LAST":
                reply = readings[-1] if readings else "no data"

            elif command == "STATS":
                if not readings:
                    reply = "no data"
                else:
                    count = len(readings)
                    reply = {
                        "packets_received": count,
                        "avg_temp": round(
                            sum(x["temp"] for x in readings) / count, 2
                        ),
                        "avg_ph": round(
                            sum(x["ph"] for x in readings) / count, 2
                        ),
                        "avg_oxygen": round(
                            sum(x["oxygen"] for x in readings) / count, 2
                        )
                    }

            elif command == "ALERTS":
                reply = alerts if alerts else "no alerts"

            elif command == "AGENT":
                reply = agent.snapshot()

            elif command == "LOG":
                reply = agent.recent_logs()

            elif command == "AERATOR_STATE":
                reply = {
                    "aerator_on": agent.aerator_on
                }

            elif command == "APPROVE_STOP":
                reply = agent.approve_stop()

            elif command == "REJECT_STOP":
                reply = agent.reject_stop()

            else:
                reply = {
                    "error": "Unknown command",
                    "available_commands": [
                        "LAST", "STATS", "ALERTS", "AGENT", "LOG",
                        "AERATOR_STATE", "APPROVE_STOP", "REJECT_STOP"
                    ]
                }

        conn.sendall(
            json.dumps(reply, indent=2, ensure_ascii=False).encode("utf-8")
        )

        print(f"[TCP] {address} asked {command}", flush=True)


def tcp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, TCP_PORT))
    sock.listen()

    print(f"[TCP] listening on {HOST}:{TCP_PORT}", flush=True)

    while True:
        connection, address = sock.accept()

        threading.Thread(
            target=handle_tcp_client,
            args=(connection, address),
            daemon=True
        ).start()


if __name__ == "__main__":
    threading.Thread(target=udp_listener, daemon=True).start()
    threading.Thread(target=tcp_listener, daemon=True).start()

    print("[SERVER] Pond Monitor Agentic AI is running.", flush=True)

    if agent.llm_key:
        print("[LLM] API configured:", agent.llm_model, flush=True)
    else:
        print(
            "[LLM] No API key. Deterministic agent remains active; "
            "LLM explanations are disabled.",
            flush=True
        )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SERVER] stopped.", flush=True)
