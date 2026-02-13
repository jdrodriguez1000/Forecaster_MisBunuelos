from .connectors.supabase_connector import get_supabase_client
import pandas as pd

def load_data(table_name: str) -> pd.DataFrame:
    """
    Loads data from a Supabase table into a Pandas DataFrame.
    
    Args:
        table_name (str): The name of the table to load.
        
    Returns:
        pd.DataFrame: The data from the table.
    """
    supabase = get_supabase_client()
    response = supabase.table(table_name).select("*").execute()
    
    if not response.data:
        return pd.DataFrame()
        
    return pd.DataFrame(response.data)
