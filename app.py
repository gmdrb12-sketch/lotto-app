import streamlit as st
import random
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(
    page_title="LUCKY PICK",
    page_icon="🍀",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS (정적 스타일만, 동적 데이터 없음) ────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0e1a !important;
    color: #e8eaf0 !important;
}
[data-testid="stAppViewContainer"] > .main { background: #0a0e1a !important; }
[data-testid="stHeader"] { background: transparent !important; }
section[data-testid="stSidebar"] {
    background: #0d1120 !important;
    border-right: 1px solid #1e2540;
}
* { font-family: 'Noto Sans KR', sans-serif; box-sizing: border-box; }
#MainMenu, footer { visibility: hidden; }

/* 히어로 */
.hero { text-align: center; padding: 40px 0 24px; }
.hero-eyebrow {
    font-size: 11px; letter-spacing: 4px; color: #c9a84c;
    text-transform: uppercase; font-weight: 500; margin-bottom: 8px;
}
.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(52px, 10vw, 80px);
    letter-spacing: 6px; line-height: 1;
    background: linear-gradient(135deg, #c9a84c 0%, #f5d98b 40%, #c9a84c 70%, #9a7a2e 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    margin: 0;
}
.hero-sub { font-size: 13px; color: #3d4668; letter-spacing: 1px; margin-top: 10px; }

/* 최신 회차 카드 */
.latest-card {
    background: linear-gradient(145deg, #131928, #0f1622);
    border: 1px solid #c9a84c44;
    border-radius: 24px; padding: 28px 24px; margin: 14px 0;
    position: relative; overflow: hidden;
}
.latest-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #c9a84c, transparent);
}
.latest-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #c9a84c18; border: 1px solid #c9a84c44;
    border-radius: 20px; padding: 4px 12px;
    font-size: 11px; letter-spacing: 2px; color: #c9a84c;
    text-transform: uppercase; font-weight: 700; margin-bottom: 14px;
}
.draw-header {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;
}
.draw-no {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 30px; letter-spacing: 2px; color: #c9a84c; line-height: 1;
}
.draw-date { font-size: 12px; color: #3d4668; font-weight: 500; }

/* 볼 공통 */
.balls-wrap {
    display: flex; flex-wrap: wrap; align-items: center;
    justify-content: center; gap: 7px; padding: 4px 0;
}
.lotto-ball {
    width: 46px; height: 46px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 15px; position: relative; flex-shrink: 0;
}
.lotto-ball::after {
    content: ''; position: absolute; top: 5px; left: 8px;
    width: 10px; height: 5px;
    background: rgba(255,255,255,0.35); border-radius: 50%;
    transform: rotate(-30deg);
}
.latest-ball { width: 54px; height: 54px; font-size: 17px; }
.b1  { background: radial-gradient(circle at 35% 35%, #ffe066, #f5a623); color: #3d2800; }
.b11 { background: radial-gradient(circle at 35% 35%, #6ea8fe, #1a56db); color: #fff; }
.b21 { background: radial-gradient(circle at 35% 35%, #f87171, #dc2626); color: #fff; }
.b31 { background: radial-gradient(circle at 35% 35%, #9ca3af, #4b5563); color: #fff; }
.b41 { background: radial-gradient(circle at 35% 35%, #4ade80, #16a34a); color: #fff; }
.bbonus { background: radial-gradient(circle at 35% 35%, #e879f9, #9333ea); color: #fff; opacity:.85; }
.plus { color: #2e3550; font-size: 18px; font-weight: 900; margin: 0 2px; }

/* 메트릭 */
.metrics-row { display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; margin: 14px 0; }
.metric-box {
    background: #0d1220; border: 1px solid #1a2240;
    border-radius: 14px; padding: 16px; text-align: center;
}
.metric-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 28px; letter-spacing: 1px; color: #c9a84c; line-height: 1;
}
.metric-label { font-size: 10px; color: #3d4668; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px; font-weight: 700; }

/* 일반 카드 */
.draw-card {
    background: #0d1220; border: 1px solid #1a2240;
    border-radius: 16px; padding: 16px 18px; margin: 8px 0;
}
.draw-card-header {
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 10px;
}
.draw-card-no {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 22px; letter-spacing: 2px; color: #c9a84c;
}
.draw-card-date { font-size: 11px; color: #2e3550; }

/* 통계 바 */
.stat-row { display: flex; align-items: center; gap: 8px; margin: 4px 0; }
.stat-lbl {
    font-family: 'Bebas Neue', sans-serif; font-size: 16px; letter-spacing: 1px;
    width: 32px; text-align: right; flex-shrink: 0;
}
.stat-bar-wrap { flex: 1; height: 5px; background: #1a2240; border-radius: 3px; overflow: hidden; }
.stat-bar { height: 100%; border-radius: 3px; }
.stat-cnt { font-size: 10px; color: #2e3550; width: 20px; text-align: right; flex-shrink: 0; }

/* 조합 카드 */
.combo-card {
    background: #0d1220; border: 1px solid #1a2240;
    border-radius: 16px; padding: 18px 18px 14px; margin: 8px 0;
}
.combo-meta { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.combo-num {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 20px; letter-spacing: 2px; color: #2e3a5c;
}
.combo-badge { font-size: 11px; font-weight: 700; letter-spacing: 1px; padding: 3px 10px; border-radius: 20px; }
.s-hot  { background:#f5a62322; color:#f5a623; border:1px solid #f5a62344; }
.s-bal  { background:#1a56db22; color:#6ea8fe; border:1px solid #1a56db44; }
.s-cold { background:#16a34a22; color:#4ade80; border:1px solid #16a34a44; }
.s-rand { background:#9333ea22; color:#e879f9; border:1px solid #9333ea44; }

/* 버튼 */
.stButton > button {
    width: 100%; height: 56px;
    background: linear-gradient(135deg, #c9a84c, #9a7a2e) !important;
    color: #0a0e1a !important; border: none !important;
    border-radius: 16px !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 20px !important; letter-spacing: 4px !important;
    box-shadow: 0 8px 32px #c9a84c33 !important;
}
.stButton > button:hover { box-shadow: 0 12px 40px #c9a84c55 !important; }

/* 경고 */
.warn-box {
    background: #c9a84c0d; border: 1px solid #c9a84c22;
    border-radius: 12px; padding: 12px 16px;
    font-size: 11px; color: #3d4668; text-align: center;
    letter-spacing: 0.5px; margin-top: 16px;
}
[data-testid="stSidebar"] * { color: #8892b0 !important; }
.stSpinner > div { border-top-color: #c9a84c !important; }
hr { border: none !important; border-top: 1px solid #1a2240 !important; margin: 20px 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── 유틸 ─────────────────────────────────────────────────────

def ball_cls(n, bonus=False):
    if bonus:   return "bbonus"
    if n <= 10: return "b1"
    if n <= 20: return "b11"
    if n <= 30: return "b21"
    if n <= 40: return "b31"
    return "b41"

def render_balls(numbers, bonus=None, big=False):
    """볼 줄 렌더링 — 각 볼을 개별 st.markdown으로 쪼개지 않고
       하나의 정적 HTML로 만들되, 파이썬에서 문자열 조합 후 markdown 1회 호출"""
    size = "latest-ball" if big else ""
    parts = []
    for n in numbers:
        parts.append(
            f'<div class="lotto-ball {ball_cls(n)} {size}">{n:02d}</div>'
        )
    if bonus is not None:
        parts.append('<span class="plus">＋</span>')
        parts.append(
            f'<div class="lotto-ball {ball_cls(bonus, True)} {size}">{bonus:02d}</div>'
        )
    html = '<div class="balls-wrap">' + "".join(parts) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


@st.cache_data(ttl=1800)
def fetch_lotto():
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
    for link in soup.select('a[href*="/lotto/"]'):
        href = link.get("href", "")
        if not re.match(r"^/lotto/\d+$", href):
            continue
        draw_no = int(re.search(r"\d+", href).group())
        text = link.get_text(separator=" ", strip=True)
        date_m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        date_str = date_m.group(1) if date_m else ""
        nums = []
        for n in re.findall(r'\b([1-9]|[1-3][0-9]|4[0-5])\b', text):
            v = int(n)
            if v not in nums:
                nums.append(v)
        if len(nums) >= 7:
            results.append({
                "draw": draw_no, "date": date_str,
                "numbers": sorted(nums[:6]), "bonus": nums[6],
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
    st.markdown(
        "<div style='font-size:11px;color:#2e3550;margin-top:20px'>"
        "picknum.com 기반 · 30분 캐시</div>",
        unsafe_allow_html=True,
    )

# ── 히어로 ───────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Korea Lotto 6/45</div>
    <h1 class="hero-title">LUCKY PICK</h1>
    <p class="hero-sub">실시간 당첨 데이터 기반 번호 분석기</p>
</div>
""", unsafe_allow_html=True)

# ── 데이터 로드 ───────────────────────────────────────────────
with st.spinner("데이터 수집 중..."):
    try:
        draw_data = fetch_lotto()
        assert draw_data
    except Exception as e:
        st.error(f"❌ 데이터 수집 실패: {e}")
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
</div>
""", unsafe_allow_html=True)
render_balls(latest["numbers"], latest["bonus"], big=True)

# ── 메트릭 ───────────────────────────────────────────────────
flat = [n for item in draw_data for n in item["numbers"]]
counts = Counter(flat)
top_num  = counts.most_common(1)[0][0]
cold_num = counts.most_common()[-1][0]

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
<div class="draw-card">
    <div class="draw-card-header">
        <div class="draw-card-no">{item['draw']}회</div>
        <div class="draw-card-date">{item['date']}</div>
    </div>
</div>""", unsafe_allow_html=True)
        render_balls(item["numbers"], item["bonus"])

# ── 빈도 통계 ────────────────────────────────────────────────
with st.expander("📊  번호별 출현 빈도"):
    max_cnt = max(counts.values()) if counts else 1
    color_map = {1: "#f5a623", 11: "#1a56db", 21: "#dc2626", 31: "#4b5563", 41: "#16a34a"}

    def bar_color(n):
        for threshold in [10, 20, 30, 40]:
            if n <= threshold:
                return color_map[threshold - 9]
        return color_map[41]

    rows_html = ""
    for num in sorted(counts.keys()):
        cnt = counts[num]
        pct = cnt / max_cnt * 100
        col = bar_color(num)
        rows_html += (
            f'<div class="stat-row">'
            f'<div class="stat-lbl" style="color:{col}">{num:02d}</div>'
            f'<div class="stat-bar-wrap"><div class="stat-bar" style="width:{pct}%;background:{col}"></div></div>'
            f'<div class="stat-cnt">{cnt}</div>'
            f'</div>'
        )
    st.markdown(f'<div style="margin-top:8px">{rows_html}</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── 번호 추출 ────────────────────────────────────────────────
weights = [counts.get(i, 0) + 1 for i in range(1, 46)]

strategies = [
    ("🔥 핫 번호 중심",   "s-hot",  "HOT"),
    ("⚖️ 균형 조합",      "s-bal",  "BAL"),
    ("❄️ 콜드 번호 중심", "s-cold", "COLD"),
    ("🎲 순수 랜덤",       "s-rand", "RAND"),
]

if st.button("✦  행운의 번호 추출하기  ✦"):
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    for i in range(num_combos):
        label, badge_cls, key = strategies[i % len(strategies)]

        # 마지막 조합은 항상 랜덤
        if key == "RAND" or i == num_combos - 1:
            game = sorted(random.sample(range(1, 46), 6))
        elif key == "COLD":
            cold_w = [max(1, 10 - counts.get(n, 0)) for n in range(1, 46)]
            game = weighted_unique_pick(cold_w)
        else:
            game = weighted_unique_pick(weights)

        # 헤더 부분만 HTML
        st.markdown(f"""
<div class="combo-card">
    <div class="combo-meta">
        <div class="combo-num">조합 {i+1:02d}</div>
        <div class="combo-badge {badge_cls}">{label}</div>
    </div>
</div>""", unsafe_allow_html=True)

        # 볼은 별도 render_balls 호출
        render_balls(game)

    st.markdown(
        '<div class="warn-box">로또는 순수 확률 게임입니다 · 오락 목적으로만 활용하세요</div>',
        unsafe_allow_html=True,
    )
