# TCP and UDP Chat Server and Client

This repository provides a Python-based implementation of both TCP and UDP chat servers and clients. These programs allow multiple clients to connect to a server and exchange messages in real time. The project supports key functionalities like broadcasting messages, handling multiple clients, and cleanly shutting down the server and client connections.

---

## Features

### TCP Server and Client
- **ServerTCP**
  - Accepts client connections.
  - Handles client messages and broadcasts to other connected clients.
  - Provides client join/exit notifications.
  - Server shutdown.
  
- **ClientTCP**
  - Connects to the TCP server.
  - Sends and receives messages.
  - Disconnection from the server.

### UDP Server and Client
- **ServerUDP**
  - Accepts clients via unique usernames.
  - Handles client messages and broadcasts them to other connected clients.
  - Provides join/exit notifications.
  - Server shutdown.
  
- **ClientUDP**
  - Connects to the UDP server.
  - Sends and receives messages.
  - Exit and disconnection.

---

## Requirements

- Python 3.7 or later.
- Standard Python libraries (`socket`, `threading`, `select`).

---

## Usage

### 1. Running the TCP Server
```python
from your_file_name import ServerTCP

# Specify the port number
server = ServerTCP(server_port=12345)
server.run()
