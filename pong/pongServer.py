# =================================================================================================
# Contributing Authors:	    Daniel Hasselwander, Donnie Tkachenko
# Email Addresses:          djha269@uky.edu, dmtk222@uky.edu
# Date:                     11/21/25
# Purpose:                  The pong server host, handles client connections and relays game state
# Misc:                     
# =================================================================================================

import socket
import threading
from socket import AF_INET, SOCK_STREAM
import struct

# Use this file to write your server logic
# You will need to support at least two clients
# You will need to keep track of where on the screen (x,y coordinates) each paddle is, the score 
# for each player and where the ball is, and relay that to each client
# I suggest you use the sync variable in pongClient.py to determine how out of sync your two
# clients are and take actions to resync the games

#CONSTANTS
HOST = 'localhost'
PORT = 12345
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Thread control
shutdown_event = threading.Event()
client_sockets = []

def readMessage(connection: socket.socket) -> None:
    # Author: Daniel Hasselwander, Donnie Tkachenko
    # Purpose: Runs as a thread to read binary data from one client and relay it to the other.
    # Pre: A valid, connected socket object.
    # Post: Continuously relays packets between clients until disconnect.

    while not shutdown_event.is_set():
        try:
            # We expect packets of 6 integers (24 bytes): [Paddle, BallX, BallY, ScoreL, ScoreR, Sync]
            data = connection.recv(1024)
            if not data:
                break
            
            # Relay data to the other clients
            for client in client_sockets:
                if client != connection:
                    try:
                        client.sendall(data)
                    except:
                        pass
        except Exception:
            break
    
    # Clean up if loop breaks
    if connection in client_sockets:
        client_sockets.remove(connection)
    connection.close()

if __name__ == "__main__":
    print("Starting Pong Server...")

    # Create socket to listen on
    serverSocket = socket.socket(AF_INET, SOCK_STREAM)
    
    # Allow port reuse to prevent "Address already in use"
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    serverSocket.bind((HOST, PORT))
    serverSocket.listen(2)

    print(f"Server listening on {HOST}:{PORT}")

    try:
        while True:
            # Accept new connections
            newConnection, addr = serverSocket.accept()
            
            # Store connection and start thread
            client_sockets.append(newConnection)
            newThread = threading.Thread(target=readMessage, args=(newConnection,))
            newThread.daemon = True
            newThread.start()

            # Logic: First connection (len 1) is Left, Second (len 2) is Right
            # We determine side based on connection order
            data = struct.pack('iii', SCREEN_WIDTH, SCREEN_HEIGHT, 1 if len(client_sockets) == 1 else 0)
            newConnection.sendall(data)

            print(f"New Connection from {addr}")

    except KeyboardInterrupt:
        print("\nServer stopping...")
        for client in client_sockets:
            client.close()
        shutdown_event.set()
        serverSocket.close()