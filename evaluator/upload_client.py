import httpx
from typing import Dict, Any
from evaluator.evaluator_logging import logger
from evaluator.configuration import Configuration

class UploadClient:
    """Submits local proof packages to backend verification services."""

    def __init__(self, config: Configuration):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {self.config.student_token}",
            "Content-Type": "application/json"
        }

    def upload_proof(self, proof_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submits the signed proof JSON package to the backend."""
        url = f"{self.config.backend_url}/api/v1/proof/submit"
        logger.info(f"Submitting proof package to backend endpoint: {url}")
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=proof_payload, headers=self.headers)
                
                if response.status_code not in (200, 201):
                    logger.error(f"Proof submission rejected. Status code: {response.status_code}. Details: {response.text}")
                    response.raise_for_status()
                    
                result = response.json()
                logger.info(f"Proof upload finished. Backend Response: {result.get('message', 'No message details')}")
                return result
        except httpx.HTTPError as e:
            logger.error(f"HTTP connection error during proof submission upload: {e}")
            raise RuntimeError(f"Network error during proof upload: {e}")
