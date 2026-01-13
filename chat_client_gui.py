"""
Chat Client GUI - Part 2 of Networking Project
GUI version of the chat client with a simple window interface.
"""

import socket
import threading
import sys
import tkinter as tk
from tkinter import scrolledtext, messagebox


class ChatClientGUI:
    """GUI Client that connects to chat server and handles messaging."""
    
    def __init__(self, host='localhost', port=9999):
        """
        Initialize the chat client GUI.
        
        Args:
            host: Server host address
            port: Server port number
        """
        self.host = host
        self.port = port
        self.client_socket = None
        self.client_name = None
        self.running = False
        
        # GUI components
        self.root = None
        self.chat_display = None
        self.message_entry = None
        self.target_entry = None
        self.send_button = None
        
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
                return True
            else:
                messagebox.showerror("Connection Error", f"Registration failed: {response}")
                if self.client_socket:
                    self.client_socket.close()
                return False
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Connection error: {e}")
            if self.client_socket:
                self.client_socket.close()
            return False
    
    def create_gui(self):
        """Create and configure the GUI window."""
        self.root = tk.Tk()
        self.root.title(f"Chat - {self.client_name}")
        self.root.geometry("500x600")
        self.root.resizable(True, True)
        
        # Configure colors
        bg_color = "#f0f0f0"
        chat_bg = "#ffffff"
        button_color = "#4CAF50"  # Green color
        
        self.root.configure(bg=bg_color)
        
        # Chat display area (read-only)
        chat_frame = tk.Frame(self.root, bg=bg_color)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Label for chat area
        chat_label = tk.Label(chat_frame, text="Chat Messages:", bg=bg_color, font=("Arial", 10, "bold"))
        chat_label.pack(anchor="w")
        
        # Scrolled text widget for chat messages
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            width=50,
            height=20,
            bg=chat_bg,
            font=("Arial", 10),
            state=tk.DISABLED,
            relief=tk.SUNKEN,
            borderwidth=2
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Input area frame
        input_frame = tk.Frame(self.root, bg=bg_color)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Target entry field (optional) - FIRST
        target_label = tk.Label(input_frame, text="Target (optional, leave empty to broadcast):", bg=bg_color, font=("Arial", 9))
        target_label.pack(anchor="w")
        
        target_container = tk.Frame(input_frame, bg=bg_color)
        target_container.pack(fill=tk.X, pady=(5, 0))
        
        self.target_entry = tk.Entry(
            target_container,
            font=("Arial", 10),
            relief=tk.SUNKEN,
            borderwidth=2
        )
        self.target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Message entry field - SECOND
        entry_label = tk.Label(input_frame, text="Your message:", bg=bg_color, font=("Arial", 9))
        entry_label.pack(anchor="w", pady=(10, 0))
        
        entry_container = tk.Frame(input_frame, bg=bg_color)
        entry_container.pack(fill=tk.X, pady=(5, 0))
        
        self.message_entry = tk.Entry(
            entry_container,
            font=("Arial", 11),
            relief=tk.SUNKEN,
            borderwidth=2
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # Send button (green)
        self.send_button = tk.Button(
            entry_container,
            text="Send",
            command=self.send_message,
            bg=button_color,
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.RAISED,
            borderwidth=2,
            padx=20,
            pady=5,
            cursor="hand2"
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # List button (optional)
        list_button = tk.Button(
            input_frame,
            text="List Clients",
            command=self.list_clients,
            bg="#2196F3",
            fg="white",
            font=("Arial", 9),
            relief=tk.RAISED,
            borderwidth=1,
            padx=10,
            pady=3,
            cursor="hand2"
        )
        list_button.pack(anchor="w", pady=(5, 0))
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Focus on message entry
        self.message_entry.focus()
    
    def add_message_to_chisplay(self, sender: str, message: str, is_status=False):
        """
        Add a message to the chat display.
        
        Args:
            sender: Name of the sender
            message: Message content
            is_status: True if this is a status message
        """
        if not self.chat_display:
            return
            
        self.chat_display.config(state=tk.NORMAL)
        
        if is_status:
            self.chat_display.insert(tk.END, f"[{sender}]: {message}\n", "status")
        else:
            self.chat_display.insert(tk.END, f"[{sender}]: {message}\n")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)  # Auto-scroll to bottom
    
    def send_message(self):
        """Send the message from the entry field."""
        if not self.running:
            messagebox.showwarning("Not Connected", "Not connected to server")
            return
        
        message = self.message_entry.get().strip()
        target = self.target_entry.get().strip() if self.target_entry else ""
        if not message:
            return
        
        # Don't send commands through GUI
        if message.lower() in ['quit', 'help']:
            return
        
        try:
            if target:
                chat_cmd = f"CHAT:{target}:{message}"
                self.client_socket.send(chat_cmd.encode('utf-8'))
                self.add_message_to_chisplay(f"You -> {target}", message)
            else:
                broadcast_cmd = f"BROADCAST:{message}"
                self.client_socket.send(broadcast_cmd.encode('utf-8'))
                self.add_message_to_chisplay("You", message)
            
            # Clear only message field (keep target)
            self.message_entry.delete(0, tk.END)
            
        except Exception as e:
            messagebox.showerror("Send Error", f"Error sending message: {e}")
            self.running = False
    
    def list_clients(self):
        """Request list of available clients from server."""
        if not self.running:
            messagebox.showwarning("Not Connected", "Not connected to server")
            return
        
        try:
            self.client_socket.send("LIST".encode('utf-8'))
        except Exception as e:
            messagebox.showerror("Error", f"Error listing clients: {e}")
    
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
                    if self.running:
                        self.root.after(0, lambda: messagebox.showerror("Receive Error", f"Error receiving message: {e}"))
                    break
                    
        except Exception as e:
            if self.running:
                self.root.after(0, lambda: messagebox.showerror("Receive Error", f"Receive thread error: {e}"))
        finally:
            self.running = False
            if self.root:
                self.root.after(0, self.on_closing)
    
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
                # Update GUI in main thread
                self.root.after(0, lambda: self.add_message_to_chisplay(sender_name, message_content))
        
        elif message.startswith("STATUS:"):
            status = message.split(":", 1)[1]
            self.root.after(0, lambda: self.add_message_to_chisplay("Server", status, is_status=True))
        
        elif message.startswith("CLIENT_LIST:"):
            client_list = message.split(":", 1)[1]
            self.root.after(0, lambda: self.add_message_to_chisplay("Server", f"Connected clients: {client_list}", is_status=True))
        
        elif message.startswith("ERROR:"):
            error = message.split(":", 1)[1]
            self.root.after(0, lambda: messagebox.showerror("Error", error))
    
    def on_closing(self):
        """Handle window closing event."""
        self.disconnect()
        if self.root:
            self.root.destroy()
    
    def disconnect(self):
        """Disconnect from server and close socket."""
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
    
    def start(self):
        """Start the GUI client."""
        if not self.running:
            messagebox.showerror("Error", "Not connected to server")
            return
        
        # Create GUI
        self.create_gui()
        
        # Start thread to receive messages
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()
        
        # Show welcome message
        self.add_message_to_chisplay("Server", f"Connected as '{self.client_name}'", is_status=True)
        self.add_message_to_chisplay("Server", "Type a message and click Send or press Enter", is_status=True)
        
        # Start GUI main loop
        self.root.mainloop()


def main():
    """Main function to run the GUI chat client."""
    if len(sys.argv) < 2:
        print("Usage: python chat_client_gui.py <client_name>")
        print("Example: python chat_client_gui.py Alice")
        sys.exit(1)
    
    client_name = sys.argv[1]
    client = ChatClientGUI(host='localhost', port=9999)
    
    if client.connect(client_name):
        client.start()
    else:
        print("Failed to connect to server")
        sys.exit(1)


if __name__ == "__main__":
    main()
