import streamlit as st
import time
from worker import process_repo

st.set_page_config(page_title="Autonomous Codebase Documenter", layout="centered")
st.title("🤖 Autonomous Codebase Documenter")
st.caption("Paste any public GitHub URL. Get complete documentation in 5 minutes. No account required.")

github_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/username/repo")

if st.button("Generate Documentation", type="primary", disabled=not github_url):
    with st.status("Starting job...", expanded=True) as status:
        job = process_repo.delay(github_url)
        
        while True:
            # Check if job is ready, meaning it's either succeeded or failed
            if job.ready():
                break
            
            # Update progress based on job state
            if job.state == 'PENDING':
                status.update(label="Waiting in queue...")
            elif job.state == 'PROGRESS':
                meta = job.info
                # Ensure 'stage' and 'progress' keys exist before accessing
                current_stage = meta.get('stage', 'Processing...')
                current_progress = meta.get('progress')
                if current_progress is not None:
                    status.update(label=f"{current_stage} ({current_progress}%)")
                else:
                    status.update(label=f"{current_stage}")
            
            time.sleep(2)
        
        # After job is ready, get the result.
        # Use a try-except block to catch any exceptions re-raised by job.get()
        try:
            # job.get() will re-raise exceptions from the worker or return the task's return value
            result = job.get() 
            print(f"Frontend: Raw result from worker: {result}") # Debug print
            
            # Check if the result is a dictionary containing an error
            if isinstance(result, dict) and result.get('error'):
                st.error(f"❌ Documentation generation failed: {result['error']}")
                status.update(label="Failed!", state="error")
                if result.get('traceback'):
                    st.subheader("Worker Traceback:")
                    st.code(result['traceback'])
            # Check for a successful result with a public_url
            elif isinstance(result, dict) and result.get('public_url'):
                status.update(label="Complete!", state="complete")
                st.success("✅ Documentation generated successfully!")
                st.link_button("View Full Documentation", result['public_url'], type="primary")
            else:
                # Fallback for unexpected result formats
                st.error("❌ An unexpected issue occurred. Please check worker logs.")
                st.json(result) # Display the raw result for debugging
                status.update(label="Failed!", state="error")
        except Exception as e:
            # This catches exceptions that job.get() directly re-raises from the worker
            st.error("❌ An unhandled error occurred during documentation generation.")
            st.exception(e)
            status.update(label="Failed!", state="error")


st.divider()
st.caption("Open source. Runs entirely on free tiers.")