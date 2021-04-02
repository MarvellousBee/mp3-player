#playlista jest zapętlona tylko dwukrotnie
import time
poprzednik = None
def start_func():
    global poprzednik
    poprzednik = playback["id"]
    if playback["loop"]!=1:
        F.set_loop(1)
def song_func():
    global poprzednik
    if playback["id"]<poprzednik:
        F.set_loop(0)
    poprzednik = playback["id"]
