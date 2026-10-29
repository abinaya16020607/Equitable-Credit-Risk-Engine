import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("CRITICAL ERROR: MONGO_URI environment variable is missing in .env")

DB_NAME = os.getenv("DB_NAME", "equitable_credit_db")

# Initialize MongoClient with a 3-second timeout for rapid failover / health verification
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client[DB_NAME]

# Collections
applicants_collection = db["Applicants"]
predictions_collection = db["Predictions"]

def check_db_connection() -> bool:
    """Verifies that MongoDB is active and accepting connections."""
    try:
        client.admin.command("ping")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False
