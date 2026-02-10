"""
Configuration loader for the Cacau Show dashboard.
Reads settings from environment variables and .env file.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from the app directory
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path)

# Snowflake configuration
SNOWFLAKE_CONFIG = {
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA", "FACT_DATA"),
}
