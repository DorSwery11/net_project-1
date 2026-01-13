"""
Chat Server - Part 2 of Networking Project
Handles multiple clients and facilitates chat between them using TCP sockets.
"""

import socket
import threading
import sys
from typing import Dict, Optional


class ChatServer:
    """Server that manages client connections and routes messages between clients."""
    
    def __init__(self, host='localhost', port=9999):
        """
        Initialize the chat server.
        
        Args:
            host: Server host address
            port: Server port number
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients: Dict[str, socket.socket] = {}  # Maps client_name -> socket
        self.client_threads: Dict[str, threading.Thread] = {}  # Maps client_name -> thread
        self.lock = threading.Lock()  # For thread-safe operations
        
    def start(self):
        """Start the server and begin listening for connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)  # Can handle at least 5 clients
            print(f"Server started on {self.host}:{self.port}")
            print("Waiting for clients to connect...")
            
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"New connection from {address}")
                
                # Start a new thread for each client
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop()
    
    def handle_client(self, client_socket: socket.socket, address):
        """
        Handle communication with a single client.
        
        Args:
            client_socket: Socket connection to the client
            address: Client address tuple
        """
        client_name = None
        
        try:
            # First message should be the client's name
            name_message = client_socket.recv(1024).decode('utf-8')
            if not name_message:
                return
                
            # Parse registration: "REGISTER:client_name"
            if name_message.startswith("REGISTER:"):
                client_name = name_message.split(":", 1)[1].strip()
                
                with self.lock:
                    if client_name in self.clients:
                        client_socket.send("ERROR:Name already taken".encode('utf-8'))
                        client_socket.close()
                        return
                    self.clients[client_name] = client_socket
                    self.client_threads[client_name] = threading.current_thread()
                
                client_socket.send("REGISTERED".encode('utf-8'))
                print(f"Client '{client_name}' registered from {address}")
                self.broadcast_status(f"{client_name} joined the server")
                
            else:
                client_socket.send("ERROR:Must register first".encode('utf-8'))
                client_socket.close()
                return
            
            # Handle messages from client
            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                
                # Targeted chat: "CHAT:target:message"
                if message.startswith("CHAT:"):
                    parts = message.split(":", 2)
                    if len(parts) == 3:
                        target_name = parts[1].strip()
                        msg_content = parts[2]
                        self.send_message(client_name, target_name, msg_content)
                    else:
                        client_socket.send("ERROR:Invalid CHAT format".encode('utf-8'))
                
                # List available clients
                elif message == "LIST":
                    self.send_client_list(client_name)
                
                # Broadcast message to all clients
                elif message.startswith("BROADCAST:"):
                    message_content = message.split(":", 1)[1]
                    self.broadcast_message(client_name, message_content)
                
                else:
                    client_socket.send("ERROR:Unknown command".encode('utf-8'))
                    
        except ConnectionResetError:
            print(f"Client {client_name or address} disconnected unexpectedly")
        except Exception as e:
            print(f"Error handling client {client_name or address}: {e}")
        finally:
            if client_name:
                self.remove_client(client_name)
    
    def send_client_list(self, client_name: str):
        """
        Send list of available clients to a client.
        
        Args:
            client_name: Name of client requesting the list
        """
        with self.lock:
            if client_name not in self.clients:
                return
            
            try:
                available_clients = [name for name in self.clients.keys() if name != client_name]
                client_list = ",".join(available_clients) if available_clients else "No other clients"
                self.clients[client_name].send(
                    f"CLIENT_LIST:{client_list}".encode('utf-8')
                )
            except Exception as e:
                print(f"Error sending client list: {e}")
    
    def send_message(self, sender_name: str, target_name: str, message: str):
        """
        Send a message from one client to another (targeted).
        
        Args:
            sender_name: Name of the client sending the message
            target_name: Name of the target client
            message: Message content
        """
        with self.lock:
            if target_name not in self.clients:
                if sender_name in self.clients:
                    try:
                        self.clients[sender_name].send(
                            f"ERROR:Client '{target_name}' not found".encode('utf-8')
                        )
                    except:
                        pass
                return
            
            try:
                target_socket = self.clients[target_name]
                formatted_message = f"MESSAGE:{sender_name}:{message}"
                target_socket.send(formatted_message.encode('utf-8'))
                # Optional ack to sender
                if sender_name in self.clients:
                    self.clients[sender_name].send("MESSAGE_SENT".encode('utf-8'))
            except Exception as e:
                print(f"Error sending message from {sender_name} to {target_name}: {e}")
                if sender_name in self.clients:
                    try:
                        self.clients[sender_name].send("ERROR:Failed to send message".encode('utf-8'))
                    except:
                        pass
    
    def broadcast_message(self, sender_name: str, message: str):
        """
        Broadcast a message from one client to all other clients.
        
        Args:
            sender_name: Name of the client sending the message
            message: Message content to broadcast
        """
        with self.lock:
            formatted_message = f"MESSAGE:{sender_name}:{message}"
            for name, sock in self.clients.items():
                if name != sender_name:  # Don't send to sender
                    try:
                        sock.send(formatted_message.encode('utf-8'))
                    except:
                        pass
    
    def broadcast_status(self, status_message: str):
        """
        Broadcast a status message to all connected clients.
        
        Args:
            status_message: Status message to broadcast
        """
        with self.lock:
            for name, sock in self.clients.items():
                try:
                    sock.send(f"STATUS:{status_message}".encode('utf-8'))
                except:
                    pass
    
    def remove_client(self, client_name: str):
        """
        Remove a client from the server.
        
        Args:
            client_name: Name of client to remove
        """
        with self.lock:
            if client_name in self.clients:
                try:
                    self.clients[client_name].close()
                except:
                    pass
                del self.clients[client_name]
                if client_name in self.client_threads:
                    del self.client_threads[client_name]
                print(f"Client '{client_name}' disconnected")
                self.broadcast_status(f"{client_name} left the server")
    
    def stop(self):
        """Stop the server and close all connections."""
        print("Shutting down server...")
        with self.lock:
            for sock in self.clients.values():
                try:
                    sock.close()
                except:
                    pass
            self.clients.clear()
            self.client_threads.clear()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("Server stopped")


def main():
    """Main function to run the chat server."""
    server = ChatServer(host='localhost', port=9999)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer interrupted by user")
        server.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
