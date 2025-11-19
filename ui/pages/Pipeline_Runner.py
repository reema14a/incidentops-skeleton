"""
Pipeline Runner Page

Allows users to execute the IncidentOps pipeline with log input or file upload.
Displays agent outputs in collapsible sections and provides JSON download.
"""

import streamlit as st
import json
import io
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from orchestrator.orchestrator import run_pipeline


def run_pipeline_with_input(log_text: str = None, file_input: Any = None) -> Dict:
    """
    Execute the pipeline with optional log input.
    
    Args:
        log_text: Raw log text input
        file_input: Uploaded file object
        
    Returns:
        Dict: Complete pipeline output including all agent results
    """
    import tempfile
    import os
    
    temp_file_path = None
    
    try:
        # If we have log text input (from text area or uploaded file), save it to a temp file
        if log_text and log_text.strip():
            # Create a temporary file to store the log data
            temp_fd, temp_file_path = tempfile.mkstemp(suffix='.txt', prefix='pipeline_input_')
            
            # Write the log text to the temp file
            with os.fdopen(temp_fd, 'w') as temp_file:
                temp_file.write(log_text)
            
            # Execute the backend pipeline with the temp file path
            result = run_pipeline(log_file_path=temp_file_path)
        else:
            # No input provided, use default behavior
            result = run_pipeline()
        
        # Wrap result in UI-friendly format
        # Note: result structure is {governance_output: {...}, notification_status: ..., notifications_sent: [...]}
        pipeline_output = {
            'status': 'success',
            'final_output': result
        }
        
        return pipeline_output
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }
    finally:
        # Clean up temporary file if it was created
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                # Log but don't fail if cleanup fails
                print(f"Warning: Failed to clean up temp file {temp_file_path}: {e}")


# Page configuration
st.title("🚀 Pipeline Runner")
st.markdown("Execute the IncidentOps pipeline with log input or file upload.")
st.markdown("---")

# Input section
st.subheader("📝 Input")

# Log text input
log_text = st.text_area(
    "Enter log data:",
    height=150,
    placeholder="Paste your log data here...\nExample:\n2024-01-15 10:23:45 ERROR Database connection failed\n2024-01-15 10:24:12 WARN High memory usage detected",
    help="Enter raw log data to be processed by the pipeline"
)

# File upload
uploaded_file = st.file_uploader(
    "Or upload a log file:",
    type=['txt', 'log'],
    help="Upload a text or log file containing incident data"
)

# Display file content if uploaded
if uploaded_file is not None:
    file_content = uploaded_file.read().decode('utf-8')
    st.info(f"📄 File uploaded: {uploaded_file.name} ({len(file_content)} characters)")
    with st.expander("View file content"):
        st.text(file_content[:1000] + ("..." if len(file_content) > 1000 else ""))

st.markdown("---")

# Run button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button("▶️ Run Pipeline", type="primary", use_container_width=True)

# Execute pipeline
if run_button:
    with st.spinner("🔄 Running pipeline... This may take a moment."):
        # Determine input source
        input_text = None
        input_file = None
        
        if uploaded_file is not None:
            input_file = uploaded_file
            input_text = file_content
        elif log_text.strip():
            input_text = log_text
        
        # Run pipeline
        result = run_pipeline_with_input(log_text=input_text, file_input=input_file)
        
        # Store result in session state
        st.session_state['pipeline_result'] = result

# Display results if available
if 'pipeline_result' in st.session_state:
    result = st.session_state['pipeline_result']
    
    st.markdown("---")
    st.subheader("📊 Pipeline Results")
    
    # Status indicator
    if result.get('status') == 'success':
        st.success("✅ Pipeline completed successfully!")
    else:
        st.error(f"❌ Pipeline failed: {result.get('error', 'Unknown error')}")
        st.stop()
    
    # Extract final output from orchestrator
    final_output = result.get('final_output', {})
    
    # Agent outputs in collapsible sections
    st.markdown("### Pipeline Output")
    
    # Governance Analysis (from final output)
    with st.expander("⚖️ Governance & Risk Analysis", expanded=True):
        governance_output = final_output.get("governance_output", {})
        gov = governance_output.get("governance_analysis")

        if gov:
            st.markdown("**Governance Analysis:**")

            risk = gov.get('risk', 'unknown')
            if risk.lower() == 'high':
                st.error(f"🔴 Risk Level: {risk}")
            elif risk.lower() == 'medium':
                st.warning(f"🟡 Risk Level: {risk}")
            else:
                st.success(f"🟢 Risk Level: {risk}")

            st.write(f"**Escalation Category:** {gov.get('escalation_category', 'N/A')}")

            st.write(f"**Escalation Details:** {gov.get('escalation', 'N/A')}")

            if gov.get('compliance_issues'):
                st.write(f"**Compliance Issues:** {', '.join(gov['compliance_issues'])}")

            if gov.get('commentary'):
                st.markdown("**Commentary:**")
                st.write(gov['commentary'])

            with st.expander("View Full Governance Data"):
                st.json(gov)
        else:
            st.info("No governance data available")

    
    # Audit Summary (from final output)
    with st.expander("📝 Audit Summary", expanded=False):
        governance_output = final_output.get("governance_output", {})
        audit = governance_output.get("audit_summary")

        if audit:
            st.markdown("**Audit Trail:**")
            st.write(f"- Status: {audit.get('status', 'N/A')}")
            st.write(f"- Count: {audit.get('count', 0)}")
            st.write(f"- Timestamp: {audit.get('timestamp', 'N/A')}")

            with st.expander("View Full Audit Data"):
                st.json(audit)
        else:
            st.info("No audit data available")

    
    # Notification Status (from final output)
    with st.expander("📬 Notification Delivery", expanded=False):
        notif_status = final_output.get('notification_status', 'N/A')
        notifications_sent = final_output.get('notifications_sent', [])
        
        st.markdown("**Notification Status:**")
        st.write(f"- Status: {notif_status}")
        st.write(f"- Notifications Sent: {len(notifications_sent)}")
        
        if notifications_sent:
            st.markdown("**Delivery Details:**")
            for idx, sent in enumerate(notifications_sent, 1):
                st.write(f"{idx}. Channel: {sent.get('channel', 'N/A')}, Status: {sent.get('status', 'N/A')}")
        
        # Show full JSON
        with st.expander("View Full Notification Data"):
            st.json(final_output)
    
    # Download section
    st.markdown("---")
    st.subheader("💾 Download Results")
    
    # Prepare JSON for download
    json_output = json.dumps(final_output, indent=2)
    json_bytes = json_output.encode('utf-8')
    
    st.download_button(
        label="📥 Download JSON Output",
        data=json_bytes,
        file_name="pipeline_output.json",
        mime="application/json",
        use_container_width=True
    )
    
    st.caption("Download the complete pipeline output as JSON for further analysis or record-keeping.")

# Footer
st.markdown("---")
st.caption("💡 Tip: The pipeline processes logs through 7 sequential agents for comprehensive incident management.")

