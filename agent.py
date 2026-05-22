import os
import tempfile
import shutil
from typing import Callable, Optional
from git import Repo, GitCommandError
from fnmatch import fnmatch
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from config import *
from storage import upload_docs
import traceback

llm = ChatGroq(model=LLM_MODEL, temperature=0.05)

IMPORTANT_FILE_NAMES = {
    "README.md", "requirements.txt", "package.json", "pyproject.toml",
    "setup.py", "Pipfile", "Dockerfile", "docker-compose.yml",
    "Makefile", "app.py", "main.py", "manage.py", "streamlit_app.py"
}

IMPORTANT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".ipynb", ".md", ".json", ".yaml", ".yml"
}

class AgentState(BaseModel):
    github_url: str
    repo_path: Optional[str] = None
    files: list = Field(default_factory=list)
    architecture: Optional[str] = None
    root_readme: Optional[str] = None
    folder_readmes: dict = Field(default_factory=dict)
    public_url: Optional[str] = None
    progress_callback: Optional[Callable] = None
    repo_tree: Optional[str] = None
    repo_context: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

def update_progress(state, stage, progress):
    if state.progress_callback:
        state.progress_callback(stage, progress)

def clean_github_url(url: str) -> str:
    if "/tree/" in url:
        url = url.split("/tree/")[0]
    if "/blob/" in url:
        url = url.split("/blob/")[0]
    return url.rstrip("/")

def is_important_file(path: str) -> bool:
    name = os.path.basename(path)
    ext = os.path.splitext(path)[1].lower()

    if name in IMPORTANT_FILE_NAMES:
        return True

    if ext in IMPORTANT_EXTENSIONS and (
        path.count(os.sep) <= 2 or
        any(k in path.lower() for k in ["src", "app", "api", "backend", "frontend", "pages", "notebooks"])
    ):
        return True

    return False

def build_repo_tree(file_paths: list[str]) -> str:
    lines = []
    for path in sorted(file_paths):
        depth = path.count(os.sep)
        indent = "  " * depth
        lines.append(f"{indent}- {os.path.basename(path) if depth else path}")
    return "\n".join(lines)

def summarize_context(files: list) -> str:
    important = [f for f in files if is_important_file(f["path"])]
    important = important[:20]

    chunks = []
    for f in important:
        content = f["content"][:2500]
        chunks.append(
            f"\n### FILE: {f['path']}\n"
            f"```text\n{content}\n```"
        )

    return "\n".join(chunks)

def clone_repo(state: AgentState):
    update_progress(state, "Cloning repository", 10)
    temp_dir = tempfile.mkdtemp()

    clean_url = clean_github_url(state.github_url)
    print(f"Agent: Attempting to clone from cleaned URL: {clean_url}")

    try:
        Repo.clone_from(clean_url, temp_dir, depth=1, single_branch=True)
        state.repo_path = temp_dir
    except GitCommandError as e:
        raise ValueError(f"Git clone failed: {e.stderr.strip()}")
    except Exception as e:
        raise ValueError(f"Unexpected error during cloning: {e}")

    return state

def scan_files(state: AgentState):
    update_progress(state, "Scanning and indexing files", 20)
    all_files = []

    for root, dirs, files in os.walk(state.repo_path):
        dirs[:] = [d for d in dirs if not any(fnmatch(d, p) for p in IGNORED_PATTERNS)]

        for file in files:
            if any(fnmatch(file, p) for p in IGNORED_PATTERNS):
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, state.repo_path)

            if os.path.getsize(full_path) > MAX_FILE_SIZE_KB * 1024:
                continue

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                all_files.append({"path": rel_path, "content": content})
            except UnicodeDecodeError:
                continue
            except Exception:
                continue

    state.files = all_files[:MAX_FILES_PER_REPO]
    state.repo_tree = build_repo_tree([f["path"] for f in state.files])
    state.repo_context = summarize_context(state.files)

    if not state.files:
        raise ValueError("No processable files found in the repository.")

    return state

def analyze_architecture(state: AgentState):
    update_progress(state, "Analyzing architecture and dependencies", 40)

    prompt = f"""
You are a senior software engineer analyzing a real code repository.

Repository URL:
{state.github_url}

Directory tree:
{state.repo_tree}

Important file excerpts:
{state.repo_context}

Write an accurate architecture overview with:
1. What this project does
2. Main folders/modules and responsibilities
3. Tech stack and dependencies
4. How the app likely runs
5. Any uncertainty or ambiguity

Rules:
- Use ONLY evidence from the provided files
- If something is unclear, explicitly say "unclear from repository contents"
- Do NOT invent frameworks, commands, features, or deployment details
- Be concrete, not generic
"""

    state.architecture = llm.invoke(prompt).content
    return state

def generate_all_docs(state: AgentState):
    update_progress(state, "Generating documentation", 70)

    root_prompt = f"""
You are generating README.md for a specific repository.

Repository URL:
{state.github_url}

Directory tree:
{state.repo_tree}

Architecture analysis:
{state.architecture}

Important file excerpts:
{state.repo_context}

Write a repository-specific README.md.

Include:
- Project title
- What this repository does
- Tech stack
- Repository structure
- Installation
- How to run
- Important files/folders
- Notes / limitations if parts are unclear

Rules:
- Only mention commands/frameworks that are supported by the provided files
- If run steps are unclear, say so explicitly
- Do not write generic filler
- Do not invent package managers, scripts, endpoints, or architecture
- Use the real repository context above
"""

    state.root_readme = llm.invoke(root_prompt).content

    folders = sorted(set(os.path.dirname(f["path"]) for f in state.files if os.path.dirname(f["path"])))

    for folder in folders[:30]:
        folder_files = [f["path"] for f in state.files if f["path"].startswith(folder + os.sep) or f["path"].startswith(folder + "/")]
        prompt = f"""
You are writing a short README for a specific folder in a repository.

Folder:
{folder}

Files in this folder:
{folder_files[:30]}

Repository architecture summary:
{state.architecture}

Write a concise folder README that explains:
- the role of this folder
- notable files
- how it fits into the project

Only use the provided information.
If unclear, say so.
"""
        state.folder_readmes[folder] = llm.invoke(prompt).content

    return state

def upload_result(state: AgentState):
    update_progress(state, "Uploading documentation", 90)

    full_bundle = {"README.md": state.root_readme or "README generation failed."}

    for folder, content in state.folder_readmes.items():
        full_bundle[f"{folder}/README.md"] = content

    state.public_url = upload_docs(state.github_url, full_bundle)

    if state.repo_path and os.path.exists(state.repo_path):
        shutil.rmtree(state.repo_path, ignore_errors=True)

    return state

workflow = StateGraph(AgentState)

workflow.add_node("clone_repo", clone_repo)
workflow.add_node("scan_files", scan_files)
workflow.add_node("analyze_architecture", analyze_architecture)
workflow.add_node("generate_all_docs", generate_all_docs)
workflow.add_node("upload_result", upload_result)

workflow.set_entry_point("clone_repo")
workflow.add_edge("clone_repo", "scan_files")
workflow.add_edge("scan_files", "analyze_architecture")
workflow.add_edge("analyze_architecture", "generate_all_docs")
workflow.add_edge("generate_all_docs", "upload_result")
workflow.add_edge("upload_result", END)

agent = workflow.compile()

def run_documentation_agent(github_url, progress_callback=None):
    initial_state = AgentState(
        github_url=github_url,
        progress_callback=progress_callback
    )

    try:
        result_state = agent.invoke(initial_state)

        if isinstance(result_state, dict):
            final_public_url = result_state.get("public_url")
        else:
            final_public_url = getattr(result_state, "public_url", None)

        if not final_public_url:
            return {"public_url": None, "error": "Documentation URL was not found in final state."}

        return {"public_url": final_public_url}

    except Exception as e:
        return {
            "public_url": None,
            "error": str(e),
            "traceback": traceback.format_exc()
        }