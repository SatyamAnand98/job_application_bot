# Job Scraper Bots

This project automates job searching by logging into multiple job portals and fetching job listings.

## 🔑 API Key Setup

To use the bot, you need a **GEMINI API Key**. Generate your API key by clicking the link below:

[Generate GEMINI_API_KEY](https://aistudio.google.com/app/apikey)

Once generated, add it to your environment variables:

```sh
export GEMINI_API_KEY=your_api_key_here
```

## 📦 Installation

Clone the repository:

```
git clone https://github.com/your-repo/job-scraper.git
cd job-scraper
```

Install dependencies:

```
pip install -r requirements.txt
```

🚀 Running the Bots

Start the bot by running:

```
python main.py
```

This will log in to the job portals and fetch job listings automatically.

📝 Logs

Logs for each bot are stored separately:

Instahyre logs → logs/instahyre.log
Naukri logs → logs/naukri.log
To monitor logs in real-time, use:

```
tail -f logs/instahyre.log
tail -f logs/naukri.log
```

🛠 Troubleshooting

Ensure your GEMINI_API_KEY is correctly set.
If dependencies fail to install, try:

```
pip install --upgrade pip
pip install -r requirements.txt
```

If logs are duplicated, check logger.py for duplicate handlers.
Enjoy automated job hunting! 🚀
