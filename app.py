import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import time
from collections import Counter

# 1. 페이지 설정
st.set_page_config(page_title="슈퍼KTS 분석기 Pro", page_icon="🎯", layout="centered")

# 2. 로또공 그래픽 디자인 (CSS)
st.markdown("""
    <style>
    .lotto-ball {
        display: inline-block; width: 42px; height: 42px; line-height: 42px;
        text-align: center; border-radius: 50%; font-weight: bold; font-size: 16px;
        margin: 4px; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        box-shadow: inset -3px -3px 5px rgba(0,0,0,0.2), 2px 2px 5px rgba(0,0,0,0.1);
    }
    .ball-1 { background: #fbc02d; color: #333; } /* 1~10 노랑 */
    .ball-2 { background: #2196f3; } /* 11~20 파랑 */
    .ball-3 { background: #f44336; } /* 21~30 빨강 */
    .ball-4 { background: #9e9e9e; } /* 31~40 회색 */
    .ball-5 { background: #4caf50; } /* 41~45 초록 */
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
        # 💡 여기가 수정된 부분입니다 (오타 제거)
        html += f'<div class="lotto-ball {cls}">{n:02d}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# 3. 데이터 수집 함수 (superkts.com)
def fetch_data():
    url = "https://superkts.com/lotto/recent/20"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        balls = soup.select('.ball_645') # 해당 사이트 번호 클래스
        
        all_draws = []
        temp = []
        for b in balls:
            temp.append(int(b.get_text()))
            if len(temp) == 6:
                all_draws.append(temp)
                temp = []
        return all_draws, None
    except Exception as e:
        return None, str(e)

# 4. 메인 화면 구성
st.title("🎯 슈퍼KTS 실시간 분석기")
st.write("제공해주신 사이트의 최신 20회차 데이터를 실시간 분석합니다.")

if 'lotto_data' not in st.session_state:
    with st.spinner("🔄 데이터 가져오는 중..."):
        data, err = fetch_data()
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
    st.info(f"원인: {err if err else '서버 연결 끊김'}")
    if st.button("🔄 다시 시도"):
        st.session_state.clear()
        st.rerun()
