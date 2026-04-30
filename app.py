import streamlit as st
import requests
import random
from collections import Counter
from datetime import datetime, timezone, timedelta

# ── 페이지 설정 ─────────────────────────────────────────────
st.set_page_config(
    page_title="로또 분석기 Pro (최근 10회)",
    page_icon="🎰",
    layout="centered"
)

# ── CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
.lotto-ball {
    display: inline-block; width: 44px; height: 44px; line-height: 44px;
    text-align: center; border-radius: 50%; font-weight: bold; font-size: 15px;
    margin: 4px; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.35);
    box-shadow: inset -3px -3px 6px rgba(0,0,0,0.2), 2px 2px 6px rgba(0,0,0,0.15);
}
.ball-y { background: linear-gradient(135deg,#fdd835,#f9a825); color: #333 !important; }
.ball-b { background: linear-gradient(135deg,#42a5f5,#1565c0); }
.ball-r { background: linear-gradient(135deg,#ef5350,#b71c1c); }
.ball-g { background: linear-gradient(135deg,#bdbdbd,#616161); }
.ball-gr { background: linear-gradient(135deg,#66bb6a,#2e7d32); }
.ball-bonus { background: linear-gradient(135deg,#ba68c8,#6a1b9a); }
.stButton>button {
    width:100%; border-radius:12px; height:3.5em; font-weight:bold;
    background: linear-gradient(to right,#f09819,#ff512f);
    color:white; border:none; font-size:16px;
}
.stButton>button:hover { opacity:0.88; }
</style>
""", unsafe_allow_html=True)


# ── 볼 렌더링 ────────────────────────────────────────────────
def ball_class(n: int, bonus: bool = False) -> str:
    if bonus:
        return "ball-bonus"
    if n <= 10:  return "ball-y"
    if n <= 20:  return "ball-b"
    if n <= 30:  return "ball-r"
    if n <= 40:  return "ball-g"
    return "ball-gr"

def render_balls(numbers: list, bonus: int = None):
    html = '<div style="display:flex;flex-wrap:wrap;align-items:center;gap:2px;margin-bottom:6px;">'
    for n in numbers:
        cls = ball_class(n)
        html += f'<div class="lotto-ball {cls}">{n:02d}</div>'
    if bonus is not None:
        html += f'<div style="margin:0 4px;font-size:18px;color:#aaa;">+</div>'
        html += f'<div class="lotto-ball ball-bonus">{bonus:02d}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ── 최신 회차 계산 (KST 기준) ────────────────────────────────
def get_latest_round() -> int:
    """
    1회: 2002-12-07 (토요일)
    매주 토요일 오후 8:35 추첨 → 추첨 전이면 전 회차 반환
    """
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)
    base = datetime(2002, 12, 7, 20, 35, tzinfo=KST)  # 1회 추첨 시각

    if now_kst < base:
        return 1

    total_seconds = (now_kst - base).total_seconds()
    weeks_elapsed = int(total_seconds // (7 * 24 * 3600))

    # 이번 주 추첨 시각
    this_draw = base + timedelta(weeks=weeks_elapsed)
    if now_kst >= this_draw:
        return weeks_elapsed + 1
    else:
        return weeks_elapsed


# ── API 호출 (동행복권 공식 + CORS 프록시 백업) ─────────────
def fetch_one_draw(draw_no: int) -> dict | None:
    """단일 회차 데이터 조회. 실패 시 None 반환."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # 1순위: 동행복권 공식 API
    try:
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        res = requests.get(url, headers=headers, timeout=4)
        data = res.json()
        if data.get("returnValue") == "success":
            return {
                "round":   data["drwNo"],
                "date":    data["drwNoDate"],
                "numbers": sorted([data[f"drwtNo{i}"] for i in range(1, 7)]),
                "bonus":   data["bnusNo"],
            }
    except Exception:
        pass

    # 2순위: allorigins.win 프록시
    try:
        api_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        proxy = f"https://api.allorigins.win/get?url={requests.utils.quote(api_url)}"
        res = requests.get(proxy, timeout=5)
        import json
        data = json.loads(res.json()["contents"])
        if data.get("returnValue") == "success":
            return {
                "round":   data["drwNo"],
                "date":    data["drwNoDate"],
                "numbers": sorted([data[f"drwtNo{i}"] for i in range(1, 7)]),
                "bonus":   data["bnusNo"],
            }
    except Exception:
        pass

    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_10_draws(latest_round: int) -> tuple[list, str | None]:
    """최근 10회차 데이터 수집. (round를 인자로 받아 캐시 key 분리)"""
    draws = []
    failed = []

    for i in range(10):
        draw_no = latest_round - i
        result = fetch_one_draw(draw_no)
        if result:
            draws.append(result)
        else:
            failed.append(draw_no)

    if not draws:
        return [], "모든 API 요청이 실패했습니다. 잠시 후 다시 시도해 주세요."

    err_msg = f"{len(failed)}개 회차 수집 실패 ({failed})" if failed else None
    return draws, err_msg


# ── 가중 무작위 추출 (중복 없이) ────────────────────────────
def weighted_sample_no_repeat(freq: Counter, k: int = 6) -> list[int]:
    """
    출현 빈도 기반 가중치로 k개 번호를 중복 없이 추출.
    random.choices 는 중복을 허용하므로 직접 구현.
    """
    population = list(range(1, 46))
    weights = [freq.get(n, 0) + 1 for n in population]  # +1: 미출현 번호도 후보
    chosen = []

    while len(chosen) < k:
        total = sum(weights)
        r = random.uniform(0, total)
        cumulative = 0
        for idx, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                chosen.append(population[idx])
                # 선택된 번호를 풀에서 제거
                population.pop(idx)
                weights.pop(idx)
                break

    return sorted(chosen)


# ── UI 메인 ─────────────────────────────────────────────────
st.title("🎰 로또 분석기 Pro")
st.caption("동행복권 공식 데이터 기반 · 최근 10회 당첨번호 실시간 분석")

latest_round = get_latest_round()
st.info(f"📅 현재 기준 최신 회차: **{latest_round}회** | 분석 범위: {latest_round - 9}회 ~ {latest_round}회")

# ── 데이터 로드 ──────────────────────────────────────────────
if "draws" not in st.session_state or st.session_state.get("loaded_round") != latest_round:
    with st.spinner("🔄 당첨 데이터 수집 중..."):
        draws, err = fetch_10_draws(latest_round)
        st.session_state.draws = draws
        st.session_state.fetch_err = err
        st.session_state.loaded_round = latest_round

draws = st.session_state.draws
err   = st.session_state.fetch_err

if err:
    st.warning(f"⚠️ {err}")

if not draws:
    st.error("데이터를 불러오지 못했습니다.")
    if st.button("🔄 다시 시도"):
        st.session_state.clear()
        st.rerun()
    st.stop()

st.success(f"✅ {len(draws)}개 회차 데이터 수집 완료!")

# ── 당첨번호 히스토리 ────────────────────────────────────────
with st.expander("📋 최근 당첨번호 보기", expanded=True):
    for d in draws:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"**{d['round']}회**<br><small>{d['date']}</small>", unsafe_allow_html=True)
        with col2:
            render_balls(d["numbers"], d["bonus"])

# ── 빈도 분석 ────────────────────────────────────────────────
flat = [n for d in draws for n in d["numbers"]]
freq = Counter(flat)

hot_nums  = [n for n, _ in freq.most_common(9)]
cold_nums = [n for n, _ in freq.most_common()[:-10:-1]]

col_h, col_c = st.columns(2)
with col_h:
    st.markdown("**🔥 자주 나온 번호**")
    render_balls(sorted(hot_nums))
with col_c:
    st.markdown("**❄️ 드물게 나온 번호**")
    render_balls(sorted(cold_nums))

# ── 번호 생성 ────────────────────────────────────────────────
st.divider()
st.subheader("🎯 추천 번호 생성")

if st.button("✨ 행운의 번호 추출하기"):
    st.balloons()
    st.markdown("#### 추천 번호 조합 (가중치 기반)")

    for i in range(4):
        nums = weighted_sample_no_repeat(freq, k=6)
        col_l, col_r = st.columns([1, 5])
        with col_l:
            st.markdown(f"**조합 {i+1}**")
        with col_r:
            render_balls(nums)

    # 마지막 1세트: 순수 랜덤
    st.markdown("---")
    col_l, col_r = st.columns([1, 5])
    with col_l:
        st.markdown("**🎲 랜덤**")
    with col_r:
        render_balls(sorted(random.sample(range(1, 46), 6)))

    st.caption("⚠️ 통계 기반 참고용 생성이며 당첨을 보장하지 않습니다. 만 19세 이상만 구매 가능합니다.")

# ── 사이드바: 데이터 초기화 ──────────────────────────────────
with st.sidebar:
    st.header("설정")
    if st.button("🔄 데이터 새로고침"):
        fetch_10_draws.clear()
        st.session_state.clear()
        st.rerun()
    st.caption(f"마지막 로드: {datetime.now().strftime('%H:%M:%S')}")
