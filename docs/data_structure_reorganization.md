# Data Directory Structure Reorganization

## Overview
Reorganized the `data/` directory to better separate persistent databases, runtime logs, sample inputs, and output dumps.

## New Structure

```
data/
├── db/              # Persistent database files (SQLite)
│   ├── .gitkeep
│   └── incidents.db
├── samples/         # Sample input logs for testing and demonstration
│   ├── .gitkeep
│   └── sample_logs.txt
└── output/          # Optional pipeline output dumps
    ├── .gitkeep
    └── output_log.json

logs/                # Runtime logs at project root (not under data/)
├── pipeline.log
└── mcp_server.log
```

## Changes Made

### 1. Directory Structure
- Created `data/db/` for persistent database files
- Created `data/samples/` for sample input files
- Created `data/output/` for pipeline output dumps
- Added `.gitkeep` files to preserve empty directories in git

### 2. File Migrations
- Moved `data/incidents.db` → `data/db/incidents.db`
- Moved `data/sample_logs.txt` → `data/samples/sample_logs.txt`
- Moved `data/output_log.json` → `data/output/output_log.json`

### 3. Configuration Updates

#### Environment Files
- `.env`: Updated `DB_PATH` and `OUTPUT_LOG_PATH`
- `.env.example`: Updated default paths

#### Code Updates
- `agents/monitor_agent.py`: Updated sample logs path
- `agents/opslog_agent.py`: Updated default output path
- `ui/pages/Governance.py`: Updated output log path
- `ui/pages/Dashboards.py`: Updated output log path

#### Documentation Updates
- `.kiro/steering/structure.md`: Updated directory organization and data structure
- `.kiro/steering/tech.md`: Updated integration points documentation
- `.kiro/specs/db_storage.spec.md`: Updated all database path references
- `README.md`: Added data directory structure documentation

### 4. Git Ignore Updates
- Updated `.gitignore` to use patterns:
  - `data/output/` (entire directory)
  - `data/db/*.db` (all database files)

## Rationale

### Before
```
data/
├── incidents.db          # Mixed: database
├── output_log.json       # Mixed: output
└── sample_logs.txt       # Mixed: sample input
```

### After
```
data/
├── db/                   # Clear: persistent storage
├── samples/              # Clear: test inputs
└── output/               # Clear: generated outputs

logs/                     # Runtime logs at project root
├── pipeline.log
└── mcp_server.log
```

## Benefits

1. **Clarity**: Each subdirectory has a clear, single purpose
2. **Maintainability**: Easier to manage backups, cleanup, and gitignore rules
3. **Scalability**: Can add more databases, samples, or outputs without clutter
4. **Standards**: Follows common project organization patterns
5. **Separation**: Runtime logs at project root separate from persistent data

## Migration Guide

If you have existing data files:

```bash
# Backup existing data
cp -r data/ data_backup/

# Create new structure
mkdir -p data/db data/samples data/output

# Move files
mv data/incidents.db data/db/ 2>/dev/null || true
mv data/sample_logs.txt data/samples/ 2>/dev/null || true
mv data/output_log.json data/output/ 2>/dev/null || true

# Remove old data/logs directory if it exists (logs are at project root)
rmdir data/logs 2>/dev/null || true

# Update .env file
# Change DB_PATH=data/incidents.db to DB_PATH=data/db/incidents.db
# Change OUTPUT_LOG_PATH=data/output_log.json to OUTPUT_LOG_PATH=data/output/output_log.json
```

## Verification

Run the following to verify the configuration:

```bash
python3 -c "from config.settings_loader import get_settings; s = get_settings(); print(f'DB_PATH: {s.database.path}'); print(f'OUTPUT_LOG: {s.paths.output_log}')"
```

Expected output:
```
DB_PATH: data/db/incidents.db
OUTPUT_LOG: data/output/output_log.json
```

## Notes

- Runtime logs are stored at project root `logs/` (not under `data/`)
- This follows common conventions where transient logs are separate from persistent data
- Log paths are hardcoded in `agents/base_agent.py` and `llm/local_mcp/server.py`
- All data paths are configurable via environment variables
- The centralized settings loader ensures consistent path resolution
