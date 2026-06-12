# POOL DISABLED — Railway deployment uses single container per job
# Uncomment this entire module when moving to a dedicated Docker host
# See architecture doc Section 7 for full pool design

'''
import docker
import redis
import logging
from typing import Optional
from app.core.config import settings
from app.db.redis import get_redis

logger = logging.getLogger(__name__)

class ContainerPoolService:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.redis = redis.Redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)

    def acquire_container(self, language: str) -> Optional[str]:
        """Atomically pop a container from the available list and add to busy set."""
        # Using RPOPLPUSH (or BLMOVE in newer redis) to move from available to busy atomically
        # But we don't have a built-in blocking move for sets. 
        # We can just LPOP and then SADD. Or use a Lua script for atomicity.
        
        container_id = self.redis.lpop(f"pool:{language}:available")
        if container_id:
            self.redis.sadd(f"pool:{language}:busy", container_id)
            logger.info(f"Acquired container {container_id} for {language}")
            return container_id
            
        logger.warning(f"No available containers for {language}!")
        return None

    def release_container(self, language: str, container_id: str):
        """Release a container back to the available pool."""
        # Optional: cleanup workspace inside container before releasing
        try:
            container = self.docker_client.containers.get(container_id)
            container.exec_run("rm -rf /tmp/workspace/*")
        except Exception as e:
            logger.error(f"Failed to cleanup container {container_id}: {e}")
            # If it's dead, don't return to pool
            self.redis.srem(f"pool:{language}:busy", container_id)
            self.redis.srem(f"pool:{language}:all", container_id)
            return

        self.redis.srem(f"pool:{language}:busy", container_id)
        self.redis.lpush(f"pool:{language}:available", container_id)
        logger.info(f"Released container {container_id} for {language}")

    def warmup_pool(self, language: str, count: int = 5):
        """Pre-warm a pool of containers for a specific language."""
        image_map = {
            "python": "python:3.10-slim",
            "java": "openjdk:17-slim",
            "cpp": "gcc:11",
            "javascript": "node:18-slim"
        }
        image = image_map.get(language)
        if not image:
            raise ValueError(f"Unsupported language: {language}")

        current_count = self.redis.scard(f"pool:{language}:all")
        to_create = count - current_count
        
        for _ in range(to_create):
            try:
                container = self.docker_client.containers.run(
                    image,
                    command="tail -f /dev/null",  # Keep alive
                    detach=True,
                    network_mode="none",
                    mem_limit="512m",
                    pids_limit=64
                )
                self.redis.sadd(f"pool:{language}:all", container.id)
                self.redis.lpush(f"pool:{language}:available", container.id)
                logger.info(f"Warmed up {language} container: {container.id}")
            except Exception as e:
                logger.error(f"Failed to create container for {language}: {e}")
'''
