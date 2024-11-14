import os
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

REQUIRED_ENV_VARS = {
    'GROQ_API_KEY': 'Groq API key for LLM processing',
    'SERPAPI_KEY': 'SerpAPI key for web searches',
    'GOOGLE_SHEETS_CREDENTIALS': 'Google Sheets API credentials'
}

def validate_env_vars() -> Dict[str, str]:
    """
    Validate that all required environment variables are set.
    Returns a dictionary of validated environment variables.
    """
    missing_vars = []
    env_vars = {}

    for var, description in REQUIRED_ENV_VARS.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({description})")
        env_vars[var] = value

    if missing_vars:
        raise EnvironmentError(
            "Missing required environment variables:\n" + 
            "\n".join(f"- {var}" for var in missing_vars)
        )

    return env_vars

# Validate environment variables on import
try:
    env_vars = validate_env_vars()
except EnvironmentError as e:
    print(f"Environment Error: {str(e)}")
    env_vars = {}

    