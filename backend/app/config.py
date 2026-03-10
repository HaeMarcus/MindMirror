import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DB_PATH = DATA_DIR / "mindmirror.db"
FAISS_INDEX_DIR = DATA_DIR / "faiss_index"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "")
LLM_MODEL = "claude-sonnet-4-6"

EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
EMBEDDING_DIM = 512

FAISS_TOP_K = 12
MAX_CONTEXT_TOKENS = 2000
SHORT_MEMORY_ROUNDS = 3           # recent conversation rounds sent to LLM
ROLLING_SUMMARY_INTERVAL = 5      # update rolling summary every N rounds
PROFILE_UPDATE_INTERVAL = 10      # update user profile every N rounds
ROLLING_SUMMARY_MAX_CHARS = 500   # rolling summary length target

APP_VERSION = os.getenv("APP_VERSION", "0.2.0")  # track which version generated each response

DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "faiss_index").mkdir(parents=True, exist_ok=True)
