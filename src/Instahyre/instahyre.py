"""Module imports"""
import time
import requests
from src.meta.logger import get_logger

logger = get_logger("instahyre")


class InstahyreApplicationBot:
    """JobApplicationBot to apply for instahyre jobs automatically"""

    BASE_URL = "https://www.instahyre.com/api/v1"
    APPLY_URL = f"{BASE_URL}/candidate_opportunity/apply"
    OPPORTUNITY_URL = f"{BASE_URL}/candidate_opportunity"
    REFERRER_URL = "https://www.instahyre.com/candidate/opportunities/?matching=true"

    def __init__(self, email, password, limit=30):
        self.email = email
        self.password = password
        self.limit = limit
        self.session = self._get_session()
        self.csrftoken, self.sessionid = self._login()
        self.headers, self.cookies = self._set_headers_cookies()

    def _get_session(self):
        if not hasattr(self, "_session"):
            self._session = requests.Session()
        return self._session

    def _login(self):
        logger.info("🔄 Attempting Instahyre login...")

        login_url = f"{self.BASE_URL}/user_login"
        payload = {"email": self.email, "password": self.password}

        response = self.session.post(login_url, json=payload)
        if response.status_code != 201:
            logger.error("❌ Login failed: %s", response.text)
            raise Exception("Login failed")

        logger.info("✅ Login successful!")
        cookies = self.session.cookies.get_dict()
        csrftoken = cookies.get("csrftoken", "")
        sessionid = cookies.get("sessionid", "")

        if not csrftoken or not sessionid:
            logger.error("❌ Error: Missing CSRF token or Session ID.")
            raise Exception("CSRF token or Session ID missing")

        return csrftoken, sessionid

    def _set_headers_cookies(self):
        cookies = {
            "csrftoken": self.csrftoken,
            "sessionid": self.sessionid,
        }

        headers = {
            "x-csrftoken": self.csrftoken,
            "Content-Type": "application/json",
            "referer": self.REFERRER_URL,
        }

        return headers, cookies

    def fetch_jobs(self, offset=0, retries=3):
        for attempt in range(retries):
            logger.info("🔍 Fetching jobs (offset: %d, limit: %d)... Attempt %d",
                        offset, self.limit, attempt + 1)

            url = f"{self.OPPORTUNITY_URL}?limit={self.limit}&offset={offset}"
            response = self.session.get(
                url, headers=self.headers, cookies=self.cookies)

            if response.status_code == 200:
                data = response.json()
                jobs = data.get("objects", [])
                total_jobs = data.get("meta", {}).get("total_count", 0)

                if jobs:
                    logger.info(
                        "✅ Fetched %d jobs (Total jobs available: %d)", len(jobs), total_jobs)
                    return jobs, total_jobs
                else:
                    logger.warning(
                        "⚠️ Received empty job list despite valid response.")

            else:
                logger.error("❌ Failed to fetch jobs: %s", response.text)

            logger.info("🔄 Retrying in 5 seconds...")
            time.sleep(5)

        logger.error("🚨 Maximum retries reached. No jobs fetched.")
        return [], 0

    def apply_to_job(self, job):
        score = float(job.get("score", 0))
        job_id = job["id"]
        company_name = job["employer"]["company_name"]
        opportunity_url = "https://www.instahyre.com" + \
            job["job"]["opportunity_url"]

        if score >= 5:
            logger.info("-" * 50)
            logger.info("🟢 Applying for %s: %s (Score: %.2f)",
                        company_name, opportunity_url, score)
            logger.info("-" * 50)

        logger.info("🟢 Applying for %s: %s (Score: %.2f)",
                    company_name, opportunity_url, score)

        payload = {"id": job_id, "is_interested": True,
                   "is_activity_page_job": True}
        response = self.session.post(
            self.APPLY_URL, json=payload, headers=self.headers, cookies=self.cookies)

        if response.status_code == 200:
            logger.info("✅ Successfully applied for %s", company_name)
        else:
            logger.error("❌ Failed to apply for %s: %s",
                         company_name, response.text)

    def run(self):
        offset = 0
        total_jobs = None

        while total_jobs is None or offset < total_jobs:
            logger.info("🚀 Fetching jobs from offset: %d", offset)
            jobs, total_jobs = self.fetch_jobs(offset)

            if not jobs:
                logger.info("✅ No more jobs to apply for. Stopping.")
                break

            for job in jobs:
                self.apply_to_job(job)
                time.sleep(2)

            offset += len(jobs)

            logger.info(
                "🔄 Moving to next batch (Offset: %d / Total: %d)", offset, total_jobs)

            if offset >= total_jobs:
                logger.info("✅ All jobs processed.")
                break

        return "Done"
