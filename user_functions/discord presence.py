#Pozwala na wyświetlanie rich presence MP3 na profilu discorda
#pip install pypresence
#[Winerror 5] Odmowa dostępu jest powodowany windowsem, należy odpalić cmd jako administrator 

import pypresence
import time
from threading import Thread

RPC = None

def start_func():
    global RPC
    #usunąć zanim repo stanie się publiczne
    client_id = "826535732218691595"

    RPC = pypresence.Presence(client_id)
    RPC.connect()

def song_func():
    start = playback["track"]
    while playback["track"]==start:
        RPC.update(
        details = playback["track"],
        state = f'{playback["time_mins"]} ----- {playback["length_mins"]}'
        )
        time.sleep(0.5)
