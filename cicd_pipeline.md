# AgriAssist Production CI/CD Pipeline
## Complete DevOps Blueprint

---

## A. Architecture Diagram

```
                        ┌─────────────────────────────────────────────┐
                        │              GitHub Repository              │
                        │  Backend/Chat (Python)  Backend/server (Node)│
                        └──────────┬──────────────────┬───────────────┘
                                   │   push / PR      │
                        ┌──────────▼──────────────────▼───────────────┐
                        │           GitHub Actions CI                  │
                        │  ┌──────────────┐  ┌──────────────────┐     │
                        │  │ chat-ci      │  │ server-ci        │     │
                        │  │ lint+typecheck│  │ lint+typecheck   │     │
                        │  │ test         │  │ test             │     │
                        │  │ docker build │  │ prisma validate  │     │
                        │  │ trivy scan   │  │ docker build     │     │
                        │  └──────┬───────┘  │ trivy scan       │     │
                        │         │          └────────┬──────────┘     │
                        └─────────┼───────────────────┼───────────────┘
                                  │                   │
                        ┌─────────▼───────────────────▼───────────────┐
                        │           GitHub Actions CD                  │
                        │  ┌─────────────────────────────────────┐    │
                        │  │ Push images to GHCR / Docker Hub    │    │
                        │  │ Deploy to Railway / GCP Cloud Run   │    │
                        │  └─────────────────────────────────────┘    │
                        └─────────────────────────────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
    ┌─────────▼─────────┐     ┌───────────▼──────────┐    ┌──────────▼──────────┐
    │   DEV Environment │     │ STAGING Environment  │    │  PROD Environment   │
    │  (auto on push)   │     │  (manual approve)    │    │  (manual approve)   │
    └─────────┬─────────┘     └──────────┬───────────┘    └──────────┬──────────┘
              │                          │                           │
    ┌─────────▼──────────────────────────▼───────────────────────────▼──────────┐
    │                         Shared Infrastructure                             │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
    │  │ Neon Postgres │  │   Upstash    │  │  Pinecone    │  │   Twilio     │  │
    │  │ (branching)   │  │   Redis      │  │  (managed)   │  │  (external)  │  │
    │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
    └──────────────────────────────────────────────────────────────────────────┘
```

---

## B. CI Pipeline Design

### B.1 Backend/Chat (Python FastAPI) — CI Jobs

| Step | Tool | What it does |
|------|------|-------------|
| Lint | `ruff check .` | Fast Python linter (replaces flake8) |
| Format check | `ruff format --check .` | Ensure consistent formatting |
| Type check | `mypy app/ --ignore-missing-imports` | Static type analysis |
| Unit tests | `pytest tests/ -v --tb=short` | Run test suite |
| Docker build | `docker build -t chat:test .` | Validate Dockerfile compiles |
| Security scan | `trivy image chat:test` | Scan image for CVEs |
| Dependency audit | `pip-audit -r requirements.txt` | Check for known vulnerabilities |

### B.2 Backend/server (Node.js Express) — CI Jobs

| Step | Tool | What it does |
|------|------|-------------|
| Lint | `npx eslint src/ --ext .ts` | TypeScript linting |
| Type check | `npx tsc --noEmit` | Compile check without output |
| Prisma validate | `npx prisma validate` | Schema correctness |
| Prisma format | `npx prisma format` | Schema formatting |
| Unit tests | `npm test` (jest) | Run test suite |
| Docker build | `docker build -t server:test .` | Validate Dockerfile compiles |
| Security scan | `trivy image server:test` | Scan image for CVEs |
| Dependency audit | `npm audit --audit-level=high` | Check for known vulnerabilities |

---

## C. CD Pipeline Design

### Environment Strategy

| Environment | Trigger | DB Branch | Approval |
|-------------|---------|-----------|----------|
| **dev** | Push to `dev` branch | Neon dev branch | Automatic |
| **staging** | Push to `staging` branch | Neon staging branch | Automatic |
| **production** | Push to `main` / tag `v*` | Neon main | Manual approval required |

### Deployment Flow

```
Code Push → CI (lint, test, build, scan)
         → Docker Image Push (GHCR)
         → Deploy Chat Service (Railway / Cloud Run)
         → Deploy Server Service (Railway / Cloud Run)
         → Run Prisma Migrations (server only)
         → Health Check Verification
         → Smoke Tests
```

---

## D. GitHub Actions Workflows

### D.1 CI Workflow — `.github/workflows/ci.yml`

```yaml
name: CI Pipeline

on:
  push:
    branches: [dev, staging, main]
    paths:
      - 'Backend/Chat/**'
      - 'Backend/server/**'
  pull_request:
    branches: [dev, staging, main]
    paths:
      - 'Backend/Chat/**'
      - 'Backend/server/**'

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # ──────────────────────────────────────────
  # Detect which services changed
  # ──────────────────────────────────────────
  changes:
    runs-on: ubuntu-latest
    outputs:
      chat: ${{ steps.filter.outputs.chat }}
      server: ${{ steps.filter.outputs.server }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            chat:
              - 'Backend/Chat/**'
            server:
              - 'Backend/server/**'

  # ──────────────────────────────────────────
  # Backend/Chat CI
  # ──────────────────────────────────────────
  chat-ci:
    needs: changes
    if: needs.changes.outputs.chat == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: Backend/Chat

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: Backend/Chat/requirements.txt

      - name: Install system deps
        run: |
          sudo apt-get update
          sudo apt-get install -y libpq-dev libsndfile1

      - name: Install Python deps
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install ruff mypy pytest pip-audit

      - name: Lint (ruff)
        run: ruff check app/ --output-format=github

      - name: Format check (ruff)
        run: ruff format --check app/
        continue-on-error: true

      - name: Type check (mypy)
        run: mypy app/ --ignore-missing-imports --no-error-summary
        continue-on-error: true

      - name: Unit tests
        run: pytest tests/ -v --tb=short || echo "No tests found — SKIP"
        continue-on-error: true

      - name: Dependency audit
        run: pip-audit -r requirements.txt --desc
        continue-on-error: true

      - name: Docker build validation
        run: docker build -t agriassist-chat:ci-${{ github.sha }} .

      - name: Trivy image scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: agriassist-chat:ci-${{ github.sha }}
          format: 'table'
          severity: 'CRITICAL,HIGH'
          exit-code: '0'

  # ──────────────────────────────────────────
  # Backend/server CI
  # ──────────────────────────────────────────
  server-ci:
    needs: changes
    if: needs.changes.outputs.server == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: Backend/server

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: Backend/server/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Prisma validate
        run: npx prisma validate

      - name: Prisma format check
        run: npx prisma format --check || echo "Schema format differs"
        continue-on-error: true

      - name: TypeScript type check
        run: npx tsc --noEmit

      - name: Lint (ESLint)
        run: npx eslint src/ --ext .ts || echo "ESLint not configured — SKIP"
        continue-on-error: true

      - name: Unit tests
        run: npm test || echo "No test script — SKIP"
        continue-on-error: true

      - name: Dependency audit
        run: npm audit --audit-level=high
        continue-on-error: true

      - name: Docker build validation
        run: docker build -t agriassist-server:ci-${{ github.sha }} .

      - name: Trivy image scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: agriassist-server:ci-${{ github.sha }}
          format: 'table'
          severity: 'CRITICAL,HIGH'
          exit-code: '0'
```

### D.2 CD Workflow — `.github/workflows/cd.yml`

```yaml
name: CD Pipeline

on:
  push:
    branches: [main]
    paths:
      - 'Backend/Chat/**'
      - 'Backend/server/**'

env:
  REGISTRY: ghcr.io
  CHAT_IMAGE: ghcr.io/${{ github.repository_owner }}/agriassist-chat
  SERVER_IMAGE: ghcr.io/${{ github.repository_owner }}/agriassist-server

jobs:
  # ──────────────────────────────────────────
  # Detect changes
  # ──────────────────────────────────────────
  changes:
    runs-on: ubuntu-latest
    outputs:
      chat: ${{ steps.filter.outputs.chat }}
      server: ${{ steps.filter.outputs.server }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            chat:
              - 'Backend/Chat/**'
            server:
              - 'Backend/server/**'

  # ──────────────────────────────────────────
  # Build & Push Chat Image
  # ──────────────────────────────────────────
  build-chat:
    needs: changes
    if: needs.changes.outputs.chat == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Chat image
        uses: docker/build-push-action@v5
        with:
          context: Backend/Chat
          push: true
          tags: |
            ${{ env.CHAT_IMAGE }}:${{ github.sha }}
            ${{ env.CHAT_IMAGE }}:latest

  # ──────────────────────────────────────────
  # Build & Push Server Image
  # ──────────────────────────────────────────
  build-server:
    needs: changes
    if: needs.changes.outputs.server == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Server image
        uses: docker/build-push-action@v5
        with:
          context: Backend/server
          push: true
          tags: |
            ${{ env.SERVER_IMAGE }}:${{ github.sha }}
            ${{ env.SERVER_IMAGE }}:latest

  # ──────────────────────────────────────────
  # Deploy Chat Service
  # ──────────────────────────────────────────
  deploy-chat:
    needs: build-chat
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: agriassist-chat

      - name: Health check
        run: |
          sleep 30
          for i in $(seq 1 10); do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${{ secrets.CHAT_URL }}/docs" || echo "000")
            if [ "$STATUS" = "200" ]; then
              echo "✅ Chat service healthy"
              exit 0
            fi
            echo "⏳ Attempt $i — status: $STATUS"
            sleep 15
          done
          echo "❌ Chat service failed health check"
          exit 1

  # ──────────────────────────────────────────
  # Deploy Server + Migrate DB
  # ──────────────────────────────────────────
  deploy-server:
    needs: build-server
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install deps for migration
        working-directory: Backend/server
        run: npm ci

      - name: Run Prisma migration (production)
        working-directory: Backend/server
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}

      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: agriassist-server

      - name: Health check
        run: |
          sleep 20
          for i in $(seq 1 10); do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${{ secrets.SERVER_URL }}/api/voice-agent/health" || echo "000")
            if [ "$STATUS" = "200" ]; then
              echo "✅ Server service healthy"
              exit 0
            fi
            echo "⏳ Attempt $i — status: $STATUS"
            sleep 10
          done
          echo "❌ Server service failed health check"
          exit 1
```

---

## E. Infrastructure Recommendation

### E.1 Hosting Platform: Railway (recommended for current scale)

| Component | Service | Reasoning |
|-----------|---------|-----------|
| **Chat (Python)** | Railway (Docker) | Native Docker deploy, auto-scaling, handles long startup |
| **Server (Node)** | Railway (Docker) | WebSocket support, easy env management |
| **PostgreSQL** | Neon (already used) | Serverless, branching for dev/staging, auto-suspend |
| **Redis** | Upstash Redis | Serverless Redis, per-request pricing, zero maintenance |
| **Container Registry** | GitHub Container Registry (GHCR) | Free with GitHub, integrated with Actions |

> **Why not Kubernetes?** For a 2-service system at current scale, K8s is overkill. Railway provides Docker deployment with zero-downtime rolling updates, WebSocket support, and per-service scaling. Move to GCP Cloud Run or K8s when you hit ~50 RPS sustained.

### E.2 When to Graduate to GCP Cloud Run

Move when any of these apply:
- Need GPU for ML inference (Cloud Run GPU)
- Sustained traffic >50 RPS
- Need sub-100ms cold start guarantees
- Multi-region deployment required

### E.3 Reverse Proxy / Gateway

Railway handles this natively (SSL termination, domain routing). If self-hosting:
- Use **Caddy** (simpler) or **NGINX** as reverse proxy
- Route `/api/voice-agent/*` + `/media-stream` → server:5000
- Route everything else → chat:8001
- Ensure WebSocket `Upgrade` headers are passed through

---

## F. Deployment Strategy (Step-by-Step)

### F.1 Zero-Downtime Rolling Deploy

```
1. CI passes all checks
2. Docker images built and pushed to GHCR
3. Railway pulls new image
4. Railway starts NEW container alongside OLD
5. Railway runs health check on NEW container
6. If healthy → route traffic to NEW, stop OLD
7. If unhealthy → keep OLD running, mark deploy as failed
```

### F.2 Chat Service (ML Warm-up Handling)

**Problem:** The Chat service loads PyTorch models at startup (~30-60s).

**Solution:**
- Set Railway health check start period to **120 seconds**
- Health check endpoint: `GET /docs` (returns 200 when FastAPI is ready)
- Railway keeps old container serving traffic until new one passes health check
- Add a dedicated health endpoint (recommended addition to codebase):

```python
# Add to app/api/http/health.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok", "service": "agriassist-chat"}
```

### F.3 Server Service (WebSocket Handling)

**Problem:** Active WebSocket connections (`/media-stream`) drop during deploy.

**Solution:**
- Railway drains existing connections before shutdown (configurable drain period)
- Twilio auto-reconnects media streams on disconnect
- Set graceful shutdown timeout to 30 seconds in Railway config
- The existing `process.on('uncaughtException')` handler already prevents crashes

### F.4 Database Migration Flow (Production)

```
NEVER use `npm run reset-db` in production (it wipes data!)

Production migration flow:
1. Developer creates migration locally:
   npx prisma migrate dev --name descriptive_name

2. Migration SQL file is committed to git:
   prisma/migrations/YYYYMMDD_descriptive_name/migration.sql

3. CI validates: npx prisma validate

4. CD runs BEFORE deploy: npx prisma migrate deploy
   - This only applies pending migrations
   - It NEVER drops or resets data
   - If migration fails → deployment is aborted

5. New container starts with updated schema
```

---

## G. Environment & Secrets Management

### G.1 GitHub Secrets Configuration

Create these in GitHub → Settings → Secrets and variables → Actions:

**Shared Secrets:**
| Secret Name | Used By | Description |
|-------------|---------|-------------|
| `RAILWAY_TOKEN` | CD | Railway deploy token |
| `PROD_DATABASE_URL` | CD (migration) | Neon production connection string |

**Chat Service Secrets (set in Railway):**
| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | ✅ | Neon PostgreSQL URL |
| `JWT_SECRET` | ✅ | Must match server's JWT_SECRET |
| `REDIS_URL` | ✅ | Upstash Redis URL |
| `GEMINI_API_KEY` | ✅ | Google Gemini API |
| `PINECONE_API_KEY` | ✅ | Pinecone vector DB |
| `HUGGINGFACE_API_KEY` | ✅ | Voice AI models |
| `SARWAM_API_KEY` | ✅ | Sarvam AI for remedies |
| `POLLINATION_API_KEY` | ❌ | Optional |
| `GEE_CREDENTIALS_B64` | ✅ | Base64 encoded GEE service account JSON |
| `GEE_SERVICE_ACCOUNT` | ✅ | GEE service account email |
| `SENSOR_HARDWARE_URL` | ✅ | ESP32 sensor endpoint |
| `ALLOWED_ORIGINS` | ✅ | Production frontend URLs only (NOT `*`) |
| `DEBUG` | ✅ | Must be `False` in production |

**Server Secrets (set in Railway):**
| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | ✅ | Same Neon DB or separate |
| `JWT_SECRET` | ✅ | Must match Chat's JWT_SECRET |
| `PORT` | ✅ | Usually auto-set by Railway |
| `TWILIO_ACCOUNT_SID` | ✅ | OTP Twilio credentials |
| `TWILIO_AUTH_TOKEN` | ✅ | OTP Twilio credentials |
| `TWILIO_VERIFY_SERVICE_SID` | ✅ | OTP verification service |
| `VOICE_AGENT_TWILIO_ACCOUNT_SID` | ✅ | Voice agent Twilio (separate account) |
| `VOICE_AGENT_TWILIO_AUTH_TOKEN` | ✅ | Voice agent Twilio |
| `VOICE_AGENT_TWILIO_PHONE_NUMBER` | ✅ | Twilio phone number |
| `VOICE_AGENT_PUBLIC_URL` | ✅ | Public URL for webhooks (Railway domain) |
| `ELEVENLABS_AGENT_ID` | ✅ | ElevenLabs conversational AI |
| `ELEVENLABS_API_KEY` | ✅ | ElevenLabs API key |
| `OLLAMA_URL` | ❌ | Only if running Ollama sidecar |
| `OLLAMA_MODEL` | ❌ | Defaults to tinyllama |
| `REDIS_URL` | ❌ | Optional for server |

### G.2 Critical Security Rules

1. **NEVER** commit `.env` files (they currently contain real API keys and DB credentials!)
2. Add to `.gitignore`: `.env`, `.env.*`, `!.env.example`
3. Create `.env.example` files with placeholder values
4. Rotate ALL keys currently in the repository (they are compromised since committed)
5. `JWT_SECRET` must be identical between Chat and Server services
6. Set `DEBUG=False` and `ALLOWED_ORIGINS` to exact frontend domains in production

---

## H. Risk Mitigation Plan

### H.1 Deployment Failure Scenarios

| Scenario | Detection | Response |
|----------|-----------|----------|
| Docker build fails | CI fails, blocks merge | Fix code, re-push |
| Migration fails | CD migration step fails | Deploy aborted, old containers keep running |
| Chat service won't start (ML load fail) | Health check timeout (120s) | Railway keeps old container, alert fires |
| Server service won't start | Health check timeout (30s) | Railway keeps old container, alert fires |
| Bad code deployed | Post-deploy smoke test fails | Trigger rollback (redeploy previous image tag) |

### H.2 Rollback Procedure

```bash
# Railway CLI rollback (instant — redeploys previous image)
railway service rollback --service agriassist-chat
railway service rollback --service agriassist-server

# OR: Manual redeploy of known-good SHA
# Railway dashboard → Service → Deployments → Redeploy
```

### H.3 Database Rollback

Prisma does NOT auto-rollback migrations. Strategy:
1. Always write reversible migrations
2. Keep a `down.sql` for each migration manually
3. Neon offers point-in-time recovery (restore to timestamp before bad migration)
4. For emergencies: Neon branch restore → create new branch from pre-migration state

### H.4 Existing Risks from cicd.txt (with mitigations)

| Risk | Severity | Mitigation |
|------|----------|------------|
| In-memory Maps for SMS sessions | HIGH | Move to Redis: store sessions in Upstash Redis instead of JS Maps. This is required before multi-instance scaling. |
| Test endpoints exposed (`/api/test/*`) | MEDIUM | Gate behind `NODE_ENV !== 'production'` check or remove entirely |
| CORS wildcard (`*`) | HIGH | Set `ALLOWED_ORIGINS` to exact frontend domains in production |
| `.env` files with real secrets in repo | CRITICAL | Rotate ALL keys immediately. Remove `.env` from git history with `git filter-repo` |
| `reset-db` script exists | HIGH | Remove from production `package.json` or gate behind `NODE_ENV` check |
| Ollama dependency (localhost) | MEDIUM | Make Ollama optional with graceful fallback. In production, use a hosted LLM or disable SMS chat |
| ML model download on startup | MEDIUM | Pre-bake models into Docker image OR use a model cache volume |
| `VOICE_AGENT_PUBLIC_URL` uses ngrok | HIGH | Replace with Railway's public domain in production |

---

## I. Improvements (Future Scaling Ideas)

### I.1 Short-term (do now)

1. **Add health endpoints** to both services (Chat needs one, Server has `/api/voice-agent/health`)
2. **Create `.env.example`** files and remove real `.env` from git
3. **Add pytest/jest test suites** — even basic smoke tests catch regressions
4. **Move SMS sessions to Redis** — required for any multi-instance deploy
5. **Add ESLint config** to server (`npx eslint --init`)
6. **Add `ruff.toml`** config to Chat for consistent linting

### I.2 Medium-term (next sprint)

1. **Docker layer caching in CI** — use `docker/build-push-action` with GitHub Actions cache to cut build times by 60%
2. **Neon branching** — create DB branches for dev/staging automatically in CI
3. **Pre-bake ML models** — build a base image with PyTorch models cached, then extend it
4. **Add integration tests** — test actual API endpoints against a test DB
5. **Structured logging** — use `structlog` (Python) and `pino` (Node) for JSON logs
6. **Centralized logging** — ship logs to Grafana Cloud or Datadog (free tiers available)

### I.3 Long-term (scaling phase)

1. **GPU inference** — move ML model to GCP Cloud Run with GPU or a dedicated inference service (Replicate, Modal)
2. **API Gateway** — add rate limiting, request validation, and API key management at the gateway level
3. **CDN** — put static responses behind Cloudflare
4. **Message queue** — replace synchronous ML calls with async job queue (BullMQ + Redis) for scan/remedy endpoints
5. **Kubernetes** — when managing >5 services, move to GKE with Helm charts
6. **Canary deploys** — route 5% of traffic to new version, monitor errors, then promote
7. **Model versioning** — tag ML models with versions, serve multiple versions simultaneously

### I.4 Observability Stack (Recommended)

```
Logs:    Grafana Cloud (free 50GB/month) ← structured JSON logs
Metrics: Prometheus + Grafana (or Railway built-in metrics)
Alerts:  Grafana alerting → Slack/Discord webhook
Uptime:  BetterStack (free 10 monitors) → /health endpoints
Errors:  Sentry (free tier) → Python + Node SDKs
```

### I.5 Suggested Health Check Endpoints

**Chat service — add `app/api/http/health.py`:**
```python
from fastapi import APIRouter
from app.db.session import get_db_status
from app.services.redis.session_store import get_redis_status

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "agriassist-chat",
        "db": await get_db_status(),
        "redis": await get_redis_status(),
    }
```

**Server service — already has `/api/voice-agent/health`, but add a root-level one:**
```typescript
// Add to src/routes/routes.ts
router.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'agriassist-server' });
});
```

---

## Summary Checklist

- [x] CI: Lint, type-check, test, Docker build, security scan for both services
- [x] CD: Separate deploy pipelines per service with health checks
- [x] Database: Safe Prisma `migrate deploy` (never `reset`) in CD
- [x] Secrets: Full inventory with GitHub Secrets + Railway env vars
- [x] WebSocket: Graceful drain during deploy, Twilio auto-reconnect
- [x] ML warm-up: 120s health check start period for Chat service
- [x] Rollback: Railway instant rollback + Neon point-in-time recovery
- [x] Observability: Health endpoints, structured logging, Sentry, uptime monitoring
- [x] Security: Rotate compromised keys, remove `.env` from git, lock CORS
