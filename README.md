# PondGuard
## A TCP/UDP-Based Intelligent Fish Pond Monitoring System

**Course:** Computer Networks  
**Assignment:** Assignment No. 4

## 1. Introduction

PondGuard is a Python-based network application designed to demonstrate TCP and UDP communication through a simulated fish pond monitoring system.

The project implements a client-server architecture using socket programming. UDP is used to transmit simulated sensor readings to the server, while TCP is used for reliable communication between monitoring clients and the server.

An Agentic AI-based decision controller processes the received sensor data, detects abnormal water conditions, and autonomously manages a virtual aerator.

The main focus of this project is to demonstrate practical Computer Networking concepts through a working application.

## 2. Problem Statement

Fish ponds require continuous monitoring of water quality. Low dissolved oxygen, abnormal temperature, and unsuitable pH levels can create serious risks for aquatic life.

PondGuard demonstrates how network communication can support a monitoring application by transmitting sensor data, processing information on a server, and providing monitoring and control services through TCP.

## 3. Project Objectives

- Implement TCP and UDP communication using Python socket programming.
- Demonstrate a practical client-server networking architecture.
- Transmit simulated sensor readings using UDP.
- Retrieve monitoring information and send commands using TCP.
- Demonstrate packet sequence-gap detection and invalid packet handling.
- Compare the behavior and purpose of TCP and UDP in one application.
- Integrate Agentic AI-based autonomous decision-making.
- Test and demonstrate the complete communication workflow.

## 4. Network Architecture

PondGuard uses a client-server architecture with separate UDP and TCP communication channels.

### Network Configuration

| Component | Protocol | IP Address | Port |
|---|---|---|---:|
| Sensor Simulator | UDP | 127.0.0.1 | 9000 |
| Monitoring Server | UDP Receiver | 127.0.0.1 | 9000 |
| Monitoring Client | TCP | 127.0.0.1 | 9001 |
| Monitoring Server | TCP Server | 127.0.0.1 | 9001 |

### Communication Flow

1. The sensor simulator generates water-quality readings.
2. Sensor readings are transmitted to the server using UDP.
3. The server receives and validates the UDP packets.
4. The Agentic AI controller analyzes the received readings.
5. Monitoring clients connect to the server using TCP.
6. Clients request sensor statistics, alerts, agent status, and action logs.
7. The server returns responses through TCP.

## 5. UDP Implementation

**UDP Port: 9000**

UDP is used for sensor data transmission.

The sensor simulator sends JSON-formatted packets containing:

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

UDP provides connectionless datagram communication with low protocol overhead. It is suitable for demonstrating sensor telemetry where individual readings can be sent without establishing a TCP connection for every transmission.

UDP does not guarantee delivery, ordering, or retransmission. PondGuard uses sequence numbers to detect possible gaps in received packets.

## 6. TCP Implementation

**TCP Port: 9001**

TCP is used for monitoring and command communication between clients and the server.

The client establishes a TCP connection, sends a command, receives the server response, and closes the connection.

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

PondGuard uses TCP for monitoring requests and control commands where reliable delivery and response handling are important.

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

PondGuard includes an autonomous decision controller that processes the sensor data received by the networking backend.

Its workflow:

1. Observe incoming sensor readings.
2. Analyze water-quality conditions.
3. Classify the current risk level.
4. Decide whether aeration is required.
5. Activate the virtual aerator when oxygen is critically low.
6. Monitor oxygen recovery.
7. Request human confirmation before stopping aeration.

The deterministic decision controller operates without requiring an external LLM API key. Optional LLM-based explanations were disabled during the reported automated tests.

## 9. Automated Testing

The project was tested using an automated test suite.

**Verified result: 21/21 tests passed in two consecutive runs.**

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
- HIGH risk detection.
- Oxygen improvement detection.
- Stop confirmation request.
- Human approval.
- Aerator deactivation after approval.
- Agent action logging.

## 10. Technologies Used

- Python
- TCP socket programming
- UDP socket programming
- Client-server architecture
- JSON
- Agentic decision-making logic
- Automated testing
- PowerShell

## 11. Project Limitations

- Sensor readings are simulated.
- Communication is demonstrated locally using the loopback address 127.0.0.1.
- The aerator is virtual and does not control physical equipment.
- UDP packet-gap detection identifies possible missing sequence numbers; it does not guarantee exact network-loss measurement.
- The optional LLM explanation component was not active during the reported tests.

## 12. Future Improvements

- Graphical network monitoring dashboard.
- Network communication between separate computers.
- Sensor data visualization and historical storage.
- Additional network performance measurements.
- Integration with physical IoT sensors and actuators.

## 13. Conclusion

PondGuard demonstrates the practical use of TCP and UDP protocols in a network-based application.

UDP handles simulated sensor telemetry, while TCP provides reliable monitoring and command communication. The application also demonstrates packet validation, sequence-gap detection, client-server communication, and Agentic AI-based autonomous decision-making.

The project combines Computer Networking concepts with an application that addresses a real-world aquaculture monitoring problem.

**Build Something. Understand the Network. Demonstrate What You Create.**
