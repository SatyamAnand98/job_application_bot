from __future__ import annotations

import json
import csv
import logging
import os
import random
import re
import time
from datetime import datetime, timedelta
import getpass
from pathlib import Path

import pandas as pd
import pyautogui
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.chrome.service import Service as ChromeService
import webdriver_manager.chrome as ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains

from src.meta.logger import get_logger
from src.meta.askAI import ai_agent
ChromeDriverManager = ChromeDriverManager.ChromeDriverManager


log = get_logger(__name__)
load_dotenv()


class LinkedinApplicationBot:
    # MAX_SEARCH_TIME is 10 hours by default, feel free to modify it
    MAX_SEARCH_TIME = 60 * 60

    def __init__(self,
                 username,
                 password,
                 phone_number,
                #  profile_path,
                 salary,
                 rate,
                 uploads={},
                 filename='output.csv',
                 blacklist=[],
                 blackListTitles=[],
                 experience_level=[]
                 ) -> None:

        log.info("Welcome to Easy Apply Bot")
        dirpath: str = os.getcwd()
        log.info("current directory is : " + dirpath)
        log.info("Please wait while we prepare the bot for you")
        if experience_level:
            experience_levels = {
                1: "Entry level",
                2: "Associate",
                3: "Mid-Senior level",
                4: "Director",
                5: "Executive",
                6: "Internship"
            }
            applied_levels = [experience_levels[level]
                              for level in experience_level]
            log.info("Applying for experience level roles: " +
                     ", ".join(applied_levels))
        else:
            log.info("Applying for all experience levels")
        self.qa_file_path = "src/meta/Linkedin/qa.csv"
        self.uploads = uploads
        self.salary = salary
        self.rate = rate
        # self.profile_path = profile_path
        past_ids: list | None = self.get_appliedIDs(filename)
        self.appliedJobIDs: list = past_ids if past_ids != None else []
        self.filename: str = filename
        self.options = self.browser_options()
        self.browser = webdriver.Chrome(service=ChromeService(
            ChromeDriverManager().install()), options=self.options)
        self.wait = WebDriverWait(self.browser, 30)
        self.blacklist = blacklist
        self.blackListTitles = blackListTitles
        self.start_linkedin(username, password)
        self.phone_number = phone_number
        self.experience_level = experience_level

        self.locator = {
            "next": (By.CSS_SELECTOR, "button[aria-label='Continue to next step']"),
            "review": (By.CSS_SELECTOR, "button[aria-label='Review your application']"),
            "submit": (By.CSS_SELECTOR, "button[aria-label='Submit application']"),
            "error": (By.CLASS_NAME, "artdeco-inline-feedback__message"),
            "upload_resume": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-resume')]"),
            "upload_cv": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]"),
            "follow": (By.CSS_SELECTOR, "label[for='follow-company-checkbox']"),
            "upload": (By.NAME, "file"),
            "search": (By.CLASS_NAME, "jobs-search-results-list"),
            "links": ("xpath", '//div[@data-job-id]'),
            "fields": (By.CLASS_NAME, "jobs-easy-apply-form-section__grouping"),
            # need to append [value={}].format(answer)
            "radio_select": (By.CSS_SELECTOR, "input[type='radio']"),
            "multi_select": (By.XPATH, "//*[contains(@id, 'text-entity-list-form-component')]"),
            "text_select": (By.CLASS_NAME, "artdeco-text-input--input"),
            "text_input_label": (By.CLASS_NAME, "artdeco-text-input--label"),
            "2fa_oneClick": (By.ID, 'reset-password-submit-button'),
            "easy_apply_button": (By.XPATH, '//button[contains(@class, "jobs-apply-button")]'),
            "fb-dash-form-element": (By.CLASS_NAME, 'fb-dash-form-element'),
            "multi_select_2": (By.ID, 'text-entity-list-form-component'),
            "form_fields": "fb-dash-form-element"
        }

        # initialize questions and answers file
        self.qa_file = Path(os.getenv("QUESTION_ANSWER_DIRECTORY"))
        self.answers = {}

        # if qa file does not exist, create it
        if self.qa_file.is_file():
            try:
                df = pd.read_csv(self.qa_file)
                for index, row in df.iterrows():
                    self.answers[row['Question']] = row['Answer']
            except FileNotFoundError:
                print("QA file not found. Please create a csv file in the QUESTION_ANSWER_DIRECTORY")
        # if qa file does exist, load it
        else:
            df = pd.DataFrame(columns=["Question", "Answer"])
            df.to_csv(self.qa_file, index=False, encoding='utf-8')

    def get_appliedIDs(self, filename) -> list | None:
        try:
            df = pd.read_csv(filename,
                             header=None,
                             names=['timestamp', 'jobID', 'job',
                                    'company', 'attempted', 'result'],
                             lineterminator='\n',
                             encoding='utf-8')

            df['timestamp'] = pd.to_datetime(
                df['timestamp'], format="%Y-%m-%d %H:%M:%S")
            df = df[df['timestamp'] > (datetime.now() - timedelta(days=2))]
            jobIDs: list = list(df.jobID)
            log.info(f"{len(jobIDs)} jobIDs found")
            return jobIDs
        except Exception as e:
            log.info(
                str(e) + "   jobIDs could not be loaded from CSV {}".format(filename))
            return None

    def browser_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")
        # options.add_argument(r'--remote-debugging-port=9222')
        # options.add_argument(r'--profile-directory=Person 1')

        # Disable webdriver flags or you will be easily detectable
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Load user profile
        # options.add_argument(r"--user-data-dir={}".format(self.profile_path))
        return options

    def start_linkedin(self, username, password) -> None:
        log.info("Logging in.....Please wait :)  ")
        self.browser.get(
            "https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
        try:
            user_field = self.browser.find_element("id", "username")
            pw_field = self.browser.find_element("id", "password")
            login_button = self.browser.find_element("xpath",
                                                     '//*[@id="organic-div"]/form/div[4]/button')
            user_field.send_keys(username)
            user_field.send_keys(Keys.TAB)
            time.sleep(2)
            pw_field.send_keys(password)
            time.sleep(2)
            login_button.click()
            time.sleep(15)
        except TimeoutException:
            log.info(
                "TimeoutException! Username/password field or login button not found")

    def fill_data(self) -> None:
        self.browser.set_window_size(1, 1)
        self.browser.set_window_position(2000, 2000)

    def start_apply(self, positions, locations) -> None:
        start: float = time.time()
        self.fill_data()
        self.positions = positions
        self.locations = locations
        combos: list = []
        while len(combos) < len(positions) * len(locations):
            position = positions[random.randint(0, len(positions) - 1)]
            location = locations[random.randint(0, len(locations) - 1)]
            combo: tuple = (position, location)
            if combo not in combos:
                combos.append(combo)
                log.info(f"Applying to {position}: {location}")
                location = "&location=" + location
                self.applications_loop(position, location)
            if len(combos) > 500:
                break

    # self.finish_apply() --> this does seem to cause more harm than good, since it closes the browser which we usually don't want, other conditions will stop the loop and just break out

    def applications_loop(self, position, location):

        count_application = 0
        count_job = 0
        jobs_per_page = 0
        start_time: float = time.time()

        log.info("Looking for jobs.. Please wait..")

        self.browser.set_window_position(1, 1)
        self.browser.maximize_window()
        self.browser, _ = self.next_jobs_page(
            position, location, jobs_per_page, experience_level=self.experience_level)
        log.info("Looking for jobs.. Please wait..")

        while time.time() - start_time < self.MAX_SEARCH_TIME:
            try:
                log.info(
                    f"{(self.MAX_SEARCH_TIME - (time.time() - start_time)) // 60} minutes left in this search")

                # sleep to make sure everything loads, add random to make us look human.
                randoTime: float = random.uniform(1.5, 2.9)
                log.debug(f"Sleeping for {round(randoTime, 1)}")
                # time.sleep(randoTime)
                self.load_page(sleep=0.5)

                # LinkedIn displays the search results in a scrollable <div> on the left side, we have to scroll to its bottom

                # scroll to bottom

                if self.is_present(self.locator["search"]):
                    scrollresults = self.get_elements("search")
                    #     self.browser.find_element(By.CLASS_NAME,
                    #     "jobs-search-results-list"
                    # )
                    # Selenium only detects visible elements; if we scroll to the bottom too fast, only 8-9 results will be loaded into IDs list
                    for i in range(300, 3000, 100):
                        self.browser.execute_script(
                            "arguments[0].scrollTo(0, {})".format(i), scrollresults[0])
                    scrollresults = self.get_elements("search")
                    # time.sleep(1)

                # get job links, (the following are actually the job card objects)
                if self.is_present(self.locator["links"]):
                    links = self.get_elements("links")
                # links = self.browser.find_elements("xpath",
                #     '//div[@data-job-id]'
                # )

                    jobIDs = {}  # {Job id: processed_status}

                    # children selector is the container of the job cards on the left
                    for link in links:
                        if 'Applied' not in link.text:  # checking if applied already
                            if link.text not in self.blacklist:  # checking if blacklisted
                                jobID = link.get_attribute("data-job-id")
                                if jobID == "search":
                                    log.debug(
                                        "Job ID not found, search keyword found instead? {}".format(link.text))
                                    continue
                                else:
                                    jobIDs[jobID] = "To be processed"
                    if len(jobIDs) > 0:
                        self.apply_loop(jobIDs)
                    self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                      location,
                                                                      jobs_per_page,
                                                                      experience_level=self.experience_level)
                else:
                    self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                      location,
                                                                      jobs_per_page,
                                                                      experience_level=self.experience_level)

            except Exception as e:
                print(e)

    def apply_loop(self, jobIDs):
        for jobID in jobIDs:
            if jobIDs[jobID] == "To be processed":
                applied = self.apply_to_job(jobID)
                if applied:
                    log.info(f"Applied to {jobID}")
                else:
                    log.info(f"Failed to apply to {jobID}")
                jobIDs[jobID] == applied

    def apply_to_job(self, jobID):
        # #self.avoid_lock() # annoying

        # get job page
        self.get_job_page(jobID)

        # let page load
        time.sleep(1)

        # get easy apply button
        button = self.get_easy_apply_button()

        # word filter to skip positions not wanted
        if button is not False:
            if any(word in self.browser.title for word in self.blackListTitles):
                log.info(
                    'skipping this application, a blacklisted keyword was found in the job position')
                string_easy = "* Contains blacklisted keyword"
                result = False
            else:
                string_easy = "* has Easy Apply Button"
                log.info("Clicking the EASY apply button")
                button.click()
                clicked = True
                time.sleep(1)
                self.fill_out_fields()
                result: bool = self.send_resume()
                if result:
                    string_easy = "*Applied: Sent Resume"
                else:
                    string_easy = "*Did not apply: Failed to send Resume"
        elif "You applied on" in self.browser.page_source:
            log.info("You have already applied to this position.")
            string_easy = "* Already Applied"
            result = False
        else:
            log.info("The Easy apply button does not exist.")
            string_easy = "* Doesn't have Easy Apply Button"
            result = False

        # position_number: str = str(count_job + jobs_per_page)
        log.info(
            f"\nPosition {jobID}:\n {self.browser.title} \n {string_easy} \n")

        self.write_to_file(button, jobID, self.browser.title, result)
        return result

    def write_to_file(self, button, jobID, browserTitle, result) -> None:
        def re_extract(text, pattern):
            target = re.search(pattern, text)
            if target:
                target = target.group(1)
            return target

        timestamp: str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        attempted: bool = False if button == False else True
        job = re_extract(browserTitle.split(' | ')[0], r"\(?\d?\)?\s?(\w.*)")
        company = re_extract(browserTitle.split(' | ')[1], r"(\w.*)")

        toWrite: list = [timestamp, jobID, job, company, attempted, result]
        with open(self.filename, 'a+') as f:
            writer = csv.writer(f)
            writer.writerow(toWrite)

    def get_job_page(self, jobID):

        job: str = 'https://www.linkedin.com/jobs/view/' + str(jobID)
        self.browser.get(job)
        # self.browser.get("https://www.linkedin.com/jobs/view/4183475661/")
        self.job_page = self.load_page(sleep=0.5)
        return self.job_page

    def get_easy_apply_button(self):
        EasyApplyButton = False
        try:
            buttons = self.get_elements("easy_apply_button")
            # buttons = self.browser.find_elements("xpath",
            #     '//button[contains(@class, "jobs-apply-button")]'
            # )
            for button in buttons:
                if "Easy Apply" in button.text:
                    EasyApplyButton = button
                    self.wait.until(
                        EC.element_to_be_clickable(EasyApplyButton))
                else:
                    log.debug("Easy Apply button not found")

        except Exception as e:
            print("Exception:", e)
            log.debug("Easy Apply button not found")

        return EasyApplyButton

    def fill_out_fields(self):
        fields = self.browser.find_elements(
            By.CLASS_NAME, "jobs-easy-apply-form-section__grouping")
        for field in fields:
            print("Field text: ", field.text)

            if "Mobile phone number" in field.text:
                field_input = field.find_element(By.TAG_NAME, "input")
                field_input.clear()
                field_input.send_keys(self.phone_number)

        return

    def get_elements(self, type) -> list:
        elements = []
        element = self.locator[type]
        if self.is_present(element):
            elements = self.browser.find_elements(element[0], element[1])
        return elements

    # def is_present(self, locator, parent=None, field=None) -> bool:
    #     # If parent is provided, search inside it
    #     search_context = field if field else (parent if parent else self.browser)
    #     return len(search_context.find_elements(locator[0], locator[1])) > 0
    
    def is_present(self, locator, parent=None, field=None) -> bool:
        search_context = field if field else (parent if parent else self.browser)
        elements = search_context.find_elements(locator[0], locator[1])
        
        return len(elements) > 0

    def send_resume(self) -> bool:
        def is_present(button_locator) -> bool:
            return len(self.browser.find_elements(button_locator[0],
                                                  button_locator[1])) > 0

        try:
            # time.sleep(random.uniform(1.5, 2.5))
            next_locator = (By.CSS_SELECTOR,
                            "button[aria-label='Continue to next step']")
            review_locator = (By.CSS_SELECTOR,
                              "button[aria-label='Review your application']")
            submit_locator = (By.CSS_SELECTOR,
                              "button[aria-label='Submit application']")
            error_locator = (By.CLASS_NAME, "artdeco-inline-feedback__message")
            upload_resume_locator = (
                By.XPATH, '//span[text()="Upload resume"]')
            upload_cv_locator = (
                By.XPATH, '//span[text()="Upload cover letter"]')
            # WebElement upload_locator = self.browser.find_element(By.NAME, "file")
            follow_locator = (
                By.CSS_SELECTOR, "label[for='follow-company-checkbox']")

            submitted = False
            loop = 0
            while loop < 3:
                time.sleep(1)
                # Upload resume
                if is_present(upload_resume_locator):
                    # upload_locator = self.browser.find_element(By.NAME, "file")
                    try:
                        resume_locator = self.browser.find_element(
                            By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-resume')]")
                        resume = self.uploads["Resume"]
                        resume_locator.send_keys(resume)
                    except Exception as e:
                        log.error("Resume upload failed")
                        log.debug("Resume: " + resume)
                        log.debug("Resume Locator: " + str(resume_locator))
                # Upload cover letter if possible
                if is_present(upload_cv_locator):
                    cv = self.uploads["Cover Letter"]
                    cv_locator = self.browser.find_element(
                        By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]")
                    cv_locator.send_keys(cv)

                    # time.sleep(random.uniform(4.5, 6.5))
                elif len(self.get_elements("follow")) > 0:
                    elements = self.get_elements("follow")
                    for element in elements:
                        button = self.wait.until(
                            EC.element_to_be_clickable(element))
                        button.click()

                if len(self.get_elements("submit")) > 0:
                    if self.get_elements(self.locator["form_fields"]):
                        self.process_questions()
                    elements = self.get_elements("submit")
                    for element in elements:
                        button = self.wait.until(
                            EC.element_to_be_clickable(element))
                        button.click()
                        log.info("Application Submitted")
                        submitted = True
                        break

                elif len(self.get_elements("error")) > 0:
                    if self.get_elements(self.locator["form_fields"]):
                        self.process_questions()
                    elements = self.get_elements("error")
                    if "application was sent" in self.browser.page_source:
                        log.info("Application Submitted")
                        submitted = True
                        break
                    elif len(elements) > 0:
                        while len(elements) > 0:
                            log.info(
                                "Please answer the questions, waiting 5 seconds...")
                            time.sleep(5)
                            elements = self.get_elements("error")

                            for element in elements:
                                self.process_questions()

                            if "application was sent" in self.browser.page_source:
                                log.info("Application Submitted")
                                submitted = True
                                break
                            elif is_present(self.locator["easy_apply_button"]):
                                log.info("Skipping application")
                                submitted = False
                                break
                        continue
                        # add explicit wait

                    else:
                        if len(self.get_elements("next")) > 0:
                            elements = self.get_elements("next")
                            for element in elements:
                                button = self.wait.until(
                                    EC.element_to_be_clickable(element))
                                button.click()

                        elif len(self.get_elements("review")) > 0:
                            elements = self.get_elements("review")
                            for element in elements:
                                button = self.wait.until(
                                    EC.element_to_be_clickable(element))
                                button.click()
                        elif len(self.get_elements("submit")) > 0:
                            elements = self.get_elements("submit")
                            for element in elements:
                                button = self.wait.until(
                                    EC.element_to_be_clickable(element))
                                button.click()
                                log.info("Application Submitted")
                                submitted = True
                                break
                    # self.process_questions()

                elif len(self.get_elements("next")) > 0:
                    if self.get_elements(self.locator["form_fields"]):
                        self.process_questions()
                    elements = self.get_elements("next")
                    for element in elements:
                        button = self.wait.until(
                            EC.element_to_be_clickable(element))
                        button.click()

                elif len(self.get_elements("review")) > 0:
                    if self.get_elements(self.locator["form_fields"]):
                        self.process_questions()
                    elements = self.get_elements("review")
                    for element in elements:
                        button = self.wait.until(
                            EC.element_to_be_clickable(element))
                        button.click()

                elif len(self.get_elements("follow")) > 0:
                    elements = self.get_elements("follow")
                    for element in elements:
                        button = self.wait.until(
                            EC.element_to_be_clickable(element))
                        button.click()

        except Exception as e:
            log.error(e)
            log.error("cannot apply to this job")
            pass
            # raise (e)

        return submitted

    def process_questions(self):
        time.sleep(1)
        form = self.get_elements("fb-dash-form-element")

        for field in form:
            time.sleep(1)
            question = field.text.strip()
            answer = self.ans_question(question)
            field_updated = False
            

            if "email" in question.lower():
                field.click()
                field.send_keys(os.getenv("LINKEDIN_EMAIL"))
                field_updated = True

            elif "country code" in question.lower():
                field.click()
                field.send_keys(os.getenv("REGION_AND_CODE"))
                field_updated = True

            elif "mobile phone number" in question.lower():
                field.click()
                text_input = field.find_element(*self.locator["text_select"])
                text_input.clear()
                text_input.send_keys(os.getenv("PHONE_NUMBER"))
                field_updated = True

            # Radio button selection
            elif self.is_present(self.locator["radio_select"], field=field):
                try:
                    radio_input = field.find_element(
                        By.CSS_SELECTOR, f"input[type='radio'][value='{answer}']")
                    self.browser.execute_script(
                        "arguments[0].click();", radio_input)
                    field_updated = True
                except Exception as e:
                    log.error(e)
            
            # Text input handling
            elif self.is_present(self.locator["text_select"], field=field):
                try:
                    text_input = field.find_element(
                        *self.locator["text_select"])
                    text_input.clear()
                    text_input.send_keys(answer)
                    field_updated = True
                except Exception as e:
                    log.error(e)

            # Multi-select dropdown handling
            elif self.is_present(self.locator["multi_select"], field=field):
                try:
                    dropdown = field.find_element(*self.locator["multi_select"])  # Ensure it's specific to this field
                    self.browser.execute_script("arguments[0].scrollIntoView(true);", dropdown)  # Ensure visibility
                    time.sleep(0.5)
                    dropdown.click()

                    actions = ActionChains(self.browser)
                    actions.move_to_element(dropdown).perform()
                    time.sleep(0.5)

                    # **Select the Correct Answer**
                    options = field.find_elements(By.TAG_NAME, "option")  # Find all options inside this dropdown
                    for option in options:
                        if answer.lower() in option.text.lower():  # Match text ignoring case
                            option.click()
                            break

                    field_updated = True
                except Exception as e:
                    log.error(e)

            if not field_updated:
                log.info(f"Skipped field: {question}")

    def ans_question(self, question, options=None):
        qa_data = {}

        # Read existing data from qa.csv
        if os.path.exists(self.qa_file_path):
            with open(self.qa_file_path, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                qa_data = {rows[0]: rows[1]
                           for rows in reader if len(rows) == 2}

        # If question exists, return the stored answer
        if question in qa_data:
            return qa_data[question]

        # Otherwise, generate answer using AI
        answer = ai_agent.answer_questions(question, log, options)

        # Store the new question and answer in qa.csv
        with open(self.qa_file_path, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([question, answer])

        return answer

    def load_page(self, sleep=1):
        scroll_page = 0
        while scroll_page < 4000:
            self.browser.execute_script(
                "window.scrollTo(0," + str(scroll_page) + " );")
            scroll_page += 500
            time.sleep(sleep)

        if sleep != 1:
            self.browser.execute_script("window.scrollTo(0,0);")
            time.sleep(sleep)

        page = BeautifulSoup(self.browser.page_source, "lxml")
        return page

    def avoid_lock(self) -> None:
        x, _ = pyautogui.position()
        pyautogui.moveTo(x + 200, pyautogui.position().y, duration=1.0)
        pyautogui.moveTo(x, pyautogui.position().y, duration=0.5)
        pyautogui.keyDown('ctrl')
        pyautogui.press('esc')
        pyautogui.keyUp('ctrl')
        time.sleep(0.5)
        pyautogui.press('esc')

    def next_jobs_page(self, position, location, jobs_per_page, experience_level=[]):
        # Construct the experience level part of the URL
        experience_level_str = ",".join(
            map(str, experience_level)) if experience_level else ""
        experience_level_param = f"&f_E={experience_level_str}" if experience_level_str else ""
        self.browser.get(
            # URL for jobs page
            "https://www.linkedin.com/jobs/search/?f_LF=f_AL&keywords=" +
            position + location + "&start=" + str(jobs_per_page) + experience_level_param)
        # self.avoid_lock()
        log.info("Loading next job page?")
        self.load_page()
        return (self.browser, jobs_per_page)

    # def finish_apply(self) -> None:
    #     self.browser.close()
