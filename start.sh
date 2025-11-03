#!/bin/bash

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Kill processes on ports if they exist
ports=(8002 5173)
for port in "${ports[@]}"; do
    if check_port $port; then
        echo "Port $port is in use. Attempting to free it..."
        pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            kill -9 $pid
            sleep 2
        fi
    fi
done

# Set working directory to script location
cd "$(dirname "$0")"

# Create and activate virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r webapp/backend/requirements.txt

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd webapp/frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

# Start backend in a new terminal
echo "Starting backend server..."
SCRIPT_PATH=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
BACKEND_PATH="$SCRIPT_PATH/webapp/backend"

case "$(uname -s)" in
    Darwin*)  # macOS
        osascript -e "tell application \"Terminal\" to do script \"cd '$BACKEND_PATH' && source ../../.venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8002\""
        ;;
    Linux*)   # Linux
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd '$BACKEND_PATH' && source ../../.venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8002"
        elif command -v xterm &> /dev/null; then
            xterm -e "cd '$BACKEND_PATH' && source ../../.venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8002" &
        else
            echo "No suitable terminal emulator found. Please install gnome-terminal or xterm."
            exit 1
        fi
        ;;
    *)
        echo "Unsupported operating system"
        exit 1
        ;;
esac

# Start frontend in a new terminal
echo "Starting frontend development server..."
case "$(uname -s)" in
    Darwin*)  # macOS
        osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_PATH/webapp/frontend' && npm run dev\""
        ;;
    Linux*)   # Linux
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd '$SCRIPT_PATH/webapp/frontend' && npm run dev"
        elif command -v xterm &> /dev/null; then
            xterm -e "cd '$SCRIPT_PATH/webapp/frontend' && npm run dev" &
        fi
        ;;
esac

echo -e "\nYouTube Downloader is starting up!\n"
echo "Frontend will be available at: http://localhost:5173"
echo "Backend API will be available at: http://localhost:8002"
echo -e "\nClose the server windows when you're done.\n"