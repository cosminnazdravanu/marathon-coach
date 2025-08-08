#!/usr/bin/env bash
set -euo pipefail

# Run from repo root
test -d backend && test -d frontend || { echo "Run from repo root."; exit 1; }

# 0) Create a place to stash local-only stuff
mkdir -p secrets

# 1) Move any existing backend/.env out of the repo (backup locally)
if [ -f backend/.env ]; then
  ts=$(date +"%Y%m%d-%H%M%S")
  mv backend/.env "secrets/backend.env.$ts"
  echo "Backed up previous backend/.env to secrets/backend.env.$ts"
fi

# 2) Root .gitignore (ignore envs, venv, db files, build artifacts, logs)
#    Append only the lines that aren't present yet.
add_ignore() {
  local pat="$1"
  grep -qxF "$pat" .gitignore 2>/dev/null || echo "$pat" >> .gitignore
}
touch .gitignore
add_ignore "# env & secrets"
add_ignore ".env"
add_ignore ".env.*"
add_ignore "*/.env"
add_ignore "secrets/"
add_ignore "# Python venv & build"
add_ignore "venv/"
add_ignore "__pycache__/"
add_ignore "*.pyc"
add_ignore "# Local DB files"
add_ignore "backend/db/RunningCoach.db"
add_ignore "backend/plans.db"
add_ignore "# Frontend build"
add_ignore "frontend/dist/"
add_ignore "frontend/node_modules/"
add_ignore "# Misc"
add_ignore "logs/"

# If backend/.env was in git history/tracked, stop tracking it now
git rm --cached -q backend/.env 2>/dev/null || true

# 3) Generate a fresh SECRET_KEY for local dev
gen_secret() {
  python - <<'PY' 2>/dev/null || openssl rand -hex 32 2>/dev/null || echo "please-set-manually"
import secrets; print(secrets.token_hex(32))
PY
}
SECRET_KEY_VALUE="$(gen_secret)"

# 4) Create a canonical template at root: .env.example (idempotent overwrite OK)
cat > .env.example <<'EOF'
# ===== Backend (copy into backend/.env) =====
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
STRAVA_REDIRECT_URI=http://localhost:8000/strava_callback

# Optional: only if you use OpenAI locally
OPENAI_API_KEY=

# FastAPI session signing key (random 64 hex chars)
SECRET_KEY=

# ===== Frontend (copy into frontend/.env) =====
# Vite exposes only VITE_* to the client
VITE_API_URL=http://127.0.0.1:8000
EOF

# 5) Create backend/.env from template, fill SECRET_KEY automatically
awk 'f;/^# ===== Frontend/{f=0}/^# ===== Backend/{f=1}' .env.example | \
  sed "s/^SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY_VALUE}/" > backend/.env

# 6) Create frontend/.env from template (only frontend section)
awk 'f;/^# ===== Frontend/{f=1}/^# ===== Backend/{f=0}' .env.example > frontend/.env

echo
echo "Created:"
echo "  backend/.env   (with SECRET_KEY prefilled)"
echo "  frontend/.env"
echo
echo "Next steps:"
echo "  - Open backend/.env and set STRAVA_* (client id/secret) + OPENAI_API_KEY (if needed)."
echo "  - Open frontend/.env and keep VITE_API_URL pointing to your backend."
echo
echo "Then commit the cleanup (no secrets):"
echo "  git add .gitignore .env.example backend/.env frontend/.env"
echo "  git commit -m 'env setup: ignore secrets, add templates, split frontend/backend envs'"
