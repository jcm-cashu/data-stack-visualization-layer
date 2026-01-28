"""
Configuration - Snowflake Connection Settings

This file contains Snowflake connection configuration.

For local development:
- Create a .env file in this directory with your credentials
- Or set environment variables directly

For Snowflake-hosted Streamlit:
- The connection is handled automatically via Snowpark Session
- These settings are only used for local development
"""
import os
from pathlib import Path

# Try to load .env file for local development
# This will silently fail in Snowflake-hosted environments where dotenv isn't installed
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    # python-dotenv not installed (Snowflake-hosted environment)
    pass

load_dotenv('/home/joao/.env')

# Snowflake configuration (only used for local development)
# In Snowflake-hosted environments, the Snowpark Session is used instead
SNOWFLAKE_CONFIG = {
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA", "FACT_DATA"),
}
