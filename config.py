import os

# Try to load from Streamlit Secrets first (for Cloud deployment)
try:
    import streamlit as st
    REDIS_URL = st.secrets["redis"]["url"]
    GROQ_API_KEY = st.secrets["groq"]["api_key"]
    R2_ENDPOINT = st.secrets["r2"]["endpoint"]
    R2_ACCESS_KEY = st.secrets["r2"]["access_key"]
    R2_SECRET_KEY = st.secrets["r2"]["secret_key"]
    R2_BUCKET = st.secrets["r2"]["bucket"]
    R2_PUBLIC_DOMAIN = st.secrets["r2"]["public_domain"]
except Exception:
    # Fallback to .env file (for local development)
    from dotenv import load_dotenv
    load_dotenv()
    REDIS_URL = os.getenv("REDIS_URL")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    R2_ENDPOINT = os.getenv("R2_ENDPOINT")
    R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
    R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
    R2_BUCKET = os.getenv("R2_BUCKET", "autodoc")
    R2_PUBLIC_DOMAIN = os.getenv("R2_PUBLIC_DOMAIN")

# Global Config
IGNORED_PATTERNS = [
    '.git', 'node_modules', 'venv', '.venv', 'build', 'dist',
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock',
    '.env', '.gitignore', 'LICENSE', '*.png', '*.jpg', '*.gif', '*.bin',
    '*.exe', '*.zip', '*.tar', '*.pdf'
]

MAX_FILES_PER_REPO = 600
MAX_FILE_SIZE_KB = 256
LLM_MODEL = "llama-3.3-70b-versatile"
