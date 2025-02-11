import time
import datetime
import pygame
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL

# Initialize pygame for audio playback
pygame.mixer.init()

# Global variables
ALARM_FILE = "alarms.json"
SONG_FOLDER = "Alarm_Sounds"
alarms = []
song_library = []

# Initialize PyCAW for volume control
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)
volume.SetMasterVolumeLevelScalar(0.1, None)

# Ensure the song folder exists
if not os.path.exists(SONG_FOLDER):
    os.makedirs(SONG_FOLDER)

def load_songs():
    """Loads available songs from the Alarm_Sounds folder."""
    global song_library
    song_library.clear()
    song_library.extend([f for f in os.listdir(SONG_FOLDER) if f.endswith(".mp3")])

def upload_song():
    """Allows the user to upload a new mp3 song to the library and refreshes the UI."""
    file_path = filedialog.askopenfilename(filetypes=[("MP3 Files", "*.mp3")])
    if file_path:
        destination = os.path.join(SONG_FOLDER, os.path.basename(file_path))
        os.rename(file_path, destination)
        load_songs()
        song_var.set(song_library[0] if song_library else "No songs available")
        song_menu['menu'].delete(0, 'end')
        for song in song_library:
            song_menu['menu'].add_command(label=song, command=tk._setit(song_var, song))

def save_alarms():
    """Saves alarms to a JSON file."""
    with open(ALARM_FILE, "w") as file:
        json.dump(alarms, file)

def load_alarms():
    """Loads alarms from the JSON file."""
    global alarms
    if os.path.exists(ALARM_FILE):
        with open(ALARM_FILE, "r") as file:
            alarms = json.load(file)

def convert_to_24_hour(hour, minute, period):
    """Converts 12-hour format to 24-hour format."""
    hour = int(hour)
    minute = int(minute)
    if period == "PM" and hour != 12:
        hour += 12
    elif period == "AM" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}:00"

def gradually_increase_volume():
    """Gradually increases the volume from 10% to 100% over 30 seconds."""
    for i in range(9):
        current_volume = volume.GetMasterVolumeLevelScalar()
        volume.SetMasterVolumeLevelScalar(min(1, current_volume + 0.1), None)
        time.sleep(3)

def play_alarm(song_path):
    if pygame.mixer.music.get_busy():
        return
    """Plays the selected alarm song."""
    if not os.path.exists(song_path):
        messagebox.showerror("Error", "Selected alarm sound file not found.")
        return
    
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play()

    gradually_increase_volume()


def check_alarms():
    """Continuously checks the time and triggers alarms."""
    while True:
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        for alarm in alarms:
            if alarm["active"] and current_time >= alarm["time"]:
                threading.Thread(target=play_alarm, args=(alarm["song"],)).start()
        time.sleep(5)

def toggle_alarm(index):
    """Toggles the active state of an alarm."""
    alarms[index]["active"] = not alarms[index]["active"]
    save_alarms()
    update_alarm_list()

def update_alarm_list():
    """Updates the alarm list in the UI."""
    for widget in alarm_frame.winfo_children():
        widget.destroy()
    
    for i, alarm in enumerate(alarms):
        frame = tk.Frame(alarm_frame, bd=2, relief=tk.RIDGE)
        frame.pack(fill="x", pady=2)

        status_color = "green" if alarm["active"] else "red"
        status_canvas = tk.Canvas(frame, width=15, height=15, bg="white", highlightthickness=0)
        status_canvas.create_oval(2, 2, 13, 13, fill=status_color)
        status_canvas.pack(side="right", padx=5)

        tk.Label(frame, text=f"{alarm['time']} - {os.path.basename(alarm['song'])}").pack(side="left", padx=5)
        tk.Button(frame, text="Toggle", command=lambda idx=i: toggle_alarm(idx)).pack(side="right", padx=5)

def add_alarm(hour, minute, period, song):
    """Adds a new alarm and updates the UI."""
    alarm_time = convert_to_24_hour(hour, minute, period)
    alarms.append({"time": alarm_time, "song": song, "active": True})
    save_alarms()
    update_alarm_list()

def create_ui():
    """Creates the Tkinter UI for the alarm clock."""
    global alarm_frame, song_var, song_menu
    root = tk.Tk()
    root.title("Alarm Clock")
    root.geometry("600x300")

    load_alarms()
    load_songs()

    tk.Label(root, text="Set Alarm Time:").pack()
    hours = [str(i) for i in range(1, 13)]
    minutes = [f"{i:02d}" for i in range(0, 60)]
    periods = ["AM", "PM"]
    hour_var, minute_var, period_var = tk.StringVar(value="07"), tk.StringVar(value="00"), tk.StringVar(value="AM")

    if not song_library:
        song_library.append("No songs available")
    
    song_var = tk.StringVar(value=song_library[0])

    tk.OptionMenu(root, hour_var, *hours).pack(side="left")
    tk.OptionMenu(root, minute_var, *minutes).pack(side="left")
    tk.OptionMenu(root, period_var, *periods).pack(side="left")
    
    song_menu = tk.OptionMenu(root, song_var, *song_library)
    song_menu.pack(side="left")

    tk.Button(root, text="Upload Song", command=upload_song).pack()
    tk.Button(root, text="Set Alarm", command=lambda: add_alarm(hour_var.get(), minute_var.get(), period_var.get(), os.path.join(SONG_FOLDER, song_var.get()) if song_var.get() != "No songs available" else "")).pack()
    
    alarm_frame = tk.Frame(root)
    alarm_frame.pack(fill="both", expand=True)

    update_alarm_list()
    threading.Thread(target=check_alarms, daemon=True).start()
    root.mainloop()

if __name__ == '__main__':
    create_ui()
