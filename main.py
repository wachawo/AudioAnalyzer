#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# brew install python-tk@3.11 tcl-tk ffmpeg
# sudo apt install python3-tk tk-dev ffmpeg alsa alsa-utils
# pip3 install pillow pydub pygame matplotlib numpy pytest pytest-mock
# sudo ln -sf ${PWD}/audioanalyzer /usr/local/bin/audioanalyzer
import logging
import pygame
import os
import shutil
from tkinter import Tk, Frame, Button, Label, Canvas
from tkinter import filedialog
from PIL import Image, ImageTk
from pydub import AudioSegment
import matplotlib.pyplot as plt
import numpy as np


# Global options and log file name
OPTIONS = ["YES", "NO", "OTHER"]
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
        try:
            pygame.mixer.init()
        except pygame.error as e:
            logging.error(f"{type(e).__name__} {str(e)}")
            self.root.quit()

        self.create_widgets()

    def create_widgets(self):
        # Info Frame
        self.info_frame = Frame(self.root)
        self.info_frame.pack(pady=10, fill="x")

        # Folder selection
        self.folder_frame = Frame(self.info_frame)
        self.folder_frame.pack()

        self.folder_button = Button(self.folder_frame, text="FOLDER", command=self.select_folder,
                                    activebackground='lightgray', activeforeground='black')
        self.folder_button.pack(side="left", padx=5)

        self.folder_label = Label(self.folder_frame, text=f"{self.selected_folder}")
        self.folder_label.pack(side="left", padx=5)
        self.folder_label.bind("<Button-1>", self.copy_folder_path)

        self.reset_button = Button(self.folder_frame, text="✖", state="disabled", command=self.reset_folder,
                                   activebackground='lightgray', activeforeground='black')
        self.reset_button.pack(side="right", padx=5)

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
        key_mapping = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        for idx, option in enumerate(self.options):
            btn = Button(self.button_frame, text=option, width=10,
                         command=lambda opt=option: self.move_file(opt),
                         activebackground='lightgray', activeforeground='black')
            btn.pack(side="left", padx=5)
            self.buttons.append(btn)
            # Bind hotkeys
            if idx < len(key_mapping):
                key = key_mapping[idx]
                self.root.bind(f'<KeyPress-{key}>', lambda event, opt=option: self.move_file(opt))
            else:
                print(f"No key binding for option '{option}' (maximum 10 options supported).")

        # Cancel button
        self.cancel_button = Button(self.button_frame, text="CANCEL", width=10, command=self.cancel_action,
                                    activebackground='lightgray', activeforeground='black', state="disabled")
        self.cancel_button.pack(side="left", padx=5)

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
            key_mapping = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
            if event.keysym in key_mapping:
                idx = key_mapping.index(event.keysym)
                if idx < len(self.options):
                    self.move_file(self.options[idx])

    def disable_widgets(self):
        self.reset_button.config(state="disabled")
        self.folder_label.config(state="disabled")
        self.file_label.config(state="disabled")
        self.counts_label.config(state="disabled")
        self.file_info_label.config(state="disabled")
        for btn in self.buttons:
            btn.config(state="disabled")
        # Keep cancel_button enabled if there is action history
        if self.action_history:
            self.cancel_button.config(state="normal")
        else:
            self.cancel_button.config(state="disabled")

    def enable_widgets(self):
        self.reset_button.config(state="normal")
        self.folder_label.config(state="normal")
        self.file_label.config(state="normal")
        self.counts_label.config(state="normal")
        self.file_info_label.config(state="normal")
        for btn in self.buttons:
            btn.config(state="normal")
        # Enable cancel_button if there is action history
        if self.action_history:
            self.cancel_button.config(state="normal")

    def select_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.selected_folder)
        if folder_selected:
            self.selected_folder = folder_selected
            self.folder_label.config(text=f"{self.selected_folder}")
            self.reset_button.config(state="normal")
            self.folder_button.config(state="disabled")
            self.load_audio_files()

            # Initialize log file and action history
            self.log_file_path = os.path.join(self.selected_folder, LOG_FILE)
            if not os.path.exists(self.log_file_path):
                with open(self.log_file_path, 'w') as f:
                    f.write("")  # Create an empty log file
            self.action_history = []

    def reset_folder(self):
        self.selected_folder = os.getcwd()
        self.folder_label.config(text=f"{self.selected_folder}")
        self.reset_button.config(state="disabled")
        self.folder_button.config(state="normal")
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
            count = len(os.listdir(os.path.join(self.selected_folder, option))) \
                if os.path.exists(os.path.join(self.selected_folder, option)) else 0
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
            self.file_info_label.config(
                text=f"{channels} Channel(s), {sample_rate} Hz, {file_size_str} Bytes, {duration} sec"
            )
            self.display_waveform()
            self.notification_label.config(text="")
        else:
            # No more files, but keep CANCEL active if there is action history
            self.disable_widgets()
            self.notification_label.config(text="NO MORE FILES TO PROCESS")
            if self.action_history:
                self.cancel_button.config(state="normal")
                self.reset_button.config(state="normal")
            else:
                # If no action history, allow resetting folder
                self.reset_button.config(state="normal")
                self.folder_button.config(state="normal")

    def play_audio(self):
        if self.current_index >= len(self.audio_files):
            return
        if self.is_playing:
            try:
                pygame.mixer.music.stop()
            except Exception as e:
                logging.error(f"{type(e).__name__} {str(e)}")
            self.is_playing = False
        file_path = os.path.join(self.selected_folder, self.audio_files[self.current_index])
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.is_playing = True
        except Exception as e:
            self.notification_label.config(text=f"AUDIO ERROR: {e}")
            logging.error(f"{type(e).__name__} {str(e)}")
            self.is_playing = False

    def move_file(self, folder_name):
        if self.current_index >= len(self.audio_files):
            return
        current_file = self.audio_files[self.current_index]
        source = os.path.join(self.selected_folder, current_file)
        dest_folder = os.path.join(self.selected_folder, folder_name)
        os.makedirs(dest_folder, exist_ok=True)
        dest = os.path.join(dest_folder, current_file)
        try:
            shutil.move(source, dest)
        except Exception as e:
            self.notification_label.config(text=f"MOVE ERROR: {e}")
            logging.error(f"{type(e).__name__} {str(e)}")
            return
        # Log the action
        try:
            with open(self.log_file_path, 'a') as log_file:
                log_file.write(f"{current_file},{folder_name}\n")
        except Exception as e:
            logging.error(f"{type(e).__name__} {str(e)}")
        self.action_history.append((current_file, folder_name))
        self.cancel_button.config(state="normal")
        # Remove the file from the list
        del self.audio_files[self.current_index]
        self.update_file_info()
        self.play_audio()

    def cancel_action(self):
        if not self.action_history:
            self.notification_label.config(text="NO ACTIONS TO CANCEL")
            self.cancel_button.config(state="disabled")
            return
        # Get the last action
        last_file, last_folder = self.action_history.pop()
        src = os.path.join(self.selected_folder, last_folder, last_file)
        dest = os.path.join(self.selected_folder, last_file)
        try:
            shutil.move(src, dest)
        except Exception as e:
            self.notification_label.config(text=f"CANCEL ERROR: {e}")
            logging.error(f"{type(e).__name__} {str(e)}")
            return
        # Remove the last line from the log file
        try:
            with open(self.log_file_path, 'r') as f:
                lines = f.readlines()
            with open(self.log_file_path, 'w') as f:
                f.writelines(lines[:-1])  # Write all lines except the last one
        except Exception as e:
            logging.error(f"{type(e).__name__} {str(e)}")
        # Insert the file back into the list and adjust current_index
        self.audio_files.insert(self.current_index, last_file)
        # Re-enable widgets if they were disabled
        self.enable_widgets()
        self.update_file_info()
        self.play_audio()
        # Disable cancel button if no more actions
        if not self.action_history:
            self.cancel_button.config(state="disabled")
            # If no more files, allow resetting folder
            if self.current_index >= len(self.audio_files):
                self.disable_widgets()
                self.reset_button.config(state="normal")
                self.folder_button.config(state="normal")
        self.notification_label.config(text="ACTION CANCELLED")

    def display_waveform(self):
        file_path = os.path.join(self.selected_folder, self.audio_files[self.current_index])
        try:
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
        except Exception as e:
            self.notification_label.config(text=f"WAVEFORM ERROR: {e}")
            logging.error(f"{type(e).__name__} {str(e)}")
        finally:
            if os.path.exists("waveform.png"):
                try:
                    os.remove("waveform.png")
                except Exception as e:
                    logging.error(f"{type(e).__name__} {str(e)}")

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
    AudioClassifierApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
