# AudioAnalyzer

AudioAnalyzer is a simple Python GUI application for classifying and sorting a dataset of audio files (WAV, MP3) into folders using hotkeys and buttons.
The program also displays the waveform of the audio file and allows quick undo of accidental actions.

![image](https://github.com/user-attachments/assets/62978992-db83-4799-9ac0-7c7dde8e5916)

[Download](https://github.com/wachawo/audioanalyzer/releases)

## Features
* Fast sorting of audio files into categories (folders) using buttons or hotkeys (1, 2, 3…)
* Audio playback (via pygame)
* Display of the audio waveform
* Copy filename and folder path to clipboard
* Logs all actions (aa.log file in the selected folder)
* Undo last action (file move)

## Dependencies
Python 3.7+ is required, along with the following libraries:

```bash
sudo apt install python3-tk tk-dev ffmpeg alsa alsa-utils
pip3 install pillow pydub pygame matplotlib numpy pytest pytest-mock
```

## Running the Application

```bash
python3 main.py
```

## Usage
1. Launch the application.
2. Select a folder with audio files (WAV, MP3).
3. For each file:
   * Listen to the audio (automatically or by clicking/pressing space).
   * View the waveform.
   * Classify the file by clicking a button or pressing a hotkey (1 — YES, 2 — NO, 3 — OTHER).
   * To undo the last action, use the CANCEL button or press C / Backspace / Delete.
4. Click on the filename or folder path to copy it to the clipboard.

## Notes
* All file moves are logged in aa.log.
* For proper audio playback on Linux, ALSA and ffmpeg may be required.
* The app does not modify original files, only moves them into subfolders.

## For Developers

```bash
pip install pre-commit flake8 pytest
pre-commit install
pre-commit run --all-files
pre-commit autoupdate
```

[GitHub](https://github.com/wachawo/audioanalyzer) [Telegram](https://t.me/wachawo) 
