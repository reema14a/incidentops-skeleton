"""
Audit Logs Page

Displays pipeline execution logs from logs/pipeline.log with real-time streaming,
formatting, and graceful handling of missing or empty log files.
"""

import streamlit as st
import time
from pathlib import Path
from typing import List, Optional


def get_log_file_path() -> Path:
    """
    Get the path to the pipeline log file.
    
    Returns:
        Path: Path object pointing to logs/pipeline.log
    """
    project_root = Path(__file__).parent.parent.parent
    return project_root / "logs" / "pipeline.log"


def read_log_file(max_lines: Optional[int] = None) -> tuple[List[str], bool]:
    """
    Read the pipeline log file.
    
    Args:
        max_lines: Maximum number of lines to read (None for all lines)
        
    Returns:
        tuple: (list of log lines, file_exists flag)
    """
    log_path = get_log_file_path()
    
    if not log_path.exists():
        return [], False
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Return most recent lines if max_lines specified
        if max_lines and len(lines) > max_lines:
            lines = lines[-max_lines:]
        
        return lines, True
    except Exception as e:
        st.error(f"Error reading log file: {str(e)}")
        return [], True


def format_log_line(line: str) -> tuple[str, str]:
    """
    Format a log line for display with color coding based on log level.
    
    Args:
        line: Raw log line
        
    Returns:
        tuple: (formatted_line, color_class)
    """
    line = line.strip()
    
    # Determine color based on log level or content
    if 'ERROR' in line or '✗' in line or 'failed' in line.lower():
        return line, 'error'
    elif 'WARNING' in line or 'WARN' in line or '⚠️' in line:
        return line, 'warning'
    elif 'CRITICAL' in line or '🔴' in line:
        return line, 'critical'
    elif '✓' in line or 'success' in line.lower():
        return line, 'success'
    else:
        return line, 'info'


def truncate_logs(lines: List[str], max_chars: int = 100000) -> tuple[List[str], bool]:
    """
    Truncate logs if they exceed maximum character count.
    
    Args:
        lines: List of log lines
        max_chars: Maximum total characters
        
    Returns:
        tuple: (truncated lines, was_truncated flag)
    """
    total_chars = sum(len(line) for line in lines)
    
    if total_chars <= max_chars:
        return lines, False
    
    # Keep most recent lines that fit within limit
    truncated = []
    char_count = 0
    
    for line in reversed(lines):
        if char_count + len(line) > max_chars:
            break
        truncated.insert(0, line)
        char_count += len(line)
    
    return truncated, True


# Page configuration
st.title("📋 Audit Logs")
st.caption("💡 Shows raw pipeline execution logs. For incident insights, check Dashboard or Governance.")

st.markdown("---")

# Controls section
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    max_lines = st.number_input(
        "Max lines to display:",
        min_value=10,
        max_value=10000,
        value=500,
        step=50,
        help="Limit the number of log lines displayed (most recent)"
    )

with col2:
    auto_refresh = st.checkbox(
        "Auto-refresh",
        value=False,
        help="Automatically refresh logs every 5 seconds"
    )

with col3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.markdown("---")

# Read log file
log_lines, file_exists = read_log_file(max_lines=int(max_lines))

# Handle missing or empty log file
if not file_exists:
    st.warning("⚠️ Log file not found")
    st.info(f"Expected location: `{get_log_file_path()}`")
    st.markdown("""
    **Possible reasons:**
    - Pipeline has not been run yet
    - Log file was deleted
    - Incorrect log file path configuration
    
    **To generate logs:**
    1. Navigate to the **Pipeline Runner** page
    2. Run the pipeline with log input
    3. Return to this page to view logs
    """)
    st.stop()

if not log_lines:
    st.info("📄 Log file is empty")
    st.markdown("Run the pipeline to generate logs.")
    st.stop()

# Truncate if necessary
log_lines, was_truncated = truncate_logs(log_lines)

if was_truncated:
    st.warning(f"⚠️ Logs truncated to most recent ~100KB for performance")

# Display log statistics
st.subheader("📊 Log Statistics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Lines", len(log_lines))

with col2:
    error_count = sum(1 for line in log_lines if 'ERROR' in line or '✗' in line)
    st.metric("Errors", error_count)

with col3:
    warning_count = sum(1 for line in log_lines if 'WARNING' in line or 'WARN' in line)
    st.metric("Warnings", warning_count)

with col4:
    success_count = sum(1 for line in log_lines if '✓' in line or 'success' in line.lower())
    st.metric("Success", success_count)

st.markdown("---")

# Filter options
st.subheader("🔍 Filter Logs")
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    filter_text = st.text_input(
        "Search logs:",
        placeholder="Enter text to filter logs...",
        help="Case-insensitive search"
    )

with filter_col2:
    log_level_filter = st.multiselect(
        "Filter by level:",
        options=['ERROR', 'WARNING', 'CRITICAL', 'SUCCESS', 'INFO'],
        default=[],
        help="Show only selected log levels"
    )

# Apply filters
filtered_lines = log_lines

if filter_text:
    filtered_lines = [line for line in filtered_lines if filter_text.lower() in line.lower()]

if log_level_filter:
    level_filtered = []
    for line in filtered_lines:
        for level in log_level_filter:
            if level == 'ERROR' and ('ERROR' in line or '✗' in line):
                level_filtered.append(line)
                break
            elif level == 'WARNING' and ('WARNING' in line or 'WARN' in line):
                level_filtered.append(line)
                break
            elif level == 'CRITICAL' and 'CRITICAL' in line:
                level_filtered.append(line)
                break
            elif level == 'SUCCESS' and ('✓' in line or 'success' in line.lower()):
                level_filtered.append(line)
                break
            elif level == 'INFO' and not any(x in line for x in ['ERROR', 'WARNING', 'CRITICAL', '✗', '✓']):
                level_filtered.append(line)
                break
    filtered_lines = level_filtered

st.markdown("---")

# Display logs
st.subheader(f"📝 Log Viewer — Showing  ({len(filtered_lines)} lines after filters)")

if not filtered_lines:
    st.info("No logs match the current filters.")
else:
    # Display in a scrollable container with formatting
    log_container = st.container()
    
    with log_container:
        # Use expander for better organization
        with st.expander("View Logs", expanded=True):
            # Create formatted log display
            log_text = ""
            for line in filtered_lines:
                formatted_line, color = format_log_line(line)
                log_text += formatted_line + "\n"
            
            # Display in code block for monospace formatting
            st.code(log_text, language=None)
        
        

# Download logs
st.markdown("---")
st.subheader("💾 Download Logs")

log_content = "".join(filtered_lines)
log_bytes = log_content.encode('utf-8')

st.download_button(
    label="📥 Download Filtered Logs",
    data=log_bytes,
    file_name="pipeline_logs.txt",
    mime="text/plain",
    use_container_width=True
)

st.caption(f"💡 Tip: Use filters to narrow down specific events or errors. Showing {len(filtered_lines)} of {len(log_lines)} total lines.")

# Auto-refresh functionality
if auto_refresh:
    time.sleep(5)
    st.rerun()

# Footer
st.markdown("---")
st.caption("🔄 Logs are read from `logs/pipeline.log` at the project root.")
