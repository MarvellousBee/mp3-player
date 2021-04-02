#Import this file to send commands from an external app/device

#1. add the F.listener() function to start_func()
#2. connect by running setup() in your external file
#3. once connected, send commands with execute()
#Examples:
# execute("F.set_song_by_id(3)")
# print(playback)

import ultra_sockets
import socket

client = None

def setup(ip =socket.gethostbyname(socket.gethostname()), port="5556"):
    print(ip)
    global client
    hostname = ip+":"+port
    name = "sender"
    client = ultra_sockets.Client(hostname,name)


def execute(command):
    client.send("receiver", command)

def terminate():
    client.terminate()
