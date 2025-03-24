#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle Maker - Audio to Subtitle Converter

Original author: Naveen Kumar Vasudevan, 400107764
                Doctoral Student, The Xi Research Group
                McMaster University, Hamilton, Canada
                naveenovan@gmail.com
                https://naveenovan.wixsite.com/kuroonai
Date: March 24, 2025

This tool converts audio files to subtitles by:
1. Breaking the audio into segments
2. Transcribing each segment using Google Speech Recognition
3. Translating the text to a chosen language
4. Formatting the output into an SRT file

Requirements:
- ffmpeg must be installed and in PATH (https://ffmpeg.org/download.html)
- Required Python packages: speech_recognition, pydub, numpy, tqdm, 
  googletrans==4.0.0-rc1, tkinter
"""

import os
import sys
import subprocess
import threading
import time
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, StringVar
import speech_recognition as sr
from pydub import AudioSegment
import numpy as np
from tqdm import tqdm
from googletrans import Translator

# Language mapping for reference
LANGUAGE_MAP = {
    "English (US)": "en-US",
    "English (UK)": "en-GB",
    "English (India)": "en-IN",
    "Spanish": "es-ES",
    "Spanish (Mexico)": "es-MX",
    "French": "fr-FR",
    "German": "de-DE",
    "Italian": "it-IT",
    "Portuguese": "pt-PT",
    "Russian": "ru-RU",
    "Japanese": "ja-JP",
    "Korean": "ko-KR",
    "Chinese (Mandarin)": "zh-CN",
    "Hindi": "hi-IN",
    "Arabic": "ar-AE",
    "Tamil": "ta-IN",
    "Vietnamese": "vi-VN",
}

class SubtitleMaker:
    def __init__(self):
        self.translator = Translator()
        self.recognizer = sr.Recognizer()
        self.audio_file = None
        self.target_lang = None
        self.segment_length = 10  # Default segment length in seconds
        self.output_dir = None
        self.processing = False
        self.progress = 0
        self.cancel_flag = False
        
    def format_time(self, milliseconds):
        """Convert milliseconds to SRT time format (HH:MM:SS,mmm)"""
        t = timedelta(milliseconds=milliseconds)
        hours, remainder = divmod(t.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds % 1000:03d}"
    
    def check_ffmpeg(self):
        """Check if ffmpeg is installed and in PATH"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def convert_to_wav(self, input_file, output_file="transcript.wav"):
        """Convert input audio file to WAV format using ffmpeg"""
        try:
            subprocess.run(['ffmpeg', '-i', input_file, '-y', output_file], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          check=True)
            return True
        except subprocess.SubprocessError as e:
            print(f"Error converting file: {e}")
            return False
    
    def process_audio(self, input_file, target_lang, segment_length, output_file=None, callback=None):
        """Process audio file and generate subtitles"""
        self.cancel_flag = False
        self.progress = 0
        
        # Check if ffmpeg is installed
        if not self.check_ffmpeg():
            if callback:
                callback("error", "ffmpeg not found. Please install ffmpeg and add it to your PATH.")
            return False
            
        # Set working directory to input file location
        input_dir = os.path.dirname(os.path.abspath(input_file))
        os.chdir(input_dir)
        
        # Determine input and output filenames
        input_filename = os.path.basename(input_file)
        base_filename = os.path.splitext(input_filename)[0]
        
        if output_file is None:
            output_file = f"{base_filename}.srt"
            
        # Convert to WAV if needed
        wav_file = "transcript.wav"
        if os.path.exists(wav_file):
            try:
                os.remove(wav_file)
            except Exception as e:
                if callback:
                    callback("error", f"Could not remove existing transcript.wav: {e}")
                return False
                
        if callback:
            callback("status", "Converting audio file to WAV format...")
                
        if not self.convert_to_wav(input_file, wav_file):
            if callback:
                callback("error", "Failed to convert audio file to WAV format.")
            return False
            
        # Load audio file
        try:
            if callback:
                callback("status", "Loading audio file...")
                
            whole_audio = AudioSegment.from_wav(wav_file)
            whole_len = len(whole_audio)
            total_segments = int(whole_len / (segment_length * 1000))
            
            if callback:
                callback("status", f"Audio length: {whole_len/1000:.2f} seconds")
                callback("status", f"Processing {total_segments} segments...")
                callback("max_progress", total_segments)
        except Exception as e:
            if callback:
                callback("error", f"Error loading audio file: {e}")
            return False
        
        # Remove existing output files
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception as e:
                if callback:
                    callback("error", f"Could not remove existing output file: {e}")
                return False
                
        # Process audio segments
        temp_wav = "temp.wav"
        successful_segments = 0
        
        for seq, start_time, end_time in zip(
            range(1, total_segments + 1),
            np.arange(0, whole_len, segment_length * 1000),
            np.arange(segment_length * 1000, whole_len + segment_length * 1000, segment_length * 1000)
        ):
            if self.cancel_flag:
                if callback:
                    callback("status", "Operation cancelled by user.")
                break
                
            # Update progress
            self.progress = seq
            if callback:
                callback("progress", seq)
                
            # Ensure end time doesn't exceed audio length
            if end_time > whole_len:
                end_time = whole_len
                
            # Extract segment
            try:
                new_audio = whole_audio[start_time:end_time]
                new_audio.export(temp_wav, format="wav")
            except Exception as e:
                if callback:
                    callback("status", f"Error extracting segment {seq}: {e}")
                continue
                
            # Transcribe segment
            try:
                with sr.AudioFile(temp_wav) as source:
                    audio = self.recognizer.record(source)
                    
                    # Format times for SRT
                    start_formatted = self.format_time(start_time)
                    end_formatted = self.format_time(end_time)
                    
                    # Recognize speech
                    if target_lang.startswith('en'):
                        transcription = self.recognizer.recognize_google(audio, language=target_lang)
                        translated_text = transcription
                    else:
                        # First recognize in the original language
                        transcription = self.recognizer.recognize_google(audio, language=target_lang)
                        # Then translate to the target language if needed
                        translated_text = self.translator.translate(transcription, dest=target_lang.split('-')[0]).text
                        
                    # Write to SRT file
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(f"{seq}\n{start_formatted} --> {end_formatted}\n{translated_text}\n\n")
                        
                    successful_segments += 1
                    if callback:
                        callback("status", f"Processed segment {seq}/{total_segments}")
            except sr.UnknownValueError:
                if callback:
                    callback("status", f"No speech detected in segment {seq}")
            except Exception as e:
                if callback:
                    callback("status", f"Error processing segment {seq}: {e}")
        
        # Clean up temporary files
        try:
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
            if os.path.exists(wav_file):
                os.remove(wav_file)
        except Exception as e:
            if callback:
                callback("status", f"Warning: Could not remove temporary files: {e}")
                
        if callback:
            callback("status", f"Complete! Successfully processed {successful_segments} out of {total_segments} segments.")
            callback("complete", output_file)
            
        return True
        
    def cancel_processing(self):
        """Cancel the ongoing processing"""
        self.cancel_flag = True


class SubtitleMakerGUI:
    def __init__(self, root):
        self.root = root
        self.subtitle_maker = SubtitleMaker()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the GUI elements"""
        self.root.title("Subtitle Maker")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Audio File", padding="10")
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.file_path = StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.RIGHT, padx=5)
        
        # Language selection section
        lang_frame = ttk.LabelFrame(main_frame, text="Language Settings", padding="10")
        lang_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(lang_frame, text="Target Language:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.language_var = StringVar()
        self.language_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, width=30)
        self.language_combo['values'] = list(LANGUAGE_MAP.keys())
        self.language_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.language_combo.current(0)  # Default to English (US)
        
        ttk.Label(lang_frame, text="Segment Length (seconds):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.segment_var = StringVar(value="10")
        segment_spin = ttk.Spinbox(lang_frame, from_=1, to=60, textvariable=self.segment_var, width=5)
        segment_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_text = tk.Text(progress_frame, height=10, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add a scrollbar to the text widget
        scrollbar = ttk.Scrollbar(self.status_text, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Buttons section
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Processing", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel_processing, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Exit", command=self.root.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Add status message
        self.add_status("Welcome to Subtitle Maker. Select an audio file and settings, then click 'Start Processing'.")
        
    def browse_file(self):
        """Open file dialog to select audio file"""
        filetypes = (
            ("Audio files", "*.mp3 *.wav *.ogg *.m4a *.flac"),
            ("All files", "*.*")
        )
        
        filename = filedialog.askopenfilename(
            title="Select an audio file",
            filetypes=filetypes
        )
        
        if filename:
            self.file_path.set(filename)
            self.add_status(f"Selected file: {filename}")
    
    def add_status(self, message):
        """Add message to status text widget"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_callback(self, message_type, message):
        """Callback function for processing updates"""
        if message_type == "status":
            self.add_status(message)
        elif message_type == "error":
            self.add_status(f"ERROR: {message}")
            messagebox.showerror("Error", message)
            self.processing_complete()
        elif message_type == "progress":
            self.progress_bar['value'] = message
        elif message_type == "max_progress":
            self.progress_bar['maximum'] = message
        elif message_type == "complete":
            self.add_status(f"Output saved to: {message}")
            messagebox.showinfo("Complete", f"Subtitle generation complete!\nOutput saved to: {message}")
            self.processing_complete()
            
    def start_processing(self):
        """Start processing the audio file"""
        audio_file = self.file_path.get()
        
        if not audio_file:
            messagebox.showerror("Error", "Please select an audio file.")
            return
            
        if not os.path.exists(audio_file):
            messagebox.showerror("Error", "The selected audio file does not exist.")
            return
            
        try:
            segment_length = int(self.segment_var.get())
            if segment_length < 1:
                raise ValueError("Segment length must be at least 1 second")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid segment length: {e}")
            return
            
        # Get the language code
        lang_name = self.language_var.get()
        if lang_name not in LANGUAGE_MAP:
            messagebox.showerror("Error", "Please select a valid language.")
            return
            
        target_lang = LANGUAGE_MAP[lang_name]
        
        # Update UI state
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress_bar['value'] = 0
        
        # Clear status
        self.status_text.delete(1.0, tk.END)
        self.add_status(f"Starting processing with these settings:")
        self.add_status(f"- Audio file: {audio_file}")
        self.add_status(f"- Target language: {lang_name} ({target_lang})")
        self.add_status(f"- Segment length: {segment_length} seconds")
        self.add_status("Processing started...")
        
        # Run processing in a separate thread to keep UI responsive
        self.processing_thread = threading.Thread(
            target=self.subtitle_maker.process_audio,
            args=(audio_file, target_lang, segment_length, None, self.update_callback)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
    def cancel_processing(self):
        """Cancel the ongoing processing"""
        if messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel processing?"):
            self.add_status("Cancelling processing...")
            self.subtitle_maker.cancel_processing()
            self.cancel_button.config(state=tk.DISABLED)
            
    def processing_complete(self):
        """Reset UI after processing is complete"""
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)


def run_cli(args):
    """Run in command-line mode"""
    if len(args) < 4:
        print("Usage: python submaker.py <audio_file> <language_code> <segment_length>")
        print("Example: python submaker.py recording.mp3 en-US 10")
        print("\nAvailable language codes:")
        for name, code in LANGUAGE_MAP.items():
            print(f"  {code} - {name}")
        return
        
    audio_file = args[1]
    lang_code = args[2]
    try:
        segment_length = int(args[3])
    except ValueError:
        print("Error: Segment length must be a number in seconds")
        return
        
    maker = SubtitleMaker()
    
    def cli_callback(message_type, message):
        if message_type == "status" or message_type == "error":
            print(message)
            
    print(f"Processing {audio_file} with language {lang_code} and {segment_length}s segments")
    maker.process_audio(audio_file, lang_code, segment_length, callback=cli_callback)
    

if __name__ == "__main__":
    # Check if running in CLI mode or GUI mode
    if len(sys.argv) > 1:
        # CLI mode
        run_cli(sys.argv)
    else:
        # GUI mode
        try:
            root = tk.Tk()
            app = SubtitleMakerGUI(root)
            root.mainloop()
        except Exception as e:
            print(f"Error starting GUI: {e}")
            print("Falling back to command-line mode...")
            print("Usage: python submaker.py <audio_file> <language_code> <segment_length>")
