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
        @st.cache_data
def extract_match_dict(match_url, save_json=True, match_id=None):
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        st.write("جارٍ تحميل الصفحة...")
        driver.get(match_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, 'script'))
        )
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        element = soup.find(lambda tag: tag.name == 'script' and 'matchCentreData' in tag.text)
        if not element:
            st.error("لم يتم العثور على matchCentreData في الصفحة")
            return None
        matchdict = json.loads(element.text.split("matchCentreData: ")[1].split(',\n')[0])
        
        # حفظ البيانات كـ JSON
        if save_json and match_id:
            os.makedirs("matches", exist_ok=True)
            json_path = f"matches/{match_id}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(matchdict, f, ensure_ascii=False)
            st.info(f"تم حفظ البيانات في {json_path}")
        
        return matchdict
    except Exception as e:
        st.error(f"خطأ أثناء استخراج البيانات: {str(e)}")
        return None
    finally:
        if driver is not None:
            try:
                driver.quit()
            except:
                pass

@app.route('/match/<match_id>')
def get_match_data(match_id):
    match_url = f"https://www.whoscored.com/Matches/{match_id}/Live/"
    data = extract_match_dict(match_url)
    if data:
        return jsonify(data)
    return jsonify({"error": "Failed to extract data"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)


def get_json_files():
    os.makedirs("matches", exist_ok=True)
    json_files = [f for f in os.listdir("matches") if f.endswith(".json")]
    return json_files if json_files else ["لا توجد ملفات JSON متاحة"]
