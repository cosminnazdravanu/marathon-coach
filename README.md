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
