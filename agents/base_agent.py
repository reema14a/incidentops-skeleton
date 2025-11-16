import logging
import os
from logging.handlers import RotatingFileHandler


class BaseAgent:
    """Base class for all agents with simple logging.
    
    Logs to both console and logs/pipeline.log using a rotating file handler.
    """
    
    _file_handler = None
    _logger = None
    
    def __init__(self, name: str):
        """Initialize the agent with a name.
        
        Args:
            name (str): The name of the agent.
        """
        self.name = name
        self._setup_logging()
    
    @classmethod
    def _setup_logging(cls):
        """Set up logging configuration with rotating file handler.
        
        Creates logs directory if it doesn't exist and configures a rotating
        file handler (max 5 MB, 3 backups) for logs/pipeline.log.
        """
        if cls._logger is not None:
            return
        
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create logger
        cls._logger = logging.getLogger("IncidentOps")
        cls._logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if cls._logger.handlers:
            return
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Rotating file handler (max 5 MB, 3 backups)
        log_file = os.path.join(log_dir, "pipeline.log")
        cls._file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3
        )
        cls._file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        cls._file_handler.setFormatter(file_formatter)
        
        # Add handlers to logger
        cls._logger.addHandler(console_handler)
        cls._logger.addHandler(cls._file_handler)

    def log(self, message: str):
        """Log a message to both console and file.
        
        Args:
            message (str): The message to log.
        """
        formatted_message = f"[{self.name}] {message}"
        self._logger.info(formatted_message)

    def run(self, input_data=None):
        """Execute the agent's main logic.
        
        Args:
            input_data (Any): Input data for the agent.
            
        Returns:
            Any: Output from the agent.
            
        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError("Each agent must implement its own run() method.")
