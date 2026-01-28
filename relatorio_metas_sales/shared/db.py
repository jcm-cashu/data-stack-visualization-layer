"""
Database connection layer - DO NOT MODIFY
Supports both local development (snowflake.connector) and 
Snowflake-hosted Streamlit (Snowpark Session).
"""
from typing import Optional, Union, Tuple, Dict, Any

import pandas as pd
import streamlit as st

# Import config from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SNOWFLAKE_CONFIG


# Cache the environment detection result
_RUNNING_IN_SNOWFLAKE: Optional[bool] = None


def is_running_in_snowflake() -> bool:
    """Detect if running inside Snowflake Streamlit environment."""
    global _RUNNING_IN_SNOWFLAKE
    
    if _RUNNING_IN_SNOWFLAKE is not None:
        return _RUNNING_IN_SNOWFLAKE
    
    try:
        from snowflake.snowpark.context import get_active_session
        get_active_session()
        _RUNNING_IN_SNOWFLAKE = True
    except Exception:
        _RUNNING_IN_SNOWFLAKE = False
    
    return _RUNNING_IN_SNOWFLAKE


def _get_snowpark_session():
    """Get the active Snowpark session (for Snowflake-hosted environment)."""
    from snowflake.snowpark.context import get_active_session
    return get_active_session()


def _get_snowflake_connection():
    """Create a new Snowflake connection (for local development)."""
    import snowflake.connector
    
    # Filter out None values from config
    conn_params = {k: v for k, v in SNOWFLAKE_CONFIG.items() if v is not None}
    
    # Check if required params are present
    required_params = ["user", "password", "account"]
    missing = [p for p in required_params if p not in conn_params or not conn_params[p]]
    if missing:
        raise ValueError(f"Missing required Snowflake config: {missing}. Check your .env file.")
    
    conn = snowflake.connector.connect(**conn_params)
    return conn


@st.cache_resource(show_spinner=False)
def get_connection():
    """Get a cached Snowflake connection (local development only)."""
    return _get_snowflake_connection()


def _format_sql_with_params(sql: str, params: Union[Tuple[Any, ...], Dict[str, Any]]) -> str:
    """
    Format SQL query with parameters for Snowpark.
    Snowpark's .sql() doesn't support parameterized queries,
    so we need to format params directly into the SQL string.
    """
    if isinstance(params, dict):
        # Named parameters
        for key, value in params.items():
            placeholder = f":{key}"
            if isinstance(value, str):
                sql = sql.replace(placeholder, f"'{value}'")
            elif isinstance(value, bool):
                sql = sql.replace(placeholder, str(value).upper())
            elif value is None:
                sql = sql.replace(placeholder, "NULL")
            else:
                sql = sql.replace(placeholder, str(value))
    elif isinstance(params, (tuple, list)):
        # Positional parameters (replace %s or ? placeholders)
        for value in params:
            if isinstance(value, str):
                replacement = f"'{value}'"
            elif isinstance(value, bool):
                replacement = str(value).upper()
            elif value is None:
                replacement = "NULL"
            else:
                replacement = str(value)
            
            # Replace first occurrence of %s or ?
            if "%s" in sql:
                sql = sql.replace("%s", replacement, 1)
            elif "?" in sql:
                sql = sql.replace("?", replacement, 1)
    
    return sql


@st.cache_data(ttl=60, show_spinner=False)
def run_query(
    sql: str,
    params: Optional[Union[Tuple[Any, ...], Dict[str, Any]]] = None,
    db_path: Optional[str] = None,  # Kept for backward compatibility, ignored
) -> pd.DataFrame:
    """
    Execute a SQL query and return results as a DataFrame.
    
    Automatically detects the runtime environment:
    - Snowflake-hosted Streamlit: Uses Snowpark Session
    - Local development: Uses snowflake.connector
    """
    if is_running_in_snowflake():
        # Running in Snowflake Streamlit - use Snowpark Session
        session = _get_snowpark_session()
        
        if params is not None:
            sql = _format_sql_with_params(sql, params)
        
        return session.sql(sql).to_pandas()
    else:
        # Running locally - use snowflake.connector
        conn = get_connection()
        cursor = conn.cursor()
        try:
            if params is not None:
                cursor.execute(sql, params)
            else:
                print(sql)
                cursor.execute(sql)
            df = cursor.fetch_pandas_all()
        finally:
            cursor.close()
        return df
