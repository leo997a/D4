import json
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import boto3
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

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

# إعداد Kinesis
kinesis_client = boto3.client('kinesis', region_name='us-east-1')

def send_to_kinesis(data, stream_name='match-stats-stream'):
    response = kinesis_client.put_record(
        StreamName=stream_name,
        Data=json.dumps(data),
        PartitionKey='match-1809770'
    )
    return response

def read_from_kinesis(stream_name='match-stats-stream'):
    try:
        shard_iterator = kinesis_client.get_shard_iterator(
            StreamName=stream_name,
            ShardId='shardId-000000000000',  # استبدل بـ Shard ID الفعلي
            ShardIteratorType='TRIM_HORIZON'
        )['ShardIterator']
        response = kinesis_client.get_records(ShardIterator=shard_iterator, Limit=10)
        return response['Records']
    except Exception as e:
        st.error(f"خطأ في استرداد البيانات من Kinesis: {str(e)}")
        return []

# استخراج البيانات
@st.cache_data
def extract_match_dict(match_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(match_url)
        # انتظار تحميل العنصر الذي يحتوي على matchCentreData
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "script"))
        )
        time.sleep(5)  # وقت إضافي لضمان التحميل
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        scripts = soup.find_all("script")
        
        for script in scripts:
            if "matchCentreData" in script.text:
                try:
                    raw_json = script.text.split("matchCentreData: ")[1].split(",\n")[0]
                    matchdict = json.loads(raw_json)
                    return matchdict
                except Exception as e:
                    st.warning(f"خطأ في تحليل السكربت: {str(e)}")
                    continue
        
        raise ValueError("matchCentreData غير موجود في الصفحة.")
    finally:
        driver.quit()

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
            events_df = pd.DataFrame(events_dict)
            st.dataframe(events_df.head(50), hide_index=True)

            if "Goal" in events_df.get("type", []).values:
                st.balloons()
                st.success("⚽ هدف جديد!")

            st.subheader("📈 تصور الأحداث")
            if not events_df.empty and "minute" in events_df and "type" in events_df:
                fig = px.scatter(events_df, x="minute", y="type", color="teamId", title="أحداث المباراة حسب الدقيقة")
                st.plotly_chart(fig)

            st.subheader("👥 اللاعبين")
            st.dataframe(players_df[["playerId", "name", "shirtNo", "position", "teamId"]])

            # Kinesis
            if st.button("إرسال البيانات إلى Kinesis"):
                send_to_kinesis(events_df.to_dict())
                st.success("✅ تم إرسال البيانات إلى Kinesis!")

            if st.button("استرداد البيانات من Kinesis"):
                records = read_from_kinesis()
                for record in records:
                    st.write(json.loads(record['Data']))

            st.success("✅ تم التحليل بنجاح!")
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء التحليل: {str(e)}")

# تحديث تلقائي
st_autorefresh(interval=60000)
