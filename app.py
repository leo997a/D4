from flask import Flask, jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json

app = Flask(__name__)

def extract_match_dict(match_url):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(match_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, 'script'))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            if 'matchCentreData' in script.text:
                raw_json = script.text.split("matchCentreData: ")[1].split(',\n')[0]
                return json.loads(raw_json)
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
    finally:
        if driver:
            driver.quit()

@app.route('/match/<match_id>')
def get_match_data(match_id):
    match_url = f"https://www.whoscored.com/Matches/{match_id}/Live/"
    data = extract_match_dict(match_url)
    if data:
        return jsonify(data)
    return jsonify({"error": "Failed to extract data"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
