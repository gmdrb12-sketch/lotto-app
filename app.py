import streamlit as st
import random
import time
import requests
from datetime import datetime
from collections import Counter

# 1. 페이지 기본 설정 및 디자인 (아이폰 최적화)
st.set_page_config(page_title="Lotto 실시간 분석기", page_icon="🎯", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@700&display=swap');
    .main { background-color: #f0f2f6; }
    .lotto-ball {
        display: inline-block; width: 40px; height: 40px; line-height: 40px;
        text-align: center; border-radius: 50%; font-weight: bold; font-size: 16px;
        margin: 3px; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        box-shadow: inset -3px -3px 5px rgba(0,0,0,0.2);
    }
    .ball-1 { background: #fbc02d; color: #333; } /* 1-10 */
    .ball-11 { background: #1976d2; } /* 11-20 */
    .ball-21 { background: #d32f2f; } /* 21-30 */
    .ball-31 { background: #616161; } /* 31-40 */
    .ball-41 { background: #388e3c; } /* 41-45 */
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background: #6200ee; color: white; border: none; }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px; }
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

# 2. 실시간 데이터 수집 (외부 오픈 API 사용 - 차단 우회)
@st.cache_data(ttl=3600) # 1시간 동안은 가져온 데이터 재사용 (속도 향상)
def fetch_realtime_20_draws():
    # 현재 날짜 기준 최신 회차 계산
    base_date = datetime(2002, 12, 7)
    latest_draw = (datetime.now() - base_date).days // 7 + 1
    
    all_numbers = []
    success_count = 0
    
    # 최근 20회차 루프
    for i in range(20):
        draw_no = latest_draw - i
        # 오픈 API 주소 (동행복권 데이터를 미러링하는 서버)
        url = f"https://api.manana.kr/lotto.json?draw={draw_no}"
        try:
            res = requests.get(url, timeout=3)
            if res.status_code == 200:
                data = res.json()[0] # 리스트 형태의 첫 번째 데이터
                nums = [int(data[f"num{j}"]) for j in range(1, 7)]
                all_numbers.append(nums)
                success_count += 1
        except:
            continue
    return all_numbers, latest_draw

# 3. 앱 메인 로직
st.title("🎯 Lotto Real-time Pro")
st.subheader("실시간 20회차 분석 엔진")

with st.spinner("최신 당첨 번호를 실시간으로 수집 중..."):
    recent_data, latest_no = fetch_realtime_20_draws()

if recent_data:
    # 데이터 평탄화 및 분석
    flat_list = [n for draw in recent_data for n in draw]
    counts = Counter(flat_list)
    weights = [counts.get(i, 0) + 1 for i in range(1, 46)]

    # 분석 요약 카드
    st.markdown(f"""
    <div class="card">
        <div style="text-align:center;">
            <small style="color:#666;">데이터 기준: {latest_no-19}회 ~ {latest_no}회</small><br>
            <b>현재 가장 뜨거운 번호 (Top 3)</b><br>
            <span style="font-size:20px; color:#6200ee;">
                {counts.most_common(3)[0][0]}번, {counts.most_common(3)[1][0]}번, {counts.most_common(3)[2][0]}번
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 추출 버튼
    if st.button("🚀 실시간 분석 조합 생성"):
        st.balloons()
        for i in range(5):
            st.markdown(f"**추천 조합 {i+1}**")
            if i < 4:
                # 통계 가중치 기반 추출
                pool = list(range(1, 46))
                w = weights.copy()
                game = []
                for _ in range(6):
                    c = random.choices(pool, weights=w, k=1)[0]
                    game.append(c)
                    idx = pool.index(c); pool.pop(idx); w.pop(idx)
                game.sort()
            else:
                # 완전 랜덤 (이변 대비)
                game = sorted(random.sample(range(1, 46), 6))
            render_balls(game)
            st.write("")
            
    with st.expander("📊 수집된 최근 20회차 데이터 확인"):
        for i, d in enumerate(recent_data):
            st.write(f"{latest_no-i}회차: {sorted(d)}")

else:
    st.error("데이터 수집 서버와 통신이 원활하지 않습니다. 잠시 후 새로고침 해주세요.")
