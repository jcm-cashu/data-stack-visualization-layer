"""
Configuration - Snowflake Connection Settings

This file contains Snowflake connection configuration.
Edit this file to configure your Snowflake credentials.

For local development:
- Create a .env file in this directory with your credentials
- Or set environment variables directly

For Snowflake-hosted Streamlit:
- The connection is handled automatically via Snowpark Session
- These settings are only used for local development
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from the app directory
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path)
load_dotenv('/Users/joaomagalhaes/cashu/.env')

# Snowflake configuration
SNOWFLAKE_CONFIG = {
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "private_key_file": os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE"),
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA", "FACT_DATA"),
}
