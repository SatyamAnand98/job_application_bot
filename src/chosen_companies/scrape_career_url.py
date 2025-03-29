""" Module imports """
import time
import yaml
import requests
from bs4 import BeautifulSoup


def get_career_url(company_name):
    '''
    Search for URL using google
    '''
    search_query = f"{company_name} careers site:jobs"  # Common query format
    search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", href=True):
                url = link["href"]
                if "careers" in url or "jobs" in url:
                    return url
    except Exception as e:
        print(f"Error fetching URL for {company_name}: {e}")
    return "Not Found"


def update_yaml(file_path):
    '''
    Update yaml for the career page url
    '''
    with open(file_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    # Ensure data is a list and extract the first dictionary
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        data_dict = data[0]  # Extract the dictionary inside the list
    else:
        print("Invalid YAML format")
        return

    for company_group in data_dict.get("Lists", []):
        for company in company_group.get("Company_info", []):
            if company.get("URL", None) is None:
                print(f"Fetching career URL for {company['Name']}...")
                company["URL"] = get_career_url(company["Name"])
                print("URL: ", company["URL"])
                time.sleep(2)

    with open(file_path, "w", encoding="utf-8") as file:
        yaml.dump([data_dict], file, default_flow_style=False,
                  allow_unicode=True)
    print("YAML file updated successfully.")


if __name__ == "__main__":
    update_yaml("companies.yaml")
