# Subtitle Maker - Installation Requirements

## System Requirements
- Python 3.6 or newer
- ffmpeg installed and in PATH (https://ffmpeg.org/download.html)

## Python Dependencies
Install the required packages using pip:

```
pip install SpeechRecognition
pip install pydub
pip install numpy
pip install tqdm
pip install googletrans==4.0.0-rc1
```

Note: The googletrans library might be unstable in newer versions, so we specify version 4.0.0-rc1.

## Verifying ffmpeg Installation
To verify that ffmpeg is correctly installed and in your PATH:

- On Windows: Open Command Prompt and type `ffmpeg -version`
- On macOS/Linux: Open Terminal and type `ffmpeg -version`

If properly installed, you should see version information rather than an error.

## Running the Application
- To run with GUI: `python submaker.py`
- To run from command line: `python submaker.py <audio_file> <language_code> <segment_length>`

Example command line usage:
```
python submaker.py recording.mp3 en-US 10
```
