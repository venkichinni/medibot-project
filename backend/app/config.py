import os  # Provides functions to read environment variables from the operating system
from dotenv import load_dotenv  # Loads variables from the .env file into the Python environment

load_dotenv()  # Reads the .env file so the values below can be accessed with os.getenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # API key used to connect to Groq LLM
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")  # Groq model name used for answer generation

QDRANT_URL = os.getenv("QDRANT_URL")  # Qdrant Cloud cluster endpoint URL
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # API key used to authenticate with Qdrant Cloud
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "medibot_docs")  # Qdrant collection name for storing document chunks

DATA_DIR = os.getenv("DATA_DIR", "backend/data/mediassist_data")  # Folder path where PDFs and Markdown files are stored
DB_PATH = os.getenv("DB_PATH", "backend/data/mediassist_data/db/mediassist.db")  # SQLite database path used for SQL RAG

HF_TOKEN = os.getenv("HF_TOKEN")  # Hugging Face token used for free model downloads