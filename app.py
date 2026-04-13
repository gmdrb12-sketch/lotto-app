import streamlit as st
import requests
import random
from collections import Counter
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="실시간 분석기 Pro (10회차)", page_icon="🎯", layout="centered")

# 2. 로또공 그래픽 디자인 (CSS)
st.markdown("""
    <style>
    .lotto-ball {
        display: inline-block; width: 42px; height: 42px; line-height: 42px;
        text-align: center; border-radius: 50%; font-weight: bold; font-size: 16px;
        margin: 4px; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        box-shadow: inset -3px -3px 5px rgba(0,0,0,0.2), 2px 2px 5px rgba(0,0,0,0.1);
    }
    .ball-1 { background: #fbc02d; color: #333; }
    .ball-2 { background: #2196f3; }
    .ball-3 { background: #f44336; }
    .ball-4 { background: #9e9e9e; }
    .ball-5 { background: #4caf50; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background: linear-gradient(to right, #6a11cb, #2575fc); color: white; border: none; }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

def render_balls(numbers):
    html = '<div style="display: flex; flex-wrap: wrap; justify-content: center; margin-bottom: 10px;">'
    for n in numbers:
        if n <= 10: cls = "ball-1"
        elif n <= 20: cls = "ball-2"
        elif n <= 30: cls = "ball-3"
        elif n <= 40: cls = "ball-4"
        else: cls = "ball-5"
        html += f'<div class="lotto-ball {cls}">{n:02d}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# 3. 데이터 수집 함수 (superkts 차단 우회를 위한 안정형 API 사용)
@st.cache_data(ttl=3600)
def fetch_10_draws():
    base_date = datetime(2002, 12, 7)
    latest_draw = (datetime.now() - base_date).days // 7 + 1
    
    all_draws = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for i in range(10):
        draw_no = latest_draw - i
        success = False
        
        # 1순위: 마나나 오픈 API (속도 빠름, 차단 없음)
        try:
            res = requests.get(f"https://api.manana.kr/lotto.json?draw={draw_no}", timeout=3)
            if res.status_code == 200:
                data = res.json()[0]
                nums = [int(data[f"num{j}"]) for j in range(1, 7)]
                all_draws.append(sorted(nums))
                success = True
        except:
            pass
            
        # 2순위: 동행복권 공식 서버 (1순위 실패 시 백업)
        if not success:
            try:
                res = requests.get(f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}", headers=headers, timeout=3)
                data = res.json()
                if data.get("returnValue") == "success":
                    nums = [data[f"drwtNo{j}"] for j in range(1, 7)]
                    all_draws.append(sorted(nums))
            except:
                pass

    if len(all_draws) > 0:
        return all_draws, None
    else:
        return None, "모든 데이터 서버가 접근을 차단했습니다."

# 4. 메인 화면 구성
st.title("🎯 실시간 로또 분석기 (10회차)")
st.write("안정적인 오픈 API 서버를 통해 최신 10회차 데이터를 실시간 분석합니다.")

if 'lotto_data' not in st.session_state:
    with st.spinner("🔄 데이터를 가져오는 중... (최초 1회 약 3초 소요)"):
        data, err = fetch_10_draws()
        st.session_state.lotto_data = data
        st.session_state.err = err

data = st.session_state.lotto_data
err = st.session_state.err

if data:
    # 통계 분석
    flat_list = [n for draw in data for n in draw]
    counts = Counter(flat_list)
    weights = [counts.get(i, 0) + 1 for i in range(1, 46)]
    
    st.success(f"✅ 최신 {len(data)}회차 데이터 수집 완료!")
    
    if st.button("🚀 행운의 번호 추출하기"):
        st.balloons()
        for i in range(5):
            st.write(f"**추천 조합 {i+1}**")
            # 4게임은 가중치, 1게임은 완전 랜덤
            game = sorted(random.choices(range(1, 46), weights=weights, k=6)) if i < 4 else sorted(random.sample(range(1, 46), 6))
            render_balls(game)
else:
    st.error("데이터 수집에 실패했습니다.")
    st.info(f"원인: {err}")
    if st.button("🔄 다시 시도"):
        st.session_state.clear()
        st.rerun()
