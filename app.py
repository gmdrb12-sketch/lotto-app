import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import time
from collections import Counter

# 페이지 설정
st.set_page_config(page_title="슈퍼KTS 기반 분석기", page_icon="🎯", layout="centered")

# 고급 CSS (로또공 그래픽)
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
    .analysis-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #eee; }
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

# 실시간 스크래핑 함수 (superkts.com 기준)
def fetch_superkts_data():
    url = "https://superkts.com/lotto/recent/20" # 최근 20회차 페이지
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    recent_numbers = []
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # 해당 사이트의 당첨번호 숫자들을 찾는 로직
            balls = soup.select('.ball_645') # superkts의 로또공 클래스 선택
            
            temp_nums = []
            for i, ball in enumerate(balls):
                num = int(ball.get_text())
                temp_nums.append(num)
                # 6개가 모일 때마다 하나의 회차로 묶음
                if len(temp_nums) == 6:
                    recent_numbers.append(temp_nums)
                    temp_nums = []
        return recent_numbers, None
    except Exception as e:
        return None, str(e)

# 메인 앱 로직
st.title("🎯 슈퍼KTS 실시간 분석기")
st.write("제공해주신 사이트의 최신 20회차 당첨 데이터를 실시간 분석합니다.")

if 'data' not in st.session_state:
    with st.spinner("🔄 실시간 데이터 동기화 중..."):
        data, err = fetch_superkts_data()
        st.session_state.data = data
        st.session_state.err = err

data = st.session_state.data
err = st.session_state.err

if data:
    # 데이터 분석
    flat_list = [n for draw in data for n in draw]
    counts = Counter(flat_list)
    weights = [counts.get(i, 0) + 1 for i in range(1, 46)]
    
    st.success(f"✅ 최신 {len(data)}회차 데이터 수집 완료!")
    
    # 분석 카드
    st.markdown(f"""
    <div class="analysis-card">
        <h4 style="margin:0; text-align:center;">📊 데이터 분석 결과</h4>
        <div style="display:flex; justify-content:space-around; margin-top:15px; text-align:center;">
            <div><small>가장 많이 나옴</small><br/><b>{counts.most_common(1)[0][0]}번</b></div>
            <div><small>가장 안 나옴</small><br/><b>{sorted(counts.items(), key=lambda x:x[1])[0][0]}번</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 행운의 번호 추출하기"):
        st.balloons()
        for i in range(5):
            st.write(f"**조합 {i+1}**")
            if i < 4:
                pool = list(range(1, 46))
                w = weights.copy()
                game = []
                for _ in range(6):
                    c = random.choices(pool, weights=w, k=1)[0]
                    game.append(c)
                    idx = pool.index(c); pool.pop(idx); w.pop(idx)
                game.sort()
            else:
                game = sorted(random.sample(range(1, 46), 6))
            render_balls(game)

else:
    st.error("데이터 수집에 실패했습니다.")
    st.info(f"원인: {err if err else '서버 차단'}")
    if st.button("🔄 다시 시도"):
        st.session_state.clear()
        st.rerun()
