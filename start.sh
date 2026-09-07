#!/usr/bin/env bash
# ==============================================================================
#  BHUMI-AI: 1-Click Universal Startup Script (macOS / Linux)
#  SIH26016 — Ministry of Rural Development
# ==============================================================================

set -e

# ANSI Color Codes
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo -e "${CYAN}${BOLD}"
echo "=============================================================================="
echo "           BHUMI-AI: National Land Acquisition & Management System           "
echo "                     1-Click Rapid Local Launcher                             "
echo "=============================================================================="
echo -e "${NC}"

# 1. Check Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}✗ Error: Python 3 is not installed or not in PATH.${NC}"
    echo "Please install Python 3.10+ from https://www.python.org"
    exit 1
fi
echo -e "${GREEN}✓ Found Python:${NC} $($PYTHON_CMD --version)"

# 2. Check Node & NPM
if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
    echo -e "${RED}✗ Error: Node.js and npm are required to run the frontend.${NC}"
    echo "Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi
echo -e "${GREEN}✓ Found Node.js:${NC} $(node -v) / NPM: $(npm -v)"

# 3. Setup Backend .env
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${YELLOW}⚙ Creating backend/.env from .env.example...${NC}"
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

# 4. Setup Python Virtual Environment
echo -e "\n${CYAN}--- [1/2] Setting up Backend Services ---${NC}"
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo -e "${YELLOW}⚙ Creating Python virtual environment in backend/venv...${NC}"
    $PYTHON_CMD -m venv "$BACKEND_DIR/venv"
fi

# Activate venv
source "$BACKEND_DIR/venv/bin/activate"

# Check dependencies
if ! python -c "import fastapi, sqlalchemy, uvicorn" &>/dev/null; then
    echo -e "${YELLOW}⚙ Installing backend dependencies (this may take a minute on first run)...${NC}"
    pip install --upgrade pip
    pip install -r "$BACKEND_DIR/requirements.txt"
else
    echo -e "${GREEN}✓ Backend dependencies verified.${NC}"
fi

# 5. Setup Frontend Dependencies
echo -e "\n${CYAN}--- [2/2] Setting up Frontend Web App ---${NC}"
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}⚙ Installing frontend node modules (npm install)...${NC}"
    cd "$FRONTEND_DIR" && npm install
else
    echo -e "${GREEN}✓ Frontend packages verified.${NC}"
fi

# Cleanup on exit (Ctrl+C)
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down BHUMI-AI services gracefully...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    echo -e "${GREEN}✓ Shutdown complete. Goodbye!${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 6. Start Backend
echo -e "\n${CYAN}🚀 Launching FastAPI Backend on http://127.0.0.1:8000 ...${NC}"
cd "$BACKEND_DIR"
./venv/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo -e "${YELLOW}⏳ Waiting for backend to start...${NC}"
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/docs >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is live at http://127.0.0.1:8000${NC}"
        break
    fi
    sleep 1
done

# 7. Start Frontend
echo -e "\n${CYAN}🚀 Launching React/Vite Frontend on http://localhost:5173 ...${NC}"
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to be ready
for i in {1..15}; do
    if curl -s http://localhost:5173 >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Open Browser automatically
echo -e "\n${GREEN}${BOLD}==============================================================================${NC}"
echo -e "${GREEN}${BOLD}  BHUMI-AI is RUNNING! Opening browser at http://localhost:5173 ...           ${NC}"
echo -e "${GREEN}${BOLD}==============================================================================${NC}"
echo -e "${CYAN}  • Web Dashboard:${NC}   http://localhost:5173"
echo -e "${CYAN}  • API Docs (Swagger):${NC} http://127.0.0.1:8000/docs"
echo -e "${CYAN}  • Demo Logins:${NC}        admin@mord.gov.in (Pass: admin123)"
echo -e "${YELLOW}Press [Ctrl + C] anytime to stop all servers.${NC}\n"

if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:5173 2>/dev/null || true
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:5173 2>/dev/null || true
fi

wait
