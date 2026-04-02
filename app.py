import streamlit as st
import random
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(page_title="로또 분석기", page_icon="🍀", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
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
    .ball-bonus { background: linear-gradient(135deg, #aaa, #555); }
    .ball-row {
        display: flex; flex-wrap: wrap; justify-content: center; align-items: center;
        background: #f8f9fa; border-radius: 16px; padding: 10px;
        margin: 4px 0; border: 1px solid #e9ecef;
    }
    .draw-label {
        font-size: 12px; color: #888; font-weight: 700;
        text-align: center; margin-top: 8px;
    }
    .plus-sign { color: #aaa; font-size: 18px; margin: 0 4px; line-height: 44px; }
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
    }
    .info-box {
        background: #e8f4fd; border-left: 4px solid #4361ee;
        border-radius: 8px; padding: 12px 16px; margin: 8px 0; font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)


def ball_html(n, is_bonus=False):
    if is_bonus:
        cls = "ball-bonus"
    elif n <= 10:   cls = "ball-1"
    elif n <= 20:   cls = "ball-11"
    elif n <= 30:   cls = "ball-21"
    elif n <= 40:   cls = "ball-31"
    else:           cls = "ball-41"
    return f'<div class="lotto-ball {cls}">{n:02d}</div>'


def render_draw(numbers, bonus=None):
    html = '<div class="ball-row">'
    for n in numbers:
        html += ball_html(n)
    if bonus:
        html += '<span class="plus-sign">+</span>'
        html += ball_html(bonus, is_bonus=True)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_balls(numbers):
    html = '<div class="ball-row">'
    for n in numbers:
        html += ball_html(n)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


@st.cache_data(ttl=1800)  # 30분 캐시
def fetch_from_picknum():
    """
    picknum.com/lotto 에서 최근 10회 당첨번호 파싱
    HTML 구조: 각 회차 링크 텍스트에 회차번호 + 날짜 + 6개 번호 + 보너스 포함
    """
    url = "https://picknum.com/lotto"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://picknum.com/",
    }
    res = requests.get(url, headers=headers, timeout=12)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    results = []

    # 각 회차 블록: <a href="/lotto/1217회"> 형태
    # 텍스트 내에 "1217회 2026-03-28 8 10 15 20 29 31 + 41 ..." 포함
    draw_links = soup.select('a[href*="/lotto/"]')

    for link in draw_links:
        href = link.get("href", "")
        # /lotto/숫자 형태만 (목록 외 링크 제외)
        if not re.match(r"^/lotto/\d+$", href):
            continue

        draw_no = int(re.search(r"\d+", href).group())
        text = link.get_text(separator=" ", strip=True)

        # 텍스트에서 1~45 사이 숫자 추출
        nums = [int(n) for n in re.findall(r'\b([1-9]|[1-3][0-9]|4[0-5])\b', text)
                if 1 <= int(n) <= 45]

        # 중복 제거하면서 순서 유지
        seen = []
        for n in nums:
            if n not in seen:
                seen.append(n)

        if len(seen) >= 7:
            numbers = sorted(seen[:6])
            bonus   = seen[6]
            results.append({
                "draw":    draw_no,
                "numbers": numbers,
                "bonus":   bonus,
            })

        if len(results) >= 10:
            break

    return results


def weighted_unique_pick(weights, k=6):
    population = list(range(1, 46))
    chosen, w = [], weights[:]
    for _ in range(k):
        total = sum(w)
        if total == 0:
            remaining = [p for p in population if p not in chosen]
            chosen.append(random.choice(remaining))
            continue
        r, cum = random.uniform(0, total), 0
        for idx, wi in enumerate(w):
            cum += wi
            if r <= cum:
                chosen.append(population[idx])
                w[idx] = 0
                break
    return sorted(chosen)


# ── 앱 UI ────────────────────────────────────────────────────

st.title("🎰 로또 번호 분석기")
st.caption("picknum.com 최근 10회 실시간 데이터 기반")

with st.sidebar:
    st.header("⚙️ 설정")
    num_combos = st.slider("생성할 조합 수", 3, 10, 5)
    st.markdown("---")
    if st.button("🔄 데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()

# ── 데이터 로드 ───────────────────────────────────────────────
with st.spinner("📡 picknum.com에서 최근 10회 데이터 수집 중..."):
    try:
        draw_data = fetch_from_picknum()
        if not draw_data:
            raise ValueError("파싱 결과 없음")
    except Exception as e:
        st.error(f"❌ 데이터 수집 실패: {e}")
        draw_data = []

# ── 결과 표시 ─────────────────────────────────────────────────
if draw_data:
    latest = draw_data[0]
    st.success(f"✅ 최근 {len(draw_data)}회차 데이터 로드 완료 (최신: {latest['draw']}회)")

    # 최신 회차 크게 표시
    st.subheader(f"🏆 최신 당첨번호 — {latest['draw']}회")
    render_draw(latest["numbers"], latest["bonus"])

    st.markdown("---")

    # 최근 10회 전체 목록
    with st.expander("📋 최근 10회 당첨번호 전체 보기", expanded=False):
        for item in draw_data:
            st.markdown(f'<div class="draw-label">{item["draw"]}회차</div>', unsafe_allow_html=True)
            render_draw(item["numbers"], item["bonus"])

    st.markdown("---")

    # 통계 (보너스 제외, 당첨번호 6개만)
    flat_list = [n for item in draw_data for n in item["numbers"]]
    counts    = Counter(flat_list)
    weights   = [counts.get(i, 0) + 1 for i in range(1, 46)]

    with st.expander("📊 번호별 출현 빈도 (최근 10회)"):
        top_nums = counts.most_common()
        cols = st.columns(5)
        for idx, (num, cnt) in enumerate(top_nums):
            cols[idx % 5].metric(f"{num:02d}번", f"{cnt}회")

    st.markdown("---")

    # 번호 추출
    if st.button("🚀 행운의 번호 추출하기"):
        st.subheader("🍀 추천 번호 조합")
        strategies = ["🔥 핫 번호 중심", "⚖️ 균형 조합", "❄️ 콜드 번호 중심", "🎲 순수 랜덤"]

        for i in range(num_combos):
            s = strategies[i % len(strategies)]

            if "랜덤" in s or i == num_combos - 1:
                game = sorted(random.sample(range(1, 46), 6))
            elif "콜드" in s:
                cold_w = [max(1, 10 - counts.get(n, 0)) for n in range(1, 46)]
                game = weighted_unique_pick(cold_w)
            else:
                game = weighted_unique_pick(weights)

            st.markdown(f'<div class="combo-label">조합 {i+1} — {s}</div>', unsafe_allow_html=True)
            render_balls(game)

        st.markdown('<div class="info-box">⚠️ 로또는 확률 게임입니다. 오락 목적으로만 활용하세요.</div>', unsafe_allow_html=True)

else:
    st.error("데이터를 불러올 수 없습니다.")
    if st.button("🔄 다시 시도"):
        st.cache_data.clear()
        st.rerun()
