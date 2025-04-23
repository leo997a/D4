import json
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import streamlit as st
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# إعداد المتصفح (chromium/chromedriver)
def init_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = "/usr/bin/chromium"

    return webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)

# استخراج البيانات من موقع WhoScored
def extract_match_dict(match_url):
    driver = init_driver()
    try:
        driver.get(match_url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        element = soup.select_one('script:-soup-contains("matchCentreData")')

        if not element:
            raise ValueError("لم يتم العثور على matchCentreData في الصفحة.")

        raw_json = element.text.split("matchCentreData: ")[1].split(',\n')[0]
        matchdict = json.loads(raw_json)
        return matchdict
    finally:
        driver.quit()

# تحويل البيانات إلى DataFrame مفيدة
def extract_data_from_dict(data):
    events_dict = data["events"]
    teams_dict = {
        data['home']['teamId']: data['home']['name'],
        data['away']['teamId']: data['away']['name']
    }

    players_home_df = pd.DataFrame(data['home']['players'])
    players_home_df["teamId"] = data['home']['teamId']

    players_away_df = pd.DataFrame(data['away']['players'])
    players_away_df["teamId"] = data['away']['teamId']

    players_df = pd.concat([players_home_df, players_away_df])
    return events_dict, players_df, teams_dict

# واجهة المستخدم
st.set_page_config(layout="wide")
st.title("تحليل مباشر لمباريات WhoScored")

default_url = "https://1xbet.whoscored.com/Matches/1809770/Live/Europe-Europa-League-2023-2024-West-Ham-Bayer-Leverkusen"
match_url = st.text_input("أدخل رابط المباراة:", default_url)

if st.button("ابدأ التحليل"):
    with st.spinner("جاري جلب البيانات..."):
        try:
            json_data = extract_match_dict(match_url)
            events_dict, players_df, teams_dict = extract_data_from_dict(json_data)

            st.subheader("📊 الأحداث")
            st.dataframe(pd.DataFrame(events_dict).head(50), hide_index=True)

            st.subheader("👥 اللاعبين")
            st.dataframe(players_df[["playerId", "name", "shirtNo", "position", "teamId"]])

            st.success("✅ تم التحليل بنجاح!")
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء التحليل: {str(e)}")
