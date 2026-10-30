import io
import os
import re
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

from fastapi import HTTPException, UploadFile
from . import config
from .services import new_id

def _is_safe_member(name: str) -> bool:
    if not name or "\x00" in name or "\\" in name:
        return False
    p = PurePosixPath(name)
    if p.is_absolute() or any(part in ("..", "") for part in p.parts):
        return False
    if p.parts and ":" in p.parts[0]:
        return False
    return True

def _is_ignored(path: Path) -> bool:
    if any(part in config.IGNORED_DIRS for part in path.parts):
        return True
    if path.name.lower() in {n.lower() for n in config.IGNORED_NAMES}:
        return True
    return False

def _safe_text_file(path: Path) -> bool:
    if _is_ignored(path) or path.suffix.lower() not in config.ALLOWED_TEXT_SUFFIXES:
        return False
    try:
        if path.stat().st_size > config.MAX_FILE_BYTES:
            return False
        data = path.read_bytes()
        if b"\x00" in data:
            return False
        data.decode("utf-8")
        return True
    except (OSError, UnicodeDecodeError):
        return False

def repo_path(repo_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{32}", repo_id):
        raise HTTPException(400, "Invalid repository ID.")
    path = (config.DATA_DIR / "repositories" / repo_id).resolve()
    base = (config.DATA_DIR / "repositories").resolve()
    if base not in path.parents or not path.is_dir():
        raise HTTPException(404, "Repository not found. Upload it again.")
    return path

async def save_zip(upload: UploadFile) -> dict:
    filename = (upload.filename or "").lower()
    if not filename.endswith(".zip"):
        raise HTTPException(400, "Upload a .zip archive.")
    raw = await upload.read(config.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(raw) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"ZIP exceeds {config.MAX_UPLOAD_MB} MB.")
    repo_id = new_id()
    base = config.DATA_DIR / "repositories"
    base.mkdir(parents=True, exist_ok=True)
    dest = base / repo_id
    dest.mkdir(parents=True, exist_ok=False)
    count = 0
    total_uncompressed = 0
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            infos = zf.infolist()
            if len(infos) > config.MAX_FILES * 3:
                raise HTTPException(413, "Archive contains too many entries.")
            for info in infos:
                if info.is_dir():
                    continue
                if not _is_safe_member(info.filename):
                    raise HTTPException(400, f"Unsafe archive path: {info.filename[:100]}")
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise HTTPException(400, "Symbolic links are not allowed in uploaded archives.")
                count += 1
                total_uncompressed += info.file_size
                if count > config.MAX_FILES:
                    raise HTTPException(413, f"Archive exceeds {config.MAX_FILES} files.")
                if info.file_size > config.MAX_FILE_BYTES * 5:
                    raise HTTPException(413, f"Archive member too large: {info.filename[:100]}")
                if total_uncompressed > 100 * 1024 * 1024:
                    raise HTTPException(413, "Uncompressed archive exceeds 100 MB.")
                target = (dest / Path(*PurePosixPath(info.filename).parts)).resolve()
                if dest.resolve() not in target.parents:
                    raise HTTPException(400, "Archive path escaped repository root.")
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, target.open("wb") as out:
                    shutil.copyfileobj(src, out, length=1024 * 1024)
        files = index_files(dest)
        if not files:
            raise HTTPException(400, "No supported text source files found in ZIP.")
        return {"repo_id": repo_id, "file_count": len(files), "files": files[:250]}
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        raise

def index_files(root: Path) -> list[dict]:
    results = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or _is_ignored(path):
            continue
        rel = path.relative_to(root).as_posix()
        if not _safe_text_file(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        results.append({
            "path": rel,
            "size": path.stat().st_size,
            "lines": text.count("\n") + (1 if text else 0),
            "language": path.suffix.lower().lstrip(".") or "text",
        })
        if len(results) >= config.MAX_FILES:
            break
    return results

def get_context(root: Path, focus_files: list[str] | None = None) -> tuple[str, list[str]]:
    index = index_files(root)
    chosen = set(focus_files or [])
    selected = [item for item in index if not chosen or item["path"] in chosen]
    if not selected:
        selected = index
    chunks = []
    used = 0
    included = []
    for item in selected:
        path = root / item["path"]
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        remaining = config.MAX_CONTEXT_CHARS - used
        if remaining <= 0:
            break
        content = content[:min(config.MAX_FILE_BYTES, remaining)]
        chunk = f"\n--- FILE: {item['path']} ---\n{content}\n"
        if used + len(chunk) > config.MAX_CONTEXT_CHARS:
            chunk = chunk[:remaining]
        chunks.append(chunk)
        used += len(chunk)
        included.append(item["path"])
    return "".join(chunks), included
