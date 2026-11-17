# Student Task Manager — DevOps CI/CD Project

**Repository:** `https://github.com/malek-hnaien/devops-demo`

## 1. Architecture
- **GitHub & GitHub Actions**: Source code management (Trunk-Based Development) and automated CI/CD pipeline.
- **Docker & Docker Compose**: Multi-stage containerization (`python:3.12-slim`, non-root `appuser`) + `postgres:16-alpine` with healthchecks.
- **GitHub Container Registry (`ghcr.io`)**: Container registry storing images tagged with `$SHORT_SHA` and `latest`.
- **Python / pyinfra (`deploy.py`)**: Automated, idempotent deployment script.
- **Uptime Kuma**: Real-time HTTP availability monitoring on `/health` (port `3001`) with automated notifications.

## 2. Pipeline Stages (`.github/workflows/ci-cd.yml`)
1. **`test` stage (Continuous Integration)**: Runs on every push and Pull Request (`main` and `feature/**`). Installs dependencies and executes automated unit tests via `pytest -v`. If a test fails, the Pull Request is blocked.
2. **`build-and-push` stage (Continuous Delivery)**: Runs only on merges/pushes to `main` after `test` succeeds. Logs into `ghcr.io` using `${{ secrets.GITHUB_TOKEN }}` (no hardcoded secrets) and pushes the Docker image tagged with both the Git commit SHA and `latest`.

## 3. How to Run & Reproduce
```bash
# 1. Clone the repository
git clone [https://github.com/malek-hnaien/devops-demo.git](https://github.com/malek-hnaien/devops-demo.git)
cd devops-demo

# 2. Start the application and PostgreSQL database
docker-compose up -d --build

# 3. Verify the health check
curl http://localhost:3000/health

# 4. Run automated deployment (pulls latest image from registry and restarts)
python deploy.py

# 5. Start Uptime Kuma monitoring (accessible at http://localhost:3001)
docker run -d --name uptime-kuma --restart unless-stopped -p 3001:3001 -v uptime-kuma-data:/app/data louislam/uptime-kuma:1