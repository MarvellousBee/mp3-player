#playlist is looped twice
import time
prev = None
def start_func():
    F.listener()
    global prev
    prev = playback["id"]
    if playback["loop"]!=1:
        F.set_loop(1)
def song_func():
    global prev
    if playback["id"]<prev:
        F.set_loop(0)
    prev = playback["id"]
