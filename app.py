import streamlit as st
import random
import time
import requests
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="로또 분석기 최종본", page_icon="🍀", layout="centered")

# 디자인 설정 (아이폰용)
st.markdown("""
    <style>
    .lotto-ball {
        display: inline-block; width: 40px; height: 40px; line-height: 40px;
        text-align: center; border-radius: 50%; font-weight: bold; font-size: 16px;
        margin: 3px; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    .ball-1 { background: #fbc02d; color: #333; }
    .ball-11 { background: #1976d2; }
    .ball-21 { background: #d32f2f; }
    .ball-31 { background: #616161; }
    .ball-41 { background: #388e3c; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background: #6200ee; color: white; }
    </style>
    """, unsafe_allow_html=True)

def render_balls(numbers):
    html = '<div style="display: flex; flex-wrap: wrap; justify-content: center;">'
    for n in numbers:
        if n <= 10: cls = "ball-1"
        elif n <= 20: cls = "ball-11"
        elif n <= 30: cls = "ball-21"
        elif n <= 40: cls = "ball-31"
        else: cls = "ball-41"
        html += f'<div class="lotto-ball {cls}">{n:02d}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# --- 실시간 데이터 수집 (3중 시도 방식) ---
def fetch_lotto_data():
    base_date = datetime(2002, 12, 7)
    latest_draw = (datetime.now() - base_date).days // 7 + 1
    
    all_numbers = []
    error_msg = ""
    
    with st.status("📡 데이터 수집 시도 중...", expanded=True) as status:
        for i in range(20):
            draw_no = latest_draw - i
            success = False
            
            # 시도 1: 마나나 API (가장 빠름)
            try:
                res = requests.get(f"https://api.manana.kr/lotto.json?draw={draw_no}", timeout=5)
                if res.status_code == 200:
                    data = res.json()[0]
                    all_numbers.append([int(data[f"num{j}"]) for j in range(1, 7)])
                    success = True
            except Exception as e:
                error_msg = str(e)

            # 시도 2: 공식 서버 (마나나 실패 시)
            if not success:
                try:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    res = requests.get(f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}", headers=headers, timeout=5)
                    data = res.json()
                    if data.get("returnValue") == "success":
                        all_numbers.append([data[f"drwtNo{j}"] for j in range(1, 7)])
                        success = True
                except Exception as e:
                    error_msg = str(e)
            
            if not success:
                st.write(f"❌ {draw_no}회차 수집 실패")
            else:
                st.write(f"✅ {draw_no}회차 완료")
            
            time.sleep(0.1)
            
        if len(all_numbers) >= 10:
            status.update(label="분석 완료!", state="complete")
        else:
            status.update(label="데이터 부족 (에러 발생)", state="error")
            
    return all_numbers, error_msg

# 앱 실행부
st.title("🎰 로또 분석기 무적 버전")

if 'lotto_data' not in st.session_state:
    st.session_state.lotto_data, st.session_state.error = fetch_lotto_data()

data = st.session_state.lotto_data

if len(data) >= 5:
    flat_list = [n for d in data for n in d]
    counts = Counter(flat_list)
    weights = [counts.get(i, 0) + 1 for i in range(1, 46)]

    st.success(f"최근 {len(data)}회차 데이터를 기반으로 분석 중입니다.")
    
    if st.button("🚀 행운의 번호 추출"):
        for i in range(5):
            st.write(f"**조합 {i+1}**")
            game = sorted(random.sample(range(1, 46), 6)) if i == 4 else sorted(random.choices(range(1, 46), weights=weights, k=6))
            render_balls(game)
else:
    st.error("데이터 수집에 실패했습니다.")
    st.info(f"에러 내용: {st.session_state.error}")
    if st.button("🔄 다시 시도하기"):
        st.session_state.clear()
        st.rerun()
