# Running the YouTube Downloader

This guide explains how to run the YouTube Downloader application on your system.

## Quick Start Guide

### Prerequisites

Before you begin, make sure you have:

1. Python 3.8 or higher installed
2. Node.js 14 or higher installed
3. npm (comes with Node.js)
4. Git (optional, for cloning the repository)

### One-Click Start (Recommended)

#### Windows Users

1. Double-click `start.bat` in the root directory

OR

Open PowerShell and run:

```powershell
.\start.ps1
```

#### Linux/macOS Users

Open terminal and run:

```bash
chmod +x start.sh
./start.sh
```

That's it! The application will automatically:

- Set up the Python virtual environment
- Install all required dependencies
- Start both the backend and frontend servers
- Open your browser to the application

### Using the Application

1. Access the web interface at [http://localhost:5173](http://localhost:5173)

2. Input YouTube URLs:
   - Single URL: Use the top input field
   - Multiple URLs: Use the text area (one URL per line)

3. Choose your options:
   - Click "Get Info" to see available formats
   - Select a download directory (optional)
   - Choose video quality/format
   - For batch downloads, optionally set a common format ID

4. Download your videos:
   - Single videos: Click the "Download" button next to your chosen format
   - Multiple videos: Use "Download All (ZIP)" to get everything at once

## Manual Setup (Alternative)

If you prefer to start services manually:

### Backend Setup

1. Open a terminal and create a Python virtual environment:

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

2. Install backend requirements:

```bash
cd webapp/backend
pip install -r requirements.txt
```

3. Start the backend server:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8002
```

### Frontend Setup

1. Open a new terminal and install frontend dependencies:

```bash
cd webapp/frontend
npm install
```

2. Start the development server:

```bash
npm run dev
```

## Troubleshooting

### Common Issues & Solutions

1. "Port already in use" error:
   - Close any applications using ports 8002 or 5173
   - OR change the ports in the startup scripts

2. Download errors:
   - Check backend logs in `webapp/backend/logs/backend.log`
   - Try a different video format/quality
   - Ensure you have write permissions in the download directory

3. SSL/TLS errors:
   - The application will automatically try different TLS versions
   - If problems persist, check your system's SSL certificates
   - Try using a different format or resolution

### Getting Help

If you encounter issues:

1. Check the backend logs at `webapp/backend/logs/backend.log`
2. Look for any error messages in the browser console
3. Make sure all prerequisites are installed correctly
4. Try running the services manually to see detailed error messages
