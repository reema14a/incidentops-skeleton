from openai import OpenAI
import json
import logging
import time
from logging.handlers import RotatingFileHandler
from utils.json_parser import extract_json_block
from config.settings_loader import get_settings

logger = logging.getLogger("IncidentOps.llm")
logger.setLevel(logging.INFO)
logger.propagate = True  # Use the same handlers as BaseAgent

class OpenAIClient:
    """OpenAI client with structured logging for all LLM interactions.
    
    Logs request metadata, response metadata, JSON parsing status,
    and fallback/error reporting to logs/pipeline.log.
    
    Implements singleton pattern to avoid repeated initialization.
    """
    
    _logger = logger
    _instance = None
    _initialized = False
    
    def __new__(cls, model: str = "gpt-4o-mini"):
        """Create or return the singleton instance.
        
        Args:
            model (str): The OpenAI model to use.
            
        Returns:
            OpenAIClient: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize the OpenAI client (only once).
        
        Args:
            model (str): The OpenAI model to use.
        """
        # Only initialize once
        if self._initialized:
            return
            
        self.model = model
        
        # Use settings_loader instead of direct env access
        settings = get_settings()
        self.api_key = settings.get_secret('OPENAI_API_KEY')
        use_real = settings.llm.use_real_openai
        self.enabled = bool(self.api_key and use_real)
        
        # self._setup_logging()
        self._log_initialization()
        
        # Mark as initialized
        OpenAIClient._initialized = True

    def _log_initialization(self):
        """Log OpenAI client initialization details."""
        status = "enabled" if self.enabled else "disabled (mock mode)"
        key_status = "present" if self.api_key else "missing"
        self._logger.info(f"[OpenAIClient] Initialized with model={self.model}, status={status}, api_key={key_status}")

    def _log(self, level: str, event: str, **fields):
        """
        Unified structured logger.
        Example:
            self._log("info", "REQUEST", model=self.model, prompt_length=len(prompt))
        """
        parts = [f"[OpenAIClient] {event}"]
        for k, v in fields.items():
            parts.append(f"{k}={v}")
        message = " | ".join(parts)
        getattr(self._logger, level)(message)

    def _preview(self, text: str, limit: int = 120) -> str:
        """Return a clean preview with newlines removed."""
        clean = text.replace("\n", " ")
        return clean[:limit] + ("..." if len(clean) > limit else "")

    def _log_request(self, prompt: str):
        self._log(
            "info",
            "REQUEST",
            model=self.model,
            prompt_length=len(prompt),
            preview=self._preview(prompt)
        )

    def _log_response(self, response: str, latency_ms: int, usage: dict | None):
        usage_str = (
            f"prompt={usage.get('prompt_tokens',0)}, "
            f"completion={usage.get('completion_tokens',0)}, "
            f"total={usage.get('total_tokens',0)}"
            if usage else "n/a"
        )

        self._log(
            "info",
            "RESPONSE",
            latency_ms=latency_ms,
            response_length=len(response),
            tokens=usage_str,
            preview=self._preview(response)
        )

    def _log_json_parsing(self, response: str, parsed: dict | None):
        if parsed:
            self._log("info", "JSON_PARSE", status="success", keys=list(parsed.keys()))
        else:
            self._log("warning", "JSON_PARSE", status="failed", preview=self._preview(response,150))

    def _log_fallback(self, reason: str, data: dict):
        self._log("warning", "FALLBACK", reason=reason, data=data)

    def _log_error(self, error: Exception, context: str = ""):
        self._log(
            "error",
            "ERROR",
            type=type(error).__name__,
            message=str(error),
            context=context
        )

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
                self._log_json_parsing(response_content, parsed_json)
            else:
                self._log_json_parsing(response_content, None)
            
            return response_content
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            self._log_error(e, context=f"generate() after {latency_ms}ms")
            
            error_response = json.dumps({"error": str(e)})
            self._log_fallback("api_error", {"error": str(e)})
            return error_response
