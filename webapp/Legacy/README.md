# YouTube Downloader (Legacy)

A simple desktop application for downloading YouTube videos, built with Python and Tkinter.

## Features

- 📺 Download single or multiple YouTube videos
- 🎵 Support for video and audio-only downloads
- 🎨 Clean, modern Tkinter interface
- 📊 Real-time progress tracking
- 📁 Custom download directory selection
- ⚙️ Multiple quality options (4K to 360p)
- 🔊 MP3 extraction for audio downloads
- 🧹 Optional filename cleaning

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Make sure you have Python 3.8+ installed:

   ```bash
   python --version
   ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Double-click `youtube-downloader.py`

OR

2. Run from command line:

   ```bash
   python youtube-downloader.py
   ```

## Usage

1. Paste one or more YouTube URLs (one per line) in the input box
2. Select your preferred quality option:
   - Video qualities: 4K, 1080p, 720p, 480p, 360p
   - Audio options: Best quality or MP3
3. Choose a download folder (defaults to user's Downloads folder)
4. Optional: Enable/disable filename cleaning
5. Click "Start Download" and monitor progress

## Known Issues & Solutions

1. **SSL/TLS Errors**:
   - Update your Python installation
   - Check your system's SSL certificates

2. **Download Errors**:
   - Try a different video quality
   - Check your internet connection
   - Verify the video is available in your region

3. **Unicode Errors**:
   - Enable filename cleaning option
   - Use English characters in save path

## Differences from Web Version

This is the legacy desktop version. For a more modern experience with additional features, try the web-based version in the parent directory which offers:

- Web interface accessibility
- Batch ZIP downloads
- Format selection per video
- API-based architecture
- Docker containerization

## License

This project is licensed under the MIT License.
