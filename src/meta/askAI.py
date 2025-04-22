import os
from dotenv import load_dotenv
# from src.meta.resume import resume_text
from src.meta.get_resume_text import get_resume_text

import time
import requests
import json

load_dotenv(override=True)

resume_text = get_resume_text()

required_env_vars = {
    "GEMINI_KEY": os.getenv("GEMINI_API_KEY")
}

missing_vars = [var for var, value in required_env_vars.items() if not value]

if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}")

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + \
    required_env_vars["GEMINI_KEY"]


class AI_Agent:
    required_env_vars = {
        "GENDER": os.getenv("GENDER"),
        "NOTICE_PERIOD": os.getenv("NOTICE_PERIOD"),
        "CURRENT_CTC": os.getenv("CURRENT_CTC"),
        "EXPECTED_CTC": os.getenv("EXPECTED_CTC")
    }

    missing_vars = [var for var,
                    value in required_env_vars.items() if not value]

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}")

    if not resume_text:
        raise AttributeError("Resume text not replaced")

    GENDER = required_env_vars["GENDER"]
    NOTICE_PERIOD = required_env_vars["NOTICE_PERIOD"]
    CURRENT_CTC = required_env_vars["CURRENT_CTC"]
    EXPECTED_CTC = required_env_vars["EXPECTED_CTC"]

    def askAI(self, msg):
        payload = json.dumps({
            "contents": [
                {
                    "parts": [
                        {
                            "text": msg
                        }
                    ]
                }
            ]
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response = json.loads(response.text)

        return response["candidates"][0]["content"]["parts"][0]["text"]

    def create_questionnaires_response(self, questionnaires, logger):
        response = {}
        max_retries = 5
        retry_delay = 30

        for attempt in range(max_retries):
            try:
                for questionnaire in questionnaires:
                    question_id = questionnaire["questionId"]
                    question_name = questionnaire["questionName"]
                    response_options = questionnaire.get("answerOption", {})

                    command = f"""
                    - answer in minimum possible words as I am pasting the same for text box.
                    - based upon my resume, answer the question very precisely.
                    - if there are values in answerOptions, return me the exact value to the correct answer associated.
                    - NOTE: Prepare each question's answer exactly as per my resume. The experience values can be more but NEVER less as per my resume.
                    - question is: '{question_name}'
                    - answerOptions is: {response_options}
                    - if required my gender is {self.GENDER}
                    - My current salary is: {self.CURRENT_CTC}
                    - My Salary expectation is: {self.EXPECTED_CTC}
                    - My Notice period is: {self.NOTICE_PERIOD}
                    - resume is: {resume_text}
                    """

                    questionnaire_response = self.askAI(
                        command).replace("\n", "")

                    if response_options:
                        response[question_id] = [questionnaire_response]
                    else:
                        response[question_id] = questionnaire_response

                    time.sleep(2)

                return response  # Return response if successful

            except Exception as e:
                logger.error(
                    f"❌ Error in processing questionnaires (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(
                        "❌ Max retries reached. Skipping questionnaire processing.")
                    return {}  # Return empty response after max retries

    def answer_questions(self, question, logger, options=None):
        response = {}
        max_retries = 5
        retry_delay = 30

        for attempt in range(max_retries):
            try:
                command = f"""
                - answer in minimum possible words as I am pasting the same for text box.
                - based upon my resume, answer the question very precisely.
                - if there are values in answerOptions, return me the exact value to the correct answer associated.
                - NOTE: Prepare each question's answer exactly as per my resume. The experience values can be more but NEVER less as per my resume
                - question is: '{question}'
                {f'- answerOptions is: {options}' if options else ''}
                - if required my gender is {self.GENDER}
                - My current salary is: {self.CURRENT_CTC}
                - My Salary expectation is: {self.EXPECTED_CTC}
                - My Notice period is: {self.NOTICE_PERIOD}
                - resume is: {resume_text}
                """

                questionnaire_response = self.askAI(
                    command).replace("\n", "")

                time.sleep(2)

                return questionnaire_response  # Return response if successful

            except Exception as e:
                logger.error(
                    f"❌ Error in processing questionnaires (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(
                        "❌ Max retries reached. Skipping questionnaire processing.")
                    return {}  # Return empty response after max retries
                
    def create_message(self,user_name, profile, logger):
        response = {}
        max_retries = 5
        retry_delay = 30

        for attempt in range(max_retries):
            try:
                command = f"""
                        - I am sending a connection request to a user on LinkedIn.
                        - Generate a message for the connection request in less than 200 characters.
                        - The message should be polite and professional, inclined to how I am interested in connecting with the user.
                        - My name is: {os.getenv('NAME')}
                        - The person I am messaging is: {user_name}, if this name is missing, just address with Hi!
                        {f'- I am attaching the person(s) information whom I am messaging.:{profile}.' if profile else ''}
                        - NOTE: not to leave any replaceable items as I am going to copy and paste exactly as it is.
                        """

                questionnaire_response = self.askAI(
                    command).replace("\n", "")

                time.sleep(2)

                return questionnaire_response  # Return response if successful

            except Exception as e:
                logger.error(
                    f"❌ Error in processing questionnaires (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(
                        "❌ Max retries reached. Skipping questionnaire processing.")
                    return {}  # Return empty response after max retries


ai_agent = AI_Agent()
