import asyncio
import io
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import HTTPException, status

from app.services.workspace_manager import clone_repository, list_workspace_files, safe_extract_zip

GITHUB_URL_PATTERN = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?$"
)


class SubmissionValidator:
    def validate_zip(self, contents: bytes, assignment_slug: str) -> None:
        if not contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded ZIP archive is empty",
            )

        try:
            with TemporaryDirectory() as temp_dir:
                safe_extract_zip(contents, Path(temp_dir))
                self._validate_assignment_rules(Path(temp_dir), assignment_slug)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ZIP archive: {exc}",
            )

    async def validate_github(self, repo_url: str, assignment_slug: str) -> None:
        if not repo_url or not isinstance(repo_url, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub repository URL is required",
            )

        if not GITHUB_URL_PATTERN.match(repo_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub repository URL",
            )

        if "week5" in assignment_slug.lower():
            return

        if "week4" in assignment_slug.lower():
            try:
                with TemporaryDirectory() as temp_dir:
                    await asyncio.to_thread(clone_repository, repo_url, Path(temp_dir))
                    self._validate_assignment_rules(Path(temp_dir), assignment_slug)
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"GitHub repository validation failed: {exc}",
                )

    def _validate_assignment_rules(self, workspace_dir: Path, assignment_slug: str) -> None:
        files = list_workspace_files(workspace_dir)
        normalized = {path.lower() for path in files}

        if "week4" in assignment_slug.lower():
            found_git = list(workspace_dir.rglob(".git"))
            if not found_git:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Week4 submissions must include a .git repository anywhere inside the zip",
                )

        if "week5" in assignment_slug.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Week5 submissions must be submitted through GitHub URL only",
            )
