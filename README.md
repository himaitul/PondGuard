# PondGuard
## A TCP/UDP-Based Intelligent Fish Pond Monitoring System

PondGuard is a Python-based fish pond monitoring application developed for a Computer Networks course project.

It demonstrates UDP sensor communication, TCP client-server communication, socket programming, JSON-based data exchange, and an autonomous Agentic AI decision system.

## Project Objectives

- Demonstrate UDP communication for sensor data transmission.
- Demonstrate TCP communication for reliable client-server commands.
- Monitor simulated fish pond water-quality readings.
- Detect abnormal temperature, pH, and dissolved oxygen levels.
- Use an autonomous agent to manage a virtual aerator.
- Demonstrate human approval for stopping aeration.

## System Architecture

```text
Simulated Sensor
      |
      | UDP (Port 9000)
      v
PondGuard Server
      |
      | Data Validation
      | Water Quality Monitoring
      | Agentic AI Decision Engine
      | Virtual Aerator Controller
      |
      ^ TCP (Port 9001)
      |
TCP Client
LAST / STATS / ALERTS / AGENT / LOG
APPROVE_STOP / REJECT_STOP
```

## Network Protocol Implementation

### UDP
- UDP server listens on port 9000.
- Simulated sensors send JSON datagrams.
- Each packet contains sequence number, temperature, pH, and dissolved oxygen.
- The server validates incoming packets and detects sequence gaps.

### TCP
- TCP server listens on port 9001.
- Client sends commands through TCP sockets.
- Server returns JSON responses.

Supported commands:
- LAST
- STATS
- ALERTS
- AGENT
- LOG
- AERATOR_STATE
- APPROVE_STOP
- REJECT_STOP

## Agentic AI Integration

The autonomous agent:
1. Analyzes sensor readings.
2. Evaluates oxygen trends and water-quality risks.
3. Switches the virtual aerator ON when oxygen is critically low or falling.
4. Monitors oxygen recovery.
5. Requests human confirmation before switching the aerator OFF.
6. Logs its actions.

The demonstrated system uses a deterministic autonomous decision engine. Optional LLM explanations require API configuration and were not enabled in the demonstration.

## Testing and Demonstration

**Automated tests: 21 / 21 passed.**

The end-to-end demonstration processed 12 simulated sensor readings and successfully demonstrated aerator activation, oxygen recovery, human approval, and shutdown.

## Project Files

- `server.py` — Main TCP/UDP server and agent logic
- `sensor.py` — Simulated sensor
- `client.py` — TCP client
- `demo.py` — End-to-end demonstration
- `automated_test.py` — Automated test suite
- `dashboard.py` — Dashboard module
- `server_updated.py` — Alternate server implementation

## How to Run

```bash
python -u demo.py
```

Run tests:

```bash
python -u automated_test.py
```

## Technologies

- Python
- TCP and UDP sockets
- JSON
- Client-server architecture
- Agentic AI decision logic

## Limitations

- Sensor readings are simulated; no physical sensor is connected.
- The aerator is virtual; no physical hardware is controlled.
- Demonstrated network communication uses localhost (`127.0.0.1`).
- Optional LLM explanations were not enabled.

## Future Improvements

- Connect real IoT sensors.
- Deploy across multiple networked devices.
- Integrate a physical aerator controller.
- Enable optional LLM explanations.
- Extend the dashboard.

## Conclusion

PondGuard demonstrates how TCP and UDP socket programming can work together in a practical monitoring application, combining network communication, sensor-data processing, automated testing, and autonomous decision-making.