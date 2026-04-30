import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import re
from collections import Counter
from datetime import datetime

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


# ── superkts.com 단독 스크래핑 (스마트 스캐닝 적용) ────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Referer": "https://superkts.com/",
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_from_superkts(count: int = 10) -> tuple[list, str | None]:
    url = f"https://superkts.com/lotto/recent/{count}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        res.raise_for_status()
    except Exception as e:
        return [], f"superkts.com 접속 실패: 웹사이트가 응답하지 않습니다. ({e})"

    soup = BeautifulSoup(res.text, "html.parser")
    draws = []

    # 1. 'XXXX회' 텍스트를 기준으로 탐색 시작
    round_tags = soup.find_all(string=re.compile(r'([1-9]\d{3})회'))
    date_pattern = re.compile(r'\b(20\d{2}[-./]\d{1,2}[-./]\d{1,2})\b')
    
    for text_node in round_tags:
        # 회차 텍스트 주변의 부모 태그(박스)를 최대 5단계까지 올라가며 검사
        container = text_node.parent
        for _ in range(5):
            if container is None: 
                break
                
            text = container.get_text(" ", strip=True)
            nums = []
            
            # 태그 단위로 1~45 사이의 공 번호를 추출
            for tag in container.find_all(['span', 'div', 'b', 'strong', 'em', 'li']):
                t = tag.get_text(strip=True)
                # 길이 1~2자리 숫자인 경우만 취급 (날짜 등 오인 방지)
                if t.isdigit() and len(t) <= 2 and 1 <= int(t) <= 45:
                    if int(t) not in nums:
                        nums.append(int(t))
            
            # 7개의 당첨번호(보너스 포함)를 완벽히 찾았을 경우
            if len(nums) >= 7:
                round_match = re.search(r'([1-9]\d{3})회', text)
                if not round_match:
                    break
                round_no = int(round_match.group(1))
                
                # 이미 추가된 회차인지 중복 검사
                if any(d['round'] == round_no for d in draws):
                    break
                    
                date_match = date_pattern.search(text)
                date_str = date_match.group(1) if date_match else ""
                
                draws.append({
                    "round": round_no,
                    "date": date_str,
                    "numbers": sorted(nums[:6]), # 앞에 6개는 일반 당첨번호 (정렬)
                    "bonus": nums[6]             # 7번째는 보너스 번호
                })
                break # 다음 회차를 찾으러 이동
                
            container = container.parent
            
    # 최신 회차가 상단에 오도록 내림차순 정렬
    draws = sorted(draws, key=lambda x: x['round'], reverse=True)
    
    if draws:
        return draws[:count], None

    return [], "데이터를 파싱할 수 없습니다. superkts.com 사이트의 디자인이 크게 변경되었을 수 있습니다."


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
st.caption("superkts.com 전용 기반 · 최근 10회 당첨번호 실시간 분석")

# ── 데이터 로드 (오직 superkts만 사용) ────────────────────────
if "draws" not in st.session_state:
    with st.spinner("🔄 superkts.com에서 실시간 데이터 수집 중..."):
        draws, err = fetch_from_superkts(10)
        
        st.session_state.draws     = draws
        st.session_state.fetch_err = err

draws     = st.session_state.draws
fetch_err = st.session_state.fetch_err

if fetch_err:
    st.warning(f"⚠️ {fetch_err}")

if not draws:
    st.error("데이터를 불러오지 못했습니다. 사이드바에서 다시 시도를 눌러주세요.")
    st.stop()

st.success(f"✅ {len(draws)}개 회차 수집 완료 — 출처: superkts.com")

# ── 당첨번호 히스토리 ────────────────────────────────────────
with st.expander("📋 최근 당첨번호", expanded=True):
    for d in draws:
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown(f"**{d['round']}회**<br><small>{d['date']}</small>", unsafe_allow_html=True)
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
        st.session_state.clear()
        st.rerun()
    st.markdown("---")
    st.markdown(f"**데이터 출처**\n\n[superkts.com](https://superkts.com/lotto/recent/10)")
    st.caption(f"마지막 로드: {datetime.now().strftime('%H:%M:%S')}")
