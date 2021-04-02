# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint, QTimer, QEvent
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QListWidgetItem, QFileDialog, QInputDialog, QMessageBox
import os
import time
import random
import sys
import eyed3
import json

from threading import Thread

from utility_functions import strip_path

#read user data
with open("data/settings.txt", encoding="utf-8") as settings:
    first_tab = settings.read().splitlines()


last_path = first_tab[-2]
last_functions = first_tab[-1]
settings_tab = [int(i) for i in first_tab[:-2]]

volume = settings_tab[0]
shuffle = bool(settings_tab[1])
loop = settings_tab[2]
hidden_volume = settings_tab[3]

last_playlist_id  = settings_tab[4]
last_song_id = settings_tab[5]
last_song_time = settings_tab[6]

quit_on_functions_change = settings_tab[7]
dark_mode = int(settings_tab[8])

#Used to retrieive information for gui's and user's purposes.
playback = {
"path":None,
"full_track":None, # MyTrack.mp3
"track":None, # MyTrack
"is_playing":True,
"time":0,
"length":0,
"length_mins":"0:00",
"time_mins":"0:00",
"volume":volume, # independent of "is_playing". You can play at 0 volume and keep 100 volume while paused.
"hidden_volume":hidden_volume, # Volume unaffected by muting. Used to go back after unmuting.
"id":0, # index in the playlist
"playlist":None,
"shuffled_playlist":None,
"playlist_id":None,
"shuffle":shuffle,
"loop":loop, # 0 - No loop, 1 - loop all tracks, 2 - loop 1 track
"module":None,
"artist":None,
"image":False,# whether the image exists. If True, returns its path.
"in_favorites":False,
"dark_mode":dark_mode,
"Pending_changes":[] # Update gui only if True (the list is not empty)
}


#Print more important parts of playback, for debugging.
def print_playback():
    print(playback["track"], playback["is_playing"], playback["time"], playback["volume"], playback["id"], playback["playlist_id"], playback["module"], playback["Pending_changes"])



#Saving changes from this list every x seconds
unsaved_list = []
x = 0.1
def autosave():
    global unsaved_list

    #A replacement for some 'if first' checks in 'set_...' functions
    while not unsaved_list:
        time.sleep(1)
    unsaved_list = []

    while True:
        #Saves from within Mpy3
        if unsaved_list:
            with open("data/settings.txt", encoding="utf-8") as settings:
                local_settings_tab = settings.read().splitlines()

            for item in unsaved_list:
                local_settings_tab[item[0]]=item[1]

            with open("data/settings.txt", "w", encoding="utf-8") as settings:
                settings.writelines([str(i)+"\n" for i in local_settings_tab])

            unsaved_list = []

        #Saves from other instances of MPy3
        with open("data/comm.txt", "r") as comm:
            comm = comm.read()
        if comm:
            if comm=="FOCUS":
                print(comm)
            else:
                custom_song(comm)
            with open("data/comm.txt", "w") as comm:
                comm.write("")
        time.sleep(x)



class Ui_MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setupUi()
        Thread(target=autosave).start()

        #load settings

        if not playback["shuffle"]:
            self.ShuffleButton.setStyleSheet("border: none;"
            "background-image : url(assets/no_shuffle.png);")
        if playback["loop"]==0:
            self.LoopButton.setStyleSheet("border: none;"
            "background-image : url(assets/no_loop.png);")
        elif playback["loop"]==2:
            self.LoopButton.setStyleSheet("border: none;"
            "background-image : url(assets/loop_1.png);")


    def get_cover_art_and_artist(self, path):
        audio_file = eyed3.load(path)

        try:
            if audio_file.tag.artist:
                playback["artist"] = audio_file.tag.artist
            else:
                playback["artist"] = None
        except AttributeError: # No author, "author" variable does not exist
            playback["artist"] = None

        try:
            if len(audio_file.tag.images)==0: # No art
                return False
        except AttributeError: # No art, "image" variable does not exist
            return False
        image = audio_file.tag.images[0]
        image_file = open(f"assets/ALBUM_ART.jpg", "wb")
        image_file.write(image.image_data)
        image_file.close()
        #returning it so playback[] users can access it easily
        return path

    def focus_window():
        self.activateWindow()
        self.setTopLevelWindow()

    def exit_button(self, e=0):
        #Save playback information
        self.close()
        os._exit(0)

    def minimize_button(self, e):
        self.showMinimized()

    def mute_unmute(self, e):
        if playback["volume"]:
            playback["volume"]=0

        else:
            playback["volume"]=playback["hidden_volume"]

        self.VolumeSlider.setSliderPosition(playback["volume"])

        playback["Pending_changes"].append("volume")



    timeslider_used = False
    update_slider = True

    def slider_change_volume(self, vol):
        global playback
        playback["volume"]=int(vol)
        playback["Pending_changes"].append("volume")


    #Only change time when the slider is released
    def TS_start(self):
        self.timeslider_used=True

    def TS_stop(self):
        curr_time = int(self.TimeSlider.sliderPosition())
        p.set_time(curr_time*1000)
        playback["time"]=curr_time
        playback["Pending_changes"].append("time")
        self.timeslider_used=False

    def auto_update_time_widgets(self):
        while True:
            time.sleep(0.1)
            if not self.timeslider_used and self.update_slider and playback["track"]:
                self.TimeSlider.setSliderPosition(playback["time"])
                self.CurrentTime.setText(playback["time_mins"])

            if playback["time"]==playback["length"]!=0 or (playback["time"]<playback["length"] and not p.will_play()):
                if playback["loop"]==2:
                    self.next_track(0)
                else:
                    self.next_track(1)


    already_pausing = False
    def play(self):
        global p, playback, already_pausing
        if not self.already_pausing:
            p.play()
            p.audio_set_volume(playback["volume"])
        self.PlayButton.setText("||")
        playback["is_playing"] = True

    #mutes volume over num_of_reps*0.001 seconds.
    #This alorithm is so complicated because it allows the user to violently mash the playbutton during a single execution of slow_pause()
    def slow_pause(self, num_of_reps):
        global p, already_pausing
        if self.already_pausing:
            return
        self.already_pausing = True
        curr_volume = playback["volume"]
        step = playback["volume"]/num_of_reps
        while True:
            time.sleep(0.001)
            if playback["is_playing"]:
                curr_volume+=step
            else:
                curr_volume-=step
            if playback["is_playing"] and curr_volume >= playback["volume"]:
                p.audio_set_volume(playback["volume"])
                self.already_pausing = False
                return
            elif not playback["is_playing"] and 1 > curr_volume:
                p.pause()
                self.already_pausing = False
                return
            p.audio_set_volume(int(curr_volume))

    def pause(self):
        global p, playback
        self.PlayButton.setText(">")

        #choose between instant and slow pause

        #instant_pause() currently removed, might add it back as a setting
        Thread(target=lambda: self.slow_pause(200)).start()
        playback["is_playing"] = False

    def pause_unpause(self):
        if not playback["is_playing"]:
            self.play()
        else:
            self.pause()


    ignore_changes = False
    search_indexes = []#account for possible duplicate names

    def next_track(self, direction):
        if not playback["playlist"]:# Don't do anything if the playlist is empty
            return
        #if out of range
        if playback["id"]+direction>=len(playback["playlist"]):
            if playback["loop"]==0:
                self.pause()
                p.set_time(0)

                if playback["is_playing"]:
                    playback["is_playing"] = False
                    self.PlayButton.setText(">")
                return
            elif playback["loop"]==1:
                playback["id"]=0

        else:
            playback["id"]+=direction
        # Setting the selected item makes pyqt5 complain about it here. Only once.
        # Only happens when the track is switched automatically.
        # However, It's not an error and it works as intended. So i don't care. Should I?
        # I'm only leaving this here (instead of fixing it by triggering a TracksList_trigger(), which does not produce this "error") to one day be told by someone smarter why is this happening.
        self.ignore_changes = True
        if playback["shuffle"]:
            set_song(playback["shuffled_playlist"][playback["id"]])
        else:
            set_song(playback["playlist"][playback["id"]])
        time.sleep(0.01) # gets triggerd twice without this pause
        self.ignore_changes = False


    def shuffle_button(self):
        playback["shuffle"] = not playback["shuffle"]
        if playback["shuffle"]:
            self.ShuffleButton.setStyleSheet("border: none;"
            "background-image : url(assets/shuffle.png);")
            unsaved_list.append([1,"1"])
        else:
            self.ShuffleButton.setStyleSheet("border: none;"
            "background-image : url(assets/no_shuffle.png);")
            unsaved_list.append([1,"0"])

    def loop_button(self, custom="weird_bug"):
        if custom!="weird_bug":
            playback["loop"] = custom
        else:
            playback["loop"] += 1
            playback["loop"] = playback["loop"]%3
        #Implement a switch case once Python 3.10  comes out
        if playback["loop"]==1:
            self.LoopButton.setStyleSheet("border: none;"
            "background-image : url(assets/loop.png);")
            unsaved_list.append([2,"1"])
        elif playback["loop"]==0:
            self.LoopButton.setStyleSheet("border: none;"
            "background-image : url(assets/no_loop.png);")
            unsaved_list.append([2,"0"])
        else:
            self.LoopButton.setStyleSheet("border: none;"
            "background-image : url(assets/loop_1.png);")
            unsaved_list.append([2,"2"])


    def TracksList_trigger(self, selected):
        #get adjusted playlist from the SearchBox
        if not self.ignore_changes:
            self.SearchBox_trigger(self.SearchBox.text())
            if self.search_indexes:
                set_song(self.search_indexes[selected])
            else:
                set_song(playback["playlist"][selected])



    def SearchBox_trigger(self, text):
        self.ignore_changes = True
        self.search_indexes = []

        target_song = playback["path"]


        self.TracksList.clear()
        for i, song in enumerate(playback["playlist"]):
            if text.lower() in strip_path(song)[1].lower():
                self.TracksList.addItem(QListWidgetItem(playlist_names_only[i]))
                self.search_indexes.append(song)


        if target_song in self.search_indexes:
            target = self.search_indexes.index(target_song)
            self.TracksList.blockSignals(True)
            self.TracksList.setCurrentRow(target)
            self.TracksList.blockSignals(False)

        self.ignore_changes = False

    def Playlists_trigger(self, selected):
        set_playlist(selected)
        self.ignore_changes = True
        add_songs_to_list()
        self.SearchBox_trigger(self.SearchBox.text())

    function_changes = False
    def TrackFunctions_trigger(self, selected):
        #quit_on_functions_change = False
        if quit_on_functions_change:
            unsaved_list.append([-1,["user_functions."+function_files[selected][:-3]][0]])
            time.sleep(.1)
            directory = "\\".join(sys.argv[0].split("\\")[:-1])
            os.popen(f'cd "{directory}" ')

            if playback["playlist_id"]=="custom":
                target =  F'"{sys.argv[0]}"' + " " + F'"{sys.argv[1]}"'
                print(target)
            else:
                target = F'"{sys.argv[0]}"'



            os.popen(f'python {target}') #"{sys.argv[1]}"')
            self.exit_button(0)
        else:
            #I wish i could spawn another console/make the first one print stuff
            #Or maybe an embedded console?

            playback["Pending_changes"].append([function_files[selected][:-3]][0])

    def show_funs_dir(self):

        path = os.path.dirname(os.path.abspath(__file__))+'/user_functions'
        if os.path.exists(path):
            os.startfile(path)
        else:
            print("[ERROR] Directory not found")

    def reload_playlists(self):
        self.Playlists.blockSignals(True)

        self.Playlists.clear()
        for i in all_playlists:
            self.Playlists.addItem(QListWidgetItem(i["Title"]))
        self.Playlists.setCurrentRow(len(all_playlists)-1)
        self.Playlists.blockSignals(False)
        self.SearchBox_trigger("")


    def add_playlist(self):
        global all_playlists
        #ask for a name

        text, okPressed = QInputDialog.getText(self, " ","Name of your Playlist:", QtWidgets.QLineEdit.Normal, flags=QtCore.Qt.FramelessWindowHint)
        if not okPressed:
            return

        if not text:
            #return
            text = f"Playlist {len(all_playlists)+1}"


        done_adding = False
        if playback["playlist_id"] == "custom":
            dialog = QMessageBox().question(self, ' ', "Would you like to use your current playlist?", QMessageBox.Yes | QMessageBox.No)
            if dialog==16384: # Yes
                all_playlists.append({"Title":text,
                                      "Tracks":playback["playlist"]
                                      })
                done_adding = True

        if not done_adding:
            all_playlists.append({"Title":text,
                                  "Tracks":[]
                                  })
        set_playlist(len(all_playlists)-1)

        self.reload_playlists()


        playback["Pending_changes"].append("new_playlist")

    def delete_playlist(self):
        global all_playlists

        #Check if there is something to delete, or It's your favorite playlist.
        #I'd check if It's "Favorite", but am afraid It will cause problems if users try to name their playlists that way
        if not all_playlists or playback["playlist_id"]==0:
            return

        selected_pl = self.Playlists.currentRow()

        pl_title = all_playlists[selected_pl]["Title"]

        dg = QMessageBox()
        dg.setWindowFlags(Qt.FramelessWindowHint)
        dialog = dg.question(self, ' ', f"Delete {pl_title}?", QMessageBox.Yes | QMessageBox.No) #flags=QtCore.Qt.FramelessWindowHint)
        #okPressed = dialog.getText(self, " ","Are you sure?", flags=QtCore.Qt.FramelessWindowHint)
        if dialog==65536: # pressed "No"
            return

        self.TracksList.blockSignals(True)
        del all_playlists[selected_pl]


        if all_playlists:
            set_playlist(0)
        else:
            set_playlist(0, empty=True)
            add_songs_to_list()
            #set_song(None, empty=True)

        self.reload_playlists()
        self.TracksList.blockSignals(False)


    supported_filetypes = ["mp3", "wav"]#Add all filetypes actually supported by vlc/whatever player i will switch to in the future

    def add_song_by_file(self, update=False, input=None, final=True):
        self.TracksList.blockSignals(True)
        if input:
            file = input
        else:
            file, type = QFileDialog.getOpenFileName(None,"Select file", "","All Files (*);;MP3 Files (*.mp3)")
            if not file:
                return
        # type != extension
        extension = file.split(".")[-1]

        if extension not in self.supported_filetypes:
            print(f"Unsupported file type ({type}):", file)
            return


        if playback["playlist_id"] == "custom":

            playback["playlist"] = playlist

            playlist.append(file)
            self.SearchBox_trigger(self.SearchBox.text())
        else:
            all_playlists[playback["playlist_id"]]["Tracks"] = playback["playlist"] + [file]
            set_playlist(playback["playlist_id"], change_song=False)
            add_songs_to_list()


        playlist_names_only.append(strip_path(file)[1])
        shuffled_playlist = random.sample(playback["playlist"], len(playlist))
        shuffled_playlist_names_only = [strip_path(i)[1] for i in shuffled_playlist]


        if playback["shuffle"]:
            playback["id"]=shuffled_playlist.index(file)
        else:
            playback["id"]=playback["playlist"].index(file)


        if final:
            self.TracksList.blockSignals(False)
            set_song(file)
            self.pause()
            time.sleep(0.5)
            self.play()



    def add_song_by_folder(self):
        path = QFileDialog.getExistingDirectory(None,"Select directory")
        if not path:
            return
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        for file in files:
            self.add_song_by_file(False, path+"\\"+file, final=False)

        self.TracksList.blockSignals(False)
        set_song(file)
        self.pause()
        time.sleep(0.5)
        self.play()

    def delete_song(self, index):
        self.TracksList.blockSignals(True)
        title = playback["track"]
        dg = QMessageBox()
        dg.setWindowFlags(Qt.FramelessWindowHint)
        dialog = dg.question(self, ' ', f"Delete {title}?", QMessageBox.Yes | QMessageBox.No) #flags=QtCore.Qt.FramelessWindowHint)
        if dialog==65536: # pressed "No"
            return


        all_playlists[playback["playlist_id"]]["Tracks"].remove(playback["path"])
        playlist_names_only.remove(strip_path(playback["path"])[1])
        set_playlist(playback["playlist_id"])
        playback["Pending_changes"].append("new_playlist")
        self.TracksList.blockSignals(False)
        self.SearchBox_trigger(self.SearchBox.text())

    def partially_refresh_gui(): # Only elements that tend to hang behind on inactivity.
        self.CurrentTime.repaint()
        self.LengthLabel.repaint()

    def CTX_Add_to_favorites(self):
        all_playlists[0]["Tracks"].append(playback["path"])
        with open('data/playlists.json','w', encoding="utf-8") as f:
            json.dump(all_playlists, f, indent=4)
        playback["Pending_changes"].append("new_playlist")

    def CTX_Remove_from_favorites(self):
        all_playlists[0]["Tracks"].remove(playback["path"])
        with open('data/playlists.json','w', encoding="utf-8") as f:
            json.dump(all_playlists, f, indent=4)
        playback["Pending_changes"].append("new_playlist")
        if playback["playlist_id"]==0:
            self.Playlists_trigger(0)

    def show_song_path(self):
        if os.path.exists(os.path.dirname(os.path.abspath(playback["path"]))):
            os.startfile(os.path.dirname(os.path.abspath(playback["path"])))
        else:
            print("[ERROR] Path not found")

    def track_in_faves(self, path):
        return path in all_playlists[0]["Tracks"]

    def toggle_faves(self):
        if not playback['playlist']:
            return

        if self.track_in_faves(playback["path"]):
            self.CTX_Remove_from_favorites()
            self.FavButton.setStyleSheet("border: none;"
            "background-image : url(assets/fav_heart_empty.png);")
        else:
            self.CTX_Add_to_favorites()
            self.FavButton.setStyleSheet("border: none;"
            "background-image : url(assets/fav_heart_full.png);")
        self.SearchBox_trigger(self.SearchBox.text())

    def swap_dark_mode(self):
        if playback["dark_mode"]:
            unsaved_list.append([8,"0"])
        else:
            unsaved_list.append([8,"1"])
        time.sleep(.1)
        playback["dark_mode"] = not playback["dark_mode"]
        self.style(playback["dark_mode"])


    def style(self,is_dark_mode):
        if is_dark_mode:
            unsaved_list.append([8,"1"])
            time.sleep(.1)
            self.setStyleSheet(open('styles dark.css').read())
            self.TrackFunctions.setStyleSheet("color : #abb2bf;")
            self.Fav_separator.setStyleSheet("background-color: #31363b;")
            self.Playlists.setStyleSheet("color : #abb2bf;")
            self.TracksList.setStyleSheet("color : #abb2bf;")
            self.CurrentTime.setStyleSheet("color : #abb2bf;font-size : 15px;")
            self.LengthLabel.setStyleSheet("color : #abb2bf;font-size : 15px;")
            self.TopLine.setStyleSheet("background-color: #26282C;")
            self.DarkModeButton.setStyleSheet("background:None;border : transparent;"
            "background-image : url(assets/set_light_mode.png);")
            self.MinimizeButton.setStyleSheet("background:None;border : transparent;background:none;"
            "background-image : url(assets/_ dark.png);")
            self.ExitButton.setStyleSheet("background:None;border : transparent;background:none;"
            "background-image : url(assets/x dark.png);")


        else:#light mode
            unsaved_list.append([8,"0"])
            time.sleep(.1)
            self.setStyleSheet(open('styles light.css').read())
            self.TracksList.setStyleSheet("color : #404040;background-color : #d9d9d9;")
            self.Playlists.setStyleSheet("color : #404040;background-color : #d9d9d9;")
            self.Fav_separator.setStyleSheet("background-color: white;")
            self.CurrentTime.setStyleSheet("color : #404040;font-size : 15px;")
            self.LengthLabel.setStyleSheet("color : #404040;font-size : 15px;")
            self.TopLine.setStyleSheet("background-color: darkgrey;")
            self.TrackFunctions.setStyleSheet("color : #404040;background-color : #d9d9d9;")
            self.DarkModeButton.setStyleSheet("background:None;border : transparent;"
            "background-image : url(assets/set_dark_mode.png);")
            self.MinimizeButton.setStyleSheet("background:None;border : transparent;background:none;"
            "background-image : url(assets/_ light.png);")
            self.ExitButton.setStyleSheet("background:None;border : transparent;background:none;"
            "background-image : url(assets/x light.png);")



    def setupUi(self):
        self.setObjectName("self")
        self.resize(1000, 576)#600 window + 36 top bar
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        self.TrackFunctions = QtWidgets.QListWidget(self.centralwidget)
        self.TrackFunctions.setGeometry(QtCore.QRect(360, 86, 280, 221))
        self.TrackFunctions.setObjectName("TrackFunctions")
        self.TrackFunctions.currentRowChanged.connect(self.TrackFunctions_trigger)
        self.TrackFunctions.installEventFilter(self)

        self.ShowFunctionsDir = QtWidgets.QPushButton(self.centralwidget)
        self.ShowFunctionsDir.setGeometry(QtCore.QRect(450, 316, 100, 23))
        self.ShowFunctionsDir.setObjectName("AddPlaylist")
        self.ShowFunctionsDir.setStyleSheet("border-color: #3DAEE9;")
        self.ShowFunctionsDir.clicked.connect(self.show_funs_dir)
        self.ShowFunctionsDir.installEventFilter(self)


        self.TracksList = QtWidgets.QListWidget(self.centralwidget)
        self.TracksList.setGeometry(QtCore.QRect(40, 86, 288, 221))
        self.TracksList.setObjectName("TracksList")
        self.TracksList.currentRowChanged.connect(self.TracksList_trigger)
        self.TracksList.installEventFilter(self)
        self.TracksList.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.Playlists = QtWidgets.QListWidget(self.centralwidget)
        self.Playlists.setGeometry(QtCore.QRect(680, 86, 280, 221))
        self.Playlists.setObjectName("Playlists")
        self.Playlists.currentRowChanged.connect(self.Playlists_trigger)
        self.Playlists.installEventFilter(self)
        self.Playlists.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.Fav_separator = QFrame(self.centralwidget)
        self.Fav_separator.setGeometry(QtCore.QRect(680, 105, 280, 4))

        self.AddFile = QtWidgets.QPushButton(self.centralwidget)
        self.AddFile.setGeometry(QtCore.QRect(62, 316, 64, 23))
        self.AddFile.setObjectName("AddPlaylist")
        self.AddFile.setStyleSheet("border-color: #3DAEE9;")
        self.AddFile.clicked.connect(self.add_song_by_file)
        self.AddFile.installEventFilter(self)

        self.AddFolder = QtWidgets.QPushButton(self.centralwidget)
        self.AddFolder.setGeometry(QtCore.QRect(148, 316, 64, 23))
        self.AddFolder.setObjectName("AddPlaylist")
        self.AddFolder.setStyleSheet("border-color: #3DAEE9;")
        self.AddFolder.clicked.connect(self.add_song_by_folder)
        self.AddFolder.installEventFilter(self)

        self.DelFile = QtWidgets.QPushButton(self.centralwidget)
        self.DelFile.setGeometry(QtCore.QRect(234, 316, 64, 23))
        self.DelFile.setObjectName("AddPlaylist")
        self.DelFile.clicked.connect(self.delete_song)
        self.DelFile.installEventFilter(self)

        self.AddPlaylist = QtWidgets.QPushButton(self.centralwidget)
        self.AddPlaylist.setGeometry(QtCore.QRect(730, 316, 75, 23))
        self.AddPlaylist.setObjectName("AddPlaylist")
        self.AddPlaylist.setStyleSheet("border-color: #3DAEE9;")
        self.AddPlaylist.clicked.connect(self.add_playlist)
        self.AddPlaylist.installEventFilter(self)

        self.DelPlaylist = QtWidgets.QPushButton(self.centralwidget)
        self.DelPlaylist.setGeometry(QtCore.QRect(845, 316, 75, 23))
        self.DelPlaylist.setObjectName("DelPlaylist")
        self.DelPlaylist.clicked.connect(self.delete_playlist)
        self.DelPlaylist.installEventFilter(self)

        self.FavButton = QtWidgets.QPushButton(self.centralwidget)
        self.FavButton.setGeometry(QtCore.QRect(305, 455, 40, 30))
        self.FavButton.setStyleSheet("border-radius : 35;border : 2px solid #b13139;")
        #self.FavButton.setFont(QFont('Trebuchet MS', 6))
        self.FavButton.clicked.connect(self.toggle_faves)
        self.FavButton.installEventFilter(self)

        self.TimeSlider = QtWidgets.QSlider(self.centralwidget)
        self.TimeSlider.setGeometry(QtCore.QRect(250, 536, 500, 32))
        self.TimeSlider.setOrientation(QtCore.Qt.Horizontal)
        self.TimeSlider.setObjectName("TimeSlider")
        self.TimeSlider.setMinimum(0)
        self.TimeSlider.sliderPressed.connect(self.TS_start)
        self.TimeSlider.sliderReleased.connect(self.TS_stop)
        self.TimeSlider.installEventFilter(self)

        self.CurrentTime = QtWidgets.QLabel(self.centralwidget)
        self.CurrentTime.setGeometry(QtCore.QRect(190, 535, 50, 31))
        self.CurrentTime.setObjectName("CurrentTime")
        self.CurrentTime.setAlignment(Qt.AlignCenter)

        self.LengthLabel = QtWidgets.QLabel(self.centralwidget)
        self.LengthLabel.setGeometry(QtCore.QRect(760, 535, 50, 31))
        self.LengthLabel.setObjectName("LengthLabel")
        self.LengthLabel.setAlignment(Qt.AlignCenter)

        self.MuteButton = QtWidgets.QPushButton(self.centralwidget)
        self.MuteButton.setGeometry(QtCore.QRect(650, 504, 40, 30 ))
        self.MuteButton.setObjectName("MuteButton")
        self.MuteButton.setStyleSheet("border: none;"
        "background-image : url(assets/no_mute.png);")
        self.MuteButton.setFont(QFont('Trebuchet MS', 12))
        self.MuteButton.clicked.connect(self.mute_unmute)
        self.MuteButton.installEventFilter(self)


        self.VolumeSlider = QtWidgets.QSlider(self.centralwidget)
        self.VolumeSlider.setGeometry(QtCore.QRect(700, 506, 141, 22))
        self.VolumeSlider.setOrientation(QtCore.Qt.Horizontal)
        self.VolumeSlider.setObjectName("VolumeSlider")
        self.VolumeSlider.setMinimum(0)
        self.VolumeSlider.setMaximum(100)
        self.VolumeSlider.valueChanged[int].connect(self.slider_change_volume)
        self.VolumeSlider.setSliderPosition(playback["volume"])
        self.VolumeSlider.installEventFilter(self)
        self.VolumeSlider.installEventFilter(self)

        self.PrevButton = QtWidgets.QPushButton(self.centralwidget)
        self.PrevButton.setGeometry(QtCore.QRect(405, 446, 50, 50 ))
        self.PrevButton.setObjectName("PrevButton")
        self.PrevButton.setStyleSheet("border-radius : 25;border : 1.6px solid #3DAEE9;")
        self.PrevButton.setFont(QFont('Trebuchet MS', 12))
        self.PrevButton.clicked.connect(lambda: self.next_track(-1))
        self.PrevButton.installEventFilter(self)

        self.PlayButton = QtWidgets.QPushButton(self.centralwidget)
        self.PlayButton.setGeometry(QtCore.QRect(465, 436, 70, 70 ))
        self.PlayButton.setObjectName("PlayButton")
        self.PlayButton.setStyleSheet("border-radius : 35;border : 2px solid #b13139;")
        self.PlayButton.setFont(QFont('Trebuchet MS', 12))
        self.PlayButton.clicked.connect(self.pause_unpause)
        self.PlayButton.installEventFilter(self)

        self.NextButton = QtWidgets.QPushButton(self.centralwidget)
        self.NextButton.setGeometry(QtCore.QRect(545, 446, 50, 50 ))
        self.NextButton.setObjectName("NextButton")
        self.NextButton.setStyleSheet("border-radius : 25;border : 1.6px solid #3DAEE9;")
        self.NextButton.setFont(QFont('Trebuchet MS', 12))
        self.NextButton.clicked.connect(lambda: self.next_track(1))
        self.NextButton.installEventFilter(self)

        self.ShuffleButton = QtWidgets.QPushButton(self.centralwidget)
        self.ShuffleButton.setGeometry(QtCore.QRect(355, 450, 41, 41 ))
        self.ShuffleButton.setObjectName("ShuffleButton")
        self.ShuffleButton.clicked.connect(self.shuffle_button)
        self.ShuffleButton.setStyleSheet("border: none;"
        "background-image : url(assets/shuffle.png);")
        self.ShuffleButton.installEventFilter(self)

        self.LoopButton = QtWidgets.QPushButton(self.centralwidget)
        self.LoopButton.setGeometry(QtCore.QRect(600, 450, 41, 41 ))
        self.LoopButton.setObjectName("LoopButton")
        self.LoopButton.clicked.connect(self.loop_button)
        self.LoopButton.setStyleSheet("border: none;"
        "background-image : url(assets/loop.png);")
        self.LoopButton.installEventFilter(self)

        self.SearchBox = QtWidgets.QLineEdit(self.centralwidget)
        self.SearchBox.setGeometry(QtCore.QRect(40, 50, 280, 30))
        self.SearchBox.setObjectName("SearchBox")
        self.SearchBox.setPlaceholderText("Search...")
        self.SearchBox.setFont(QFont('Trebuchet MS', 12))
        self.SearchBox.mousePressEvent = lambda _ : self.SearchBox.selectAll()
        self.SearchBox.textChanged[str].connect(self.SearchBox_trigger)


        self.TrackLabel = QtWidgets.QLabel(self.centralwidget)
        self.TrackLabel.setGeometry(QtCore.QRect(0, 386, 1000, 31))
        self.TrackLabel.setObjectName("TrackLabel")
        self.TrackLabel.setAlignment(Qt.AlignCenter)

        self.ArtistLabel = QtWidgets.QLabel(self.centralwidget)
        self.ArtistLabel.setGeometry(QtCore.QRect(0, 355, 1000, 31))
        # Independent of light/dark mode. Scandalous!
        self.ArtistLabel.setStyleSheet("border: none; font-size: 15px; color: grey;")
        self.ArtistLabel.setObjectName("ArtistLabel")
        self.ArtistLabel.setAlignment(Qt.AlignCenter)


        # Custom top bar
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)


        self.TopLine = QFrame(self.centralwidget)
        self.TopLine.setGeometry(QtCore.QRect(0, 0, 1000, 36))
        self.TopLine.setObjectName("TopLine")

        self.logo = QLabel(self)
        self.logo.setStyleSheet("background:none")
        self.pixmap = QPixmap('assets/mini_logo.png')
        self.logo.setPixmap(self.pixmap)
        self.logo.setGeometry(QtCore.QRect(10, 3, 30, 30))

        self.art = QLabel(self)
        self.art.setScaledContents(True)
        self.art.setPixmap(QPixmap('assets/no_art.png'))
        self.art.setGeometry(QtCore.QRect(100, 360, 160, 160))

        self.DarkModeButton = QtWidgets.QPushButton(self.centralwidget)
        self.DarkModeButton.setGeometry(QtCore.QRect(40, 0, 55, 36))
        self.DarkModeButton.setObjectName("DarkModeButton")
        self.DarkModeButton.clicked.connect(self.swap_dark_mode)
        self.DarkModeButton.setFont(QFont('Trebuchet MS', 10))
        self.DarkModeButton.installEventFilter(self)

        self.MinimizeButton = QtWidgets.QPushButton(self.centralwidget)
        self.MinimizeButton.setGeometry(QtCore.QRect(890, 0, 55, 36))
        self.MinimizeButton.setObjectName("ExitButton")
        self.MinimizeButton.clicked.connect(self.minimize_button)
        self.MinimizeButton.setFont(QFont('Trebuchet MS', 10))
        self.MinimizeButton.installEventFilter(self)

        self.ExitButton = QtWidgets.QPushButton(self.centralwidget)
        self.ExitButton.setGeometry(QtCore.QRect(945, 0, 55, 36))
        self.ExitButton.setObjectName("ExitButton")
        self.ExitButton.clicked.connect(self.exit_button)
        self.ExitButton.setFont(QFont('Trebuchet MS', 10))
        self.ExitButton.installEventFilter(self)

        #css
        self.style(playback["dark_mode"])


        self.retranslateUi()

        self.setWindowIcon(QtGui.QIcon('assets/logo.png'))
        QtCore.QMetaObject.connectSlotsByName(self)
        self.show()

        #Prevent gui from not updating itself
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(False)
        self.update_timer.timeout.connect(lambda: self.CurrentTime.repaint())
        self.update_timer.setInterval(500)
        self.update_timer.start()

        #Threads
        Thread(target=self.auto_update_time_widgets).start()


    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate

        self.setWindowTitle(_translate("self", "MPy3 2"))
        self.ShowFunctionsDir.setText(_translate("self", "Show Directory"))
        self.AddPlaylist.setText(_translate("self", "+"))
        self.DelPlaylist.setText(_translate("self", "-"))
        self.PlayButton.setText(_translate("self", "||"))
        self.NextButton.setText(_translate("self", ">>"))
        self.PrevButton.setText(_translate("self", "<<"))
        self.TrackLabel.setText(_translate("self", " "))
        self.AddFile.setText(_translate("self", "+ File"))
        self.AddFolder.setText(_translate("self", "+ Folder"))
        self.DelFile.setText(_translate("self", "-"))

    # Press and Move events are used drag the window
    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.TopLine.underMouse():
            delta = QPoint (event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
            time.sleep(0.005)#decreases CPU usage


    #toggle pause by pressing space
    def eventFilter(self, widget, event):
        if (event.type() == QEvent.KeyPress):
            if (event.key() == Qt.Key_Space):
                self.pause_unpause()
                return True
            elif (event.type() == QEvent.KeyPress):
                #left  16777234
                #right 16777251
                if (event.key() == Qt.Key_Left):


                    playback["time"] = playback["time"]-5
                    if playback["time"]<0:
                        playback["time"]=0
                    playback["Pending_changes"].append("time")
                    return True

                elif (event.key() == Qt.Key_Right):


                    playback["time"] = playback["time"]+5
                    if playback["time"]>playback["length"]:
                        playback["time"]=playback["length"]
                    playback["Pending_changes"].append("time")
                    return True



                elif event.key() in [Qt.Key_Down, Qt.Key_Up]:
                    return True #Dont close itself fro some reason

        return super(Ui_MainWindow, self).eventFilter(widget, event)
