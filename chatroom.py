import socket
import threading
import select

class ServerTCP:
    
    def __init__(self, server_port):
        
        self.server_port = server_port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Bind the socket to the port
        addr = socket.gethostbyname(socket.gethostname())    
        self.server_socket.bind((addr, self.server_port))

        # Listen for incoming connections 
        self.server_socket.listen(5)
        
        # Dictionary to store the client addresses and names
        self.clients = {}
        
        # Threading events
        self.run_event = threading.Event()
        self.handle_event = threading.Event()
        
    def accept_client(self):
        
        try:
            # Ensure the socket is available
            if select.select([self.server_socket], [], [], 1)[0]:
                client_socket, client_address = self.server_socket.accept()
                
                # Recieve client namne
                client_name = client_socket.recv(1024).decode()
                
                # If name is already taken false is returned
                if client_name in self.clients.values():
                    client_socket.send("Name already taken".encode())
                    client_socket.close()
                    return False
                
                # Otherwise try to accept the client
                else:
                    self.clients[client_socket] = client_name
                    welcome_message = "Welcome"
                    client_socket.send(welcome_message.encode())
                    
                    # Broadcast a message saying the user has joined
                    join_message = "join"
                    self.broadcast(client_socket, join_message)
                    
                    return True
                
        except Exception as e:
            return False
        
    def close_client(self, client_socket):
        
        if client_socket in self.clients:
            
            # Remove the client from dictionary
            del self.clients[client_socket]
            
            client_socket.close()
            
            return True
        
        else:
            # Client not found
            return False
            
    def broadcast(self, client_socket_sent, message):
        
        # Determine the most appropriate message based on the parameter
        client_name = self.clients.get(client_socket_sent, "Unknown")
        if message == 'join':
            broadcast_message = f"User {client_name} joined"
        elif message == 'exit':
            broadcast_message = f"User {client_name} left"
        else:
            broadcast_message = f"{client_name}: {message}"
        
        # Send broadcast message to all except who sent it
        for client_socket in self.clients:
            # Make sure we do not send it to the sender
            if client_socket != client_socket_sent:
                client_socket.send(broadcast_message.encode())
        
    def shutdown(self):
        
        # Send message that the server is being shut down
        self.broadcast(None, "server-shutdown")
        
        # Close all of the client sockets
        for client_socket in list(self.clients):    
            self.close_client(client_socket)
                        
        # Set the run_event and handle_event to stop operation
        self.run_event.set()
        self.handle_event.set()
        
        # Close the server socket
        self.server_socket.close()
        
    def get_clients_number(self):
        
        return len(self.clients)
        
    def handle_client(self, client_socket):
        # Listen for messages until the client is set
        while not self.handle_event.is_set():
            try:
                if select.select([client_socket], [], [], 1)[0]:
                    # receive and decode the message
                    message = client_socket.recv(1024).decode()
                    
                    self.broadcast(client_socket, message)
                    
                    # Exite loop to close the client
                    if 'exit' in message:
                        break
            except Exception as e:
                break
        self.close_client(client_socket)
        
    def run(self):
        
        while not self.run_event.is_set():
            try:
                if select.select([self.server_socket], [], [], 1)[0]: 
                    # Accept new connection
                    client_accepted = self.accept_client()
                    
                    if client_accepted:
                        # Get the most recent connection and create a thread
                        client_socket = list(self.clients.keys())[-1]
                        client_thread = threading.Thread(target=self.handle_client, args = (client_socket,))
                        client_thread.start()
                    
            # If exception is thrown exit loop and shutdown 
            except KeyboardInterrupt:
                print("Keyboard interrupt")
                break
            except Exception as e:
                print(f"Error: {e}")
                break
        self.shutdown()


class ClientTCP:
    def __init__(self, client_name, server_port):
        # get local host
        self.server_addr = socket.gethostbyname(socket.gethostname())
        
        # Set up client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_port = server_port
        self.client_name = client_name
        # Initialize threading
        self.exit_run = threading.Event()
        self.exit_receive = threading.Event()
        
    def connect_server(self):
        
        try:
            # Connect to server
            self.client_socket.connect((self.server_addr, self.server_port))
            
            # Send client name to server
            self.client_socket.send(self.client_name.encode())
            
            response = self.client_socket.recv(1024).decode()
            
            # Check if the client joined the chatroom
            if 'Welcome' in response:
                return True
            else:
                return False
        
        except Exception as e:
            return False

    def send(self, text):
        
        # Encode message and send it to the server through the clients socket
        self.client_socket.send(text.encode())
        
    def receive(self):
        
        # Loop and listen for messages
        while not self.exit_receive.is_set():
            #Listen and receive message
            if select.select([self.client_socket], [], [], 1)[0]:
                message = self.client_socket.recv(1024).decode()
                print(f"{message}")
                
                # If the message is server-shutdown, set events
                if 'server-shutdown' in message:
                    
                    self.exit_run.set()
                    self.exit_receive.set()
                    
                    break
                # If not server-shutdown dhow message
                
    def run(self):
        
        # Connect to server
        if self.connect_server():
        
            receive_thread = threading.Thread(target=self.receive)
            receive_thread.start()
            
            try:    
            # Runs unill the exit run is set
                while not self.exit_run.is_set():
                    message = input(f"{self.client_name}:")
                    self.send(message)
                    
                    if message == 'exit':
                        # set the events
                        self.exit_run.set()
                        self.exit_receive.set()
                        break
            # Set the Events
            except KeyboardInterrupt:
                self.send('exit')
                self.exit_run.set()
                self.exit_receive.set()
                

class ServerUDP:
    def __init__(self, server_port):
        
        self.server_port = server_port
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        server_addr = socket.gethostbyname(socket.gethostname())
        # Bind 
        self.server_socket.bind((server_addr, self.server_port))

        self.clients = {}
        self.messages = []
    
    def accept_client(self, client_addr, message):
        
        try:
            
            # get the name of the client from the message
            client_name = message.split(":", 1)[0].strip()
            
            # Check if name is already taken
            if client_name in self.clients.values():
                self.send("Name already taken")
                return False
            else:
                self.clients[client_addr] = client_name
                self.server_socket.sendto(b"Welcome", client_addr)

                # dont do anything with this
                join_message = f"{client_name} joined"
                
                # Append a tuple to add to messages
                self.messages.append((None, join_message))
                self.broadcast()
                
                return True
            
        except Exception as e:
            return False

    def close_client(self, client_addr):
        
        #change how this is done
        if client_addr in self.clients:
            
            # Get the name of the client
            client_name = self.clients.get(client_addr, "Unknown")
            
            del self.clients[client_addr]
            
            # remove cline and lose the client
            message = f'User {client_name} left'
            self.messages.append((client_addr, message))
            self.broadcast()
            return True
        else:
            return False
        
    def broadcast(self):
        
        # Get the most recent message to broadcast
        sender_addr, message = self.messages[-1]
        
        # skip the sender when sending the message back
        for client_addr in self.clients:
            if client_addr is None or client_addr != sender_addr:
                # Send the message with the client address
                self.server_socket.sendto(message.encode(), client_addr)
        
    def shutdown(self):
        
        shutdown_message = "server-shutdown"
        for client_addr in list(self.clients.keys()):
            self.server_socket.sendto(shutdown_message.encode(), client_addr)
            self.close_client(client_addr)
        
        # Close the server
        self.server_socket.close()
    
    def get_clients_number(self):
        return len(self.clients)
    
    def run(self):
        # Continuously listen for messages
        while True:
            
            try:
                #
                if select.select([self.server_socket], [], [], 1)[0]: 
                    # Receive tha data and decode it
                    message, client_addr = self.server_socket.recvfrom(1024)
                    message = message.decode()

                    # Determine what to do
                    #call accept client
                    if 'join' in message:
                        self.accept_client(client_addr, message)
                        # Call close client
                    elif 'exit' in message:
                        self.close_client(client_addr)
                    elif client_addr in self.clients:
                        self.messages.append((client_addr, message))
                        self.broadcast()

            # If there is an exception break the loop and shutdown
            except KeyboardInterrupt:
                print("Keyboard Interrupt")
                break
                
            except Exception as e:
                print(e)
                break
            
        self.shutdown()

class ClientUDP:
    def __init__(self, client_name, server_port):
        
        #get Server address
        
        self.server_port = server_port
        
        self.server_addr = socket.gethostbyname(socket.gethostname())
        
        # UDP socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.client_name = client_name
        
        # Set up the threading events
        self.exit_run = threading.Event()
        self.exit_receive = threading.Event()
        
    def connect_server(self):
        try:
            
            self.send('join')
            # Avoid blocking
            if select.select([self.client_socket], [], [], 1)[0]:
                # Connect to the server        
                
                
                response, _ = self.client_socket.recvfrom(2048)
                response = response.decode()

                # return true is welcome is in the reponse
                if 'Welcome' in response:
                    return True
                # if something fails or no welcome return false
                else:
                    return False
        
        except Exception as e:
            return False
        
    def send(self, text):
        
        try:
            # Encode the message and add it with client name and send it
            message = f"{self.client_name}:{text}"
            
            # Use sendto to send the message
            self.client_socket.sendto(message.encode(), (self.server_addr, self.server_port))
        except Exception as e:
            print(e)
            
    def receive(self):
        
        while not self.exit_receive.is_set():
            # receive the data and decode it
            if select.select([self.client_socket], [], [], 1)[0]:
                message, _ = self.client_socket.recvfrom(1024)
                message = message.decode()
                
                print(f"{message}")
            
            # Check if the server is shutting down, set the events and exit loop
                if 'server-shutdown' in message:
                    self.exit_run.set()
                    self.exit_receive.set()
                    break

                
    def run(self):

        if self.connect_server():
            
            # Set receive to run when thread starts
            receive_thread = threading.Thread(target=self.receive)
            receive_thread.start()
            
            try:    
            # Runs unil the exit run is set
                while not self.exit_run.is_set():
                    message = input(f"{self.client_name}:")
                    # Send the message to the user
                    self.send(message)
                    
                    # Set events and break the loop
                    if 'exit' in message:
                        self.exit_run.set()
                        self.exit_receive.set()
                        break
                        
            # Set events and exit
            except KeyboardInterrupt:
                self.send('exit')
                self.exit_run.set()
                self.exit_receive.set()