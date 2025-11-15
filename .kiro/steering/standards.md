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
