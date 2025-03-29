import os
from dotenv import load_dotenv
from pathlib import Path
from src.Instahyre.instahyre import InstahyreApplicationBot
from src.Naukri.naukri import NaukriApplicationBot
from src.Linkedin.linkedin import LinkedinApplicationBot
from src.meta.logger import get_logger

# Load environment variables
load_dotenv()

# Get the project root dynamically
PROJECT_ROOT = Path(__file__).resolve().parent

# Required environment variables
required_env_vars = {
    "INSTAHYRE_EMAIL": os.getenv("INSTAHYRE_EMAIL"),
    "INSTAHYRE_PASSWORD": os.getenv("INSTAHYRE_PASSWORD"),
    "NAUKRI_EMAIL": os.getenv("NAUKRI_EMAIL"),
    "NAUKRI_PASSWORD": os.getenv("NAUKRI_PASSWORD"),
    "LINKEDIN_EMAIL": os.getenv("LINKEDIN_EMAIL"),
    "LINKEDIN_PASSWORD": os.getenv("LINKEDIN_PASSWORD"),
    "PHONE_NUMBER": os.getenv("PHONE_NUMBER"),
    "SALARY": os.getenv("SALARY"),
    "RATE": os.getenv("RATE"),
    "OUTPUT_FILENAME": os.getenv("OUTPUT_FILENAME"),
}

# Check for missing required variables
missing_vars = [var for var, value in required_env_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

log = get_logger(__name__)

# Helper function to process comma-separated values
def get_list(env_var, default=""):
    return [item.strip() for item in os.getenv(env_var, default).split(",") if item.strip()]

# Load optional variables
positions = get_list("POSITIONS")
locations = get_list("LOCATIONS")

# Convert relative paths to absolute paths
uploads = {
    "Resume": str(PROJECT_ROOT / os.getenv("UPLOAD_RESUME", ""))
}
output_filename = str(PROJECT_ROOT / os.getenv("OUTPUT_FILENAME", "output.csv"))

blacklist_companies = get_list("BLACKLIST_COMPANIES")
blacklist_titles = get_list("BLACKLIST_TITLES")
experience_level = [int(x) for x in get_list("EXPERIENCE_LEVEL") if x.isdigit()]

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

    bot = LinkedinApplicationBot(
        username=required_env_vars["LINKEDIN_EMAIL"],
        password=required_env_vars["LINKEDIN_PASSWORD"],
        phone_number=required_env_vars["PHONE_NUMBER"],
        salary=int(required_env_vars["SALARY"]),
        rate=int(required_env_vars["RATE"]),
        uploads=uploads,
        filename=output_filename,
        blacklist=blacklist_companies,
        blackListTitles=blacklist_titles,
        experience_level=experience_level
    )
    
    bot.start_apply(positions, locations)
