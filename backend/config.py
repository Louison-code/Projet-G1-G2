"""Configuration centralisée de l'application."""
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/base_reindustrialisation.db")
LLM_MODE = os.getenv("LLM_MODE", "local")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:11434")
LLM_MODELE = os.getenv("LLM_MODELE", "llama3.2")
