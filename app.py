import streamlit as st
import random
import time
import requests
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="로또 분석기", page_icon="🍀", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .lotto-ball {
        display: inline-block; width: 44px; height: 44px; line-height: 44px;
        text-align: center; border-radius: 50%; font-weight: 900; font-size: 15px;
        margin: 4px; color: white;
        box-shadow: 0 3px 8px rgba(0,0,0,0.25);
    }
    .ball-1  { background: linear-gradient(135deg, #f9c74f, #f3722c); color: #333; }
    .ball-11 { background: linear-gradient(135deg, #4361ee, #3a0ca3); }
    .ball-21 { background: linear-gradient(135deg, #f72585, #b5179e); }
    .ball-31 { background: linear-gradient(135deg, #6c757d, #343a40); }
    .ball-41 { background: linear-gradient(135deg, #2dc653, #1a7431); }
    .ball-row {
        display: flex; flex-wrap: wrap; justify-content: center;
        background: #f8f9fa; border-radius: 16px; padding: 10px;
        margin: 6px 0; border: 1px solid #e9ecef;
    }
    .combo-label {
        font-size: 13px; color: #6c757d; font-weight: 700;
        margin-bottom: 4px; text-align: center;
    }
    .stButton>button {
        width: 100%; border-radius: 14px; height: 3.5em;
        font-weight: 900; font-size: 17px;
        background: linear-gradient(135deg, #4361ee, #7209b7);
        color: white; border: none;
        box-shadow: 0 4px 15px rgba(67,97,238,0.4);
        transition: transform 0.1s;
    }
    .stButton>button:hover { transform: scale(1.02); }
    .info-box {
        background: #e8f4fd; border-left: 4px solid #4361ee;
        border-radius: 8px; padding: 12px 16px; margin: 8px 0;
        font-size: 14px; color: #1a1a2e;
    }
    </style>
""", unsafe_allow_html=True)


def render_balls(numbers):
    html = '<div class="ball-row">'
    for n in numbers:
        if n <= 10:   cls = "ball-1"
        elif n <= 20: cls = "ball-11"
        elif n <= 30: cls = "ball-21"
        elif n <= 40: cls = "ball-31"
        else:         cls = "ball-41"
        html += f'<div class="lotto-ball {cls}">{n:02d}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def get_draw_number():
    """현재 회차 계산"""
    base_date = datetime(2002, 12, 7)
    return (datetime.now() - base_date).days // 7 + 1


def fetch_from_official(draw_no):
    """동행복권 공식 API"""
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
        "Referer": "https://www.dhlottery.co.kr/",
    }
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
    res = requests.get(url, headers=headers, timeout=8)
    data = res.json()
    if data.get("returnValue") == "success":
        return [data[f"drwtNo{j}"] for j in range(1, 7)]
    return None


def fetch_from_manana(draw_no):
    """마나나 API"""
    url = f"https://api.manana.kr/lotto.json?draw={draw_no}"
    res = requests.get(url, timeout=6)
    if res.status_code == 200:
        d = res.json()[0]
        return [int(d[f"num{j}"]) for j in range(1, 7)]
    return None


def fetch_lotto_data(num_draws=20):
    latest = get_draw_number()
    all_numbers = []
    failed = []

    progress = st.progress(0, text="데이터 수집 중...")

    for i in range(num_draws):
        draw_no = latest - i
        result = None

        # API 1: 마나나 (빠름)
        try:
            result = fetch_from_manana(draw_no)
        except Exception:
            pass

        # API 2: 공식 서버 (fallback)
        if result is None:
            try:
                result = fetch_from_official(draw_no)
            except Exception:
                pass

        if result:
            all_numbers.append(result)
        else:
            failed.append(draw_no)

        progress.progress((i + 1) / num_draws, text=f"{draw_no}회차 수집 중... ({i+1}/{num_draws})")
        time.sleep(0.15)

    progress.empty()
    return all_numbers, failed, latest


def weighted_unique_pick(weights, k=6):
    """가중치 기반으로 중복 없는 6개 추출"""
    population = list(range(1, 46))
    chosen = []
    w = weights[:]
    for _ in range(k):
        total = sum(w)
        r = random.uniform(0, total)
        cum = 0
        for idx, wi in enumerate(w):
            cum += wi
            if r <= cum:
                chosen.append(population[idx])
                w[idx] = 0  # 이미 선택된 번호 제거
                break
    return sorted(chosen)


# ─── 앱 시작 ───────────────────────────────────────────────
st.title("🎰 로또 번호 분석기")
st.caption("실시간 당첨 데이터 기반 확률 추출기")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    num_draws = st.slider("분석할 최근 회차 수", 10, 50, 20, 5)
    num_combos = st.slider("생성할 조합 수", 3, 10, 5)
    st.markdown("---")
    if st.button("🔄 데이터 새로고침"):
        st.session_state.clear()
        st.rerun()

# 데이터 로드 (캐싱)
if 'lotto_data' not in st.session_state:
    with st.spinner(""):
        data, failed, latest_draw = fetch_lotto_data(num_draws)
        st.session_state.lotto_data = data
        st.session_state.failed = failed
        st.session_state.latest_draw = latest_draw

data = st.session_state.lotto_data
failed = st.session_state.failed
latest_draw = st.session_state.latest_draw

# 상태 표시
col1, col2, col3 = st.columns(3)
col1.metric("📡 수집 성공", f"{len(data)}회차")
col2.metric("❌ 수집 실패", f"{len(failed)}회차")
col3.metric("🔢 최신 회차", f"{latest_draw}회")

if failed:
    st.warning(f"실패 회차: {', '.join(map(str, failed))}")

# 번호 생성
if len(data) >= 5:
    flat_list = [n for d in data for n in d]
    counts = Counter(flat_list)
    weights = [counts.get(i, 0) + 1 for i in range(1, 46)]

    # 통계 표시
    with st.expander("📊 번호별 출현 빈도 TOP 10"):
        top10 = counts.most_common(10)
        for num, cnt in top10:
            st.write(f"**{num:02d}번** — {cnt}회 출현")

    st.markdown("---")

    if st.button("🚀 행운의 번호 추출하기"):
        st.subheader("🍀 추천 번호 조합")

        for i in range(num_combos):
            label_map = {
                0: "🔥 핫 번호 중심",
                1: "⚖️ 균형 조합",
                2: "❄️ 콜드 번호 중심",
                3: "🎲 순수 랜덤",
            }

            if i == num_combos - 1:
                # 마지막은 완전 랜덤
                game = sorted(random.sample(range(1, 46), 6))
                label = "🎲 순수 랜덤"
            elif i % 4 == 2:
                # 콜드 번호 (적게 나온 번호 중심)
                cold_weights = [max(1, 20 - counts.get(n, 0)) for n in range(1, 46)]
                game = weighted_unique_pick(cold_weights)
                label = "❄️ 콜드 번호 중심"
            else:
                # 핫 번호 가중치
                game = weighted_unique_pick(weights)
                label = "🔥 핫 번호 중심" if i == 0 else "⚖️ 균형 조합"

            st.markdown(f'<div class="combo-label">조합 {i+1} — {label}</div>', unsafe_allow_html=True)
            render_balls(game)

        st.markdown('<div class="info-box">⚠️ 로또는 완전한 확률 게임입니다. 이 번호는 오락 목적으로만 활용하세요.</div>', unsafe_allow_html=True)

else:
    st.error("데이터 수집에 실패했습니다. 잠시 후 새로고침해 주세요.")
    if st.button("🔄 다시 시도"):
        st.session_state.clear()
        st.rerun()
