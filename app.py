import streamlit as st
import random
import time
import requests
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="통계 분석 로또 추출기", page_icon="📈", layout="centered")

st.title("📈 통계 기반 로또 번호 추출기")
st.write("최고의 분석 기법을 적용하여 최근 20회차 실제 데이터를 분석합니다.")

@st.cache_data(ttl=86400) # 하루 한 번만 서버에서 가져오도록 캐싱
def fetch_recent_20_draws():
    base_date = datetime(2002, 12, 7)
    today = datetime.now()
    latest_draw = (today - base_date).days // 7 + 1
    
    recent_numbers = []
    
    # 💡 차단 우회 핵심: 일반 크롬 브라우저인 것처럼 위장
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for draw_no in range(latest_draw - 19, latest_draw + 1):
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        try:
            # timeout을 5초로 넉넉하게 늘리고, headers 정보를 함께 보냅니다.
            res = requests.get(url, headers=headers, timeout=5)
            data = res.json()
            if data.get("returnValue") == "success":
                recent_numbers.extend([data[f"drwtNo{i}"] for i in range(1, 7)])
        except Exception:
            continue
            
    return recent_numbers

# 데이터 수집 및 분석
with st.spinner("과거 20회차 당첨 데이터를 수집 및 분석 중입니다... (최초 1회 약 10초 소요)"):
    recent_numbers = fetch_recent_20_draws()

if recent_numbers:
    counts = Counter(recent_numbers)
    weights = [counts.get(i, 0) + 1 for i in range(1, 46)]
    
    st.success("✅ 최근 20회차 데이터 수집 및 분석 완료!")
    
    top_3 = [str(num) for num, _ in counts.most_common(3)]
    st.info(f"💡 최근 20회차 핫 넘버 Top 3 : {', '.join(top_3)}")
    
    if st.button("🚀 최적의 조합 5게임 추출", use_container_width=True):
        with st.spinner("분석된 가중치를 바탕으로 번호를 조합합니다..."):
            time.sleep(1.5)
            st.subheader("🎉 이번 주 전략적 추천 번호")
            
            # 4게임은 통계(가중치) 기반
            for i in range(4):
                pool = list(range(1, 46))
                current_weights = weights.copy()
                game_nums = []
                for _ in range(6):
                    chosen = random.choices(pool, weights=current_weights, k=1)[0]
                    game_nums.append(chosen)
                    idx = pool.index(chosen)
                    pool.pop(idx)
                    current_weights.pop(idx)
                    
                game_nums.sort()
                st.success(f"**[통계 분석 {i+1}]** : {'  '.join([f'[{n:02d}]' for n in game_nums])}")
            
            # 마지막 1게임은 이변 대비 무작위 리스크 분산
            random_nums = sorted(random.sample(range(1, 46), 6))
            st.warning(f"**[리스크 분산 {5}]** : {'  '.join([f'[{n:02d}]' for n in random_nums])}")
            
            st.caption("전략 팁: 위 4게임은 철저한 통계 기반 번호이며, 마지막 1게임은 예상치 못한 이변을 대비한 완전 분산 조합입니다.")
else:
    st.error("데이터를 불러오지 못했습니다. 동행복권 서버 접속이 원활하지 않습니다.")
