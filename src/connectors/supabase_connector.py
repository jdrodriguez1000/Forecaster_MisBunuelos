import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    """
    Connects to the Supabase database using credentials from environment variables.
    
    Returns:
        Client: The Supabase client object.
        
    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY are not set in the environment variables.
    """
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("Environment variables SUPABASE_URL and SUPABASE_KEY must be set.")
        
    return create_client(url, key)
