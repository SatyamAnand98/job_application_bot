"""Module imports"""
from dotenv import load_dotenv
import os
import urllib.parse
from datetime import datetime
import requests
from src.meta.logger import get_logger

from src.meta.askAI import ai_agent

logger = get_logger("naukri")

load_dotenv(override=True)


class NaukriApplicationBot:

    BASE_URL = "https://www.naukri.com"
    LOGIN_SUBDIRECTORY = "/central-login-services/v1/login"
    SEARCH = "/jobapi/v3/search"
    
    if os.getenv('NAUKRI_DESIGNATION_COMPANY') and len(os.getenv('NAUKRI_DESIGNATION_COMPANY')) > 0:
        keyword = {
            "keyword": os.getenv('NAUKRI_DESIGNATION_COMPANY'),
            "pageNo": 1,
            "noOfResults": 20,
            "k": os.getenv('NAUKRI_DESIGNATION_COMPANY'),
            "searchType": "adv"
        }
        
        if os.getenv('NAUKRI_LOCATION') and len(os.getenv('NAUKRI_LOCATION')) > 0:
            keyword["location"] = os.getenv('NAUKRI_LOCATION')
            keyword["l"] = os.getenv('NAUKRI_LOCATION')
            keyword["seoKey"] = f"{'-'.join([item.strip().replace(' ', '-').lower() for item in os.getenv('NAUKRI_DESIGNATION_COMPANY').split(',')])}-jobs-in-{os.getenv('NAUKRI_LOCATION').split(',')[0].replace(' ', '-').lower()}"
        else:
            keyword["seoKey"] = f"{'-'.join([item.strip().replace(' ', '-').lower() for item in os.getenv('NAUKRI_DESIGNATION_COMPANY').split(',')])}-jobs"
        RECOMMENDED_JOBS = f'{SEARCH}/?{urllib.parse.urlencode(keyword)}'
    else:
        RECOMMENDED_JOBS = "/jobapi/v2/search/recom-jobs"
    
    APPLY = "/cloudgateway-workflow/workflow-services/apply-workflow/v1/apply"
    RESPONSE = "/cloudgateway-chatbot/chatbot-services/botapi/v5/respond"

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = self._get_session()
        self.bearer_token, self.nkparam = self._login()
        self.count = 0
        self.pageNo = 1
        self.number_of_jobs = 0
        self.applied_jobs_count = 0

    def _get_session(self):
        if not hasattr(self, "_session"):
            self._session = requests.Session()
        return self._session

    def _login(self):
        logger.info("🔄 Attempting Naukri login...")

        login_url = self.BASE_URL + self.LOGIN_SUBDIRECTORY
        payload = {
            "username": self.email,
            "password": self.password,
            "isLoginByEmail": True
        }

        headers = {
            'appid': '103',
            'systemid': 'jobseeker',
            'Content-Type': 'application/json'
        }

        response = self.session.post(login_url, headers=headers, json=payload)

        if response.status_code != 200:
            logger.error("❌ Login failed: %s", response.text)
            raise Exception("Login failed")

        logger.info("✅ Login successful!")

        data = response.json()
        cookies = data['cookies']

        # Extract nauk_at (Bearer token)
        bearer_token = next((cookie['value'] for cookie in cookies if cookie['name'] == 'nauk_at'), None)

        # Extract nkparam (NKWAP value)
        nkparam = next((cookie['value'] for cookie in cookies if cookie['name'] == 'NKWAP'), None)

        return bearer_token, nkparam

    def recommended_jobs(self):
        logger.info("🔍 Fetching jobs")
        formatted_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "clusterSplitDate": {
                "apply": formatted_datetime,
                "preference": "1980-01-01 05:30:00",
                "profile": "1980-01-01 05:30:00",
                "similar_jobs": "1980-01-01 05:30:00"
            },
            "searches": None
        }
        url = self.BASE_URL + self.RECOMMENDED_JOBS

        headers = {
            "appid": "109",
            "systemid": "Naukri",
            "nkparam": self.nkparam
        }

        if "/jobapi/v2/search/recom-jobs" in url:
            response = self.session.get(url=url, headers=headers, json=payload)
        else:
            # find pageNo and update the url using the keyword
            if self.keyword.get("pageNo") is not None:
                self.keyword["pageNo"] = self.pageNo
                self.keyword["noOfResults"] = 20
                self.keyword["k"] = os.getenv('NAUKRI_DESIGNATION_COMPANY')
                self.keyword["l"] = os.getenv('NAUKRI_LOCATION')
                self.keyword["seoKey"] = f"{'-'.join([item.strip().replace(' ', '-').lower() for item in os.getenv('NAUKRI_DESIGNATION_COMPANY').split(',')])}-jobs-in-{os.getenv('NAUKRI_LOCATION').split(',')[0].replace(' ', '-').lower()}"
            else:
                logger.error("❌ Page number not found in keyword")
                return []
            url = self.BASE_URL + self.SEARCH + "/?" + urllib.parse.urlencode(self.keyword)
            # payload = {
            #     "clusterSplitDate": {
            #         "apply": formatted_datetime,
            #         "preference": "1980-01-01 05:30:00",
            #         "profile": "1980-01-01 05:30:00",
            #         "similar_jobs": "1980-01-01 05:30:00"
            #     },
            #     "searches": None
            # }
            # headers = {
            #     "appid": "109",
            #     "systemid": "Naukri",
            #     "nkparam": self.nkparam,
            #     "Content-Type": "application/json"
            # }
            response = self.session.get(url=url, headers=headers)

        if response.status_code != 200:
            logger.error("❌ Failed to fetch jobs: %s", response.text)

        data = response.json()

        if self.number_of_jobs == 0:
            self.number_of_jobs = data["noOfJobs"]
        jobs = data["jobDetails"]

        if not jobs:
            logger.warning(
                "⚠️ Received empty job list despite valid response.")
        else:
            logger.info(
                "✅ Total jobs available: %d", self.number_of_jobs)

        return jobs

    def apply_to_job(self, job):
        job_id = job["jobId"]
        job_title = job["title"]
        company_name = job["companyName"]
        skills = job["tagsAndSkills"]
        job_url = self.BASE_URL + job["jdURL"]

        logger_data = {
            "company_name": company_name,
            "title": job_title,
            "job_url": job_url,
            "skills": skills
        }
        logger.info(
            f"✅ Applying for {company_name} and data is: {logger_data}")
        try:
            url = self.BASE_URL + self.APPLY
            payload = {
                "strJobsarr": [job_id],
                "applyTypeId": "107",
                "applySrc": "----F-0-1---"
            }
            headers = {
                "appid": "121",
                "authorization": f"ACCESSTOKEN = {self.bearer_token}",
                "clientid": "d3skt0p",
                "systemid": "jobseeker"
            }

            response = self.session.post(
                url=url, headers=headers, json=payload)
            data = response.json()

            # Handle missing or empty "jobs" key
            if not data.get("jobs"):
                logger.warning(
                    f"⚠️ No jobs found in response for {company_name}: {data}")
                return False

            job_response = data["jobs"][0]  # Safe to access after checking

            if job_response.get("message") == "You have successfully applied to this job.":
                logger.info(f"✅ Applied to {company_name}")
                self.count += 1
                return True
            elif "questionnaire" in job_response:
                questionnaires = job_response["questionnaire"]
                questionnaires_response = ai_agent.create_questionnaires_response(
                    questionnaires, logger)

                if questionnaires_response == {}:
                    return False

                payload["applyData"] = {
                    str(job_id): {"answers": questionnaires_response}}

                response = self.session.post(
                    url=url, headers=headers, json=payload)

                if response.status_code >= 200 and response.status_code < 300:
                    self.count += 1
                    logger.info(
                        f"✅ Applied to {company_name} after filling questionnaire")
                    return True
                else:
                    logger.error(
                        f"❌ Failed to apply at {company_name}. Response: {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(
                f"❌ Failed to apply for {company_name} with data: {logger_data} and error: {e}")
        
    def run(self):
        try:
            self.recommended_jobs()
            
            while self.number_of_jobs > 0 and self.count < 20:
                jobs = self.recommended_jobs()
                self.pageNo += 1
                logger.info(f"🔄 Page number: {self.pageNo}"
                            f" and total jobs available: {self.number_of_jobs}")

                if jobs and len(jobs) > 0:
                    for job in jobs:
                        if self.apply_to_job(job):
                            self.number_of_jobs -= len(jobs)
                else:
                    logger.warning("⚠️ No New jobs found at the moment")
                    break

            logger.info(f"🥳 Applied application count: {self.count}")

            return "Done"
        except Exception as e:
            logger.error(f"❌ Error in Naukri Bot: {e}")
            return "Error"
        finally:
            self.session.close()
            logger.info("🔒 Naukri session closed")
