# Aether Code

**Understand. Fix. Test. Improve.**

Aether Code is a repository-focused coding-agent prototype built for the Nebius Global AI Hackathon's Coding and Agentic Engineering track. It uses the OpenAI-compatible Nebius Token Factory API and lets the user inspect a project, request an evidence-based code review, generate a reviewable unified diff, and run existing tests in an isolated Docker container.

> Important: this repository is a functional starter implementation, not a claim that a year of development has already occurred. Validate the exact model and account access with your own Nebius key. No API key is included.

## Current features

- Live Nebius Token Factory model catalog lookup.
- Only uses model IDs returned by the configured Token Factory catalog; model selection is explicit.
- Upload a ZIP source repository with path-traversal and symlink checks.
- File tree and source inspection with size/file-count limits.
- AI code review with findings, evidence, severity, and confidence.
- AI-generated unified diff preview and downloadable `.patch` file.
- Optional patch application to a **working copy** after path and diff checks.
- Existing test suite execution inside Docker with network disabled, resource limits, read-only root filesystem, dropped capabilities, and a timeout.
- Human-readable run events and clear errors.
- API key remains on the backend; it is never sent to the browser.
- Local frontend/backend setup; no database or external account required beyond Token Factory.

## Architecture

```text
React + Vite frontend
        |
        | HTTP (same-origin in production / Vite proxy in development)
        v
FastAPI backend
  ├── Nebius Token Factory client (NVIDIA Nemotron model selection)
  ├── Tavily web research (documentation, bug reports, CVEs/advisories)
  ├── ZIP intake and repository index
  ├── bounded prompt/context builder
  ├── review and patch generation
  ├── patch validation/application
  └── Docker test runner (opt-in)
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- A Nebius Token Factory API key and access to an NVIDIA Nemotron model
- A Tavily API key (optional; enables web research during reviews and patch generation)
- Docker Desktop running if you want to run repository tests in the sandbox

Do not run uploaded/untrusted source code directly on your host. The test endpoint requires Docker and runs tests with the network disabled. Docker is a risk-reduction boundary, not a perfect security guarantee; use a disposable environment for untrusted projects.

## Setup on Windows (PowerShell)

From the project root:

```powershell
Copy-Item .env.example backend/.env
```

Edit `backend/.env` and set `NEBIUS_API_KEY`. Set `TAVILY_API_KEY` to your Tavily key to enable research (keep it private). Initially leave `NEBIUS_MODEL` empty. The model list endpoint will show model IDs visible to your account.

### Backend

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

If PowerShell blocks activation for this terminal, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Open `http://127.0.0.1:8000/api/health` to verify the backend.

### Verify Nebius and choose a model

Open `http://127.0.0.1:8000/api/models` or use the frontend's **Connect model** button. The endpoint performs a real catalog request. Select an NVIDIA Nemotron model returned by your account, then set its exact ID as `NEBIUS_MODEL` in `backend/.env` and restart the backend. Do not assume a model ID from an old README or screenshot is still available.

To test a real inference call:

```powershell
cd backend
python verify_nebius.py
```

The script lists available models, verifies the configured model appears in the catalog, then sends a small coding prompt. A successful catalog call alone does not prove inference works.

### Frontend

Open a second PowerShell terminal at the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (usually `http://localhost:5173`).

## Basic workflow

1. Confirm the API health indicator.
2. Click **Connect model** and confirm the account returns Nemotron models.
3. Set the exact selected model ID in `backend/.env`, restart the backend.
4. Upload a ZIP of a small code repository.
5. Enter a concrete task, e.g. “Review this Python project for correctness issues and missing edge cases.”
6. Review the evidence-backed findings.
7. Ask for a patch. Inspect and download the `.patch` file.
8. Only apply patches to a working copy after reviewing them.
9. If Docker is installed and running, run the repository's existing tests in the sandbox.

## API endpoints

- `GET /api/health` — service and configuration status (never returns secrets)
- `GET /api/models` — live Token Factory model catalog
- `POST /api/research` — Tavily search (`{"query":"...","max_results":5,"topic":"general"}`)
- Tavily research is automatically added as untrusted reference context to code reviews and patch generation when configured; repository evidence remains authoritative.
- `POST /api/repositories` — upload a ZIP archive
- `GET /api/repositories/{repo_id}` — file tree and metadata
- `POST /api/analyze` — AI review of selected repository/task
- `POST /api/patch` — generate a unified diff
- `POST /api/apply-patch` — validate and apply a patch to a separate working copy
- `POST /api/test` — run existing tests in Docker with network disabled
- `GET /api/runs/{run_id}` — retrieve a saved operation result

## Safety and limitations

- Model output is untrusted. Review all suggestions before applying them.
- The first version sends bounded source text to the selected model API. Do not upload secrets, private keys, production credentials, or source you are not allowed to share with the provider.
- `.env`, common secrets, build output, dependency folders, and binary files are excluded from the source context.
- The API is intended for local development. Before public deployment, add user authentication, rate limiting, per-user storage isolation, upload quotas, HTTPS, observability, and a stronger disposable sandbox.
- The patch endpoint does not claim that generated code is correct; run tests and review the diff.
- Docker tests use the repository's existing tests. This version does not automatically install arbitrary project dependencies, because dependency installation can execute untrusted code and require network access.
- A static review can produce false positives and miss defects. Findings include confidence and evidence so a human can verify them.
- No model calls, Tavily searches, tests, or deployment have been performed merely by generating this ZIP. Configure keys and verify each integration locally. You must run the project locally and confirm results.

## Hackathon submission checklist

- [ ] Verify a live Nemotron model ID and successful inference using your own Token Factory key.
- [ ] Run the project locally and capture genuine working evidence.
- [ ] Deploy a demo if required for your chosen track.
- [ ] Record a public YouTube demo of 3 minutes or less.
- [ ] Keep the GitHub repository public and include this MIT license.
- [ ] Describe the exact NVIDIA model, Token Factory use, and any Nebius services actually used.
- [ ] Do not claim unsupported features or benchmark results.

## Suggested 12-month roadmap

This is a proposed future roadmap, not completed work.

1. Month 1 — Stabilize API integration, repository intake, and secure local workflow.
2. Month 2 — Add structured multi-step agent plans and traceable tool-call events.
3. Month 3 — Add Python/JavaScript parsing and language-specific diagnostics.
4. Month 4 — Improve patch validation and test coverage.
5. Month 5 — Add Git branch/worktree isolation and reviewable pull-request diffs.
6. Month 6 — Add test-failure repair loops with strict budgets and stopping criteria.
7. Month 7 — Add retrieval over large repositories and symbol indexing.
8. Month 8 — Add authentication, project ownership, quotas, and audit logs.
9. Month 9 — Add a benchmark suite with reproducible tasks and human-reviewed labels.
10. Month 10 — Evaluate model quality, latency, and cost across eligible models.
11. Month 11 — Improve accessibility, usability, telemetry, and deployment reliability.
12. Month 12 — Security review, documentation, release process, and public evaluation report.

## License

MIT. See `LICENSE`.

## UI design reference

The frontend uses a dark navy/black interface with neon-red accents, matching the approved Aether Code visual direction. The eight-screen visual concept is included at `docs/assets/AETHER_CODE_RED_UI_REFERENCE.png`. The running application is the functional implementation; the reference image is a design guide and illustrative mockup, not a screenshot of live application data.
#   A E T H E R  
 