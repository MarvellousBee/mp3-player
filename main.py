#First, make sure MPy3 is not running already
from filelock import Timeout, FileLock
import time
from threading import Thread
import sys
file_path = "lockfile.txt.lock"
lock = FileLock(file_path)

#direct py:
# only path
#direct exe:
# main.py, exe path
#direct mp3:
# main.py, mp3 path

#if executed via exe
if len(sys.argv)>1 and sys.argv[1][-8:]=="Mpy3.exe":
    del sys.argv[1]

try:
    with lock.acquire(timeout=0.1):
        #No need to define this if it's not going to be used anyway
        def hold_file():
            with lock:
                while True: time.sleep(1)
        Thread(target=hold_file).start()
except Timeout:
    with open("data/comm.txt", "w") as comm:
        #If selected a file, write its path
        if sys.argv[1:]:
            comm.write(sys.argv[1])
        exit()

#sound, I'm heavily considering changing this library to avoid depending on vlc.
#I'm almost certain you need to have VLC (application with a GUI, not just the module) installed to run this file.
import vlc

#built-in
import random
import json
import sys
import importlib
import os
import socket

#sockets, but simpler
import ultra_sockets

#Gui
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QListWidgetItem, QAction
from PyQt5.QtGui import QPixmap


#My files
import gui
from utility_functions import mins, strip_path

playback = gui.playback

module = None
def load_playback_and_user_functions(file):
    global module
    module = importlib.import_module(file)
    playback["module"] = file.split(".")[-1]+".py"
    module.playback = playback
    module.F = F
    gui.unsaved_list.append([-1,file])


def look_for_file_changes():
    path = "user_functions"

    before = dict ([(f, None) for f in os.listdir (path)])

    while True:
        time.sleep(1)
        after = dict ([(f, None) for f in os.listdir (path)])
        if before != after:
            ui.TracksList.blockSignals(True)
            add_functions("user_functions")
            if playback["module"] != "empty_module.py":
                ui.TrackFunctions.setCurrentRow(gui.function_files.index(playback["module"]))
            ui.TracksList.blockSignals(False)
            before = after



def Autosave_time():
    last_save = None

    while True:
        #Check if less than 5% of the song has passed.
        if playback["time"]*20<playback["length"]:
            new_time = "0"
        else:
            new_time = playback["time"]

        if new_time != last_save:
            gui.unsaved_list.append([6,new_time])
            last_save = new_time

        time.sleep(1)

def gui_updates():
    global playback, p, all_playlists
    while True:
        time.sleep(0.01)
        if playback["Pending_changes"]:
            for i in playback["Pending_changes"]:
                if i=="volume":
                     set_volume(playback["volume"])
                elif i=="time":
                     p.set_time(playback["time"]*1000)
                elif i=="new_playlist":
                    all_playlists = gui.all_playlists
                elif  isinstance(i, list): # new function to load, very professional (lazy, yet acceptably efficient) way to check
                    load_playback_and_user_functions("user_functions."+playback["Pending_changes"][0])

            playback["Pending_changes"]=[]




gui.function_files = []
def add_functions(directory):
    gui.function_files = []
    ui.TrackFunctions.blockSignals(True)

    ui.TrackFunctions.clear()
    for file in os.listdir(directory):

        if file.endswith(".py"):
            gui.function_files.append(file)
            ui.TrackFunctions.addItem(QListWidgetItem(file))

    local_fun = gui.last_functions
    module_name = local_fun.split(".")[1]+".py"

    if gui.function_files:
        if module_name in gui.function_files:
            ui.TrackFunctions.setCurrentRow(gui.function_files.index(module_name))
            load_playback_and_user_functions(f"user_functions.{module_name[:-3]}")
        else:
            print(f"{module_name} not found.")
            load_playback_and_user_functions(f"data.empty_module")

    else:
        print("No function files.")
        load_playback_and_user_functions(f"data.empty_module")

    ui.TrackFunctions.blockSignals(False)




all_playlists = {}
def add_playlists_to_list():

    ui.Playlists.clear()
    for pl in all_playlists:
        ui.Playlists.addItem(QListWidgetItem(pl["Title"]))



search_list = []
def add_songs_to_list():
    global search_list
    search_list = []
    ui.TracksList.clear()
    for song in playlist_names_only:
        ui.TracksList.addItem(QListWidgetItem(song))



path_to_empty_mp3 = os.path.dirname(os.path.abspath(__file__))+'\\data\\empty.mp3'
def set_song(path, empty=False, first=False):
    global playback

    if playlist and path not in playlist:#Last song was a custom one, probably
        path = playlist[0]

    for i in ui.TracksList.actions():
        ui.TracksList.removeAction(i)

    if empty:
        ui.DelFile.hide()
        ui.TrackLabel.setText(" ")
        media = vlc.Media(path_to_empty_mp3)
        p.set_media(media)
        ui.pause()
        playback["path"] = None
        playback["full_track"] =  None
        playback["track"] = None
        playback["is_playing"] = False
        get_time(empty=True)
        get_length(empty=True)

    TracksList_menu = {

    "CTX_Add_a_song" : QAction("Add a song ...", ui),
    "CTX_Add_a_folder" : QAction("Add a folder...", ui),
    "CTX_Delete_from_playlist" : QAction("Delete from playlist", ui),
    "CTX_Show_directory" : QAction("Show directory", ui)
    }

    if playback["playlist_id"]!=0:
        if ui.track_in_faves(path):
            ui.FavButton.setStyleSheet("border: none;"
            "background-image : url(assets/fav_heart_full.png);")
        else:
            ui.FavButton.setStyleSheet("border: none;"
            "background-image : url(assets/fav_heart_empty.png);")
            TracksList_menu["CTX_Add_to_favorites"] =  QAction("Add to favorites", ui)

            for a,b in TracksList_menu.items():
                ui.TracksList.addAction(b)

            TracksList_menu["CTX_Add_to_favorites"].triggered.connect(ui.CTX_Add_to_favorites)

    else:
        if not playback["playlist"]:
            ui.FavButton.setStyleSheet("border: none;"
            "background-image : url(assets/fav_heart_empty.png);")
            return
        ui.FavButton.setStyleSheet("border: none;"
        "background-image : url(assets/fav_heart_full.png);")

        for a,b in TracksList_menu.items():
            ui.TracksList.addAction(b)

    TracksList_menu["CTX_Add_a_song"].triggered.connect(ui.add_song_by_file)
    TracksList_menu["CTX_Add_a_folder"].triggered.connect(ui.add_song_by_folder)
    TracksList_menu["CTX_Delete_from_playlist"].triggered.connect(ui.delete_song)
    TracksList_menu["CTX_Show_directory"].triggered.connect(ui.show_song_path)

    if empty:
        return
    ui.DelFile.show()
    media = vlc.Media(path)
    p.set_media(media)
    ui.play()
    ui.PlayButton.setText("||")

    song_names = strip_path(path)

    playback["path"] = path
    playback["full_track"] =  song_names[0]
    playback["track"] = song_names[1]
    playback["is_playing"] = True
    playback["image"] = ui.get_cover_art_and_artist(path)
    if playback["artist"]:
        ui.ArtistLabel.setText(playback["artist"])
    else:
        ui.ArtistLabel.setText("")


    if playback["image"]:
        ui.art.setPixmap(QPixmap("assets/ALBUM_ART.jpg"))
    else:
        ui.art.setPixmap(QPixmap("assets/no_art.png"))



    if playback["shuffle"]:
        playback["id"] = shuffled_playlist.index(path)
    else:
        playback["id"] = playlist.index(path)

    ui.TrackLabel.setText(playback["track"])

    # Whenever MPY3 is initialized for the first time after OS' startup, the very first song has 0 length for a few milisceconds.
    # ALmost certainly VLC's fault
    while not get_length():
        time.sleep(0.01)


    if first:
        module.start_func()

    Thread(target=module.song_func).start()




    if playback["shuffle"]:
        target = playlist.index(path)
    else:
        target = playback["id"]


    ui.TracksList.blockSignals(True)
    ui.TracksList.setCurrentRow(target)
    ui.TracksList.blockSignals(False)

    gui.unsaved_list.append([5,str(playback["id"])])
    gui.unsaved_list.append([-2,str(playback["path"])])

def get_length(empty=False):
    global p
    if empty or not p.get_length()/1000:
        playback["length"] = 0
        playback["length_mins"] = "0:00"
        ui.LengthLabel.setText(playback["length_mins"])
        return False


    time.sleep(0.05)

    playback["length"] = int(p.get_length()/1000)
    playback["length_mins"] = mins(int(p.get_length()/1000))
    ui.TimeSlider.setMaximum(playback["length"])
    ui.LengthLabel.setText(playback["length_mins"])

    return p.get_length()/1000

def get_time(empty=False):
    global p, playback

    if empty:
        playback["time"] = 0
        playback["time_mins"] = "00:00"
        return

    #CurrentTimeButton.setText(mins(int(p.get_time()/1000)))
    playback["time"] = int(p.get_time()/1000)
    playback["time_mins"] = mins(int(p.get_time()/1000))
    return p.get_time()/1000

def track_time():
    while True:
        get_time()
        time.sleep(0.01)

def set_volume(value, update_slider=False):
    playback["volume"]=value

    if playback["volume"]:#Check if not muted
        playback["hidden_volume"] = playback["volume"]
        ui.MuteButton.setStyleSheet("border: none;"
        "background-image : url(assets/no_mute.png);")
    else:
        ui.MuteButton.setStyleSheet("border: none;"
        "background-image : url(assets/mute.png);")

    p.audio_set_volume(playback["volume"])

    if update_slider:
        ui.VolumeSlider.blockSignals(True)
        ui.VolumeSlider.setSliderPosition(playback["volume"])
        ui.VolumeSlider.blockSignals(False)


    gui.unsaved_list.append([0, str(playback["volume"])])
    gui.unsaved_list.append([3, str(playback["hidden_volume"])])

#first is true if playback is resumed from the previous session

playlist, shuffled_playlist, playlist_names_only, shuffled_playlist_names_only = ([],[],[],[])


def set_playlist(pl_id, first=False, empty=False, change_song = True):
    global playlist, shuffled_playlist, playlist_names_only, shuffled_playlist_names_only

    if pl_id==0:
        ui.DelPlaylist.hide()
        #No deleting this playlist
        for i in ui.Playlists.actions():
            ui.Playlists.removeAction(i)

        Playlists_menu = {
        "CTX_Add_playlist": QAction("Add playlist", ui),
        }
        for a,b in Playlists_menu.items():
            ui.Playlists.addAction(b)

        Playlists_menu["CTX_Add_playlist"].triggered.connect(ui.add_playlist)
    elif len(ui.Playlists.actions())<=1:
        ui.DelPlaylist.show()
        for i in ui.Playlists.actions():
            ui.Playlists.removeAction(i)
        Playlists_menu = {
        "CTX_Add_playlist": QAction("Add playlist", ui),
        "CTX_Delete_playlist": QAction("Delete playlist", ui),
        }
        for a,b in Playlists_menu.items():
            ui.Playlists.addAction(b)

        Playlists_menu["CTX_Delete_playlist"].triggered.connect(ui.add_playlist)
        Playlists_menu["CTX_Delete_playlist"].triggered.connect(ui.delete_playlist)


    #Actually empty
    if not all_playlists[pl_id]["Tracks"]:
        ui.DelFile.hide()
        ui.art.setPixmap(QPixmap("assets/no_art.png"))
    #Pretend its empty
    if empty:
        ui.DelPlaylist.hide()
        ui.art.setPixmap(QPixmap("assets/no_art.png"))
        playback["is_playing"] = False
        playback["id"] = None
        playback["playlist"] = []
        #playback["playlist_id"] = 0
        playback["playlist_id"] = pl_id
        gui.playlist, gui.shuffled_playlist, gui.playlist_names_only, gui.shuffled_playlist_names_only = playlist, shuffled_playlist, playlist_names_only, shuffled_playlist_names_only
        set_song(None, empty=True)
        return

    playlist, shuffled_playlist, playlist_names_only, shuffled_playlist_names_only = ([],[],[],[])

    playlist = all_playlists[pl_id]["Tracks"]

    #check if all tracks are valid:
    for i in playlist:
        if not os.path.exists(i):
            playlist.remove(i)
            print(f"Could not find {i}")
    shuffled_playlist = random.sample(playlist, len(playlist))


    for track in playlist:
        playlist_names_only.append(strip_path(track)[1])

    for track in shuffled_playlist:
        shuffled_playlist_names_only.append(strip_path(track)[1])

    playback["is_playing"] = True

    if first:
        playback["id"] = gui.last_song_id
    else:
        playback["id"] = 0


    playback["playlist"] = playlist
    playback["shuffled_playlist"] = shuffled_playlist
    playback["playlist_id"] = pl_id

    get_time()

    ui.Playlists.blockSignals(True)
    ui.Playlists.setCurrentRow(pl_id)
    ui.Playlists.blockSignals(False)

    #update gui side
    gui.playlist, gui.shuffled_playlist, gui.playlist_names_only, gui.shuffled_playlist_names_only = playlist, shuffled_playlist, playlist_names_only, shuffled_playlist_names_only



    if playlist and change_song:#Check if playlist actually contains anything
        if first:
            set_song(gui.last_path, first=True)
            p.set_time(gui.last_song_time*1000)
            if playback["volume"]==0:
                playback["volume"], playback["hidden_volume"] = 0,0
                ui.mute_unmute(0)



        else:
            if playback["shuffle"]:
                set_song(shuffled_playlist[playback["id"]])
            else:
                set_song(playlist[playback["id"]])
    else:
        set_song(None, empty=True, first=first)


    #Save


    gui.unsaved_list.append([4, str(playback["playlist_id"])])
    gui.unsaved_list.append([5, str(playback["id"])])
    gui.unsaved_list.append([-2, str(playback["path"])])

    with open('data/playlists.json','w', encoding="utf-8") as f:
        json.dump(gui.all_playlists, f, indent=4)

def custom_song(selected_file,first=False):
    global playlist, shuffled_playlist, playlist_names_only, shuffled_playlist_names_only

    print("[PICKED]", selected_file)
    if not os.path.exists(selected_file):
        print("This file does not exist.")
        exit()


    playlist = [selected_file]
    playlist_names_only = [strip_path(selected_file)[1]]
    shuffled_playlist = playlist
    shuffled_playlist_names_only = playlist_names_only

    playback["is_playing"] = True
    playback["id"] = 0
    playback["playlist"] = playlist
    playback["shuffled_playlist"] = playlist
    playback["playlist_id"] = "custom" # Not a "real" playlist
    get_time()
    set_song(playlist[0], first=first)
    ui.TracksList.blockSignals(True)
    add_songs_to_list()
    #ui.TracksList.setCurrentRow(playback["id"])
    ui.TracksList.blockSignals(False)


#Functions used for threading below
def threaded_time_change(seconds):
    time.sleep(0.0001)
    p.set_time(seconds*1000)

def threaded_shuffle_change():
    time.sleep(0.0001)
    ui.shuffle_button()

def threaded_loop_change(what="weird_bug"):
    time.sleep(0.0001)
    ui.loop_button(what)

def threaded_listener(ip, port):
    hostname = ip+":"+port
    connections = 1
    name = "receiver"

    server = ultra_sockets.Server(hostname,connections,name)

    while True:
        time.sleep(0.1)
        thing = server.get(1)
        if thing:
            exec(thing[0][1])

#Class for functions that users can call within their custom code.

#While monkey patching may not be considered good practice,
#I went with it anyway to maximize user-side simplicity.
class F():
    def set_song_by_id(id):
        ui.TracksList.setCurrentRow(id)

    def set_song_by_path(path):
        id = playlist.index(path)
        ui.TracksList.setCurrentRow(id)

    def set_song_by_name(name):
        id = playlist_names_only.index(name)
        ui.TracksList.setCurrentRow(id)

    def set_volume(volume):
        playback["volume"] = volume
        set_volume(volume, update_slider=True)

    def play():
        ui.play()

    def pause():
        ui.pause()

    def set_time(seconds):
        Thread(target= lambda: threaded_time_change(seconds)).start()
        playback["time"]=seconds

    def change_playlist(id):
        set_playlist(id)

    def toggle_shuffle():
        Thread(target=threaded_shuffle_change).start()

    def toggle_loop():
        Thread(target=threaded_loop_change).start()

    def set_loop(what):
        Thread(target=lambda: threaded_loop_change(what)).start()

    def change_module(modules):
        load_playback_and_user_functions("user_functions."+modules)

    def listener(ip =socket.gethostbyname(socket.gethostname()), port="5556"):
        try:
            Thread(target= lambda: threaded_listener(ip, port)).start()
        except Exception as e:
            print(e)


if __name__ == "__main__":

    with open("data/playlists.json", encoding="utf-8") as json_file:
    	all_playlists = json.load(json_file)


    gui.all_playlists = all_playlists

    #media object
    p = vlc.MediaPlayer()
    gui.p = p
    #gui
    app = QtWidgets.QApplication(sys.argv)
    ui = gui.Ui_MainWindow()

    #Functions

    add_functions("user_functions")

    Thread(target=track_time).start()
    Thread(target=gui_updates).start()

    Thread(target=Autosave_time).start()
    Thread(target=look_for_file_changes).start()

    # check if user has selected a file to open with MPy3
    playlist = []
    playlist_names_only = []
    shuffled_playlist = []
    shuffled_playlist_names_only = []


    add_playlists_to_list()


    if len(sys.argv)!=1:
        custom_song(selected_file=sys.argv[1], first=True)
    elif all_playlists:#Otherwise, resume playing (if possible).
        print("[RESUMED]", playback["playlist"])
        set_playlist(gui.last_playlist_id, first=True)
    else:
        print("[NO PLAYLISTS]")


    #Monkey patching
    gui.playlist = playlist
    gui.playlist_names_only = playlist_names_only
    gui.shuffled_playlist = shuffled_playlist
    gui.shuffled_playlist_names_only = shuffled_playlist_names_only

    gui.set_song = set_song
    gui.set_playlist = set_playlist
    gui.add_songs_to_list = add_songs_to_list
    gui.custom_song = custom_song


    #No need to call the  set_volume() function, since it does more than I need done.
    p.audio_set_volume(playback["volume"])
    add_songs_to_list()


    if playlist:
        if playback["shuffle"]:
            target = playlist.index(playback["path"])
        else:
            target = playback["id"]

        ui.TracksList.blockSignals(True)
        ui.TracksList.setCurrentRow(target)
        ui.TracksList.blockSignals(False)

    sys.exit(app.exec_())
