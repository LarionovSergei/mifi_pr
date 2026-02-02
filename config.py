import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CHROMA_PATH = os.path.join(os.getcwd(), "chroma_db")
    # Using a small, fast model for embeddings
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2" 
    
    # Habr RSS feed for tech articles
    HABR_RSS_URL = "https://habr.com/ru/rss/hubs/python/all/?fl=ru"
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

config = Config()
