# =================================================================================================
# Contributing Authors:	    <Anyone who touched the code>
# Email Addresses:          <Your uky.edu email addresses>
# Date:                     <The date the file was last edited>
# Purpose:                  <How this file contributes to the project>
# Misc:                     <Not Required.  Anything else you might want to include>
# =================================================================================================

import socket
import threading
from socket import AF_INET, SOCK_STREAM

# Use this file to write your server logic
# You will need to support at least two clients
# You will need to keep track of where on the screen (x,y coordinates) each paddle is, the score 
# for each player and where the ball is, and relay that to each client
# I suggest you use the sync variable in pongClient.py to determine how out of sync your two
# clients are and take actions to resync the games

# Thread function to handle client messages
shutdown_event = threading.Event() #for shutting down the thread
def readMessage(connection):
    while not shutdown_event.is_set(): #only exit loop when event fires
        message = connection.recv(1024).decode()
        if not message:
            break
        print(f"Received: {message}")
    connection.close()

print("Starting Pong Server...")

HOST = 'localhost'
PORT = 12345

serverSocket = socket.socket(AF_INET, SOCK_STREAM)
serverSocket.bind((HOST, PORT))
serverSocket.settimeout(0.5) #allow interrupts between socket timeouts for keyboard readings
serverSocket.listen(2)

threads = []
client_sockets = []

print(f"Server listening on {HOST}:{PORT}")

#main loop for polling and accepting connections
try:
    while True:
        try:
            # use socket sock to communicate
            # with client process
            newConnection, addr = serverSocket.accept()
            client_sockets.append(newConnection)
            t = threading.Thread(target=readMessage, args=(newConnection,))
            t.start()
            threads.append(t)
            print(f"New Connection from {addr}")
        except socket.timeout: #allow interrupts between socket timeouts for keyboard readings
            continue
except KeyboardInterrupt: #detect Ctrl+C to quit program
    #cleanup
    #close client sockets
    for client in client_sockets:
        client.close()

    #end threads
    shutdown_event.set()  # signal threads to exit
    for t in client_threads:
        t.join()  # wait for each to finish
        
    #close server socket
    serverSocket.close()