#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# brew install python-tk@3.11 tcl-tk ffmpeg
# sudo apt install python3-tk tk-dev ffmpeg
# pip3 install pillow pydub pygame matplotlib numpy
import os
import shutil
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
from pydub import AudioSegment
import matplotlib.pyplot as plt
import numpy as np
import pygame

# Global options and log file name
OPTIONS = ["YES", "NO", "SKIP"]  # You can add up to 10 options
LOG_FILE = "aa.log"

class AudioClassifierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AudioAnalyzer")
        self.selected_folder = os.getcwd()
        self.audio_files = []
        self.current_index = 0
        self.is_playing = False
        self.log_file_path = None
        self.action_history = []

        # File moving options
        self.options = OPTIONS

        pygame.mixer.init()

        self.create_widgets()

    def create_widgets(self):
        # Info Frame
        self.info_frame = Frame(self.root)
        self.info_frame.pack(pady=10, fill=X)

        # Folder selection
        self.folder_frame = Frame(self.info_frame)
        self.folder_frame.pack()

        self.folder_button = Button(self.folder_frame, text="FOLDER", command=self.select_folder,
                                    activebackground='lightgray', activeforeground='black')
        self.folder_button.pack(side=LEFT, padx=5)

        self.folder_label = Label(self.folder_frame, text=f"{self.selected_folder}")
        self.folder_label.pack(side=LEFT, padx=5)
        self.folder_label.bind("<Button-1>", self.copy_folder_path)

        self.reset_button = Button(self.folder_frame, text="✖", state=DISABLED, command=self.reset_folder,
                                   activebackground='lightgray', activeforeground='black')
        self.reset_button.pack(side=RIGHT, padx=5)

        # File name
        self.file_label = Label(self.info_frame, text="None")
        self.file_label.pack()
        self.file_label.bind("<Button-1>", self.copy_file_name)

        # Notification label
        self.notification_label = Label(self.info_frame, text="", fg="red", font=("Helvetica", 10, "bold"))
        self.notification_label.pack(pady=5)

        # Counts
        options_counts = ", ".join([f"{opt}: 0" for opt in self.options])
        self.counts_label = Label(self.info_frame, text=f"FILES: 0\n{options_counts}")
        self.counts_label.pack(pady=5)

        # Waveform display
        self.waveform_frame = Frame(self.root)
        self.waveform_frame.pack(pady=10)

        self.waveform_canvas = Canvas(self.waveform_frame, width=400, height=200)
        self.waveform_canvas.pack()
        self.waveform_canvas.bind("<Button-1>", self.on_waveform_click)

        # File info under waveform
        self.file_info_label = Label(self.waveform_frame, text="")
        self.file_info_label.pack(pady=5)

        # Control buttons
        self.button_frame = Frame(self.root)
        self.button_frame.pack(pady=10)

        self.buttons = []
        # Map keys from '1' to '9' and '0' to options
        key_mapping = ['1','2','3','4','5','6','7','8','9','0']
        for idx, option in enumerate(self.options):
            btn = Button(self.button_frame, text=option, width=10,
                         command=lambda opt=option: self.move_file(opt),
                         activebackground='lightgray', activeforeground='black')
            btn.pack(side=LEFT, padx=5)
            self.buttons.append(btn)
            # Bind hotkeys
            if idx < len(key_mapping):
                key = key_mapping[idx]
                self.root.bind(f'<KeyPress-{key}>', lambda event, opt=option: self.move_file(opt))
            else:
                print(f"No key binding for option '{option}' (maximum 10 options supported).")

        # Cancel button
        self.cancel_button = Button(self.button_frame, text="CANCEL", width=10, command=self.cancel_action,
                                    activebackground='lightgray', activeforeground='black', state=DISABLED)
        self.cancel_button.pack(side=LEFT, padx=5)

        # Bind keys for cancel action
        self.bind_cancel_keys()

        # Bind spacebar for replay
        self.root.bind('<space>', lambda event: self.play_audio())

        # Initially disable certain widgets
        self.disable_widgets()

    def bind_cancel_keys(self):
        # Bind to all key presses
        self.root.bind('<Key>', self.on_keypress)

    def on_keypress(self, event):
        # Check for cancel keys
        cancel_chars = ('c', 'C', 'с', 'С')  # Latin and Cyrillic 'C' and 'c'
        if event.char in cancel_chars:
            self.cancel_action()
        elif event.keysym in ('BackSpace', 'Delete'):
            self.cancel_action()
        else:
            # Check if key is associated with an option
            key_mapping = ['1','2','3','4','5','6','7','8','9','0']
            if event.keysym in key_mapping:
                idx = key_mapping.index(event.keysym)
                if idx < len(self.options):
                    self.move_file(self.options[idx])

    def disable_widgets(self):
        self.reset_button.config(state=DISABLED)
        self.folder_label.config(state=DISABLED)
        self.file_label.config(state=DISABLED)
        self.counts_label.config(state=DISABLED)
        self.file_info_label.config(state=DISABLED)
        for btn in self.buttons:
            btn.config(state=DISABLED)
        # Keep cancel_button enabled if there is action history
        if self.action_history:
            self.cancel_button.config(state=NORMAL)
        else:
            self.cancel_button.config(state=DISABLED)

    def enable_widgets(self):
        self.reset_button.config(state=NORMAL)
        self.folder_label.config(state=NORMAL)
        self.file_label.config(state=NORMAL)
        self.counts_label.config(state=NORMAL)
        self.file_info_label.config(state=NORMAL)
        for btn in self.buttons:
            btn.config(state=NORMAL)
        # Enable cancel_button if there is action history
        if self.action_history:
            self.cancel_button.config(state=NORMAL)

    def select_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.selected_folder)
        if folder_selected:
            self.selected_folder = folder_selected
            self.folder_label.config(text=f"{self.selected_folder}")
            self.reset_button.config(state=NORMAL)
            self.folder_button.config(state=DISABLED)
            self.load_audio_files()

            # Initialize log file and action history
            self.log_file_path = os.path.join(self.selected_folder, LOG_FILE)
            if not os.path.exists(self.log_file_path):
                with open(self.log_file_path, 'w') as f:
                    pass  # Create empty log file
            self.action_history = []

    def reset_folder(self):
        self.selected_folder = os.getcwd()
        self.folder_label.config(text=f"{self.selected_folder}")
        self.reset_button.config(state=DISABLED)
        self.folder_button.config(state=NORMAL)
        self.disable_widgets()
        self.audio_files = []
        self.current_index = 0
        options_counts = ", ".join([f"{opt}: 0" for opt in self.options])
        self.counts_label.config(text=f"FILES: 0\n{options_counts}")
        self.file_label.config(text="None")
        self.file_info_label.config(text="")
        self.waveform_canvas.delete("all")
        self.action_history = []
        self.log_file_path = None
        self.notification_label.config(text="")

    def load_audio_files(self):
        self.audio_files = [f for f in os.listdir(self.selected_folder) if f.lower().endswith(('.wav', '.mp3'))]
        if not self.audio_files:
            self.disable_widgets()
            self.notification_label.config(text="NO AUDIO FILES FOUND")
            return
        self.current_index = 0
        self.update_file_info()
        self.enable_widgets()
        self.play_audio()
        self.notification_label.config(text="")

    def update_counts(self):
        files_remaining = len(self.audio_files) - self.current_index
        counts = []
        for option in self.options:
            count = len(os.listdir(os.path.join(self.selected_folder, option))) if os.path.exists(os.path.join(self.selected_folder, option)) else 0
            counts.append(f"{option}: {count}")
        counts_str = ", ".join(counts)
        self.counts_label.config(text=f"FILES: {files_remaining}\n{counts_str}")

    def update_file_info(self):
        self.update_counts()
        if self.current_index < len(self.audio_files):
            current_file = self.audio_files[self.current_index]
            file_path = os.path.join(self.selected_folder, current_file)
            # Get file size
            file_size_bytes = os.path.getsize(file_path)
            file_size_str = "{:,}".format(file_size_bytes).replace(',', ' ')
            # Get audio details
            audio = AudioSegment.from_file(file_path)
            duration = round(audio.duration_seconds, 2)
            channels = audio.channels
            sample_rate = audio.frame_rate
            # Update labels
            self.file_label.config(text=current_file)
            self.file_info_label.config(text=f"{channels} Channel(s), {sample_rate} Hz, {file_size_str} Bytes, {duration} sec")
            self.display_waveform()
            self.notification_label.config(text="")
        else:
            # No more files, but keep CANCEL active if there is action history
            self.disable_widgets()
            self.notification_label.config(text="NO MORE FILES TO PROCESS")
            if self.action_history:
                self.cancel_button.config(state=NORMAL)
                self.reset_button.config(state=NORMAL)
            else:
                # If no action history, allow resetting folder
                self.reset_button.config(state=NORMAL)
                self.folder_button.config(state=NORMAL)

    def play_audio(self):
        if self.current_index >= len(self.audio_files):
            return
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
        file_path = os.path.join(self.selected_folder, self.audio_files[self.current_index])
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        self.is_playing = True

    def move_file(self, folder_name):
        if self.current_index >= len(self.audio_files):
            return
        current_file = self.audio_files[self.current_index]
        source = os.path.join(self.selected_folder, current_file)
        dest_folder = os.path.join(self.selected_folder, folder_name)
        os.makedirs(dest_folder, exist_ok=True)
        dest = os.path.join(dest_folder, current_file)
        shutil.move(source, dest)
        # Log the action
        with open(self.log_file_path, 'a') as log_file:
            log_file.write(f"{current_file},{folder_name}\n")
        self.action_history.append((current_file, folder_name))
        self.cancel_button.config(state=NORMAL)
        # Remove the file from the list
        del self.audio_files[self.current_index]
        self.update_file_info()
        self.play_audio()

    def cancel_action(self):
        if not self.action_history:
            self.notification_label.config(text="NO ACTIONS TO CANCEL")
            self.cancel_button.config(state=DISABLED)
            return
        # Get the last action
        last_file, last_folder = self.action_history.pop()
        # Move the file back
        src = os.path.join(self.selected_folder, last_folder, last_file)
        dest = os.path.join(self.selected_folder, last_file)
        shutil.move(src, dest)
        # Remove the last line from the log file
        with open(self.log_file_path, 'r') as f:
            lines = f.readlines()
        with open(self.log_file_path, 'w') as f:
            f.writelines(lines[:-1])  # Write all lines except the last one
        # Insert the file back into the list and adjust current_index
        self.audio_files.insert(self.current_index, last_file)
        # Re-enable widgets if they were disabled
        self.enable_widgets()
        self.update_file_info()
        self.play_audio()
        # Disable cancel button if no more actions
        if not self.action_history:
            self.cancel_button.config(state=DISABLED)
            # If no more files, allow resetting folder
            if self.current_index >= len(self.audio_files):
                self.disable_widgets()
                self.reset_button.config(state=NORMAL)
                self.folder_button.config(state=NORMAL)
        self.notification_label.config(text="ACTION CANCELLED")

    def display_waveform(self):
        file_path = os.path.join(self.selected_folder, self.audio_files[self.current_index])
        audio = AudioSegment.from_file(file_path)
        data = np.array(audio.get_array_of_samples())
        plt.figure(figsize=(4, 2))
        plt.plot(data)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig("waveform.png")
        plt.close()
        self.waveform_image = ImageTk.PhotoImage(Image.open("waveform.png"))
        self.waveform_canvas.delete("all")
        self.waveform_canvas.create_image(200, 100, image=self.waveform_image)
        os.remove("waveform.png")

    def copy_folder_path(self, event):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.selected_folder)
        self.notification_label.config(text="PATHNAME COPIED")

    def copy_file_name(self, event):
        if self.current_index < len(self.audio_files):
            file_name = self.audio_files[self.current_index]
            self.root.clipboard_clear()
            self.root.clipboard_append(file_name)
            self.notification_label.config(text="FILENAME COPIED")
        else:
            self.notification_label.config(text="NO FILE TO COPY")

    def on_waveform_click(self, event):
        self.play_audio()

def main():
    root = Tk()
    app = AudioClassifierApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
