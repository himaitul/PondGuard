
"""
Pond Monitor - Complete Automated Test Suite
Tests TCP, UDP, Agentic AI decisions and human approval.

Run:
    python automated_test.py
"""

import json
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SERVER_FILE = BASE_DIR / (
    sys.argv[1] if len(sys.argv) > 1 else "server.py"
)

HOST = "127.0.0.1"
UDP_PORT = 9000
TCP_PORT = 9001


def wait_for_server(process, timeout=8):
    deadline = time.time() + timeout

    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Server stopped unexpectedly.")

        try:
            with socket.create_connection(
                (HOST, TCP_PORT), timeout=0.3
            ):
                return
        except OSError:
            time.sleep(0.15)

    raise TimeoutError("Server did not start.")


def tcp_request(command):
    with socket.create_connection(
        (HOST, TCP_PORT), timeout=3
    ) as client:
        client.settimeout(3)
        client.sendall(command.encode("utf-8"))

        chunks = []

        while True:
            try:
                part = client.recv(4096)
            except socket.timeout:
                break

            if not part:
                break

            chunks.append(part)

    raw = b"".join(chunks).decode("utf-8")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def send_packet(udp, packet):
    udp.sendto(
        json.dumps(packet).encode("utf-8"),
        (HOST, UDP_PORT)
    )


def main():
    if not SERVER_FILE.exists():
        print("FAIL: server.py not found.")
        return 1

    results = []
    server_log = ""
    return_code = 0

    # Temporary file prevents server stdout pipe blocking.
    with tempfile.TemporaryFile(
        mode="w+t",
        encoding="utf-8"
    ) as server_output:

        process = subprocess.Popen(
            [sys.executable, "-u", str(SERVER_FILE)],
            cwd=str(BASE_DIR),
            stdout=server_output,
            stderr=subprocess.STDOUT
        )

        def check(label, passed):
            results.append((label, bool(passed)))

        try:
            wait_for_server(process)

            udp = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            )

            # PART 1: UDP and TCP tests

            packets = [
                {
                    "seq": 1,
                    "temp": 25.0,
                    "ph": 7.2,
                    "oxygen": 6.0
                },
                {
                    "seq": 2,
                    "temp": 26.0,
                    "ph": 7.1,
                    "oxygen": 3.0
                },
                {
                    "seq": 4,
                    "temp": 33.0,
                    "ph": 8.8,
                    "oxygen": 5.0
                }
            ]

            for packet in packets:
                send_packet(udp, packet)

            udp.sendto(
                b"{not valid json",
                (HOST, UDP_PORT)
            )

            send_packet(
                udp,
                {
                    "seq": 5,
                    "temp": "hot",
                    "ph": 7.0,
                    "oxygen": 5.0
                }
            )

            time.sleep(0.6)

            stats = tcp_request("STATS")
            alerts = tcp_request("ALERTS")
            last = tcp_request("LAST")
            initial_agent = tcp_request("AGENT")

            check(
                "UDP valid packets counted",
                isinstance(stats, dict)
                and stats.get("packets_received") == 3
            )

            check(
                "TCP STATS averages",
                isinstance(stats, dict)
                and stats.get("avg_temp") == 28.0
            )

            alert_text = ""

            if isinstance(alerts, list):
                alert_text = " ".join(
                    str(a.get("problem", ""))
                    for a in alerts
                    if isinstance(a, dict)
                ).lower()

            check(
                "Low oxygen alert",
                "dissolved oxygen" in alert_text
            )

            check(
                "Temperature alert",
                "temperature" in alert_text
            )

            check(
                "pH alert",
                "ph" in alert_text
            )

            check(
                "TCP LAST response",
                isinstance(last, dict)
                and last.get("seq") == 4
            )

            # PART 2: Autonomous agent decisions

            check(
                "Agent autonomously switched aerator ON",
                isinstance(initial_agent, dict)
                and initial_agent.get("virtual_aerator") == "ON"
            )

            check(
                "Agent detected HIGH risk",
                isinstance(initial_agent, dict)
                and initial_agent.get("risk_level") == "HIGH"
            )

            # PART 3: Oxygen recovery

            recovery_packets = [
                {
                    "seq": 5,
                    "temp": 27.0,
                    "ph": 7.2,
                    "oxygen": 5.8
                },
                {
                    "seq": 6,
                    "temp": 27.2,
                    "ph": 7.3,
                    "oxygen": 6.0
                },
                {
                    "seq": 7,
                    "temp": 27.1,
                    "ph": 7.2,
                    "oxygen": 6.2
                }
            ]

            for packet in recovery_packets:
                send_packet(udp, packet)

            time.sleep(0.6)

            recovery_agent = tcp_request("AGENT")
            logs = tcp_request("LOG")

            check(
                "Agent detected oxygen improvement",
                isinstance(recovery_agent, dict)
                and recovery_agent.get(
                    "oxygen_improvement_detected"
                ) is True
            )

            check(
                "Agent requested human stop confirmation",
                isinstance(recovery_agent, dict)
                and recovery_agent.get(
                    "pending_stop_confirmation"
                ) is True
            )

            check(
                "TCP LOG returns agent actions",
                isinstance(logs, list)
                and any(
                    item.get("event") == "AERATOR_ON"
                    for item in logs
                )
            )

            # PART 4: Human approval

            approval = tcp_request("APPROVE_STOP")

            check(
                "Human approval accepted",
                isinstance(approval, dict)
                and approval.get("success") is True
            )

            final_agent = tcp_request("AGENT")

            check(
                "Aerator switched OFF after approval",
                isinstance(final_agent, dict)
                and final_agent.get("virtual_aerator") == "OFF"
            )

            check(
                "Pending stop confirmation cleared",
                isinstance(final_agent, dict)
                and final_agent.get(
                    "pending_stop_confirmation"
                ) is False
            )

            check(
                "Final agent action is AERATOR_OFF",
                isinstance(final_agent, dict)
                and final_agent.get("last_action") == "AERATOR_OFF"
            )

            udp.close()

        except Exception as exc:
            print("TEST ERROR:", str(exc))
            return_code = 1

        finally:
            if process.poll() is None:
                process.terminate()

            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            server_output.seek(0)
            server_log = server_output.read()

    # PART 5: Server log verification

    log_checks = [
        (
            "UDP sequence-gap detection",
            "1 packet(s) may have been lost" in server_log
        ),
        (
            "Malformed JSON rejected",
            "rejected invalid JSON" in server_log
        ),
        (
            "Invalid sensor fields rejected",
            "rejected invalid sensor data" in server_log
        ),
        (
            "Agent logged AERATOR_ON",
            "'event': 'AERATOR_ON'" in server_log
        ),
        (
            "Agent logged STOP_CONFIRMATION_REQUIRED",
            "'event': 'STOP_CONFIRMATION_REQUIRED'" in server_log
        ),
        (
            "Agent logged AERATOR_OFF",
            "'event': 'AERATOR_OFF'" in server_log
        )
    ]

    results.extend(log_checks)

    print("\n===== POND MONITOR COMPLETE TEST RESULTS =====")

    for label, passed in results:
        print(
            "{}: {}".format(
                "PASS" if passed else "FAIL",
                label
            )
        )

    print("\n===== SERVER LOG EVIDENCE =====")
    print(server_log.strip())

    passed_count = sum(
        1 for _, passed in results if passed
    )

    total_count = len(results)

    print(
        "\nTOTAL:",
        passed_count,
        "/",
        total_count,
        "TESTS PASSED"
    )

    failed = [
        label for label, passed in results if not passed
    ]

    if failed:
        print("\nFAILED TESTS:", ", ".join(failed))
        return 1 if return_code == 0 else return_code

    print("\nALL POND MONITOR TESTS PASSED.")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
