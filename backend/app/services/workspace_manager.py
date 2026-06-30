import io
import os
import shutil
import subprocess
import zipfile
from pathlib import Path


def _normalize_zip_path(path: str) -> str:
    return Path(path).as_posix().lstrip("./")


def safe_extract_zip(contents: bytes, dest_dir: Path) -> None:
    with zipfile.ZipFile(io.BytesIO(contents)) as archive:
        for member in archive.namelist():
            normalized = _normalize_zip_path(member)
            if normalized.startswith("../") or normalized.startswith("/"):
                raise ValueError("ZIP archive contains invalid paths")
        archive.extractall(path=dest_dir)


import re
import tempfile

def parse_github_url(url: str) -> tuple[str, str | None, str | None]:
    match = re.match(r"^(https://github\.com/[^/]+/[^/]+?)(?:\.git)?(?:/tree/([^/]+)(?:/(.*))?)?$", url)
    if not match:
        return url, None, None
    subpath = match.group(3)
    if subpath == "":
        subpath = None
    return match.group(1), match.group(2), subpath


def clone_repository(repo_url: str, dest_dir: Path) -> None:
    base_url, branch, subpath = parse_github_url(repo_url)
    
    if not branch and not subpath:
        subprocess.run(
            ["git", "clone", base_url, str(dest_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        clone_cmd = ["git", "clone"]
        if branch:
            clone_cmd.extend(["-b", branch])
        clone_cmd.extend([base_url, temp_dir])
        
        subprocess.run(
            clone_cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        
        source_dir = Path(temp_dir)
        if subpath:
            source_dir = source_dir / subpath
            if not source_dir.exists() or not source_dir.is_dir():
                raise ValueError(f"Subdirectory '{subpath}' not found in repository")
                
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)


def list_workspace_files(base_dir: Path) -> list[str]:
    items: list[str] = []
    for path in base_dir.rglob("*"):
        if path.is_file():
            items.append(str(path.relative_to(base_dir)).replace(os.sep, "/"))
    return items


def cleanup_workspace(path: Path) -> None:
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
