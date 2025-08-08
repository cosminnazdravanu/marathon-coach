# New Machine Setup — Marathon Coach

Use this checklist whenever you switch to a new laptop (Windows/macOS/Linux).

---

## 1) Install prerequisites
- **Git** and **VS Code**
- **Python 3.13** (or the version required by the repo)
- **Node.js 18+** (comes with npm)

**Check versions (Git Bash / Terminal):**
```bash
git --version
python --version
node --version
npm --version
```

---

## 2) Clone the repo
```bash
git clone https://github.com/cosminnazdravanu/marathon-coach.git
cd marathon-coach
```

---

## 3) One-command setup (recommended)
Runs checks, creates venv, installs Python deps, scaffolds local .env files, and installs frontend deps.

```bash
bash scripts/new_machine_setup.sh
```

What it does:
- Verifies `git`, `python`, `node`, `npm` exist and prints versions
- Creates/activates **root venv** (`venv/`)
- `pip install -r requirements.txt`
- Runs `bash scripts/setup_env.sh` to copy `.env.example` → `backend/.env` & `frontend/.env`
- Installs frontend deps with `npm ci`

> Now open **backend/.env** and **frontend/.env** and fill **your local dev secrets** (never commit them):
> - `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REDIRECT_URI`
> - `OPENAI_API_KEY`
> - `SECRET_KEY`, `REDIS_URL` (if used)

---

## 4) Run locally

### Backend (FastAPI)
```bash
# from repo root with venv active
python -m uvicorn backend.main:app --reload
```

### Frontend (Vite/React)
```bash
cd frontend
npm run dev
```

Open the printed URLs in your browser.

---

## 5) Your daily Git loop

```bash
# pull latest before starting work
git pull

# after making changes
git add -A
git commit -m "short: what you changed"
git push
```

---

## Common gotchas & fixes

**`uvicorn` not found**  
Use the module form (works even if the script entrypoint isn’t on PATH):
```bash
python -m uvicorn backend.main:app --reload
```

**`ModuleNotFoundError` for a Python package**  
You’re likely outside the venv. Activate it and reinstall:
```bash
# Windows Git Bash
source venv/Scripts/activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
```

**Vite port already in use (5173)**  
Stop the other process or pick a different port:
```bash
npm run dev -- --port 5174
```

**Merge conflicts on pull**  
Open the files, resolve the `<<<<<<<` markers, then:
```bash
git add -A
git commit
git push
```

---

## Where secrets live
- Local development: **backend/.env** and **frontend/.env** (git-ignored)
- CI/CD: **GitHub Secrets** (Repository → Settings → Secrets and variables → Actions)

---

## Need help?
Ping me here with the terminal output and I’ll walk you through the fix.
