import json
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# إعداد واجهة المستخدم
st.set_page_config(layout="wide")
st.markdown("""
<style>
.main {
    background-color: #1e1e2f;
    color: #ffffff;
    font-family: 'Roboto', sans-serif;
}
h1 {
    color: #00ff99;
    text-align: center;
}
.stButton>button {
    background-color: #ff4b4b;
    color: white;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# استخراج البيانات باستخدام Selenium
def extract_match_dict(match_url):
    options = Options()
    options.add_argument("--headless")  # تشغيل المتصفح في الوضع المخفي
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(match_url)
        time.sleep(3)  # الانتظار لتحميل الصفحة بالكامل
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        scripts = soup.find_all("script")
        
        for script in scripts:
            if "matchCentreData" in script.text:
                try:
                    raw_json = script.text.split("matchCentreData: ")[1].split(",\n")[0]
                    matchdict = json.loads(raw_json)
                    return matchdict
                except Exception:
                    continue
        
        raise ValueError("matchCentreData غير موجود في الصفحة.")
    finally:
        driver.quit()

# تحويل البيانات إلى DataFrame
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
st.title("تحليل مباشر لمباريات WhoScored ⚽")
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
