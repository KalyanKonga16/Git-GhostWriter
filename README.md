# 👻 Git-GhostWriter

### Autonomous Codebase Documenter

*Transform any GitHub repository into intelligent, structured documentation using AI.*

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B.svg?logo=streamlit&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A.svg?logo=celery&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C.svg?logo=langchain&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Overview

**Git-GhostWriter** is a distributed, asynchronous application that clones public GitHub repositories, analyzes their structure using a LangGraph AI agent, and generates production-ready README documentation.

Built with a **Local-First Cloud-Hybrid** architecture: your machine handles all compute (UI + Worker), while free-tier cloud services provide the message broker (Redis), AI brain (Groq), and storage (R2).

---

## 🏗️ System Architecture

The system follows a strict **async producer-consumer pattern** running entirely on your local machine, connected to cloud APIs.

```text
┌─────────────────────────────────────────────────────────────┐
│  🖥️  LOCAL MACHINE                                          │
│                                                             │
│  ┌──────────────────┐         ┌──────────────────────┐     │
│  │  🎨 Streamlit    │ ──────► │  ☁️  Redis Cloud     │     │
│  │  Frontend        │         │  (Message Broker)    │     │
│  │  localhost:8501  │ ◄────── │                      │     │
│  └──────────────────┘         └──────────┬───────────┘     │
│                                          │                  │
│  ┌──────────────────┐         ┌──────────▼───────────┐     │
│  │  📄 Generated    │         │  ⚙️  Celery Worker   │     │
│  │  Documentation   │ ◄────── │  (Local Process)     │     │
│  │  (View in Browser│         │                      │     │
│  └──────────────────┘         └──────────┬───────────┘     │
└──────────────────────────────────────────│──────────────────┘
                                           │
                                           ▼
                          ┌──────────────────────────────────┐
                          │  🧠 LangGraph Agent Pipeline     │
                          │  1. Clone Repo (GitPython)       │
                          │  2. Scan Files (Local FS)        │
                          │  3. Analyze (Groq API)           │
                          │  4. Generate (Groq API)          │
                          │  5. Upload (R2 API)              │
                          └──────────────────┬───────────────┘
                                             │
                          ┌──────────────────▼───────────────┐
                          │  ☁️  Cloudflare R2               │
                          │  (Public Doc Storage)            │
                          └──────────────────────────────────┘
```

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **⚡ Async Processing** | Celery queue prevents UI freezing during long documentation jobs. |
| **🧠 Contextual AI** | Uses actual file contents and tree structure, not just repo names. |
| **📂 Hierarchical Docs** | Generates both root README and individual folder READMEs. |
| **🔒 Secret Safety** | `.env` based configuration; no keys committed to Git. |
| **💸 100% Free Ops** | Uses free tiers for Redis, Groq, and R2. |

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | Streamlit | Interactive web UI |
| **Queue** | Celery + Redis Cloud | Async task distribution |
| **Workflow** | LangGraph | Multi-step AI pipeline state machine |
| **LLM** | Groq (Llama 3.3 70B) | Code analysis & text generation |
| **Git** | GitPython | Repository cloning |
| **Storage** | Cloudflare R2 (boto3) | Public hosting of generated markdown |

---

## 📁 Project Structure

```text
git-ghostwriter/
├── 📄 frontend.py          # Streamlit UI entry point
├── ⚙️  worker.py           # Celery worker definition
├── 🧠 agent.py             # LangGraph nodes & state logic
├── ☁️  storage.py          # R2/S3 upload utilities
├── ⚙️  config.py           # Environment & constants loader
├── 📋 requirements.txt     # Python dependencies
├── 🔒 .env.example         # Template for secrets
└── 🚫 .gitignore           # Excludes venv/, .env, __pycache__
```

---

## 🚀 Quick Start

### 1. Prerequisites (Free Accounts)
You need API keys from these free services:
- **[Redis Cloud](https://redis.com/try-free/)**: Get a Redis URL.
- **[Groq](https://console.groq.com/)**: Get an API Key.
- **[Cloudflare R2](https://www.cloudflare.com/developer-platform/r2/)**: Create a bucket, get S3-compatible keys.

### 2. Local Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/Git-GhostWriter.git
cd Git-GhostWriter

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root:

```env
REDIS_URL=redis://default:PASSWORD@HOST:PORT
GROQ_API_KEY=gsk_YOUR_KEY_HERE
R2_ENDPOINT=https://ACCOUNT_ID.r2.cloudflarestorage.com
R2_ACCESS_KEY=YOUR_ACCESS_KEY
R2_SECRET_KEY=YOUR_SECRET_KEY
R2_BUCKET=autodoc
R2_PUBLIC_DOMAIN=https://pub-xxx.r2.dev
```

---

## ▶️ Usage

**Requires two terminals** running simultaneously.

### Terminal 1: Start the Worker
```bash
celery -A worker worker --loglevel=info --pool=solo
```
> **Note:** `--pool=solo` is required for Windows compatibility.

### Terminal 2: Start the Frontend
```bash
streamlit run frontend.py
```

Open `http://localhost:8501`, paste a GitHub URL, and click **Generate**.

---

## ⚠️ Deployment Note: Local-First Design

This application is designed as a **Local-First Cloud-Hybrid** system.

| Component | Location | Reason |
| :--- | :--- | :--- |
| **Frontend** | Local (`localhost`) | Streamlit Cloud cannot reach a local Celery worker behind NAT. |
| **Worker** | Local | Free-tier cloud platforms (Fly.io, Render) no longer offer reliable always-on background workers without payment or verification barriers. |
| **External APIs** | Cloud | Redis, Groq, and R2 provide managed infrastructure without hosting compute. |

To use this tool, simply keep both terminal windows open while processing jobs.

---

## 🔮 Future Roadmap

- [ ] GitHub Actions integration (serverless worker trigger).
- [ ] Support for private repositories (PAT authentication).
- [ ] Caching layer for repeated repo analysis.
- [ ] Migration to serverless functions when feasible free tiers emerge.

---

## 📜 License

MIT License — See `LICENSE` file for details.

---

<p align="center">
  <b>Built with 🖤 by Kalyan Konga</b><br>
  <a href="https://github.com/KalyanKonga16">@KalyanKonga16</a>
</p>
