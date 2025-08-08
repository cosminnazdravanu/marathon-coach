#!/usr/bin/env bash
set -euo pipefail

echo "==> New Machine Setup for Marathon Coach"

# Ensure we're in repo root (has .git and backend/frontend folders)
if [ ! -d ".git" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
  echo "❌ Please run this script from the repository root (it should contain .git/, backend/, frontend/)."
  exit 1
fi

# --- Check required commands ---
need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Missing required command: $1"
    echo "   Please install it and re-run this script."
    exit 1
  fi
}

echo "==> Checking prerequisites..."
need git
need python
need node
need npm

echo "   git:    $(git --version)"
echo "   python: $(python --version)"
echo "   node:   $(node --version)"
echo "   npm:    $(npm --version)"

# --- Python venv ---
echo "==> Creating Python virtual environment (venv/) if missing..."
if [ ! -d "venv" ]; then
  python -m venv venv
fi

# Activate venv (Windows Git Bash vs POSIX)
ACTIVATED="false"
if [ -f "venv/Scripts/activate" ]; then
  # Windows Git Bash
  # shellcheck disable=SC1091
  source venv/Scripts/activate
  ACTIVATED="true"
elif [ -f "venv/bin/activate" ]; then
  # macOS/Linux
  # shellcheck disable=SC1091
  source venv/bin/activate
  ACTIVATED="true"
fi

if [ "$ACTIVATED" != "true" ]; then
  echo "❌ Could not activate venv. Please activate manually and re-run:"
  echo "   Windows Git Bash: source venv/Scripts/activate"
  echo "   macOS/Linux:      source venv/bin/activate"
  exit 1
fi

echo "==> Upgrading pip and installing Python dependencies..."
python -m pip install -U pip
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
else
  echo "⚠️ requirements.txt not found. Skipping Python package install."
fi

# --- Local .env scaffolding ---
echo "==> Preparing local .env files via scripts/setup_env.sh ..."
if [ -f "scripts/setup_env.sh" ]; then
  chmod +x scripts/setup_env.sh || true
  bash scripts/setup_env.sh
else
  echo "⚠️ scripts/setup_env.sh not found; creating minimal copies from .env.example."
  if [ -f ".env.example" ]; then
    mkdir -p backend frontend
    cp -n .env.example backend/.env || true
    cp -n .env.example frontend/.env || true
  else
    echo "❌ .env.example missing. Please add it to the repo or create backend/.env and frontend/.env manually."
  fi
fi

echo "==> Installing frontend dependencies (npm ci) ..."
pushd frontend >/dev/null
if [ -f "package-lock.json" ]; then
  npm ci
else
  echo "⚠️ package-lock.json not found; using npm install instead."
  npm install
fi
popd >/dev/null

cat <<'DONE'

✅ Setup complete.

Next steps:

1) Fill secrets in these files (do NOT commit them):
   - backend/.env
   - frontend/.env

2) Start backend:
   source venv/Scripts/activate   # Windows Git Bash
   # source venv/bin/activate     # macOS/Linux
   python -m uvicorn backend.main:app --reload

3) Start frontend:
   cd frontend
   npm run dev

Happy hacking!
DONE
