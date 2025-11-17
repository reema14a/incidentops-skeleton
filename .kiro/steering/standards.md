---
inclusion: always
---

# Additional Code Generation Standards
This steering file adds stricter rules and constraints that extend (not replace) the foundational product, structure, and tech steering files.

These rules exist to improve consistency and ensure safe, predictable code generation.

---

# Overwrite & Modification Policy
Kiro must:
- Prefer incremental edits instead of full rewrites  
- Preserve developer-written code  
- Avoid deleting custom code unless explicitly instructed  
- Regenerate entire files ONLY when specifically asked  

---

# Import & Module Rules
- Always use absolute imports  
- Never use relative imports (e.g., `from ..agents`)  
- Never use wildcard imports (`from x import *`)  

---

# Orchestrator Constraints
The orchestrator must NOT:
- contain business logic  
- contain agent-specific logic  
- perform file I/O (unless explicitly allowed)  
- invoke agents out of pipeline order  

It may only:
- instantiate agents  
- pass data sequentially  
- handle pipeline-level logging  
- catch and report errors  

---

# Type Hint Requirements
All generated functions must include type hints.

Example:
```python
def run(self, input_data: list[str]) -> dict:
    ...
```

---

# Docstring Standard
All generated classes and methods must include **Google-style docstrings**:

```python
"""Short summary.

Args:
    input_data (Any): Description.

Returns:
    Any: Description.
"""
```

---

# Disallowed Patterns
Kiro must avoid:
- Generating duplicate class definitions  
- Mixing business logic between agents  
- Creating circular imports  
- Writing code outside expected folders  
- Adding unused imports  
- Using print() inside agents (must use self.log())  

---

# Runtime Guarantee
All generated code must remain executable via:

```
python3 -m ui.console_client
```

Kiro must ensure all imports remain valid after modifications.

---
## Testing Standards

### Unit Tests
- Must mock OpenAIClient.generate() for any AI agent.
- Must validate agent behavior in isolation.
- Must be placed under tests/unit/.
- Must not perform disk I/O or execute the whole pipeline.

### Integration Tests
- Must validate multi-agent flows or the entire pipeline.
- Should use deterministic mock responses for LLM behavior.
- Must be placed under tests/integration/.

### Naming Conventions
- Unit test filenames: test_<agent>.py
- Integration test filenames: test_<flow>.py or test_<pipeline>.py

### Test File Retention
- When Kiro generates temporary test files during task execution, they should be preserved as permanent unit tests and placed in the `tests/` directory.  
- If a test file validates an agent’s behavior, Kiro should convert it into a stable test file rather than deleting it.

## LLM Agent Standards

All LLM-driven agents must follow these patterns:

### JSON Parsing
- All agents must use the shared JSON extraction helper:
  from utils.json_parser import extract_json_block
- Direct json.loads() inside agents should not be used.
- Each agent must include a private method:
  _parse_llm_response()
  which uses extract_json_block() for structured output.

### Fallback Behavior
If the response cannot be parsed as JSON:
- Log a warning
- Return a summary based on the first 200 characters of raw text
- categories → []
- severity_breakdown → {}
- root_causes → []
- (or equivalent fields depending on the agent)

### Method & Structure Conventions
- Agent logic must remain deterministic and stateless.
- Logging should use self.log().
- All LLM agents must call the OpenAIClient.generate() method.

## Separation of Responsibilities Between OpsLogAgent and LLMGovernanceAgent

- OpsLogAgent must ONLY produce a factual, deterministic audit log.
  It should not:
  * perform interpretation
  * compute risk
  * generate human-readable summaries
  * perform escalation logic

- LLMGovernanceAgent is the ONLY agent responsible for:
  * governance summaries
  * risk scoring
  * escalation decisions
  * compliance analysis

- If overlapping functionality is detected, Kiro should move:
  * explanatory or interpretive logic → LLMGovernanceAgent
  * factual structured data recording → OpsLogAgent

## Logging Standard
- All agents must use BaseAgent.log().
- BaseAgent.log() must write to both console and file.
- File logging must use a rotating handler.
- No agent must write directly using print() except BaseAgent.log().

## Database access standard

- Use a single SQLite connection per request/context
- Wrap all writes in transactions
- Use prepared statements (parameterized queries)
- Avoid raw SQL strings inside business logic
- Use descriptive, JSON-safe formats for TEXT fields


## Configuration Access Policy

All configuration access must go through the centralized `config.settings_loader` module.

### ✅ REQUIRED Pattern

```python
from config.settings_loader import get_settings

settings = get_settings()
value = settings.get_my_setting()
```

### ❌ PROHIBITED Patterns

The following patterns are **strictly prohibited** in all application code:

1. **Direct environment variable access**:
   ```python
   # ❌ WRONG
   import os
   api_key = os.getenv('OPENAI_API_KEY')
   endpoint = os.environ['MCP_ENDPOINT']
   ```

2. **Direct YAML file reading**:
   ```python
   # ❌ WRONG
   import yaml
   with open('config/settings.yaml', 'r') as f:
       config = yaml.safe_load(f)
   ```

3. **Direct .env file loading**:
   ```python
   # ❌ WRONG
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Exemptions

Only the following files may access configuration directly:
- `config/settings_loader.py` (the centralized configuration module)
- `tests/unit/test_settings_loader.py` (tests for the settings loader)

### Validation

Run the validation script to check for violations:
```bash
python3 scripts/validate_config_access.py
```

### Rationale

- **Single Source of Truth**: All configuration logic in one place
- **Priority Management**: Enforces env vars > YAML > defaults
- **Security**: Secrets must come from environment variables only
- **Validation**: Configuration values validated in one place
- **Testability**: Easy to mock/override configuration
- **Consistency**: All code uses the same interface

See `docs/configuration_enforcement.md` for complete details.
