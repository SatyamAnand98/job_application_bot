import os
from dotenv import load_dotenv

from instahyre import InstahyreApplicationBot
from naukri import NaukriApplicationBot

load_dotenv()

# Required environment variables
required_env_vars = {
    "INSTAHYRE_EMAIL": os.getenv("INSTAHYRE_EMAIL"),
    "INSTAHYRE_PASSWORD": os.getenv("INSTAHYRE_PASSWORD"),
    "NAUKRI_EMAIL": os.getenv("NAUKRI_EMAIL"),
    "NAUKRI_PASSWORD": os.getenv("NAUKRI_PASSWORD"),
}

# Check for missing environment variables
missing_vars = [var for var, value in required_env_vars.items() if not value]

if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}")

if __name__ == "__main__":
    instahyre_bot = InstahyreApplicationBot(
        email=required_env_vars["INSTAHYRE_EMAIL"],
        password=required_env_vars["INSTAHYRE_PASSWORD"],
        limit=30
    )
    naukri_bot = NaukriApplicationBot(
        email=required_env_vars["NAUKRI_EMAIL"],
        password=required_env_vars["NAUKRI_PASSWORD"]
    )

    instahyre_bot.run()
    naukri_bot.run()
