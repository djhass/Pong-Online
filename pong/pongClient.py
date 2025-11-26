# =================================================================================================
# Contributing Authors:	    Daniel Hasselwander, Donnie Tkachenko, Jackson Russell
# Email Addresses:          djha269@uky.edu, dmtk222@uky.edu, jgru225@uky.edu
# Date:                     11/25/25
# Purpose:                  The pong client, connects to the server and runs the game loop
# Misc:                     
# =================================================================================================

import pygame
import tkinter as tk
import sys
import socket
import struct
import threading
from typing import Dict, Any

from assets.code.helperCode import *

def receive_updates(server_socket: socket.socket, opponentPaddleObj: Paddle, ballObj: Ball, shared_state: Dict[str, int]) -> None:
    # Author: Donnie Tkachenko
    # Purpose: Thread to listen for game state. Uses SYNC variable to reconcile state (Catch-up logic).
    # Pre: Connected socket, game objects, and shared state dict with 'sync' key.
    # Post: Updates opponent paddle. Updates Ball/Score ONLY if remote sync > local sync.

    # Packet: [OpponentY, BallX, BallY, ScoreL, ScoreR, Sync] = 6 ints = 24 bytes
    packet_size = struct.calcsize('!iiiiii')
    
    while True:
        try:
            data = server_socket.recv(packet_size)
            if not data:
                break
            
            # Unpack data
            unpacked = struct.unpack('!iiiiii', data)
            op_y, ball_x, ball_y, score_l, score_r, remote_sync = unpacked

            # 1. Always update Opponent Paddle (This is always authoritative for that player)
            opponentPaddleObj.rect.y = op_y
            
            # 2. Sync Logic: If the opponent is "ahead" of us in time (larger sync), 
            # we accept their reality for the Ball and Score to catch up.
            local_sync = shared_state.get('sync', 0)
            
            if remote_sync > local_sync:
                shared_state['ball_x'] = ball_x
                shared_state['ball_y'] = ball_y
                shared_state['lScore'] = score_l
                shared_state['rScore'] = score_r
                # We update a flag to tell the main loop to apply these changes
                shared_state['should_update'] = 1
                
        except Exception:
            break

# This is the main game loop.  For the most part, you will not need to modify this.  The sections
# where you should add to the code are marked.  Feel free to change any part of this project
# to suit your needs.
def playGame(screenWidth: int, screenHeight: int, playerPaddle: str, client: socket.socket) -> None:
    # Author: Daniel Hasselwander, Donnie Tkachenko
    # Purpose: The main game loop. Runs physics symmetrically and reconciles via Sync.
    # Pre: Pygame init, valid screen dims, player side string, and connected socket.
    # Post: Runs game loop until exit.

    # Pygame inits
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.init()

    # Constants
    WHITE = (255,255,255)
    clock = pygame.time.Clock()
    scoreFont = pygame.font.Font("./assets/fonts/pong-score.ttf", 32)
    winFont = pygame.font.Font("./assets/fonts/visitor.ttf", 48)
    pointSound = pygame.mixer.Sound("./assets/sounds/point.wav")
    bounceSound = pygame.mixer.Sound("./assets/sounds/bounce.wav")

    # Display objects
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    winMessage = pygame.Rect(0,0,0,0)
    topWall = pygame.Rect(-10,0,screenWidth+20, 10)
    bottomWall = pygame.Rect(-10, screenHeight-10, screenWidth+20, 10)
    centerLine = []
    for i in range(0, screenHeight, 10):
        centerLine.append(pygame.Rect((screenWidth/2)-5,i,5,5))

    # Paddle properties and init
    paddleHeight = 50
    paddleWidth = 10
    paddleStartPosY = (screenHeight/2)-(paddleHeight/2)
    leftPaddle = Paddle(pygame.Rect(10,paddleStartPosY, paddleWidth, paddleHeight))
    rightPaddle = Paddle(pygame.Rect(screenWidth-20, paddleStartPosY, paddleWidth, paddleHeight))

    ball = Ball(pygame.Rect(screenWidth/2, screenHeight/2, 5, 5), -5, 0)

    if playerPaddle == "left":
        opponentPaddleObj = rightPaddle
        playerPaddleObj = leftPaddle
    else:
        opponentPaddleObj = leftPaddle
        playerPaddleObj = rightPaddle

    # Shared container for the thread. We init 'should_update' to 0 (False)
    shared_state = {
        'ball_x': ball.rect.x,
        'ball_y': ball.rect.y,
        'lScore': 0,
        'rScore': 0,
        'sync': 0,
        'should_update': 0
    }

    # Networking Thread
    t = threading.Thread(target=receive_updates, args=(client, opponentPaddleObj, ball, shared_state))
    t.daemon = True
    t.start()

    lScore = 0
    rScore = 0

    sync = 0

    while True:
        # Wiping the screen
        screen.fill((0,0,0))
        
        # Update shared sync so thread knows time
        shared_state['sync'] = sync

        # If the thread flagged an update (because remote sync > local sync), we apply it.
        if shared_state['should_update'] == 1:
            ball.rect.x = shared_state['ball_x']
            ball.rect.y = shared_state['ball_y']
            lScore = shared_state['lScore']
            rScore = shared_state['rScore']
            shared_state['should_update'] = 0 # Reset flag

        # Getting keypress events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    playerPaddleObj.moving = "down"

                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    playerPaddleObj.moving = "up"

            elif event.type == pygame.KEYUP:
                playerPaddleObj.moving = ""

        # =========================================================================================
        # Your code here to send an update to the server on your paddle's information,
        # where the ball is and the current score.
        
        try:
            # We send [MyPaddle, MyBallX, MyBallY, MyLScore, MyRScore, MySync]
            # We send OUR version of reality. The opponent will only accept it if our sync > theirs.
            packet = struct.pack('!iiiiii', 
                                 playerPaddleObj.rect.y, 
                                 ball.rect.x, 
                                 ball.rect.y, 
                                 lScore, 
                                 rScore,
                                 sync)
            
            client.sendall(packet)
        except:
            pass
        
        # =========================================================================================

        # Update the player paddle and opponent paddle's location on the screen
        for paddle in [playerPaddleObj, opponentPaddleObj]:
            if paddle.moving == "down":
                if paddle.rect.bottomleft[1] < screenHeight-10:
                    paddle.rect.y += paddle.speed
            elif paddle.moving == "up":
                if paddle.rect.topleft[1] > 10:
                    paddle.rect.y -= paddle.speed

        # If the game is over, display the win message
        if lScore > 4 or rScore > 4:
            winText = "Player 1 Wins! " if lScore > 4 else "Player 2 Wins! "
            textSurface = winFont.render(winText, False, WHITE, (0,0,0))
            textRect = textSurface.get_rect()
            textRect.center = ((screenWidth/2), screenHeight/2)
            winMessage = screen.blit(textSurface, textRect)
        else:

            # ==== Ball Logic =====================================================================
            ball.updatePos()

            # If the ball makes it past the edge of the screen, update score, etc.
            if ball.rect.x > screenWidth:
                lScore += 1
                pointSound.play()
                ball.reset(nowGoing="left")
            elif ball.rect.x < 0:
                rScore += 1
                pointSound.play()
                ball.reset(nowGoing="right")
                
            # If the ball hits a paddle
            if ball.rect.colliderect(playerPaddleObj.rect):
                bounceSound.play()
                ball.hitPaddle(playerPaddleObj.rect.center[1])
            elif ball.rect.colliderect(opponentPaddleObj.rect):
                bounceSound.play()
                ball.hitPaddle(opponentPaddleObj.rect.center[1])
                
            # If the ball hits a wall
            if ball.rect.colliderect(topWall) or ball.rect.colliderect(bottomWall):
                bounceSound.play()
                ball.hitWall()
            
            pygame.draw.rect(screen, WHITE, ball)
            # ==== End Ball Logic =================================================================

        # Drawing the dotted line in the center
        for i in centerLine:
            pygame.draw.rect(screen, WHITE, i)
        
        # Drawing the player's new location
        for paddle in [playerPaddleObj, opponentPaddleObj]:
            pygame.draw.rect(screen, WHITE, paddle)

        pygame.draw.rect(screen, WHITE, topWall)
        pygame.draw.rect(screen, WHITE, bottomWall)
        scoreRect = updateScore(lScore, rScore, screen, WHITE, scoreFont)
        
        pygame.display.flip() 
        clock.tick(60)
        
        # This number should be synchronized between you and your opponent.  If your number is larger
        # then you are ahead of them in time, if theirs is larger, they are ahead of you, and you need to
        # catch up (use their info)
        sync += 1
        # =========================================================================================
        # Send your server update here at the end of the game loop to sync your game with your
        # opponent's game

        # =========================================================================================




# This is where you will connect to the server to get the info required to call the game loop.  Mainly
# the screen width, height and player paddle (either "left" or "right")
# If you want to hard code the screen's dimensions into the code, that's fine, but you will need to know
# which client is which
def joinServer(ip:str, port:str, errorLabel:tk.Label, app:tk.Tk) -> None:
    # Author:       Daniel Hasselwander, Donnie Tkachenko
    # Purpose:      This method is fired when the join button is clicked. Connects and handshakes.
    # Pre:          IP and Port are valid strings.
    # Post:         Establishes connection, determines side, and starts game loop.

    # Arguments:
    # ip            A string holding the IP address of the server
    # port          A string holding the port the server is using
    # errorLabel    A tk label widget, modify it's text to display messages to the user (example below)
    # app           The tk window object, needed to kill the window
    
    # Create a socket and connect to the server
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ip, int(port)))

        #wait to receive the initial handshake from the server
        errorLabel.config(text=f"Waiting for Player 2...")
        errorLabel.update()

        # Get the required information from your server (screen width, height & player paddle)
        # Handshake: Receive 3 integers [Width, Height, Side]
        data = client.recv(12)
        screen_width, screen_height, leftNRight = struct.unpack('iii', data)
        
        # Map integer to string: 1 -> "left", 0 -> "right"
        player_side = "left" if leftNRight else "right"

        # Close this window and start the game with the info passed to you from the server
        app.withdraw()     # Hides the window (we'll kill it later)
        playGame(screen_width, screen_height, player_side, client)  # User will be either left or right paddle
        app.quit()         # Kills the window

    except Exception as e:
        errorLabel.config(text=f"Error: {e}")
        errorLabel.update()


# This displays the opening screen, you don't need to edit this (but may if you like)
def startScreen():
    app = tk.Tk()
    app.title("Server Info")

    image = tk.PhotoImage(file="./assets/images/logo.png")

    titleLabel = tk.Label(image=image)
    titleLabel.grid(column=0, row=0, columnspan=2)

    ipLabel = tk.Label(text="Server IP:")
    ipLabel.grid(column=0, row=1, sticky="W", padx=8)

    ipEntry = tk.Entry(app)
    ipEntry.grid(column=1, row=1)
    ipEntry.insert(0, "localhost") # Default for easier testing

    portLabel = tk.Label(text="Server Port:")
    portLabel.grid(column=0, row=2, sticky="W", padx=8)

    portEntry = tk.Entry(app)
    portEntry.grid(column=1, row=2)
    portEntry.insert(0, "12345") # Default for easier testing

    errorLabel = tk.Label(text="")
    errorLabel.grid(column=0, row=4, columnspan=2)

    joinButton = tk.Button(text="Join", command=lambda: joinServer(ipEntry.get(), portEntry.get(), errorLabel, app))
    joinButton.grid(column=0, row=3, columnspan=2)

    app.mainloop()

if __name__ == "__main__":
    startScreen()
