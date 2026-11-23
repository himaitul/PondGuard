
import json
import random
import socket
import sys
import time

SERVER = ("127.0.0.1", 9000)
TCP_SERVER = ("127.0.0.1", 9001)

count = int(sys.argv[1]) if len(sys.argv) > 1 else 20

oxygen = 3.2


def get_aerator_state():
    try:
        with socket.create_connection(TCP_SERVER, timeout=2) as client:
            client.sendall(b"AERATOR_STATE")
            response = client.recv(4096).decode("utf-8")
            result = json.loads(response)
            return result.get("aerator_on", False)
    except Exception:
        return False


udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("[SENSOR] Starting virtual pond sensor.")

for seq in range(1, count + 1):
    aerator_on = get_aerator_state()

    if aerator_on:
        oxygen = min(8.0, oxygen + 0.45)
    else:
        oxygen = max(2.5, oxygen + random.uniform(-0.12, 0.02))

    reading = {
        "seq": seq,
        "temp": round(random.uniform(26.0, 30.0), 1),
        "ph": round(random.uniform(7.0, 8.2), 2),
        "oxygen": round(oxygen, 2)
    }

    udp.sendto(
        json.dumps(reading).encode("utf-8"),
        SERVER
    )

    print(
        "sent:",
        reading,
        "| virtual aerator:",
        "ON" if aerator_on else "OFF"
    )

    time.sleep(1)

udp.close()

print("[SENSOR] Finished sending readings.")
