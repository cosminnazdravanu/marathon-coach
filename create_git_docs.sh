#!/usr/bin/env bash
set -euo pipefail

# Ensure we run from the repo root (where .git exists)
if [ ! -d ".git" ]; then
  echo "❌ Please run this script from your repo root (where the .git folder is)."
  exit 1
fi

mkdir -p docs

# --- Create docs/GIT_QUICKSTART.md ---
cat > docs/GIT_QUICKSTART.md <<'MD'
# Git for this repo — one-page quickstart

## What & why
- **Git** = snapshots of your project (*commits*).
- **GitHub** = online home for those snapshots + robots (*CI*).
- **push** = upload your latest commit → CI runs.

## First-time setup
```bash
git clone https://github.com/cosminnazdravanu/marathon-coach.git
cd marathon-coach
bash scripts/setup_env.sh        # creates backend/.env & frontend/.env locally
# open those two files and fill secrets (DON'T commit them)
```

## Daily loop
```bash
git status
git add -A
git commit -m "short: what you changed"
git push          # uploads; CI runs on GitHub
git pull          # get latest before new work
```

## Branches / PRs
```bash
git checkout -b feat/my-change
git add -A && git commit -m "feat: my change" && git push -u origin feat/my-change
# open Pull Request on GitHub and merge when green
```

## CI (robots)
- On each push, GitHub Actions:
  - installs deps (`requirements.txt`, `package.json`)
  - creates `backend/.env` & `frontend/.env` from **GitHub Secrets**
- Check runs: GitHub → **Actions**

## Secrets & .env
- Never commit real secrets. `.env` files are git-ignored.
- Real values live in **GitHub → Settings → Secrets and variables → Actions**.
- `.env.example` lists the keys only (no secrets).

## Common fixes
**Blocked push: “secret detected”**
```bash
git rm --cached path/to/leaked.txt
echo "path/to/leaked.txt" >> .gitignore
git add .gitignore && git commit --amend --no-edit && git push
# rotate the leaked key with the provider
```

**CI: “Could not open requirements.txt”**
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "ci: add requirements"
git push
```

**Undo local edits to a file**
```bash
git restore path/to/file
```
MD

# --- Create or update README.md with CI badge + docs link ---
if [ ! -f README.md ]; then
  cat > README.md <<'MD'
# Marathon Coach

![CI](https://github.com/cosminnazdravanu/marathon-coach/actions/workflows/ci.yml/badge.svg)

Mono-repo for a FastAPI backend and Vite/React frontend.

- Env mgmt: `.env.example` template; real secrets in GitHub Secrets.
- Local setup: `bash scripts/setup_env.sh`, then fill `backend/.env` and `frontend/.env`.
- Docs: see [docs/GIT_QUICKSTART.md](docs/GIT_QUICKSTART.md).

## Dev quickstart
```bash
# backend
python -m uvicorn backend.main:app --reload

# frontend
cd frontend && npm run dev
```
MD
else
  # Add badge if missing
  if ! grep -q 'actions/workflows/ci.yml/badge.svg' README.md; then
    printf '\n%s\n\n' '![CI](https://github.com/cosminnazdravanu/marathon-coach/actions/workflows/ci.yml/badge.svg)' >> README.md
  fi
  # Add docs link if missing
  if ! grep -q 'docs/GIT_QUICKSTART.md' README.md; then
    printf '\n%s\n' 'See [docs/GIT_QUICKSTART.md](docs/GIT_QUICKSTART.md) for a one-page Git guide.' >> README.md
  fi
fi

# Stage, commit, push
git add docs/GIT_QUICKSTART.md README.md
if git diff --cached --quiet; then
  echo "ℹ️ Nothing to commit. Files are already up to date."
else
  git commit -m "docs: add Git quickstart + CI badge"
  git push
fi

echo "✅ Done. Check docs/GIT_QUICKSTART.md and README.md."
