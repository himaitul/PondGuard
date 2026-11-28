
# PondGuard
## A TCP/UDP-Based Intelligent Fish Pond Monitoring System

**Course:** Computer Networks  
**Assignment:** Assignment No. 4

## 1. Introduction

PondGuard is a Python-based fish pond monitoring application developed to demonstrate TCP and UDP communication through a practical client-server networking system.

The application uses UDP to transmit simulated sensor readings and TCP to provide reliable monitoring and control commands.

It also integrates an autonomous Agentic AI decision controller that analyzes water-quality readings and manages a virtual aerator.

## 2. Problem Statement

Fish ponds require continuous monitoring of water quality. Low dissolved oxygen, abnormal temperature, and unsuitable pH levels can create risks for aquatic life.

PondGuard demonstrates how network communication and autonomous decision-making can support a fish pond monitoring application.

## 3. Project Objectives

- Demonstrate UDP communication for sensor data transmission.
- Implement TCP client-server communication.
- Apply Python socket programming.
- Monitor simulated fish pond water-quality readings.
- Detect abnormal temperature, pH, and dissolved oxygen levels.
- Demonstrate UDP packet validation and sequence-gap detection.
- Integrate an autonomous Agentic AI decision controller.
- Demonstrate virtual aerator control and human approval.

## 4. System Architecture

PondGuard uses separate UDP and TCP communication channels.

### Network Configuration

| Component | Protocol | IP Address | Port |
|---|---|---|---|
| Sensor Simulator | UDP | 127.0.0.1 | 9000 |
| Monitoring Server | UDP Receiver | 127.0.0.1 | 9000 |
| Monitoring Client | TCP | 127.0.0.1 | 9001 |
| Monitoring Server | TCP Server | 127.0.0.1 | 9001 |

### Communication Flow

1. The sensor simulator generates water-quality readings.
2. Sensor readings are transmitted using UDP.
3. The server receives and validates incoming packets.
4. The Agentic AI controller analyzes the readings.
5. Monitoring clients connect through TCP.
6. Clients request statistics, alerts, agent status, and logs.
7. The server returns responses through TCP.

## 5. UDP Implementation

**UDP Port: 9000**

UDP is used for sensor data transmission.

Each JSON packet contains:

- Sequence number
- Temperature
- pH
- Dissolved oxygen

Example:

```json
{
  "seq": 1,
  "temp": 25.0,
  "ph": 7.2,
  "oxygen": 6.0
}
```

### UDP Features Demonstrated

- UDP socket creation and binding.
- Datagram transmission and reception.
- JSON packet parsing.
- Sensor data validation.
- Sequence-number monitoring.
- Detection of possible missing packets.
- Rejection of malformed JSON and invalid sensor data.

### Why UDP?

UDP provides connectionless datagram communication with low protocol overhead. It is suitable for demonstrating sensor telemetry without establishing a TCP connection for every reading.

UDP does not guarantee delivery, ordering, or retransmission. PondGuard uses sequence numbers to identify possible gaps in received packets.

## 6. TCP Implementation

**TCP Port: 9001**

TCP is used for monitoring and command communication between clients and the server.

The client establishes a TCP connection, sends a command, receives a response, and closes the connection.

### Supported TCP Commands

| Command | Function |
|---|---|
| LAST | Retrieve the latest sensor reading |
| STATS | Retrieve sensor statistics |
| ALERTS | Retrieve active alerts |
| AGENT | Retrieve agent status |
| LOG | Retrieve agent action history |
| AERATOR_STATE | Retrieve virtual aerator status |
| APPROVE_STOP | Approve stopping the aerator |
| REJECT_STOP | Reject stopping the aerator |

### Why TCP?

TCP provides connection-oriented, reliable, ordered byte-stream communication.

PondGuard uses TCP for monitoring requests and control commands where reliable communication is important.

## 7. TCP vs UDP Comparison

| Feature | TCP | UDP |
|---|---|---|
| Connection | Connection-oriented | Connectionless |
| Reliability | Reliable delivery | No delivery guarantee |
| Ordering | Ordered byte stream | No ordering guarantee |
| Acknowledgment | Uses acknowledgments | No transport-level acknowledgment |
| Retransmission | Supports retransmission | No automatic retransmission |
| PondGuard usage | Monitoring and commands | Sensor telemetry |

## 8. Agentic AI Integration

PondGuard includes an autonomous decision controller that processes incoming sensor readings.

Its workflow:

1. Observe incoming sensor readings.
2. Analyze water-quality conditions.
3. Evaluate oxygen trends and risk levels.
4. Decide whether aeration is required.
5. Activate the virtual aerator when oxygen is critically low or falling.
6. Monitor oxygen recovery.
7. Request human confirmation before stopping aeration.
8. Record decisions and actions in the action log.

The demonstrated system uses a deterministic autonomous decision engine that operates without an external LLM API key.

Optional LLM-based explanations require API configuration and were not enabled during the demonstration.

## 9. Automated Testing and Demonstration

**Verified automated test result: 21/21 tests passed in two consecutive runs.**

### Networking Tests

- UDP valid packet reception and counting.
- TCP statistics retrieval.
- TCP LAST response.
- TCP AGENT, ALERTS, and LOG commands.
- UDP sequence-gap detection.
- Malformed JSON rejection.
- Invalid sensor data rejection.

### Application and Agent Tests

- Low oxygen alert.
- Temperature alert.
- pH alert.
- Autonomous aerator activation.
- High-risk detection.
- Oxygen recovery detection.
- Stop confirmation request.
- Human approval.
- Aerator deactivation after approval.
- Agent action logging.

### End-to-End Demonstration

The demonstration successfully processed 12 simulated sensor readings and showed:

1. UDP sensor data transmission.
2. TCP monitoring commands.
3. Low oxygen detection.
4. Automatic virtual aerator activation.
5. Oxygen recovery monitoring.
6. Human approval to stop aeration.
7. Successful virtual aerator shutdown.

## 10. Project Files

| File | Description |
|---|---|
| `server.py` | Main TCP/UDP server and agent logic |
| `sensor.py` | Simulated sensor |
| `client.py` | TCP monitoring client |
| `demo.py` | End-to-end demonstration |
| `automated_test.py` | Automated test suite |
| `dashboard.py` | Dashboard module |
| `server_updated.py` | Alternate server implementation |
| `.gitignore` | Excludes temporary and sensitive files |

## 11. How to Run

### Requirements
- Python 3 installed
- Tkinter available for the graphical dashboard
- No external Python packages are required for the core system.

### Option 1: Run the GUI Dashboard

Open three separate terminals in the project directory.

**Terminal 1 — Start the Server**
```bash
python -u server.py
```

## 12. Technologies Used

- Python
- TCP socket programming
- UDP socket programming
- JSON
- Client-server architecture
- Agentic AI decision logic
- Automated testing
- PowerShell
- Git and GitHub

## 13. Project Limitations

- Sensor readings are simulated; no physical sensors are connected.
- The aerator is virtual and does not control physical equipment.
- Network communication was demonstrated locally using `127.0.0.1`.
- UDP sequence-gap detection identifies possible missing packets but does not guarantee exact network-loss measurement.
- Optional LLM explanations were not enabled during the reported tests.

## 14. Future Improvements

- Connect real IoT sensors.
- Deploy across multiple networked devices.
- Integrate a physical aerator controller.
- Add historical sensor data storage.
- Extend the monitoring dashboard.
- Measure network performance and latency.
- Enable optional LLM-based explanations.

## 15. Conclusion

PondGuard demonstrates the practical use of TCP and UDP protocols in a real-world-inspired monitoring application.

UDP handles simulated sensor telemetry, while TCP provides reliable monitoring and command communication. The application also demonstrates packet validation, sequence-gap detection, client-server architecture, automated testing, and Agentic AI-based autonomous decision-making.

The project combines Computer Networking concepts with an application addressing a real-world aquaculture monitoring problem.

**Build Something. Understand the Network. Demonstrate What You Create.**
