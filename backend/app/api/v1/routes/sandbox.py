from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import os
from pathlib import Path

from app.db.session import get_db
from app.models.models import Submission, Mentor
from app.api.v1.dependencies import get_current_mentor
from app.services.sandbox_manager import start_sandbox, stop_sandbox, get_docker_client

router = APIRouter()

@router.post("/start/{submission_id}")
async def create_sandbox(submission_id: str, db: AsyncSession = Depends(get_db), current_user: Mentor = Depends(get_current_mentor)):
    # Verify user is an admin or the appropriate mentor
    submission = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    sandbox_info = await start_sandbox(submission)
    return sandbox_info

@router.post("/stop/{sandbox_id}")
async def delete_sandbox(sandbox_id: str, current_user: Mentor = Depends(get_current_mentor)):
    await stop_sandbox(sandbox_id)
    return {"message": "Sandbox stopped successfully"}

@router.get("/files/{sandbox_id}")
async def list_sandbox_files(sandbox_id: str, current_user: Mentor = Depends(get_current_mentor)):
    client = get_docker_client()
    container_name = f"mentor-sandbox-{sandbox_id}"
    try:
        container = client.containers.get(container_name)
    except Exception:
        raise HTTPException(status_code=404, detail="Sandbox container not found")
        
    # Execute a simple command to list files in the working directory
    exit_code, output = container.exec_run("find . -type f", workdir=f"/autograder_jobs/{sandbox_id}/submission")
    if exit_code != 0:
        return {"files": []}
        
    files = output.decode("utf-8").strip().split("\n")
    files = [f for f in files if f]
    return {"files": files}

@router.get("/file/{sandbox_id}")
async def read_sandbox_file(sandbox_id: str, path: str, current_user: Mentor = Depends(get_current_mentor)):
    client = get_docker_client()
    container_name = f"mentor-sandbox-{sandbox_id}"
    try:
        container = client.containers.get(container_name)
    except Exception:
        raise HTTPException(status_code=404, detail="Sandbox container not found")
        
    exit_code, output = container.exec_run(["cat", path], workdir=f"/autograder_jobs/{sandbox_id}/submission")
    if exit_code != 0:
        raise HTTPException(status_code=404, detail="File not found or cannot be read")
        
    return {"content": output.decode("utf-8", errors="replace")}

@router.websocket("/pty/{sandbox_id}")
async def sandbox_pty(websocket: WebSocket, sandbox_id: str):
    await websocket.accept()
    client = get_docker_client()
    container_name = f"mentor-sandbox-{sandbox_id}"
    try:
        container = client.containers.get(container_name)
    except Exception:
        await websocket.close(code=1008, reason="Sandbox not found")
        return

    # Create an exec instance with a TTY
    exec_instance = client.api.exec_create(
        container.id, 
        cmd=["/bin/bash"], 
        stdin=True, 
        tty=True, 
        workdir=f"/autograder_jobs/{sandbox_id}/submission"
    )
    
    # Attach socket
    sock = client.api.exec_start(exec_instance["Id"], socket=True, tty=True)
    # The socket returned by docker-py on unix is a socket._socketobject
    sock.setblocking(False)

    async def read_from_socket():
        loop = asyncio.get_event_loop()
        while True:
            try:
                # Read from socket asynchronously
                data = await loop.sock_recv(sock._sock if hasattr(sock, '_sock') else sock, 4096)
                if not data:
                    break
                await websocket.send_bytes(data)
            except Exception as e:
                break

    async def read_from_ws():
        loop = asyncio.get_event_loop()
        while True:
            try:
                data = await websocket.receive_bytes()
                await loop.sock_sendall(sock._sock if hasattr(sock, '_sock') else sock, data)
            except WebSocketDisconnect:
                break
            except Exception:
                break

    # Run both tasks concurrently
    tasks = [
        asyncio.create_task(read_from_socket()),
        asyncio.create_task(read_from_ws())
    ]
    
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
        
    try:
        sock.close()
    except Exception:
        pass
    
    try:
        await websocket.close()
    except Exception:
        pass
