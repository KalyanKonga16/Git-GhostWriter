import os
from dotenv import load_dotenv
load_dotenv()

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

# Services
REDIS_URL = os.getenv("REDIS_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_BUCKET = os.getenv("R2_BUCKET", "autodoc")
R2_PUBLIC_DOMAIN = os.getenv("R2_PUBLIC_DOMAIN")