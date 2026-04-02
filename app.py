import streamlit as st
import random
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(
    page_title="LOTTO 번호 분석기",
    page_icon="🍀",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

/* ── 전체 배경 ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #0a0e1a !important;
    color: #e8eaf0 !important;
}
[data-testid="stAppViewContainer"] > .main {
    background: #0a0e1a !important;
}
[data-testid="stHeader"] { background: transparent !important; }
section[data-testid="stSidebar"] {
    background: #0d1120 !important;
    border-right: 1px solid #1e2540;
}
* { font-family: 'Noto Sans KR', sans-serif; box-sizing: border-box; }

/* ── 히어로 타이틀 ── */
.hero {
    text-align: center;
    padding: 48px 0 32px;
    position: relative;
}
.hero-eyebrow {
    font-size: 11px;
    letter-spacing: 4px;
    color: #c9a84c;
    text-transform: uppercase;
    font-weight: 500;
    margin-bottom: 10px;
}
.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(52px, 10vw, 80px);
    letter-spacing: 6px;
    line-height: 1;
    background: linear-gradient(135deg, #c9a84c 0%, #f5d98b 40%, #c9a84c 70%, #9a7a2e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}
.hero-sub {
    font-size: 13px;
    color: #5a6180;
    letter-spacing: 1px;
    margin-top: 12px;
}

/* ── 카드 ── */
.card {
    background: linear-gradient(145deg, #111627, #0d1220);
    border: 1px solid #1e2845;
    border-radius: 20px;
    padding: 28px;
    margin: 14px 0;
    position: relative;
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #c9a84c44, transparent);
}
.card-title {
    font-size: 11px;
    letter-spacing: 3px;
    color: #c9a84c;
    text-transform: uppercase;
    font-weight: 700;
    margin-bottom: 20px;
}

/* ── 당첨번호 볼 ── */
.balls-wrap {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 4px 0;
}
.lotto-ball {
    width: 48px; height: 48px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 15px;
    position: relative;
    flex-shrink: 0;
    animation: ballPop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
.lotto-ball::after {
    content: '';
    position: absolute;
    top: 5px; left: 8px;
    width: 12px; height: 6px;
    background: rgba(255,255,255,0.35);
    border-radius: 50%;
    transform: rotate(-30deg);
}
@keyframes ballPop {
    from { transform: scale(0); opacity: 0; }
    to   { transform: scale(1); opacity: 1; }
}
/* 번호대별 색상 */
.b1  { background: radial-gradient(circle at 35% 35%, #ffe066, #f5a623); color: #3d2800; }
.b11 { background: radial-gradient(circle at 35% 35%, #6ea8fe, #1a56db); color: #fff; }
.b21 { background: radial-gradient(circle at 35% 35%, #f87171, #dc2626); color: #fff; }
.b31 { background: radial-gradient(circle at 35% 35%, #9ca3af, #4b5563); color: #fff; }
.b41 { background: radial-gradient(circle at 35% 35%, #4ade80, #16a34a); color: #fff; }
.bonus-ball {
    background: radial-gradient(circle at 35% 35%, #e879f9, #9333ea);
    color: #fff; opacity: 0.85;
}
.plus { color: #2e3550; font-size: 20px; font-weight: 900; margin: 0 2px; }

/* ── 회차 헤더 ── */
.draw-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}
.draw-no {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 28px;
    letter-spacing: 2px;
    color: #c9a84c;
    line-height: 1;
}
.draw-date {
    font-size: 12px;
    color: #3d4668;
    font-weight: 500;
}

/* ── 최신 회차 큰 카드 ── */
.latest-card {
    background: linear-gradient(145deg, #131928, #0f1622);
    border: 1px solid #c9a84c33;
    border-radius: 24px;
    padding: 36px 28px;
    margin: 14px 0;
    position: relative;
    overflow: hidden;
}
.latest-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #c9a84c, transparent);
}
.latest-card::after {
    content: '';
    position: absolute;
    bottom: -60px; right: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, #c9a84c08, transparent 70%);
    pointer-events: none;
}
.latest-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #c9a84c18;
    border: 1px solid #c9a84c44;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 11px;
    letter-spacing: 2px;
    color: #c9a84c;
    text-transform: uppercase;
    font-weight: 700;
    margin-bottom: 16px;
}
.latest-ball {
    width: 58px; height: 58px;
    font-size: 18px;
}

/* ── 조합 카드 ── */
.combo-card {
    background: #0d1220;
    border: 1px solid #1a2240;
    border-radius: 16px;
    padding: 20px 20px 16px;
    margin: 10px 0;
    transition: border-color 0.2s, transform 0.2s;
}
.combo-card:hover {
    border-color: #c9a84c44;
    transform: translateY(-2px);
}
.combo-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.combo-num {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 20px;
    letter-spacing: 2px;
    color: #2e3a5c;
}
.combo-strategy {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 3px 10px;
    border-radius: 20px;
}
.strategy-hot  { background: #f5a62322; color: #f5a623; border: 1px solid #f5a62344; }
.strategy-bal  { background: #1a56db22; color: #6ea8fe; border: 1px solid #1a56db44; }
.strategy-cold { background: #16a34a22; color: #4ade80; border: 1px solid #16a34a44; }
.strategy-rand { background: #9333ea22; color: #e879f9; border: 1px solid #9333ea44; }

/* ── 통계 바 ── */
.stat-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 5px 0;
}
.stat-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 18px;
    letter-spacing: 1px;
    width: 36px;
    text-align: right;
    flex-shrink: 0;
}
.stat-bar-wrap {
    flex: 1;
    height: 6px;
    background: #1a2240;
    border-radius: 3px;
    overflow: hidden;
}
.stat-bar {
    height: 100%;
    border-radius: 3px;
    transition: width 0.6s ease;
}
.stat-count {
    font-size: 11px;
    color: #3d4668;
    width: 24px;
    text-align: right;
    flex-shrink: 0;
}

/* ── 메트릭 ── */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 14px 0;
}
.metric-box {
    background: #0d1220;
    border: 1px solid #1a2240;
    border-radius: 14px;
    padding: 16px;
    text-align: center;
}
.metric-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 28px;
    letter-spacing: 1px;
    color: #c9a84c;
    line-height: 1;
}
.metric-label {
    font-size: 10px;
    color: #3d4668;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 4px;
    font-weight: 700;
}

/* ── 버튼 ── */
.stButton > button {
    width: 100%;
    height: 58px;
    background: linear-gradient(135deg, #c9a84c, #9a7a2e) !important;
    color: #0a0e1a !important;
    border: none !important;
    border-radius: 16px !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 20px !important;
    letter-spacing: 4px !important;
    box-shadow: 0 8px 32px #c9a84c33 !important;
    transition: all 0.2s !important;
    margin: 8px 0 !important;
}
.stButton > button:hover {
    box-shadow: 0 12px 40px #c9a84c55 !important;
    transform: translateY(-2px) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] * { color: #8892b0 !important; }
[data-testid="stSidebar"] .stSlider > div { background: transparent !important; }

/* ── 구분선 ── */
hr {
    border: none !important;
    border-top: 1px solid #1a2240 !important;
    margin: 24px 0 !important;
}

/* ── 경고 박스 ── */
.warn-box {
    background: #c9a84c0d;
    border: 1px solid #c9a84c22;
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 12px;
    color: #6b7490;
    text-align: center;
    letter-spacing: 0.5px;
    margin-top: 20px;
}

/* streamlit 기본 요소 숨김/스타일 */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stStatusWidget"] { display: none; }
.stSpinner > div { border-top-color: #c9a84c !important; }
</style>
""", unsafe_allow_html=True)


# ── 유틸 ─────────────────────────────────────────────────────

def ball_class(n, is_bonus=False):
    if is_bonus: return "bonus-ball"
    if n <= 10:  return "b1"
    if n <= 20:  return "b11"
    if n <= 30:  return "b21"
    if n <= 40:  return "b31"
    return "b41"

def balls_html(numbers, bonus=None, size_class=""):
    parts = []
    for i, n in enumerate(numbers):
        delay = f"animation-delay:{i*0.06:.2f}s"
        parts.append(f'<div class="lotto-ball {ball_class(n)} {size_class}" style="{delay}">{n:02d}</div>')
    if bonus is not None:
        parts.append('<span class="plus">＋</span>')
        delay = f"animation-delay:{len(numbers)*0.06:.2f}s"
        parts.append(f'<div class="lotto-ball {ball_class(bonus, True)} {size_class}" style="{delay}">{bonus:02d}</div>')
    return f'<div class="balls-wrap">{"".join(parts)}</div>'


@st.cache_data(ttl=1800)
def fetch_from_picknum():
    url = "https://picknum.com/lotto"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://picknum.com/",
    }
    res = requests.get(url, headers=headers, timeout=12)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    results = []
    draw_links = soup.select('a[href*="/lotto/"]')

    for link in draw_links:
        href = link.get("href", "")
        if not re.match(r"^/lotto/\d+$", href):
            continue
        draw_no = int(re.search(r"\d+", href).group())
        text = link.get_text(separator=" ", strip=True)

        # 날짜 파싱
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        date_str = date_match.group(1) if date_match else ""

        nums = [int(n) for n in re.findall(r'\b([1-9]|[1-3][0-9]|4[0-5])\b', text)
                if 1 <= int(n) <= 45]
        seen = []
        for n in nums:
            if n not in seen:
                seen.append(n)

        if len(seen) >= 7:
            results.append({
                "draw":    draw_no,
                "date":    date_str,
                "numbers": sorted(seen[:6]),
                "bonus":   seen[6],
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


# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    num_combos = st.slider("조합 수", 3, 10, 5)
    st.markdown("---")
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("<div style='font-size:11px;color:#2e3550;margin-top:20px'>picknum.com 기반 · 30분 캐시</div>", unsafe_allow_html=True)


# ── 히어로 ───────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Korea Lotto 6/45</div>
    <h1 class="hero-title">LUCKY PICK</h1>
    <p class="hero-sub">실시간 당첨 데이터 기반 번호 분석기</p>
</div>
""", unsafe_allow_html=True)


# ── 데이터 로드 ───────────────────────────────────────────────
with st.spinner(""):
    try:
        draw_data = fetch_from_picknum()
        if not draw_data:
            raise ValueError("파싱 결과 없음")
        ok = True
    except Exception as e:
        st.error(f"데이터 수집 실패: {e}")
        draw_data = []
        ok = False


if not ok:
    st.stop()

latest = draw_data[0]

# ── 최신 회차 ────────────────────────────────────────────────
st.markdown(f"""
<div class="latest-card">
    <div class="latest-badge">✦ 최신 당첨번호</div>
    <div class="draw-header">
        <div class="draw-no">{latest['draw']}회</div>
        <div class="draw-date">{latest['date']}</div>
    </div>
    {balls_html(latest['numbers'], latest['bonus'], 'latest-ball')}
</div>
""", unsafe_allow_html=True)

# ── 메트릭 ───────────────────────────────────────────────────
flat_list = [n for item in draw_data for n in item["numbers"]]
counts    = Counter(flat_list)
top_num   = counts.most_common(1)[0][0]
cold_num  = counts.most_common()[-1][0]

st.markdown(f"""
<div class="metrics-row">
    <div class="metric-box">
        <div class="metric-value">{len(draw_data)}</div>
        <div class="metric-label">분석 회차</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">{top_num:02d}</div>
        <div class="metric-label">핫 번호</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">{cold_num:02d}</div>
        <div class="metric-label">콜드 번호</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 최근 10회 목록 ───────────────────────────────────────────
with st.expander("📋  최근 10회 당첨번호"):
    for item in draw_data:
        st.markdown(f"""
        <div class="card" style="padding:18px 22px;margin:8px 0;">
            <div class="draw-header" style="margin-bottom:10px">
                <div class="draw-no" style="font-size:22px">{item['draw']}회</div>
                <div class="draw-date">{item['date']}</div>
            </div>
            {balls_html(item['numbers'], item['bonus'])}
        </div>
        """, unsafe_allow_html=True)

# ── 빈도 통계 ────────────────────────────────────────────────
with st.expander("📊  번호별 출현 빈도"):
    max_cnt = max(counts.values()) if counts else 1
    # 번호별 색상 매핑
    def bar_color(n):
        if n <= 10:  return "#f5a623"
        if n <= 20:  return "#1a56db"
        if n <= 30:  return "#dc2626"
        if n <= 40:  return "#4b5563"
        return "#16a34a"

    st.markdown('<div style="margin-top:8px">', unsafe_allow_html=True)
    for num in sorted(counts.keys()):
        cnt  = counts[num]
        pct  = cnt / max_cnt * 100
        col  = bar_color(num)
        st.markdown(f"""
        <div class="stat-row">
            <div class="stat-label" style="color:{col}">{num:02d}</div>
            <div class="stat-bar-wrap">
                <div class="stat-bar" style="width:{pct}%;background:{col}"></div>
            </div>
            <div class="stat-count">{cnt}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── 번호 추출 버튼 ───────────────────────────────────────────
weights = [counts.get(i, 0) + 1 for i in range(1, 46)]

if st.button("✦  행운의 번호 추출하기  ✦"):
    strategies = [
        ("HOT",  "🔥 핫 번호 중심",  "strategy-hot"),
        ("BAL",  "⚖️ 균형 조합",     "strategy-bal"),
        ("COLD", "❄️ 콜드 번호 중심","strategy-cold"),
        ("RAND", "🎲 순수 랜덤",      "strategy-rand"),
    ]

    combos_html = ""
    for i in range(num_combos):
        key, label, cls = strategies[i % len(strategies)]

        if key == "RAND" or i == num_combos - 1:
            game = sorted(random.sample(range(1, 46), 6))
        elif key == "COLD":
            cold_w = [max(1, 10 - counts.get(n, 0)) for n in range(1, 46)]
            game = weighted_unique_pick(cold_w)
        else:
            game = weighted_unique_pick(weights)

        combos_html += f"""
        <div class="combo-card">
            <div class="combo-meta">
                <div class="combo-num">조합 {i+1:02d}</div>
                <div class="combo-strategy {cls}">{label}</div>
            </div>
            {balls_html(game)}
        </div>
        """

    st.markdown(f"""
    <div class="card" style="padding:24px">
        <div class="card-title">✦ 추천 번호 조합</div>
        {combos_html}
        <div class="warn-box">
            로또는 순수 확률 게임입니다 · 본 번호는 오락 목적으로만 활용하세요
        </div>
    </div>
    """, unsafe_allow_html=True)
