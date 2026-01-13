"""
Chat Client - Part 2 of Networking Project
Connects to chat server and allows sending/receiving messages with other clients.
"""

import socket
import threading
import sys


class ChatClient:
    """Client that connects to chat server and handles messaging."""
    
    def __init__(self, host='localhost', port=9999):
        """
        Initialize the chat client.
        
        Args:
            host: Server host address
            port: Server port number
        """
        self.host = host
        self.port = port
        self.client_socket = None
        self.client_name = None
        self.running = False
    
    def connect(self, name: str):
        """
        Connect to the server and register with a name.
        
        Args:
            name: Unique name for this client
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            
            # Register with server
            register_message = f"REGISTER:{name}"
            self.client_socket.send(register_message.encode('utf-8'))
            
            # Wait for registration confirmation
            response = self.client_socket.recv(1024).decode('utf-8')
            
            if response == "REGISTERED":
                self.client_name = name
                self.running = True
                print(f"Connected to server as '{name}'")
                return True
            else:
                print(f"Registration failed: {response}")
                self.client_socket.close()
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            if self.client_socket:
                self.client_socket.close()
            return False
    
    def start(self):
        """Start the client - begin listening for messages in a separate thread."""
        if not self.running:
            print("Not connected to server")
            return
        
        # Start thread to receive messages
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()
        
        # Main loop for sending messages
        self.print_help()
        print()  # Empty line for spacing
        
        try:
            while self.running:
                user_input = input("Your message: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'help':
                    self.print_help()
                elif user_input.lower() == 'list':
                    self.list_clients()
                else:
                    # Command: send <name> <message>
                    if user_input.lower().startswith("send "):
                        parts = user_input[5:].strip().split(" ", 1)
                        if len(parts) == 2:
                            target, msg = parts
                            self.send_direct_message(target, msg)
                        else:
                            print("Usage: send <client_name> <message>")
                    else:
                        # Default: send as broadcast message to everyone
                        self.broadcast_message(user_input)
                    
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.disconnect()
    
    def receive_messages(self):
        """Receive messages from server in a separate thread."""
        try:
            while self.running:
                try:
                    message = self.client_socket.recv(1024).decode('utf-8')
                    if not message:
                        break
                    
                    self.handle_server_message(message)
                    
                except socket.error:
                    break
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    break
                    
        except Exception as e:
            print(f"Receive thread error: {e}")
        finally:
            self.running = False
            print("\nDisconnected from server")
    
    def handle_server_message(self, message: str):
        """
        Handle messages received from server.
        
        Args:
            message: Message string from server
        """
        if message.startswith("MESSAGE:"):
            # Format: MESSAGE:sender_name:message_content
            parts = message.split(":", 2)
            if len(parts) == 3:
                sender_name = parts[1]
                message_content = parts[2]
                print(f"\n[{sender_name}]: {message_content}")
                sys.stdout.write("Your message: ")
                sys.stdout.flush()
        
        elif message.startswith("STATUS:"):
            status = message.split(":", 1)[1]
            print(f"\n[Server]: {status}")
            sys.stdout.write("Your message: ")
            sys.stdout.flush()
        
        elif message.startswith("CLIENT_LIST:"):
            client_list = message.split(":", 1)[1]
            print(f"\nAvailable clients: {client_list}")
            sys.stdout.write("Your message: ")
            sys.stdout.flush()
        
        elif message.startswith("ERROR:"):
            error = message.split(":", 1)[1]
            print(f"\n[Error]: {error}")
            sys.stdout.write("Your message: ")
            sys.stdout.flush()
    
    def broadcast_message(self, message: str):
        """
        Send a broadcast message to all connected clients.
        
        Args:
            message: Message content to broadcast
        """
        if not self.running:
            print("Not connected to server")
            return
        
        try:
            broadcast_cmd = f"BROADCAST:{message}"
            self.client_socket.send(broadcast_cmd.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def send_direct_message(self, target_name: str, message: str):
        """
        Send a direct message to a specific client by name.
        
        Args:
            target_name: Name of the target client
            message: Message content
        """
        if not self.running:
            print("Not connected to server")
            return
        
        try:
            chat_cmd = f"CHAT:{target_name}:{message}"
            self.client_socket.send(chat_cmd.encode('utf-8'))
        except Exception as e:
            print(f"Error sending direct message: {e}")
    
    def list_clients(self):
        """Request list of available clients from server."""
        if not self.running:
            print("Not connected to server")
            return
        
        try:
            self.client_socket.send("LIST".encode('utf-8'))
            # Response will be handled in receive_messages thread
        except Exception as e:
            print(f"Error listing clients: {e}")
    
    def print_help(self):
        """Print help message with available commands."""
        print("\n" + "="*50)
        print("Simple Chat - Broadcast or direct messages")
        print("\nAvailable Commands:")
        print("  <message>               - Send to everyone (broadcast)")
        print("  send <name> <message>   - Send direct message to a client")
        print("  list                    - List all available clients")
        print("  help                    - Show this help message")
        print("  quit                    - Disconnect and exit")
        print("="*50)
    
    def disconnect(self):
        """Disconnect from server and close socket."""
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        print("Disconnected from server")


def main():
    """Main function to run the chat client."""
    if len(sys.argv) < 2:
        print("Usage: python chat_client.py <client_name>")
        print("Example: python chat_client.py Alice")
        sys.exit(1)
    
    client_name = sys.argv[1]
    client = ChatClient(host='localhost', port=9999)
    
    if client.connect(client_name):
        client.start()
    else:
        print("Failed to connect to server")
        sys.exit(1)


if __name__ == "__main__":
    main()
