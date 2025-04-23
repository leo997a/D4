import json
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import warnings
import streamlit as st

warnings.filterwarnings("ignore", category=DeprecationWarning)

whoscored_url = "https://1xbet.whoscored.com/Matches/1809770/Live/Europe-Europa-League-2023-2024-West-Ham-Bayer-Leverkusen"

def extract_match_dict(match_url, save_output=False):
    """Extract match event from whoscored match center"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        st.write("جارٍ تحميل الصفحة...")
        driver.get(match_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, 'script'))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            if 'matchCentreData' in script.text:
                try:
                    raw_json = script.text.split("matchCentreData: ")[1].split(',\n')[0]
                    matchdict = json.loads(raw_json)
                    return matchdict
                except Exception as e:
                    st.warning(f"خطأ في تحليل السكربت: {str(e)}")
                    continue
        st.error("لم يتم العثور على matchCentreData في الصفحة")
        return None
    except Exception as e:
        st.error(f"خطأ أثناء استخراج البيانات: {str(e)}")
        return None
    finally:
        if driver is not None:
            try:
                driver.quit()
            except:
                pass

def extract_data_from_dict(data):
    events_dict = data["events"]
    teams_dict = {data['home']['teamId']: data['home']['name'],
                  data['away']['teamId']: data['away']['name']}
    players_home_df = pd.DataFrame(data['home']['players'])
    players_home_df["teamId"] = data['home']['teamId']
    players_away_df = pd.DataFrame(data['away']['players'])
    players_away_df["teamId"] = data['away']['teamId']
    players_df = pd.concat([players_home_df, players_away_df])
    return events_dict, players_df, teams_dict

# واجهة Streamlit
st.title("تحليل مباراة كرة القدم")
match_url = st.text_input("أدخل رابط المباراة من WhoScored:", value=whoscored_url)
uploaded_file = st.file_uploader("أو قم بتحميل ملف JSON (اختياري):", type="json")

if st.button("تحليل المباراة"):
    with st.spinner("جارٍ استخراج بيانات المباراة..."):
        if uploaded_file:
            try:
                json_data = json.load(uploaded_file)
            except Exception as e:
                st.error(f"خطأ في تحميل ملف JSON: {str(e)}")
                st.stop()
        else:
            json_data = extract_match_dict(match_url)
        
        if json_data:
            events_dict, players_df, teams_dict = extract_data_from_dict(json_data)
            df = pd.DataFrame(events_dict)
            dfp = pd.DataFrame(players_df)
            st.success("✅ تم استخراج البيانات بنجاح!")
            st.subheader("أحداث المباراة")
            st.dataframe(df.head(), hide_index=True)
            st.subheader("بيانات اللاعبين")
            st.dataframe(dfp.head(), hide_index=True)
        else:
            st.error("❌ فشل في جلب بيانات المباراة.")
