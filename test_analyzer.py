#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pytest
import tkinter as tk
import warnings
from main import AudioClassifierApp
from unittest.mock import patch, MagicMock

warnings.filterwarnings("ignore", category=DeprecationWarning)


@pytest.fixture(autouse=True)
def mock_external_libs():
    """
    Mock external libraries (pydub, pygame, matplotlib) to avoid errors
    and dependencies on audio hardware/files during testing.
    """
    with patch("main.AudioSegment.from_file") as mock_from_file, \
            patch("main.pygame.mixer") as mock_mixer, \
            patch("main.plt.savefig") as mock_savefig:

        # Mock AudioSegment to return a dummy audio object
        mock_audio = MagicMock()
        mock_audio.duration_seconds = 1.23
        mock_audio.channels = 2
        mock_audio.frame_rate = 44100
        mock_audio.get_array_of_samples.return_value = [0, 1, 2, 3]
        mock_from_file.return_value = mock_audio

        # Mock pygame mixer
        mock_mixer.init.return_value = None
        mock_mixer.music.load.return_value = None
        mock_mixer.music.play.return_value = None
        mock_mixer.music.stop.return_value = None

        yield mock_from_file, mock_mixer, mock_savefig


@pytest.fixture
def temp_audio_folder(tmp_path):
    """
    Create a temporary folder with dummy test audio files.
    """
    folder = tmp_path / "audio"
    folder.mkdir()
    (folder / "test1.wav").touch()
    (folder / "test2.mp3").touch()
    return str(folder)


@pytest.fixture
def app(temp_audio_folder):
    """
    Initialize the AudioClassifierApp with the temporary folder for testing.
    """
    root = tk.Tk()
    app_instance = AudioClassifierApp(root)
    app_instance.selected_folder = temp_audio_folder
    # Manually create the log file for tests
    app_instance.log_file_path = os.path.join(temp_audio_folder, "aa.log")
    with open(app_instance.log_file_path, 'w') as f:
        f.write("")
    app_instance.load_audio_files()
    yield app_instance
    root.destroy()


def test_load_audio_files(app):
    """
    Test that audio files are loaded correctly into the application.
    """
    assert len(app.audio_files) == 2
    assert app.current_index == 0
    assert app.file_label.cget("text") in ["test1.wav", "test2.mp3"]
    assert app.notification_label.cget("text") == ""


def test_move_file_creates_folder_and_moves(app):
    """
    Test that moving a file creates the destination folder and moves the file.
    """
    file_to_move = app.audio_files[app.current_index]
    app.move_file("YES")

    moved_path = os.path.join(app.selected_folder, "YES", file_to_move)
    assert os.path.exists(moved_path)
    assert file_to_move not in app.audio_files


def test_cancel_action_restores_file(app):
    """
    Test that the cancel action restores a moved file to its original location.
    """
    file_to_move = app.audio_files[app.current_index]
    app.move_file("NO")
    assert file_to_move not in app.audio_files

    app.cancel_action()

    restored_path = os.path.join(app.selected_folder, file_to_move)
    assert os.path.exists(restored_path)
    assert file_to_move in app.audio_files
    assert app.notification_label.cget("text") == "ACTION CANCELLED"


def test_copy_folder_path(app, mocker):
    """
    Test that the folder path is copied to the clipboard.
    """
    mocker.patch.object(app.root, 'clipboard_clear')
    mocker.patch.object(app.root, 'clipboard_append')

    app.copy_folder_path(mocker.Mock())

    app.root.clipboard_clear.assert_called_once()
    app.root.clipboard_append.assert_called_with(app.selected_folder)
    assert app.notification_label.cget("text") == "PATHNAME COPIED"


def test_copy_file_name(app, mocker):
    """
    Test that the current file name is copied to the clipboard.
    """
    mocker.patch.object(app.root, 'clipboard_clear')
    mocker.patch.object(app.root, 'clipboard_append')
    current_file = app.audio_files[app.current_index]

    app.copy_file_name(mocker.Mock())

    app.root.clipboard_clear.assert_called_once()
    app.root.clipboard_append.assert_called_with(current_file)
    assert app.notification_label.cget("text") == "FILENAME COPIED"
