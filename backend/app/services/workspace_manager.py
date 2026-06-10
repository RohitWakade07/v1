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


def clone_repository(repo_url: str, dest_dir: Path) -> None:
    subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(dest_dir)],
        check=True,
        capture_output=True,
        text=True,
    )


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
