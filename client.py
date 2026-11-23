
import socket
import sys
import json

SERVER = ("127.0.0.1", 9001)

command = sys.argv[1] if len(sys.argv) > 1 else "STATS"

try:
    with socket.create_connection(SERVER, timeout=5) as client:
        client.settimeout(5)
        client.sendall(command.upper().encode("utf-8"))

        chunks = []

        while True:
            try:
                data = client.recv(4096)
            except socket.timeout:
                break

            if not data:
                break

            chunks.append(data)

    response = b"".join(chunks).decode("utf-8")

    try:
        print(json.dumps(json.loads(response), indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(response)

except OSError as exc:
    print("Connection error:", exc)
