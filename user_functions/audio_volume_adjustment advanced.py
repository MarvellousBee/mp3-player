#This version automatically adjusts volume in tracks.json when changed in the GUI
#Means not having to mess with files to set custom volumes


import json
import time
dict = None
default = None
def start_func():
    global dict, default
    F.listener(port = "5556")
    with open("user_functions/tracks.json", encoding="utf-8") as json_file:
    	dict = json.load(json_file)
    default = dict["default"]

def song_func():
    global default, dict
    if playback["track"] in dict:
    	F.set_volume(dict["default"]+dict[playback["track"]])
    else:
    	F.set_volume(dict["default"])

    print(playback["track"], playback["volume"])
    track = playback["track"]
    last = playback["volume"]
    while track==playback["track"]:
        if playback["volume"]!=last:
            last = playback["volume"]
            with open("user_functions/tracks.json", encoding="utf-8") as json_file:
            	dict = json.load(json_file)
            dict[playback["track"]] = playback["volume"]-default
            with open('user_functions/tracks.json','w', encoding="utf-8") as f:
                json.dump(dict, f, indent=4)
        time.sleep(.5)
