"""
Pond Monitor Server
- UDP port 9000: receives and validates sensor readings.
- TCP port 9001: answers LAST, STATS and ALERTS commands.
- A rule-based monitoring agent raises alerts for unsafe water readings.
"""
import json
import math
import socket
import threading
import time

HOST = "127.0.0.1"
UDP_PORT = 9000
TCP_PORT = 9001

readings = []
alerts = []
last_sequence = {}
lock = threading.Lock()


def valid_reading(data):
    """Return True only when the sensor packet has the required valid fields."""
    if not isinstance(data, dict):
        return False

    required = ("seq", "temp", "ph", "oxygen")
    if any(key not in data for key in required):
        return False

    # bool is a subclass of int in Python, so reject it explicitly.
    if isinstance(data["seq"], bool) or not isinstance(data["seq"], int):
        return False
    if data["seq"] < 1:
        return False

    for key in ("temp", "ph", "oxygen"):
        value = data[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if not math.isfinite(value):
            return False

    return True


def agent_check(reading):
    """Check one reading and return any water-quality warnings."""
    problems = []

    if reading["temp"] > 32 or reading["temp"] < 18:
        problems.append(
            f"temperature {reading['temp']}C out of range (18-32)"
        )

    if reading["ph"] > 8.5 or reading["ph"] < 6.5:
        problems.append(
            f"pH {reading['ph']} out of range (6.5-8.5)"
        )

    if reading["oxygen"] < 4:
        problems.append(
            f"dissolved oxygen {reading['oxygen']} mg/L too low (<4)"
        )

    return problems


def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, UDP_PORT))
    print(f"[UDP] listening on {HOST}:{UDP_PORT}", flush=True)

    while True:
        data, address = sock.recvfrom(2048)

        try:
            reading = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            print(f"[UDP] rejected invalid JSON from {address}", flush=True)
            continue

        if not valid_reading(reading):
            print(f"[UDP] rejected invalid sensor data from {address}", flush=True)
            continue

        # Track sequence numbers per sender. UDP itself does not guarantee delivery.
        sender = address
        with lock:
            previous = last_sequence.get(sender)

            if previous is not None and reading["seq"] > previous + 1:
                lost = reading["seq"] - previous - 1
                print(f"[UDP] WARNING: {lost} packet(s) may have been lost", flush=True)

            last_sequence[sender] = max(previous or 0, reading["seq"])
            readings.append(reading)

            problems = agent_check(reading)
            for problem in problems:
                alerts.append({
                    "seq": reading["seq"],
                    "problem": problem
                })

        print(f"[UDP] from {address} -> {reading}", flush=True)
        for problem in problems:
            print(f"[AGENT] ALERT: {problem}", flush=True)


def handle_tcp_client(connection, address):
    with connection:
        try:
            command = connection.recv(1024).decode("utf-8").strip().upper()
        except (UnicodeDecodeError, OSError):
            print(f"[TCP] invalid request from {address}", flush=True)
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
                            sum(item["temp"] for item in readings) / count, 2
                        ),
                        "avg_ph": round(
                            sum(item["ph"] for item in readings) / count, 2
                        ),
                        "avg_oxygen": round(
                            sum(item["oxygen"] for item in readings) / count, 2
                        )
                    }

            elif command == "ALERTS":
                reply = alerts if alerts else "no alerts"

            else:
                reply = "unknown command (use LAST, STATS, ALERTS)"

        connection.sendall(json.dumps(reply, indent=2).encode("utf-8"))
        print(f"[TCP] {address} asked {command}", flush=True)


def tcp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, TCP_PORT))
    sock.listen()
    print(f"[TCP] listening on {HOST}:{TCP_PORT}", flush=True)

    while True:
        connection, address = sock.accept()
        thread = threading.Thread(
            target=handle_tcp_client,
            args=(connection, address),
            daemon=True
        )
        thread.start()


if __name__ == "__main__":
    threading.Thread(target=udp_listener, daemon=True).start()
    threading.Thread(target=tcp_listener, daemon=True).start()

    print("[SERVER] Pond Monitor is running. Press Ctrl+C to stop.", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SERVER] stopped.", flush=True)
