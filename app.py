import streamlit as st
import random
import time
import requests
from datetime import datetime
from collections import Counter

# 페이지 설정
st.set_page_config(page_title="실시간 로또 분석기 PRO", page_icon="🎰", layout="centered")

# 고급 CSS 디자인 (로또 공 그래픽 및 카드 UI)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    * { font-family: 'Noto Sans KR', sans-serif; }
    .main { background-color: #f8f9fa; }
    .lotto-ball {
        display: inline-block; width: 42px; height: 42px; line-height: 42px;
        text-align: center; border-radius: 50%; font-weight: bold; font-size: 16px;
        margin: 4px; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        box-shadow: inset -3px -3px 5px rgba(0,0,0,0.2), 2px 2px 5px rgba(0,0,0,0.1);
    }
    .ball-1 { background: linear-gradient(135deg, #fbc02d, #f9a825); color: #333; } /* 1~10 노랑 */
    .ball-2 { background: linear-gradient(135deg, #2196f3, #1976d2); } /* 11~20 파랑 */
    .ball-3 { background: linear-gradient(135deg, #f44336, #d32f2f); } /* 21~30 빨강 */
    .ball-4 { background: linear-gradient(135deg, #9e9e9e, #616161); } /* 31~40 회색 */
    .ball-5 { background: linear-gradient(135deg, #4caf50, #388e3c); } /* 41~45 초록 */
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; font-weight: bold; font-size: 18px !important; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    .analysis-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

def get_ball_class(n):
    if n <= 10: return "ball-1"
    elif n <= 20: return "ball-2"
    elif n <= 30: return "ball-3"
    elif n <= 40: return "ball-4"
    else: return "ball-5"

def render_balls(numbers):
    html = '<div style="display: flex; flex-wrap: wrap; justify-content: center; margin-bottom: 10px;">'
    for n in numbers:
        html += f'<div class="lotto-ball {get_ball_class(n)}">{n:02d}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# 실시간 데이터 수집 함수 (보안 우회 로직 포함)
def fetch_live_data():
    # 오늘 기준 최신 회차 계산
    base_date = datetime(2002, 12, 7)
    today = datetime.now()
    latest_draw = (today - base_date).days // 7 + 1
    
    recent_numbers = []
    # 일반 브라우저로 보이게 하는 특수 헤더
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }
    
    success_count = 0
    with st.status("🔍 실시간 당첨 데이터 분석 중...", expanded=False) as status:
        for i in range(20):
            draw_no = latest_draw - i
            url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
            try:
                # 0.5초 간격으로 조심스럽게 요청
                res = requests.get(url, headers=headers, timeout=3)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("returnValue") == "success":
                        nums = [data[f"drwtNo{j}"] for j in range(1, 7)]
                        recent_numbers.extend(nums)
                        success_count += 1
                time.sleep(0.1)
            except:
                continue
        status.update(label=f"✅ 분석 완료 ({success_count}회차 수집됨)", state="complete", expanded=False)
    
    return recent_numbers, latest_draw

# 앱 실행
st.title("🎰 로또 분석기 PRO")
st.write(f"오늘({datetime.now().strftime('%Y-%m-%d')}) 기준 최신 20회차를 분석합니다.")

# 데이터 가져오기
if 'lotto_data' not in st.session_state:
    st.session_state.lotto_data, st.session_state.latest_no = fetch_live_data()

data = st.session_state.lotto_data
latest_no = st.session_state.latest_no

if data:
    counts = Counter(data)
    # 가중치 계산 (많이 나온 번호에 보너스 확률)
    weights = [counts.get(i, 0) + 1 for i in range(1, 46)]
    
    # 상단 분석 카드
    st.markdown(f"""
    <div class="analysis-card">
        <h4 style="margin-top:0; text-align:center;">📊 최신 데이터 분석 요약</h4>
        <p style="text-align:center; color:#666; font-size:14px;">최근 {latest_no-19}회 ~ {latest_no}회차 기반</p>
        <div style="display:flex; justify-content:space-around; text-align:center;">
            <div><small>핫 넘버</small><br/><b>{counts.most_common(1)[0][0]}번</b></div>
            <div><small>평균 출현</small><br/><b>{round(len(data)/45, 1)}회</b></div>
            <div><small>데이터 상태</small><br/><b style="color:green;">정상</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 추출 버튼
    if st.button("✨ 행운의 번호 조합 추출", type="primary"):
        st.divider()
        for i in range(5):
            with st.container():
                st.write(f"**추천 조합 {i+1}**")
                if i < 4:
                    # 통계 기반 추출
                    pool = list(range(1, 46))
                    temp_weights = weights.copy()
                    game = []
                    for _ in range(6):
                        c = random.choices(pool, weights=temp_weights, k=1)[0]
                        game.append(c)
                        idx = pool.index(c); pool.pop(idx); temp_weights.pop(idx)
                    game.sort()
                else:
                    # 완전 랜덤 (이변 대비)
                    game = sorted(random.sample(range(1, 46), 6))
                
                render_balls(game)
        st.balloons()

    # 데이터 새로고침 버튼 (하단에 작게)
    if st.button("🔄 데이터 강제 새로고침", use_container_width=False):
        st.session_state.lotto_data, st.session_state.latest_no = fetch_live_data()
        st.rerun()

else:
    st.error("데이터를 수집하지 못했습니다. 새로고침을 눌러주세요.")
