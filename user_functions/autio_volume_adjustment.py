#Ustawia głośność wg słownika w tracks.json 
import json
dict = None

def start_func():
    global dict
    with open("user_functions/tracks.json", encoding="utf-8") as json_file:
    	dict = json.load(json_file)

def song_func():
    if playback["track"] in dict:
    	F.set_volume(dict["default"]+dict[playback["track"]])
    else:
    	F.set_volume(dict["default"])
