import os
import re
import sys
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver

import webdriver_manager.chrome as ChromeDriverManager

from src.meta.logger import get_logger
from src.meta.askAI import ai_agent
from connections.connection_check import connection_monitor

ChromeDriverManager = ChromeDriverManager.ChromeDriverManager

load_dotenv(override=True)

log = get_logger(__name__)
                
class LinkedinConnectionBot:
    MAX_CHARACTER_COUNT = 300
    DAILY_LIMIT = 10
    WEEKLY_LIMIT = 70
    
    def __init__(self, 
                username, 
                password,
                phone_number,
                company_names=None,
                job_title=None,
                location=None,
                ):
        self.locator = {
            "location_button": (By.ID, "searchFilter_geoUrn"),
            "company_button": (By.ID, "searchFilter_currentCompany"),
            "company_input": (By.CSS_SELECTOR, "input[aria-label='Add a company']"),
            "show_results_button_locator": (By.XPATH, "(//button[@aria-label='Apply current filter to show results'])[2]"),
            "profile_locator": (By.CLASS_NAME, 'linked-area'),
            # "connect_button": (By.CSS_SELECTOR, "div.artdeco-dropdown__item--is-dropdown"),
            "connect_button": (By.XPATH, "//div[contains(@class, 'artdeco-dropdown__item') and contains(., 'Connect')]"),
            "more_button": (By.CSS_SELECTOR, "button.artdeco-dropdown__trigger"),
            "add_note_button": (By.CSS_SELECTOR, 'button[aria-label="Add a note"]'),
            "profile_info": (By.CLASS_NAME, 'pv-profile-card'),
            "add_message": (By.ID, 'custom-message'),
            "send_button": (By.XPATH, '//button[@aria-label="Send invitation"]'),
            "card_info": (By.CSS_SELECTOR, 'section.artdeco-card.pv-profile-card'),

            "next": (By.CSS_SELECTOR, "button[aria-label='Continue to next step']"),
            "review": (By.CSS_SELECTOR, "button[aria-label='Review your application']"),
            "submit": (By.CSS_SELECTOR, "button[aria-label='Submit application']"),
            "error": (By.CLASS_NAME, "artdeco-inline-feedback__message"),
            "search": (By.CLASS_NAME, "jobs-search-results-list"),
            "links": ("xpath", '//div[@data-job-id]'),
            "fields": (By.CLASS_NAME, "jobs-easy-apply-form-section__grouping"),
            "easy_apply_button": (By.XPATH, '//button[contains(@class, "jobs-apply-button")]'),
        }
        
        self.urls = {
            "base_search_url": "https://www.linkedin.com/search/results/people/",
            "login": "https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin",
            "search_people": "https://www.linkedin.com/search/results/people/?keywords={}",
            "search_people_network": "https://www.linkedin.com/search/results/people/?keywords={}&network={}&page={}",
        }
        
        self.username = username
        self.password = password
        self.phone_number = phone_number
        self.company_names = company_names
        self.job_title = job_title
        self.location = location
        self.linkedin = None
        self.ai_agent = ai_agent
        self.options = self.browser_options()
        self.browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.options)
        self.browser_initialized = False
        self.wait = WebDriverWait(self.browser, 30)
        self.start_linkedin(username, password)
        self.page_number = 1
        
        log.info("Starting LinkedinConnectionBot ...")
        
    def start_linkedin(self, username, password):
        log.info("Logging in.....Please wait :)")
        self.browser.get(self.urls["login"])
        try:
            user_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            pw_field = self.wait.until(EC.presence_of_element_located((By.ID, "password")))
            login_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="organic-div"]/form/div[4]/button')))
            
            user_field.send_keys(username)
            user_field.send_keys(Keys.TAB)
            time.sleep(2)
            pw_field.send_keys(password)
            time.sleep(2)
            login_button.click()
            time.sleep(15)
        except TimeoutException:
            log.error("TimeoutException! Username/password field or login button not found")
            raise
        except NoSuchElementException as e:
            log.error(f"Element not found: {e}")
            raise
    
    def browser_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        return options

    def parse_keyword(self, keyword: str) -> str:
        return quote(keyword)
    
    def fill_data(self) -> None:
        self.browser.set_window_size(1, 1)
        self.browser.set_window_position(2000, 2000)
    
    def extract_username(self, url):
        # Regular expression to find the username after "/in/"
        match = re.search(r'linkedin\.com/in/([^/?]+)', url)
        if match:
            return match.group(1)  # Return the username part
        else:
            return None
    
    def click_connect_button(self):
        try:
            # Try to find the "Connect" button directly (Case 1)
            # connect_button = self.browser.find_element(*self.locator["connect_button"])
            buttons = self.browser.find_elements(By.CSS_SELECTOR, 'button.artdeco-button--primary span.artdeco-button__text')
            for btn in buttons:
                if btn.text.strip() == "Connect":
                    btn.click()
                    
                    # check if self.browser has h2 element with text "Add a note to your invitation?"
                    h2_element = self.browser.find_elements(By.CSS_SELECTOR, 'h2')
                    for h2 in h2_element:
                        if h2.text.strip() == "Add a note to your invitation?":
                            connection_monitor.update_requested_connections(self.user_name)
                            return False
                    return True
            raise Exception("Connect button not found")
        except:
            # If not found, find the "More" button and click it (Case 2)
            try:
                self.browser.find_elements(*self.locator["more_button"])[3].click()  # Click the "More" button to reveal the dropdown
                time.sleep(3)  # Wait a bit for the dropdown to appear
                
                # Now find and click the "Connect" button inside the dropdown
                self.browser.find_elements(*self.locator["connect_button"])[1].click()
                return True
            except Exception as e:
                print(f"Error: {str(e)}")
                return False
            
    def add_note(self):
        try:
            person_info = self.browser.find_element(*self.locator["profile_info"]).text
            # Click the "Add a note" button
            add_note_button = self.browser.find_element(*self.locator["add_note_button"])
            add_note_button.click()
            time.sleep(2)
            message = self.ai_agent.create_message(self.user_first_name, person_info, log)
            message = message[:self.MAX_CHARACTER_COUNT]
            self.browser.find_element(*self.locator["add_message"]).send_keys(message)
            time.sleep(2)
            self.browser.find_element(*self.locator["send_button"]).click()
            log.info("Note added successfully.")
        except Exception as e:
            log.error(f"Error adding note: {e}")
    
    def open_new_tab(self, profile_url):
        self.browser.execute_script("window.open('');")
        self.browser.switch_to.window(self.browser.window_handles[-1])
        self.browser.get(profile_url)
        
    def close_current_tab(self):
        self.browser.close()
        self.browser.switch_to.window(self.browser.window_handles[0])
    
    def start_apply(self) -> None:
        self.fill_data()
        self.success_connection_count = 0
        self.failed_connection_count = 0
        self.total_connection_count = 0
        
        self.browser.set_window_position(1, 1)
        self.browser.maximize_window()
        
        while True:
            log.info(f"Opening Search People page... With keyword: {self.job_title} and network: ['S', 'O']")
            
            
            # get current url
            if self.browser_initialized:
                current_url = self.browser.current_url
                parsed_url = urlparse(current_url)
                query_params = parse_qs(parsed_url.query)

                # Update page number in the query params
                query_params['page'] = [str(self.page_number)]

                # Reconstruct the URL with updated page number
                updated_query = urlencode(query_params, doseq=True)
                formed_url = urlunparse(parsed_url._replace(query=updated_query))
                # change page number of the current_url
            else:
                formed_url = self.urls["search_people_network"].format(
                    self.parse_keyword(self.job_title),
                    self.parse_keyword('["S","O"]'),
                    self.page_number
                )
            
            self.browser.get(formed_url)
            time.sleep(10)
            
            if not self.browser_initialized:
                log.info("Searching for companies: {}".format(self.company_names))
                self.browser.find_element(*self.locator["company_button"]).click()
                time.sleep(3)
                for company in self.company_names:
                    self.browser.find_element(*self.locator["company_input"]).send_keys(company)
                    time.sleep(2)
                    self.browser.find_element(*self.locator["company_input"]).send_keys(Keys.ARROW_DOWN)
                    self.browser.find_element(*self.locator["company_input"]).send_keys(Keys.ENTER)
                    time.sleep(2)
                    self.browser.find_element(*self.locator["company_input"]).clear()

                try:
                    self.browser.find_element(*self.locator["show_results_button_locator"]).click()
                    log.info("Successfully clicked the 'Show results' button.")
                except TimeoutException:
                    log.error("Timed out waiting for the 'Show results' button to become clickable.")
                except Exception as e:
                    log.error(f"An error occurred: {e}")
            
            self.visit_profiles()
            self.browser_initialized = True
            self.page_number += 1
            
    def process_profile(self, profile_url):
        try:
            self.user_name = self.extract_username(profile_url)
            # TODO:
            # 1. Extract the user's profile information
            # 2. Extract the user's name
            self.open_new_tab(profile_url)
            time.sleep(5)
            self.print_cards()
            time.sleep(2)
            self.click_connect_button()
            time.sleep(2)
            self.add_note()
            time.sleep(5)
            self.close_current_tab()
            connection_monitor.update_requested_connections(self.user_name)
            connection_monitor.update_daily_count(1)
            time.sleep(3)
        except Exception as e:
            log.error(f"Error processing profile {profile_url}: {e}")
    
    def extract_profile_url(self, profile):
        try:
            profile_url = profile.find_element(By.TAG_NAME, "a").get_attribute("href")
            if self.urls["base_search_url"] in profile_url:
                log.warning("Skipping base search URL.")
                return None
            log.info(f"Visiting profile URL: {profile_url}")
            return profile_url
        except Exception as e:
            log.error(f"Error extracting profile URL: {e}")
            return None
        
    def extract_profile_info(self, profile_url):
        try:
            page_source = self.browser.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract full name
            name_tag = soup.find('h1')
            full_name = name_tag.get_text(strip=True) if name_tag else None

            # Extract headline
            headline_tag = soup.find('div', {'class': 'text-body-medium break-words'})
            headline = headline_tag.get_text(strip=True) if headline_tag else None

            # Extract experience section
            experience_section = []
            exp_container = soup.find('section', {'id': 'experience'})
            if exp_container:
                roles = exp_container.find_all('li')
                for role in roles:
                    title_tag = role.find('span', string=lambda text: text and 'title' in text.lower())
                    company_tag = role.find('span', string=lambda text: text and 'company' in text.lower())
                    duration_tag = role.find('span', string=lambda text: text and 'date' in text.lower())

                    title = title_tag.get_text(strip=True) if title_tag else None
                    company = company_tag.get_text(strip=True) if company_tag else None
                    duration = duration_tag.get_text(strip=True) if duration_tag else None

                    experience_section.append({
                        "title": title,
                        "company": company,
                        "duration": duration
                    })

            return {
                "full_name": full_name,
                "headline": headline,
                "experience": experience_section,
            }
        except Exception as e:
            log.error(f"Failed to extract profile info from {profile_url}: {e}")
            return {}
        
    def print_cards(self):
        button = self.browser.find_element(By.XPATH, "//button[contains(@aria-label, 'Invite')]")
        aria_label = button.get_attribute("aria-label")
        match = re.search(r"Invite\s([A-Za-z]+)", aria_label)

        if match:
            name = match.group(1)
            self.user_first_name = name
        
        cards = self.browser.find_elements(*self.locator["card_info"])
        for card in cards:
            h2_element = card.find_element(By.CSS_SELECTOR, 'h2.pvs-header__title')
            
            if "experience" in h2_element.text.strip().lower():
                # check for li with class name = "artdeco-list__item" inside it
                experience_elements = card.find_elements(By.CSS_SELECTOR, 'li.artdeco-list__item')[0]
                print(experience_elements.text.strip())
    
    def visit_profiles(self):
        time.sleep(5)
        profiles = self.browser.find_elements(*self.locator["profile_locator"])
        log.info(f"Found {len(profiles)} profiles.")

        for profile in profiles:
            self.total_connection_count += 1
            log.info(f"Total connections: {self.total_connection_count}")
            
            try:
                # Locate the <a> tag inside each profile and extract the href attribute
                profile_url = self.extract_profile_url(profile)
                if not profile_url:
                    log.error("Profile URL not found!")
                    continue
                
                # profile_url = "https://www.linkedin.com/in/pranati-benawri-616318100/"
                self.process_profile(profile_url)

            except Exception as e:
                log.error(f"Error visiting profile: {e}")
                
    def close_browser(self):
        self.browser.quit()

# --- Main Program ---
def main():
    required_env_vars = {
        "LINKEDIN_EMAIL": os.getenv("LINKEDIN_EMAIL"),
        "LINKEDIN_PASSWORD": os.getenv("LINKEDIN_PASSWORD"),
        "PHONE_NUMBER": os.getenv("PHONE_NUMBER"),
        "CONNECTION_JOB_TITLE": os.getenv("CONNECTION_JOB_TITLE"),
    }
    
    # Check for missing required variables
    missing_vars = [var for var, value in required_env_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    def get_list(env_var, default=""):
        return [item.strip() for item in os.getenv(env_var, default).split(",") if item.strip()]
    
    bot = LinkedinConnectionBot(
        username=required_env_vars["LINKEDIN_EMAIL"],
        password=required_env_vars["LINKEDIN_PASSWORD"],
        phone_number=required_env_vars["PHONE_NUMBER"],
        company_names=get_list("CONNECTION_COMPANY_NAMES", default=[]),
        job_title=required_env_vars["CONNECTION_JOB_TITLE"],
        location=get_list("CONNECTION_LOCATIONS", default=[]),
    )
    
    log.info("LinkedinConnectionBot initialized successfully.")
    
    try:
        bot.start_apply()
    except Exception as e:
        log.error(f"An error occurred: {e}")
    finally:
        bot.close_browser()
