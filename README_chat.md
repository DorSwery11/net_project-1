# Chat Application - Part 2

Simple TCP-based chat application with server and multiple clients.

## Files

- `chat_server.py` - The chat server that manages client connections
- `chat_client.py` - The chat client application

## Requirements

- Python 3.x
- No external dependencies (uses only standard library)

## How to Run

### 1. Start the Server

Open a terminal and run:
```bash
python chat_server.py
```

The server will start on `localhost:8888` and wait for clients to connect.

### 2. Start Clients

Open additional terminals (at least 2) and run:
```bash
python chat_client.py <client_name>
```

For example:
```bash
python chat_client.py Alice
python chat_client.py Bob
python chat_client.py Charlie
```

Each client must have a unique name.

## Usage

### Client Commands

Once connected, clients can use these commands:

- **Just type a message and press Enter** - Broadcast to everyone
- `send <client_name> <message>` - Direct message to a specific client
- `list` - Show all available clients
- `help` - Show help message
- `quit` - Disconnect and exit

### Example Session

**Client 1 (Alice):**
```
> Hello everyone!
> send Bob Hi Bob, this is a private message.
```

**Client 2 (Bob):**
```
[Alice]: Hello everyone!
[Alice]: Hi Bob, this is a private message.

> Hi Alice! How are you?
```

**Client 3 (Charlie):**
```
[Alice]: Hello everyone!
[Bob]: Hi Alice! How are you?

> I'm here too!
```

**All clients will see all messages!**

## Features

- ✅ TCP protocol communication
- ✅ Bidirectional communication
- ✅ Server handles at least 5 clients simultaneously
- ✅ Clients can request chats with other clients by name
- ✅ Real-time messaging
- ✅ Error handling for disconnections
- ✅ Thread-safe server operations
- ✅ Simple text-based interface

## Architecture

- **Server**: Uses threading to handle multiple clients concurrently
- **Client**: Uses a separate thread to receive messages while main thread handles user input
- **Protocol**: Simple text-based protocol with command prefixes (REGISTER, CHAT, REQUEST, etc.)
