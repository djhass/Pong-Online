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

print("Starting Pong Server...")

HOST = 'localhost'
PORT = 12345

serverSocket = socket.socket(AF_INET, SOCK_STREAM)
serverSocket.bind((HOST, PORT))
serverSocket.settimeout(0.5) #allow interrupts between socket timeouts for keyboard readings
serverSocket.listen(2)

print(f"Server listening on {HOST}:{PORT}")

try:
    while True:
        try:
            connectionSocket, addr = serverSocket.accept()
            sentence = connectionSocket.recv(1024).decode()
            print(f"Received from {addr}: {sentence}")
            # use socket sock to communicate
            # with client process
        except socket.timeout: #allow interrupts between socket timeouts for keyboard readings
            continue
except KeyboardInterrupt: #detect Ctrl+C to quit program
    s.close()

