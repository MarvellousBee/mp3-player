import os

#Convert seconds to minutes
def mins(length):
    minutes = int(length/60)
    seconds = str(length-minutes*60)
    if len(seconds)==1:
        seconds="0"+seconds
    return f"{minutes}:{seconds}"

def strip_path(song):
    song_name = os.path.basename(song)# path > filenames
    song_name_no_extension = ".".join(song_name.split(".")[:-1])
    return [song_name, song_name_no_extension]#delete the extension, better use regex or sth
