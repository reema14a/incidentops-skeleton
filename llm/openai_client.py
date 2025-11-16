from openai import OpenAI
import os
import json
import logging
import time
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from utils.json_parser import extract_json_block

# Load .env variables into environment
load_dotenv()


class OpenAIClient:
    """OpenAI client with structured logging for all LLM interactions.
    
    Logs request metadata, response metadata, JSON parsing status,
    and fallback/error reporting to logs/pipeline.log.
    """
    
    _logger = None
    
    def __init__(self, model: str = "gpt-4.1-mini"):
        """Initialize the OpenAI client.
        
        Args:
            model (str): The OpenAI model to use.
        """
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        use_real = os.getenv("USE_REAL_OPENAI", "false").lower() == "true"
        self.enabled = bool(self.api_key and use_real)
        
        self._setup_logging()
        self._log_initialization()

    @classmethod
    def _setup_logging(cls):
        """Set up logging configuration with rotating file handler.
        
        Uses the same logging configuration as BaseAgent to ensure
        all LLM-related logs are written to logs/pipeline.log.
        """
        if cls._logger is not None:
            return
        
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create logger
        cls._logger = logging.getLogger("IncidentOps.LLM")
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
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Add handlers to logger
        cls._logger.addHandler(console_handler)
        cls._logger.addHandler(file_handler)

    def _log_initialization(self):
        """Log OpenAI client initialization details."""
        status = "enabled" if self.enabled else "disabled (mock mode)"
        key_status = "present" if self.api_key else "missing"
        self._logger.info(f"[OpenAIClient] Initialized with model={self.model}, status={status}, api_key={key_status}")

    def _log_request(self, prompt: str):
        """Log request metadata.
        
        Args:
            prompt (str): The prompt being sent to the LLM.
        """
        prompt_length = len(prompt)
        prompt_preview = prompt[:100].replace('\n', ' ') + ('...' if len(prompt) > 100 else '')
        self._logger.info(f"[OpenAIClient] REQUEST | model={self.model} | prompt_length={prompt_length} | preview='{prompt_preview}'")

    def _log_response(self, response_content: str, latency_ms: int, usage: dict = None):
        """Log response metadata.
        
        Args:
            response_content (str): The response content from the LLM.
            latency_ms (int): Request latency in milliseconds.
            usage (dict): Token usage information from the API response.
        """
        response_length = len(response_content)
        response_preview = response_content[:100].replace('\n', ' ') + ('...' if len(response_content) > 100 else '')
        
        usage_str = ""
        if usage:
            usage_str = f" | tokens={{prompt={usage.get('prompt_tokens', 0)}, completion={usage.get('completion_tokens', 0)}, total={usage.get('total_tokens', 0)}}}"
        
        self._logger.info(f"[OpenAIClient] RESPONSE | latency={latency_ms}ms | response_length={response_length}{usage_str} | preview='{response_preview}'")

    def _log_json_parsing(self, response_content: str, parsed_data: dict = None, success: bool = True):
        """Log JSON parsing status.
        
        Args:
            response_content (str): The raw response content.
            parsed_data (dict): The parsed JSON data if successful.
            success (bool): Whether parsing was successful.
        """
        if success and parsed_data:
            keys = list(parsed_data.keys())
            self._logger.info(f"[OpenAIClient] JSON_PARSE | status=success | keys={keys}")
        else:
            preview = response_content[:150].replace('\n', ' ') + ('...' if len(response_content) > 150 else '')
            self._logger.warning(f"[OpenAIClient] JSON_PARSE | status=failed | raw_preview='{preview}'")

    def _log_fallback(self, reason: str, fallback_data: dict):
        """Log fallback behavior when normal processing fails.
        
        Args:
            reason (str): The reason for the fallback.
            fallback_data (dict): The fallback data being returned.
        """
        self._logger.warning(f"[OpenAIClient] FALLBACK | reason={reason} | fallback_data={fallback_data}")

    def _log_error(self, error: Exception, context: str = ""):
        """Log error details.
        
        Args:
            error (Exception): The exception that occurred.
            context (str): Additional context about where the error occurred.
        """
        error_type = type(error).__name__
        error_msg = str(error)
        self._logger.error(f"[OpenAIClient] ERROR | type={error_type} | message='{error_msg}' | context={context}")

    def generate(self, prompt: str) -> str:
        """Generate a response from the OpenAI API with structured logging.
        
        Args:
            prompt (str): The prompt to send to the LLM.
            
        Returns:
            str: The response content from the LLM or a mock/error response.
        """
        self._log_request(prompt)
        
        if not self.enabled:
            mock_response = json.dumps({"_mock": True, "text": "MOCK_RESPONSE"})
            self._log_fallback("mock_mode_enabled", {"_mock": True, "text": "MOCK_RESPONSE"})
            return mock_response

        client = OpenAI(api_key=self.api_key)
        start_time = time.time()
        
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            response_content = resp.choices[0].message.content
            
            # Extract usage information if available
            usage = None
            if hasattr(resp, 'usage') and resp.usage:
                usage = {
                    'prompt_tokens': resp.usage.prompt_tokens,
                    'completion_tokens': resp.usage.completion_tokens,
                    'total_tokens': resp.usage.total_tokens
                }
            
            self._log_response(response_content, latency_ms, usage)
            
            # Attempt to parse as JSON for logging purposes
            parsed_json = extract_json_block(response_content)
            if parsed_json:
                self._log_json_parsing(response_content, parsed_json, success=True)
            else:
                self._log_json_parsing(response_content, success=False)
            
            return response_content
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            self._log_error(e, context=f"generate() after {latency_ms}ms")
            
            error_response = json.dumps({"error": str(e)})
            self._log_fallback("api_error", {"error": str(e)})
            return error_response
