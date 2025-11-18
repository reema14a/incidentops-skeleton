# Logging Configuration

## Overview

IncidentOps uses a dual logging system with runtime logs stored at the project root in the `logs/` directory.

## Log Files

### logs/pipeline.log
- **Purpose**: Agent pipeline execution logs
- **Configured in**: `agents/base_agent.py`
- **Format**: `YYYY-MM-DD HH:MM:SS - [AgentName] message`
- **Rotation**: 5MB max size, 3 backup files
- **Handler**: RotatingFileHandler

### logs/mcp_server.log
- **Purpose**: MCP server operation logs
- **Configured in**: `llm/local_mcp/server.py`
- **Format**: Standard Python logging format
- **Rotation**: Configured in MCP server

## Why logs/ at Project Root?

Runtime logs are kept at the project root (`logs/`) rather than under `data/` for several reasons:

1. **Common Convention**: Most projects keep logs at root level
2. **Separation of Concerns**: Transient runtime logs vs. persistent data
3. **Easy Cleanup**: Can delete/rotate logs without affecting data
4. **Tool Compatibility**: Many monitoring tools expect logs at root
5. **Gitignore Simplicity**: Single `logs/` entry in .gitignore

## Directory Structure

```
project-root/
├── data/              # Persistent data
│   ├── db/           # Databases
│   ├── samples/      # Sample inputs
│   └── output/       # Generated outputs
├── logs/              # Runtime logs (transient)
│   ├── pipeline.log
│   └── mcp_server.log
└── ...
```

## Configuration

### Pipeline Logs (BaseAgent)

Location: `agents/base_agent.py` (lines ~30-60)

```python
# Create logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Rotating file handler (max 5 MB, 3 backups)
log_file = os.path.join(log_dir, "pipeline.log")
cls._file_handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3
)
```

### MCP Server Logs

Location: `llm/local_mcp/server.py`

The MCP server configures its own logging to `logs/mcp_server.log`.

## Log Rotation

Both log files use rotating file handlers:
- **Max Size**: 5MB per file
- **Backups**: 3 backup files kept
- **Naming**: `pipeline.log.1`, `pipeline.log.2`, `pipeline.log.3`
- **Automatic**: Rotation happens automatically when size limit reached

## Accessing Logs

### Via CLI
```bash
# View pipeline logs
tail -f logs/pipeline.log

# View MCP server logs
tail -f logs/mcp_server.log

# Search for errors
grep ERROR logs/pipeline.log
```

### Via Streamlit UI
Navigate to the **Audit Logs** page to view `logs/pipeline.log` with:
- Real-time updates
- Filtering by log level
- Search functionality
- Download capability

## Log Levels

- **INFO**: Normal operation messages
- **WARNING**: Non-critical issues
- **ERROR**: Errors that don't stop execution
- **CRITICAL**: Severe errors requiring attention

## Best Practices

1. **Don't commit logs**: The `logs/` directory is in `.gitignore`
2. **Monitor disk space**: Logs can grow large over time
3. **Use log rotation**: Configured automatically
4. **Check logs regularly**: Use Streamlit UI or CLI tools
5. **Archive old logs**: Move to backup storage if needed

## Troubleshooting

### Logs not appearing
- Check that `logs/` directory exists (created automatically)
- Verify write permissions on `logs/` directory
- Check that BaseAgent._setup_logging() is called

### Logs too large
- Adjust `maxBytes` in `base_agent.py`
- Reduce `backupCount` to keep fewer backups
- Implement external log rotation (logrotate)

### Can't find logs
- Logs are at project root: `./logs/`
- NOT under `data/logs/` (that directory doesn't exist)
- Check current working directory

## Future Enhancements

Potential improvements to logging:

- [ ] Centralized log configuration via settings.yaml
- [ ] Configurable log levels per agent
- [ ] Structured logging (JSON format)
- [ ] External log aggregation (ELK, Splunk)
- [ ] Log streaming to cloud services
- [ ] Separate log files per agent
