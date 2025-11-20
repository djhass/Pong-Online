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

#create socket to listen on
serverSocket = socket.socket(AF_INET, SOCK_STREAM)
serverSocket.bind((HOST, PORT))
serverSocket.settimeout(0.5) #allow interrupts between socket timeouts for keyboard readings
serverSocket.listen(2)

#lists to keep track of threads and client sockets
threads = []
client_sockets = []

print(f"Server listening on {HOST}:{PORT}")

#main loop for polling and accepting connections
try:
    while True:
        try:
            # use socket sock to communicate
            # with client process
            newConnection, addr = serverSocket.accept() #wait for connection

            #start new thread to listen to client messages
            client_sockets.append(newConnection)
            newThread = threading.Thread(target=readMessage, args=(newConnection,))
            newThread.start()
            threads.append(newThread) #keep track of threads for shutdown

            #send initial info: screen width, screen height, player paddle, left or right
            leftNRight = (len(client_sockets) % 2) #left if number of clients is even, right if not
            data = struct.pack('iii', SCREEN_WIDTH, SCREEN_HEIGHT, leftNRight) #pack data into bytes
            newConnection.sendall(data) #send data to client

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