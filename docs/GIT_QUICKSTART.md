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
