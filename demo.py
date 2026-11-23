
import os
import subprocess
import sys
import time

folder = os.path.dirname(os.path.abspath(__file__))
py = sys.executable

server = subprocess.Popen(
    [py, "-u", "server.py"],
    cwd=folder
)

time.sleep(2)

try:
    print("\n===== UDP SENSOR SIMULATION =====")
    subprocess.run([py, "sensor.py", "12"], cwd=folder)

    time.sleep(1)

    commands = [
        "STATS",
        "ALERTS",
        "LAST",
        "AGENT",
        "LOG"
    ]

    for command in commands:
        print(f"\n===== TCP COMMAND: {command} =====")
        subprocess.run([py, "client.py", command], cwd=folder)

    answer = input(
        "\nIf AGENT shows pending_stop_confirmation=true, "
        "approve stopping the virtual aerator? (y/n/skip): "
    ).strip().lower()

    if answer == "y":
        subprocess.run([py, "client.py", "APPROVE_STOP"], cwd=folder)
    elif answer == "n":
        subprocess.run([py, "client.py", "REJECT_STOP"], cwd=folder)

    print("\n===== FINAL AGENT STATE =====")
    subprocess.run([py, "client.py", "AGENT"], cwd=folder)

finally:
    server.terminate()

    try:
        server.wait(timeout=3)
    except subprocess.TimeoutExpired:
        server.kill()

    print("\nDemo finished. Server stopped.")
