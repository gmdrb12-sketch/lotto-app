import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import time
from collections import Counter

# 페이지 설정
st.set_page_config(page_title="Lotto Analysis Pro (10회 안정버전)", page_icon="🍀", layout="centered")

# 디자인 설정 (아이폰 최적화)
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
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background: #6200ee; color: white; border: none; }
    .card { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px; border: 1px solid #eee; }
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

# --- 슈퍼KTS 10회차 실시간 스크래핑 (가장 빠르고 안정적) ---
@st.cache_data(ttl=3600)
def fetch_data_10_draws():
    url = "https://superkts.com/lotto/recent/10"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        balls = soup.select('.ball_645')
        
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

# --- 통계적 조합 필터링 엔진 ---
def validate_combination(combination):
    # 합계(Sum) 필터: 100 ~ 170 사이만 통과
    total = sum(combination)
    if not (100 <= total <= 170):
        return False
        
    # 홀짝(Even/Odd) 필터: 2:4, 3:3, 4:2 비율만 통과
    evens = len([n for n in combination if n % 2 == 0])
    if evens not in [2, 3, 4]:
        return False
        
    return True

# --- 전략적 조합 생성기 ---
def generate_strategy_combinations(strategy_type, w, c_w, top_hot):
    for _ in range(1000): # 필터 통과할 때까지 반복
        if strategy_type == "HOT":
            game = sorted(random.sample(top_hot, 6))
        elif strategy_type == "COLD":
            pool = list(range(1, 46))
            game = sorted(random.choices(pool, weights=c_w, k=6))
        elif strategy_type == "BALANCED":
            evens = 0
            while evens != 3: 
                game = sorted(random.choices(range(1, 46), weights=w, k=6))
                evens = len([n for n in game if n % 2 == 0])
        else: # RANDOM
            game = sorted(random.sample(range(1, 46), 6))

        if validate_combination(game):
            return game
            
    return sorted(random.sample(range(1, 46), 6))

# 앱 실행 화면
st.title("🎯 Lotto Analysis Pro")
st.subheader("10회차 실시간 안정화 버전")

with st.spinner("가장 안정적인 10회차 데이터를 수집 중입니다..."):
    recent_data, err = fetch_data_10_draws()

if recent_data:
    flat_list = [n for draw in recent_data for n in draw]
    counts = Counter(flat_list)
    weights = [counts.get(i, 0) + 1 for i in range(1, 46)]
    cold_weights = [1 / (counts.get(i, 0) + 1) for i in range(1, 46)]
    
    # 10회차 분석은 데이터가 적으므로 핫 번호 풀을 15개로 넉넉히 잡음
    top_15_hot = [num for num, count in counts.most_common(15)]

    st.success(f"✅ 최근 {len(recent_data)}회차 데이터 실시간 동기화 완료!")

    if st.button("🚀 통계 최적화 조합 추출하기"):
        st.divider()
        
        # 조합 1, 2 (핫 번호 중심)
        for i in range(2):
            with st.container():
                st.markdown(f'<div class="card"><b style="color:#d32f2f;">조합 {i+1} (핫 번호 중심)</b></div>', unsafe_allow_html=True)
                game = generate_strategy_combinations("HOT", weights, cold_weights, top_15_hot)
                render_balls(game)

        # 조합 3 (균형 조합)
        with st.container():
            st.markdown('<div class="card"><b style="color:#1976d2;">조합 3 (균형 조합)</b></div>', unsafe_allow_html=True)
            game = generate_strategy_combinations("BALANCED", weights, cold_weights, top_15_hot)
            render_balls(game)

        # 조합 4 (콜드 번호 중심)
        with st.container():
            st.markdown('<div class="card"><b style="color:#388e3c;">조합 4 (콜드 번호 중심)</b></div>', unsafe_allow_html=True)
            game = generate_strategy_combinations("COLD", weights, cold_weights, top_15_hot)
            render_balls(game)
            
        # 조합 5 (순수 랜덤)
        with st.container():
            st.markdown('<div class="card"><b style="color:#616161;">조합 5 (순수 랜덤)</b></div>', unsafe_allow_html=True)
            game = generate_strategy_combinations("RANDOM", weights, cold_weights, top_15_hot)
            render_balls(game)

else:
    st.error("데이터 수집에 실패했습니다.")
    st.info(f"원인: {err if err else '서버 연결 끊김'}")
    if st.button("🔄 다시 시도"):
        st.cache_data.clear()
        st.rerun()
