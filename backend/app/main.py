import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .agent import analyze, generate_patch
from .repository import get_context, index_files, repo_path, save_zip
from .sandbox import docker_available, run_tests
from .schemas import AnalyzeRequest, ApplyPatchRequest, PatchRequest, TestRequest
from .services import get_models, new_id
from .tavily_service import is_configured as tavily_configured, search_web

app = FastAPI(
    title="Aether Code",
    description="Repository analysis and coding-agent prototype powered by Nebius Token Factory.",
    version="0.1.0",
)
# Local development origins only. Configure authentication and proper CORS before public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

RUNS_DIR = config.DATA_DIR / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

def save_run(kind: str, result: dict) -> dict:
    run_id = result.get("run_id") or new_id()
    record = {
        "run_id": run_id,
        "kind": kind,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }
    (RUNS_DIR / f"{run_id}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Aether Code",
        "api_key_configured": bool(config.API_KEY),
        "model_configured": bool(config.MODEL_ID),
        "model_id": config.MODEL_ID or None,
        "tavily_configured": tavily_configured(),
        "docker_cli_available": docker_available(),
        "warning": "Local prototype; not hardened for public multi-user deployment.",
    }

@app.get("/api/models")
def models():
    try:
        items = get_models()
        return {
            "ok": True,
            "models": items,
            "nemotron_models": [m for m in items if "nemotron" in m.lower()],
            "configured_model": config.MODEL_ID or None,
            "base_url": config.BASE_URL,
        }
    except Exception as exc:
        raise HTTPException(502, f"Token Factory catalog request failed: {type(exc).__name__}: {exc}")

@app.post("/api/research")
def research_web(payload: dict):
    query = str(payload.get("query", "")).strip()
    topic = str(payload.get("topic", "general")).strip().lower()
    try:
        return search_web(query, max_results=payload.get("max_results", 5), topic=topic)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"Tavily search failed: {type(exc).__name__}: {exc}")

@app.post("/api/repositories")
async def upload_repository(file: UploadFile = File(...)):
    return await save_zip(file)

@app.get("/api/repositories/{repo_id}")
def repository_details(repo_id: str):
    root = repo_path(repo_id)
    files = index_files(root)
    tree = []
    for item in files[:500]:
        tree.append(item)
    return {
        "repo_id": repo_id,
        "file_count": len(files),
        "files": tree,
        "root_label": "Uploaded repository",
    }

@app.post("/api/analyze")
def analyze_repository(req: AnalyzeRequest):
    root = repo_path(req.repo_id)
    try:
        result = analyze(root, req.task, req.focus_files)
        save_run("analysis", result)
        return result
    except Exception as exc:
        raise HTTPException(502, f"Analysis failed: {type(exc).__name__}: {exc}")

@app.post("/api/patch")
def patch_repository(req: PatchRequest):
    root = repo_path(req.repo_id)
    try:
        result = generate_patch(root, req.task, req.finding_ids)
        result["run_id"] = new_id()
        save_run("patch", result)
        return result
    except Exception as exc:
        raise HTTPException(502, f"Patch generation failed: {type(exc).__name__}: {exc}")

@app.post("/api/apply-patch")
def apply_patch(req: ApplyPatchRequest):
    source = repo_path(req.repo_id)
    # Apply only to a new working copy; original upload remains unchanged.
    if not req.patch.startswith(("diff --git ", "--- ")):
        raise HTTPException(400, "Patch must be a unified diff.")
    if "\x00" in req.patch or len(req.patch) > 100000:
        raise HTTPException(400, "Patch is invalid or too large.")
    work_id = new_id()
    work_root = config.DATA_DIR / "workspaces" / work_id
    work_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, work_root, symlinks=False)
    patch_file = config.DATA_DIR / f"{work_id}.patch"
    patch_file.write_text(req.patch, encoding="utf-8")
    try:
        check = subprocess.run(
            ["git", "apply", "--check", "--whitespace=nowarn", str(patch_file)],
            cwd=work_root, capture_output=True, text=True, timeout=10,
        )
        if check.returncode != 0:
            shutil.rmtree(work_root, ignore_errors=True)
            raise HTTPException(400, f"Patch validation failed: {(check.stderr or check.stdout)[-2000:]}")
        applied = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", str(patch_file)],
            cwd=work_root, capture_output=True, text=True, timeout=10,
        )
        if applied.returncode != 0:
            shutil.rmtree(work_root, ignore_errors=True)
            raise HTTPException(400, f"Patch application failed: {(applied.stderr or applied.stdout)[-2000:]}")
        return {
            "workspace_id": work_id,
            "message": "Patch applied to a separate working copy. The uploaded original is unchanged.",
            "files": index_files(work_root)[:500],
        }
    except HTTPException:
        raise
    except (OSError, subprocess.SubprocessError) as exc:
        shutil.rmtree(work_root, ignore_errors=True)
        raise HTTPException(500, f"Patch operation failed: {exc}")
    finally:
        patch_file.unlink(missing_ok=True)

@app.post("/api/test")
def test_repository(req: TestRequest):
    root = repo_path(req.repo_id)
    return run_tests(root, req.command)

@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    if not run_id.isalnum() or len(run_id) != 32:
        raise HTTPException(400, "Invalid run ID.")
    path = RUNS_DIR / f"{run_id}.json"
    if not path.is_file():
        raise HTTPException(404, "Run not found.")
    return json.loads(path.read_text(encoding="utf-8"))

# Serve the built frontend if frontend/dist exists. In development Vite proxies /api to port 8000.
FRONTEND_DIST = config.PROJECT_ROOT / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
