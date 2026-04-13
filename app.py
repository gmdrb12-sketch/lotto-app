import streamlit as st
import random
import time
import requests
from datetime import datetime
from collections import Counter

# 페이지 설정
st.set_page_config(page_title="Lotto Analysis Pro", page_icon="🍀", layout="centered")

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
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background: #6200ee; color: white; }
    .card { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px; }
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

# 실시간 데이터 수집 (외부 오픈 API 사용)
@st.cache_data(ttl=3600)
def fetch_data():
    base_date = datetime(2002, 12, 7)
    latest_draw = (datetime.now() - base_date).days // 7 + 1
    all_numbers = []
    
    with st.spinner("최신 당첨 번호를 실시간으로 분석 중..."):
        for i in range(20):
            draw_no = latest_draw - i
            url = f"https://api.manana.kr/lotto.json?draw={draw_no}"
            try:
                res = requests.get(url, timeout=3)
                if res.status_code == 200:
                    data = res.json()[0]
                    nums = [int(data[f"num{j}"]) for j in range(1, 7)]
                    all_numbers.append(nums)
            except: continue
    return all_numbers, latest_draw

# --- NEW: 통계적 조합 필터링 엔진 ---
def validate_combination(combination):
    # Sum Filter (통계적 정상 범위: 100-170)
    total = sum(combination)
    if not (100 <= total <= 170):
        return False
        
    # 홀짝(Even/Odd) Ratio Filter (정상 범위: 2:4, 3:3, 4:2)
    evens = len([n for n in combination if n % 2 == 0])
    if evens not in [2, 3, 4]:
        return False
        
    # 필터를 통과함
    return True

# --- NEW: 전략적 조합 생성 함수 ---
def generate_strategy_combinations(strategy_type, w, c_w, top_hot):
    # 통과하는 조합이 나올 때까지 최대 1000번 시도
    for _ in range(1000):
        if strategy_type == "HOT": # 분석된 상위 번호 집중 투하 (당첨 번호 뭉치기 핵심 전략)
            # 상위 핫 넘버 12개 중 6개 랜덤 선택 (가중치 적용 안 함)
            game = sorted(random.sample(top_hot, 6))
        elif strategy_type == "COLD":
            # 콜드 가중치 기반
            pool = list(range(1, 46))
            game = sorted(random.choices(pool, weights=c_w, k=6))
        elif strategy_type == "BALANCED":
            # 핫 가중치 기반 + 매우 엄격한 필터링 (예: 엄격히 3:3 홀짝)
            evens = 0
            while evens != 3:
                game = sorted(random.choices(range(1, 46), weights=w, k=6))
                evens = len([n for n in game if n % 2 == 0])
        else: # PURE_RANDOM
            game = sorted(random.sample(range(1, 46), 6))

        # 생성된 조합 검증 (필터링 엔진 통과 여부 확인)
        if validate_combination(game):
            return game
            
    # 시도 실패 시 그냥 리턴 (거의 발생 안 함)
    return sorted(random.sample(range(1, 46), 6))

# 앱 실행
st.title("🎯 Lotto Analysis Pro")
st.subheader("실시간 20회차 분석 및 통계 조합 엔진")

recent_data, latest_no = fetch_data()

if recent_data:
    flat_list = [n for draw in recent_data for n in draw]
    counts = Counter(flat_list)
    # 핫 가중치 (기본)
    weights = [counts.get(i, 0) + 1 for i in range(1, 46)]
    # 콜드 가중치 (나오지 않은 번호 확률 UP)
    cold_weights = [1 / (counts.get(i, 0) + 1) for i in range(1, 46)]
    # 상위 핫 넘버 12개 추출
    top_12_hot = [num for num, count in counts.most_common(12)]

    st.success(f"최근 {latest_no}회차 기반 실시간 분석 완료")

    if st.button("🚀 통계 최적화 조합 추출하기"):
        st.divider()
        
        # 1-2게임: 핫 번호 중심 (상위 핫 넘버 집중 투하 전략)
        for i in range(2):
            with st.container():
                st.markdown(f'<div class="card"><b style="color:red;">조합 {i+1} (핫 번호 중심)</b></div>', unsafe_allow_html=True)
                game = generate_strategy_combinations("HOT", weights, cold_weights, top_12_hot)
                render_balls(game)
                st.write("")

        # 3게임: 균형 조합
        with st.container():
            st.markdown('<div class="card"><b style="color:blue;">조합 3 (균형 조합)</b></div>', unsafe_allow_html=True)
            game = generate_strategy_combinations("BALANCED", weights, cold_weights, top_12_hot)
            render_balls(game)
            st.write("")

        # 4게임: 콜드 번호 중심
        with st.container():
            st.markdown('<div class="card"><b style="color:green;">조합 4 (콜드 번호 중심)</b></div>', unsafe_allow_html=True)
            game = generate_strategy_combinations("COLD", weights, cold_weights, top_12_hot)
            render_balls(game)
            st.write("")
            
        # 5게임: 순수 랜덤
        with st.container():
            st.markdown('<div class="card"><b style="color:gray;">조합 5 (순수 랜덤)</b></div>', unsafe_allow_html=True)
            game = generate_strategy_combinations("RANDOM", weights, cold_weights, top_12_hot)
            render_balls(game)
            st.write("")

else:
    st.error("데이터 수집 서버와 통신이 원활하지 않습니다. 잠시 후 새로고침 해주세요.")
