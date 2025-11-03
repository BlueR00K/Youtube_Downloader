# YouTube Downloader

A modern web application for downloading videos from YouTube with real-time progress tracking and batch download capabilities.

## Features

- ✨ Modern web interface with real-time progress updates
- 📦 Single and batch download support
- 🎯 Format/quality selection for each video
- 📂 Custom download directory selection
- 📊 Live progress tracking with progress bar
- 🔄 Batch download with ZIP archive output
- 🛡️ Robust error handling and download retries
- 🌐 TLS 1.2/1.1 support with fallback options

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm (usually comes with Node.js)

## Quick Start

### Windows Users

1. Double-click `start.bat`

OR

Run in PowerShell:

```powershell
.\start.ps1
```

### Linux/macOS Users

```bash
chmod +x start.sh
./start.sh
```

The startup script will:

1. Set up a Python virtual environment
2. Install all required dependencies
3. Start both backend and frontend servers
4. Open browser windows with the application

## Manual Setup

If you prefer to set up manually or if the startup script doesn't work:

### Backend Setup

1. Create and activate virtual environment:

   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install backend dependencies:

   ```bash
   cd webapp/backend
   pip install -r requirements.txt
   ```

3. Start the backend server:

   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8002
   ```

### Frontend Setup

1. Install frontend dependencies:

   ```bash
   cd webapp/frontend
   npm install
   ```

2. Start the development server:

   ```bash
   npm run dev
   ```

## Usage

1. Open your web browser and navigate to:
   - Frontend: <http://localhost:5173>
   - Backend API (if needed): <http://localhost:8002>

2. Enter a YouTube URL in either:
   - Single URL field for individual downloads
   - Multiple URLs field (one per line) for batch downloads

3. Click "Get Info" to fetch available formats

4. Optional: Select a download directory
   - Enter a path in the "Download directory" field
   - Leave empty to use browser's default download location

5. Choose your download options:
   - For single videos: Click the "Download" button next to your preferred format
   - For batch downloads:
     - Optionally enter a format ID in the batch format field
     - Click "Download All (ZIP)" to get everything in one archive

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   - The startup script will attempt to free ports 8002 and 5173
   - Manually close any applications using these ports if needed

2. **SSL/TLS Issues**
   - The application includes multiple fallback mechanisms for SSL issues
   - Tries TLS 1.2, then 1.1, then system downloaders (aria2c/curl)

3. **Download Errors**
   - Check the backend logs at `webapp/backend/logs/backend.log`
   - Ensure you have write permissions in the download directory
   - Try a different format or resolution

### Manual Port Changes

If you need to use different ports:

- Backend: Change the port in the startup script or manual uvicorn command
- Frontend: Update the VITE_BACKEND_URL in environment variables or `App.jsx`

## Project Structure

```
Youtube_Downloader/
├── webapp/                # Main application directory
│   ├── backend/          # FastAPI backend
│   │   ├── app/         # Application code
│   │   ├── tests/      # Backend tests
│   │   └── requirements.txt
│   ├── frontend/         # React frontend
│   │   ├── src/        # Source code
│   │   └── package.json
│   └── Legacy/          # Legacy scripts (if any)
├── start.bat            # Windows startup script
├── start.ps1           # PowerShell startup script
└── start.sh            # Linux/macOS startup script
```

## Development

- Backend code is in `webapp/backend/app/`
- Frontend code is in `webapp/frontend/src/`
- Main API endpoints are documented at <http://localhost:8002/docs>

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Legacy Scripts

The old scripts have been preserved in the `webapp/Legacy/` directory for reference.
