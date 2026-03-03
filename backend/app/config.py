import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "mindmirror.db"
FAISS_INDEX_PATH = DATA_DIR / "faiss_index" / "index.faiss"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "")
LLM_MODEL = "claude-sonnet-4-6"

EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
EMBEDDING_DIM = 512

FAISS_TOP_K = 12
MAX_CONTEXT_TOKENS = 2000
SHORT_MEMORY_ROUNDS = 15
ROLLING_SUMMARY_INTERVAL = 7  # every N rounds

DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "faiss_index").mkdir(parents=True, exist_ok=True)
