import os
from evaluator.evaluator_logging import logger
from evaluator.configuration import Configuration

class SessionManager:
    """Manages local directories, checks workspace paths, and guarantees execution resources."""
    
    def __init__(self, config: Configuration):
        self.config = config

    def prepare_environment(self) -> None:
        """Ensures directories and workspace structures are ready."""
        logger.info("Initializing environment configurations...")
        
        # Verify workspace directory availability
        if not os.path.exists(self.config.workspace_dir):
            os.makedirs(self.config.workspace_dir)
            logger.info(f"Created workspace directory: {self.config.workspace_dir}")
            
        # Verify scripts directory availability
        if not os.path.exists(self.config.scripts_dir):
            os.makedirs(self.config.scripts_dir)
            logger.info(f"Created scripts directory: {self.config.scripts_dir}")

    def clean_session(self) -> None:
        """Safely purges temporary local configurations."""
        logger.info("Cleaning up temporary local assets...")
        
        if os.path.exists(self.config.state_file):
            try:
                os.remove(self.config.state_file)
                logger.info("State history cleared from disk.")
            except Exception as e:
                logger.warning(f"Error purging state file: {e}")
