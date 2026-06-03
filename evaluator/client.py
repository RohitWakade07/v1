import httpx
from typing import Dict, Any
from evaluator.evaluator_logging import logger
from evaluator.configuration import Configuration

class ChallengeClient:
    """Network communicator client to manage session challenges from the backend API."""

    def __init__(self, config: Configuration):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {self.config.student_token}",
            "Content-Type": "application/json"
        }

    def fetch_challenge(self) -> Dict[str, Any]:
        """Fetches the authoritative assignment evaluation challenge package from the backend."""
        url = f"{self.config.backend_url}/api/v1/sessions/{self.config.session_id}/challenge"
        logger.info(f"Fetching challenge package from backend endpoint: {url}")
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self.headers)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch challenge. Status code: {response.status_code}. Response: {response.text}")
                    response.raise_for_status()
                    
                logger.info("Successfully fetched challenge package.")
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP connection error during challenge package retrieval: {e}")
            raise RuntimeError(f"Network error during challenge fetch: {e}")

    def abort_session(self) -> None:
        """Sends an abort signal to the backend to mark the session as ABORTED."""
        url = f"{self.config.backend_url}/api/v1/sessions/{self.config.session_id}/abort"
        logger.info(f"Sending abort request to backend: {url}")
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, headers=self.headers)
                if response.status_code == 200:
                    logger.info("Session successfully aborted on the server.")
                else:
                    logger.warning(f"Failed to abort session on the server (Status: {response.status_code}). Details: {response.text}")
        except Exception as e:
            logger.warning(f"Could not contact server to abort session: {e}")
