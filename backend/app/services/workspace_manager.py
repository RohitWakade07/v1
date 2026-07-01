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

GITHUB_URL_PATTERN = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?:/tree/([^/]+)/(.*))?$"
)

def parse_github_url(url: str):
    match = GITHUB_URL_PATTERN.match(url)
    if not match:
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    owner = match.group(1)
    repo = match.group(2)
    branch = match.group(3)
    path = match.group(4)
    
    base_url = f"https://github.com/{owner}/{repo}.git"
    return {
        "base_url": base_url,
        "branch": branch,
        "path": path
    }

def clone_repository(repo_url: str, dest_dir: Path) -> None:
    parsed = parse_github_url(repo_url)
    
    cmd = ["git", "clone", "--depth", "1"]
    if parsed["branch"]:
        cmd.extend(["--branch", parsed["branch"]])
    
    cmd.extend([parsed["base_url"], str(dest_dir)])
    
    subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
    )
    
    if parsed["path"]:
        # Move contents of subpath to root of dest_dir
        subpath_dir = dest_dir / parsed["path"]
        if not subpath_dir.exists() or not subpath_dir.is_dir():
            raise ValueError(f"Path '{parsed['path']}' not found in repository.")
        
        # Move everything out of the subpath to a temp location, then to root
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Move from subpath to temp
            for item in subpath_dir.iterdir():
                shutil.move(str(item), str(temp_path / item.name))
            
            # Delete original clone contents
            for item in dest_dir.iterdir():
                if item.name == ".git":
                    continue
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            
            # Move from temp to root
            for item in temp_path.iterdir():
                shutil.move(str(item), str(dest_dir / item.name))

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
