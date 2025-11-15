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