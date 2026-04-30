import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
from collections import Counter
from datetime import datetime, timezone, timedelta

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="로또 분석기 Pro",
    page_icon="🎰",
    layout="centered"
)

st.markdown("""
<style>
.lotto-ball {
    display: inline-block; width: 44px; height: 44px; line-height: 44px;
    text-align: center; border-radius: 50%; font-weight: bold; font-size: 15px;
    margin: 4px; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.35);
    box-shadow: inset -3px -3px 6px rgba(0,0,0,0.2), 2px 2px 6px rgba(0,0,0,0.15);
}
.ball-y  { background: linear-gradient(135deg,#fdd835,#f9a825); color: #333 !important; }
.ball-b  { background: linear-gradient(135deg,#42a5f5,#1565c0); }
.ball-r  { background: linear-gradient(135deg,#ef5350,#b71c1c); }
.ball-g  { background: linear-gradient(135deg,#bdbdbd,#616161); }
.ball-gr { background: linear-gradient(135deg,#66bb6a,#2e7d32); }
.ball-bonus { background: linear-gradient(135deg,#ba68c8,#6a1b9a); }
.stButton>button {
    width:100%; border-radius:12px; height:3.5em; font-weight:bold;
    background: linear-gradient(to right,#f09819,#ff512f);
    color:white; border:none; font-size:16px;
}
</style>
""", unsafe_allow_html=True)


# ── 볼 렌더링 ─────────────────────────────────────────────────
def ball_class(n: int, bonus: bool = False) -> str:
    if bonus: return "ball-bonus"
    if n <= 10: return "ball-y"
    if n <= 20: return "ball-b"
    if n <= 30: return "ball-r"
    if n <= 40: return "ball-g"
    return "ball-gr"

def render_balls(numbers: list, bonus: int = None):
    html = '<div style="display:flex;flex-wrap:wrap;align-items:center;gap:2px;margin-bottom:6px;">'
    for n in numbers:
        html += f'<div class="lotto-ball {ball_class(n)}">{n:02d}</div>'
    if bonus:
        html += '<div style="margin:0 6px;font-size:18px;color:#aaa;">+</div>'
        html += f'<div class="lotto-ball ball-bonus">{bonus:02d}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ── superkts.com 스크래핑 ─────────────────────────────────────
HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Referer":         "https://superkts.com/",
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_from_superkts(count: int = 10) -> tuple[list, str | None]:
    """
    https://superkts.com/lotto/recent/{count} 스크래핑
    반환: (draws_list, error_message)
    draws_list 원소: {"round": int, "date": str, "numbers": list, "bonus": int}
    """
    url = f"https://superkts.com/lotto/recent/{count}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        res.raise_for_status()
    except Exception as e:
        return [], f"superkts.com 접속 실패: {e}"

    soup = BeautifulSoup(res.text, "html.parser")
    draws = []

    # ── superkts HTML 파싱 ────────────────────────────────────
    # 회차별 행: <tr> 또는 특정 div 안에 번호가 있음
    # 번호는 <span class="nB ..."> 또는 <li class="ball ..."> 형태
    # 실제 구조에 맞게 여러 셀렉터 시도

    # 전략 1: 테이블 행에서 파싱
    rows = soup.select("table tbody tr")
    for row in rows:
        try:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            # 회차 추출 (첫 번째 셀)
            round_text = cells[0].get_text(strip=True).replace("회", "").strip()
            if not round_text.isdigit():
                continue
            round_no = int(round_text)

            # 날짜 추출 (두 번째 셀)
            date_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""

            # 번호 추출 — span/li/div 안의 숫자
            all_nums = []
            for tag in row.find_all(["span", "li", "div", "em", "b"]):
                txt = tag.get_text(strip=True)
                if txt.isdigit() and 1 <= int(txt) <= 45:
                    all_nums.append(int(txt))

            # 중복 제거 & 순서 유지
            seen = set()
            nums = []
            for n in all_nums:
                if n not in seen:
                    seen.add(n)
                    nums.append(n)

            if len(nums) >= 7:
                draws.append({
                    "round":   round_no,
                    "date":    date_text,
                    "numbers": sorted(nums[:6]),
                    "bonus":   nums[6],
                })
        except Exception:
            continue

    if draws:
        return draws[:count], None

    # 전략 2: 테이블이 없을 경우 — 번호 블록 단위 파싱
    # superkts는 각 회차를 .winNum 또는 .lottoNum 같은 컨테이너로 묶는 경우도 있음
    containers = soup.select(".winNum, .lottoRow, .lotto_num, .num_wrap, [class*='lotto'], [class*='draw']")
    for container in containers:
        try:
            # 회차: 텍스트에서 숫자 추출
            text = container.get_text(" ", strip=True)
            tokens = text.split()
            nums = [int(t) for t in tokens if t.isdigit() and 1 <= int(t) <= 45]

            round_candidates = [int(t.replace("회", "")) for t in tokens
                                if t.replace("회", "").isdigit() and int(t.replace("회", "")) > 1000]
            round_no = round_candidates[0] if round_candidates else 0

            if len(nums) >= 7 and round_no > 0:
                draws.append({
                    "round":   round_no,
                    "date":    "",
                    "numbers": sorted(nums[:6]),
                    "bonus":   nums[6],
                })
        except Exception:
            continue

    if draws:
        return draws[:count], None

    # 전략 3: 전체 페이지에서 패턴 매칭으로 번호 추출
    # 1~45 사이 숫자 6+1개가 연속으로 나오는 패턴 찾기
    all_text_nums = []
    for tag in soup.find_all(["span", "td", "li", "em", "strong"]):
        t = tag.get_text(strip=True)
        if t.isdigit() and 1 <= int(t) <= 45:
            all_text_nums.append(int(t))

    # 7개씩 슬라이딩 윈도우로 회차 번호 후보 탐색
    i = 0
    while i <= len(all_text_nums) - 7:
        chunk = all_text_nums[i:i+7]
        if len(set(chunk)) == 7:  # 중복 없는 7개
            draws.append({
                "round":   len(draws) + 1,
                "date":    "",
                "numbers": sorted(chunk[:6]),
                "bonus":   chunk[6],
            })
            i += 7
        else:
            i += 1
        if len(draws) >= count:
            break

    if draws:
        return draws[:count], "회차 정보를 일부 파싱하지 못했습니다 (번호는 정확합니다)"

    return [], "HTML 구조를 파싱할 수 없습니다. 사이트 구조가 변경되었을 수 있습니다."


# ── 동행복권 API 폴백 ─────────────────────────────────────────
def get_latest_round() -> int:
    KST  = timezone(timedelta(hours=9))
    now  = datetime.now(KST)
    base = datetime(2002, 12, 7, 20, 35, tzinfo=KST)
    elapsed = int((now - base).total_seconds() // (7 * 24 * 3600))
    draw_time = base + timedelta(weeks=elapsed)
    return elapsed + 1 if now >= draw_time else elapsed

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_from_dhlottery(latest_round: int, count: int = 10) -> tuple[list, str | None]:
    draws = []
    for i in range(count):
        try:
            url = (f"https://www.dhlottery.co.kr/common.do"
                   f"?method=getLottoNumber&drwNo={latest_round - i}")
            r = requests.get(url, headers=HEADERS, timeout=5)
            d = r.json()
            if d.get("returnValue") == "success":
                draws.append({
                    "round":   d["drwNo"],
                    "date":    d["drwNoDate"],
                    "numbers": sorted([d[f"drwtNo{j}"] for j in range(1, 7)]),
                    "bonus":   d["bnusNo"],
                })
        except Exception:
            pass
    if draws:
        return draws, None
    return [], "동행복권 API도 응답하지 않습니다."


# ── 가중 무작위 (중복 없이) ───────────────────────────────────
def weighted_sample(freq: Counter, k: int = 6) -> list[int]:
    pool    = list(range(1, 46))
    weights = [freq.get(n, 0) + 1 for n in pool]
    chosen  = []
    while len(chosen) < k:
        total = sum(weights)
        r     = random.uniform(0, total)
        cum   = 0
        for i, w in enumerate(weights):
            cum += w
            if r <= cum:
                chosen.append(pool.pop(i))
                weights.pop(i)
                break
    return sorted(chosen)


# ════════════════════════════════════════════════════════════
#  UI
# ════════════════════════════════════════════════════════════
st.title("🎰 로또 분석기 Pro")
st.caption("superkts.com 기반 · 최근 10회 당첨번호 실시간 분석")

# ── 데이터 로드 ───────────────────────────────────────────────
if "draws" not in st.session_state:
    with st.spinner("🔄 superkts.com에서 데이터 수집 중..."):
        draws, err = fetch_from_superkts(10)

        # superkts 실패 시 동행복권 API로 폴백
        if not draws:
            st.warning(f"⚠️ superkts 스크래핑 실패: {err}\n\n동행복권 API로 재시도 중...")
            latest = get_latest_round()
            draws, err = fetch_from_dhlottery(latest, 10)

        st.session_state.draws     = draws
        st.session_state.fetch_err = err
        st.session_state.source    = "superkts.com" if draws and not err else "동행복권 API"

draws     = st.session_state.draws
fetch_err = st.session_state.fetch_err
source    = st.session_state.get("source", "알 수 없음")

if fetch_err:
    st.warning(f"⚠️ {fetch_err}")

if not draws:
    st.error("데이터를 불러오지 못했습니다.")
    if st.button("🔄 다시 시도"):
        fetch_from_superkts.clear()
        fetch_from_dhlottery.clear()
        st.session_state.clear()
        st.rerun()
    st.stop()

st.success(f"✅ {len(draws)}개 회차 수집 완료 — 출처: {source}")

# ── 당첨번호 히스토리 ────────────────────────────────────────
with st.expander("📋 최근 당첨번호", expanded=True):
    for d in draws:
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown(f"**{d['round']}회**<br><small>{d['date']}</small>",
                        unsafe_allow_html=True)
        with c2:
            render_balls(d["numbers"], d["bonus"])

# ── 빈도 분석 ────────────────────────────────────────────────
flat = [n for d in draws for n in d["numbers"]]
freq = Counter(flat)
hot  = sorted([n for n, _ in freq.most_common(9)])
cold = sorted([n for n, _ in freq.most_common()[:-10:-1]])

c1, c2 = st.columns(2)
with c1:
    st.markdown("**🔥 자주 나온 번호**")
    render_balls(hot)
with c2:
    st.markdown("**❄️ 드물게 나온 번호**")
    render_balls(cold)

# ── 번호 생성 ────────────────────────────────────────────────
st.divider()
st.subheader("🎯 추천 번호 생성")

if st.button("✨ 행운의 번호 추출하기"):
    st.balloons()
    st.markdown("#### 추천 조합")
    for i in range(4):
        nums = weighted_sample(freq)
        c1, c2 = st.columns([1, 5])
        with c1: st.markdown(f"**조합 {i+1}**")
        with c2: render_balls(nums)

    st.markdown("---")
    c1, c2 = st.columns([1, 5])
    with c1: st.markdown("**🎲 랜덤**")
    with c2: render_balls(sorted(random.sample(range(1, 46), 6)))

    st.caption("⚠️ 통계 기반 참고용 · 당첨을 보장하지 않습니다 · 만 19세 이상 구매 가능")

# ── 사이드바 ──────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")
    if st.button("🔄 데이터 새로고침"):
        fetch_from_superkts.clear()
        fetch_from_dhlottery.clear()
        st.session_state.clear()
        st.rerun()
    st.markdown("---")
    st.markdown(f"**데이터 출처**\n\n[superkts.com](https://superkts.com/lotto/recent/10)")
    st.caption(f"마지막 로드: {datetime.now().strftime('%H:%M:%S')}")
