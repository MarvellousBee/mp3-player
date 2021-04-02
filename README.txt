# MPy3
(nazwa kradziona ale martwa od 2013)
### Użyte technologie:

* pip3 install python-vlc (Potrzebny też jest [libvlc](https://www.videolan.org/vlc/libvlc.html) __LUB__ [vlc](https://www.videolan.org/vlc/index.pl.html))
* pip3 install filelock
* pip3 install ultra_sockets
* pip3 install PyQt5 
* pip3 install eyed3

### Co to jest i do czego służy?
Odtwarzacz mp3. 
Jego dodatkową możliwością jest wykonywania funkcji napisanych przez użytkownika (W pythoniku oczywiście).

### Jak włączyć
Po zainstalowaniy bibliotek i vlc należy uruchomić plik `main.py`.
Pozostwaiłem kilka przykładowych utworów i funkcji.

Opcjonalnie można podać ścieżkę do utworu jako argument. Spowoduje to odtworzenie tego utworu zamiast ostatniej playlisty, np:
`cd C:\mp3-player & python3 main.py "C:\przyklad.mp3"
`
### Krótki poradnik użytkownika
Klikając w drugą ikonkę w lewym górnym rogu można zmienić tryb na jasny/ciemny.

Trzy listy zawierają kolejno: utwory, pliki funkcji (więcej o tym w kolejnej sekcji), playlisty.
Searchbox pozwala na filtrowanie playlisty.

opis przycisków nieoczywistych:
__Jeśli klikniemy na liście utworów lub playlist__, niemal wszystkie guziory dostępne są również pod prawym przyciskiem myszy. 

`<3` pozwala na łatwiejsze dodawnie i usuwanie z `Favorites`

Pod lewą listą:
`+ File` dodaje 1 utwór do aktualnej playlisty
`+ Folder` dodaje wszystkie utwory z zaznaczonego folderu
`-` usuwa zaznaczony utwór. Znika, jesli nie ma utworów.
pod prawą listą:
`+` dodaje playlistę
`-` usuwa playlistę. Znika, Jeśli zaznaczona jest `Favorites`. Nie można usuwać tej playlisty.

### Jak działają funkcje?
MPy3 przed włączeniem GUI __zawsze__ wykonuje funkcję `start_func()`, zaś przy zmiany utworu wykonuje `song_func()`.
GUI nie włączy się przed ukończeniem `start_func()`. `song_func()` jest threadowane, więc nie zatrzymuje aplikacji.

Wybieramy parę funkcji przez zaznaczenie jej z środkowej listy. Powoduje to restart aplikacji. 
Wszystkie pliki w folderze `user_functions` o zakończeniu .py się na niej znajdą.

Napisałem kilka przykładów.

Użytkownik w tych funkcjach ma dostęp do następujących wartości (Dzięki magii monkey patchingu nie trzeba ich importować):
`playback` słownik zawierający informacje o stanie aplikacji
`F` klasa z funkcjami, za pomocą których można manipulować aplikacją.

### Dokumentacja `playback`

Nie należny niczego tu zmieniać.
Wszelki działania na aplikacji powinny być wykonywane za pomocą klasy `F`.

* `playback['path']`:`str`
pełna ścieżka do utworu
* `playback['full_track']`:`str`
nazwa pliku utworu
* `playback['track']`: `str`
nazwa utworu
* `playback['is_playing']`:`bool`
Czy aktualnie utwór jest grany
* `playback['time']`:`int`
Jaka część utworu mineła
* `playback['length']`:`int`
Jaka jest długość utworu
* `playback['length_mins']`:`str`
Jaka część utworu mineła (w minutach)
* `playback['time_mins']`:`str`
Jaka jest długość utworu (w minutach)
* `playback['volume']`:`int`
Aktualna głośność
* `playback['hidden_volume']`:`int`
Aktualna głośność, ale niezależna od wyciszenia.
głośność powraca do tej wartości po wyłączeniu wyciszenia
* `playback['id']`:`int`
id utworu w playliście
* `playback['playlist']`:`list`
wszystkie ścieżki utworów aktualnej playlisty
* `playback['shuffled_playlist']`:`list`
`playback['playlist']`, ale pomieszany. Używany, gdy użytkownik wybierze mieszanie playlisty.
* `playback['playlist_id']`:`int`
id playlisty
* `playback['shuffle']`:`bool`
czy odtwarzać wymieszaną playlistę?
* `playback['loop']`:`bool`
czy zapętlić playlistę?
* `playback['module']`:`str`
aktualny plik funkcji
* `playback['artist']`:`str`/`None`
twórca utworu
* `playback['image']`:`str`/`None`
ścieżka do obrazka, jeśli  obrazek istnieje.
(aplikcja zapisuje ostatni cover art w `assets`)
* `playback['in_favorites']`:`bool`
Czy utwór jest w ulubionych?
* `playback['dark_mode']`:`int`
Czy tryb ciemny jest włączony? 
* `playback['Pending_changes']`:`list`
Nieważna dla użytkownika

### Dokumantacja `F`

* `F.set_song_by_id(id)`
Odtwórz utwór z playlisty podanym id
* `F.set_song_by_path(path)`
Odtwórz utwór z playlisty z podanej ścieżki
* `F.set_song_by_name(name)`
Odtwórz utwór z playlisty z podanym tytułem
* `F.set_volume(volume)`
ustaw głośność
* `F.play()`
Odtwarzaj
* `F.pause()`
Pauza
* `F.set_time(seconds)`
ustaw czas utworu w sekundach
wartości `float` mogą nie działać.
* `F.change_playlist(id)`
ustaw playlistę wg id
* `f.toggle_shuffle()`
włącz/wyłącz mieszanie playlisty
* `f.toggle_loop()`
bez zapętlenia/zapętl całą playlistę/ zapetl cały utwór
* `f.set_loop(what)`
0 = bez zapętlenia
1 = zapętl całą playlistę
2 = zapetl ten utwór
* `F.change_module(module)`
wybierz plik funkcji
* `F.listener(ip, port)`
Eksperymentalna funkcja, testowana tylko w `start_func()`.
Otwiera port (domyślnie 5556) z podanego ip (domyślnie ip urządzenia) i nasłuchuje.
Gdy port jest otwarty, można podłączyć się do niego z innej aplikacji. Działa przez Wi-Fi.
plik `przykładowy_komunikator.py` zawiera niezbędne funkcje do wysyłania komend z innej aplikacji oraz instrukcje.


