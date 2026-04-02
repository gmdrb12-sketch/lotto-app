import streamlit as st
import random
import requests
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime

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
    .ball-row {
        display: flex; flex-wrap: wrap; justify-content: center;
        background: #f8f9fa; border-radius: 16px; padding: 10px;
        margin: 6px 0; border: 1px solid #e9ecef;
    }
    .draw-label {
        font-size: 12px; color: #888; font-weight: 700;
        text-align: center; margin-top: 6px;
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
    }
    .info-box {
        background: #e8f4fd; border-left: 4px solid #4361ee;
        border-radius: 8px; padding: 12px 16px; margin: 8px 0; font-size: 14px;
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


@st.cache_data(ttl=1800)  # 30분 캐시
def fetch_from_superkts(count=10):
    """
    superkts.com에서 최근 당첨번호 스크래핑
    URL: https://superkts.com/lotto/recent/{count}
    """
    url = f"https://superkts.com/lotto/recent/{count}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://superkts.com/",
    }

    res = requests.get(url, headers=headers, timeout=12)
    res.raise_for_status()
    res.encoding = "utf-8"

    soup = BeautifulSoup(res.text, "html.parser")

    results = []

    # superkts 구조: 각 회차 블록 파싱
    # 번호는 보통 <span class="..."> 또는 <li> 안에 있음
    # 여러 선택자를 시도해서 파싱
    
    # 방법 1: ul/li 기반 번호 리스트
    draw_blocks = soup.select("ul.lotto_num_wrap, ul.ball_wrap, div.lotto_result, div.win_result")
    
    if not draw_blocks:
        # 방법 2: 번호를 담은 span/li 직접 탐색
        draw_blocks = soup.find_all("div", class_=lambda c: c and "lotto" in c.lower())

    if not draw_blocks:
        # 방법 3: 전체 HTML에서 패턴으로 번호 추출
        import re
        # 6개 연속된 1-45 숫자 패턴 탐색
        all_nums = re.findall(r'\b([1-9]|[1-3][0-9]|4[0-5])\b', res.text)
        # 숫자를 6개씩 묶어서 유효한 회차 데이터로 변환 (휴리스틱)
        nums = [int(n) for n in all_nums if 1 <= int(n) <= 45]
        i = 0
        while i + 5 < len(nums) and len(results) < count:
            chunk = nums[i:i+6]
            if len(set(chunk)) == 6:  # 중복 없는 6개
                results.append(sorted(chunk))
                i += 6
            else:
                i += 1

    else:
        for block in draw_blocks[:count]:
            nums = []
            for tag in block.find_all(["span", "li", "em", "strong"]):
                txt = tag.get_text(strip=True)
                if txt.isdigit() and 1 <= int(txt) <= 45:
                    nums.append(int(txt))
            if len(nums) >= 6:
                results.append(sorted(nums[:6]))

    return results, res.text  # HTML도 반환 (디버그용)


def fetch_from_official_fallback(count=10):
    """동행복권 공식 API fallback"""
    from datetime import datetime
    base_date = datetime(2002, 12, 7)
    latest = (datetime.now() - base_date).days // 7 + 1
    
    results = []
    for i in range(count):
        draw_no = latest - i
        try:
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.dhlottery.co.kr/"}
            url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
            res = requests.get(url, headers=headers, timeout=8)
            d = res.json()
            if d.get("returnValue") == "success":
                results.append({
                    "draw": draw_no,
                    "numbers": [d[f"drwtNo{j}"] for j in range(1, 7)],
                    "bonus": d["bnusNo"]
                })
        except Exception:
            pass
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
st.caption("superkts.com 최근 10회 실시간 데이터 기반")

with st.sidebar:
    st.header("⚙️ 설정")
    num_combos = st.slider("생성할 조합 수", 3, 10, 5)
    show_debug = st.checkbox("디버그 모드 (파싱 확인)", False)
    st.markdown("---")
    if st.button("🔄 데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()

# ── 데이터 로드 ───────────────────────────────────────────────
draw_data   = []  # [{"draw": N, "numbers": [...], "bonus": N}]
source_label = ""

with st.spinner("📡 superkts.com에서 최근 10회 데이터 수집 중..."):
    try:
        raw_results, html_text = fetch_from_superkts(10)

        if show_debug:
            with st.expander("🔍 파싱된 원시 데이터"):
                st.write(raw_results)
                st.text(html_text[:3000])

        if raw_results and len(raw_results) >= 3:
            # draw 번호는 역산
            from datetime import datetime as dt
            base = dt(2002, 12, 7)
            latest_draw = (dt.now() - base).days // 7 + 1
            for i, nums in enumerate(raw_results):
                draw_data.append({
                    "draw": latest_draw - i,
                    "numbers": nums,
                    "bonus": None
                })
            source_label = "superkts.com"
        else:
            raise ValueError("파싱 결과 부족")

    except Exception as e:
        st.warning(f"⚠️ superkts.com 파싱 실패 ({e}) → 동행복권 API 시도 중...")
        try:
            draw_data = fetch_from_official_fallback(10)
            source_label = "동행복권 공식 API"
        except Exception as e2:
            st.error(f"❌ 모든 소스 실패: {e2}")

# ── 결과 표시 ─────────────────────────────────────────────────
if draw_data:
    st.success(f"✅ {source_label} — 최근 {len(draw_data)}회차 데이터 로드 완료")

    # 최근 당첨번호 표시
    with st.expander("📋 최근 당첨번호 확인", expanded=True):
        for item in draw_data:
            st.markdown(f'<div class="draw-label">{item["draw"]}회차</div>', unsafe_allow_html=True)
            render_balls(item["numbers"])

    st.markdown("---")

    # 통계
    flat_list = [n for item in draw_data for n in item["numbers"]]
    counts    = Counter(flat_list)
    weights   = [counts.get(i, 0) + 1 for i in range(1, 46)]

    with st.expander("📊 번호별 출현 빈도"):
        top_nums = counts.most_common()
        cols = st.columns(5)
        for idx, (num, cnt) in enumerate(top_nums[:15]):
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
                cold_w = [max(1, 15 - counts.get(n, 0)) for n in range(1, 46)]
                game = weighted_unique_pick(cold_w)
            else:
                game = weighted_unique_pick(weights)

            st.markdown(f'<div class="combo-label">조합 {i+1} — {s}</div>', unsafe_allow_html=True)
            render_balls(game)

        st.markdown('<div class="info-box">⚠️ 로또는 확률 게임입니다. 오락 목적으로만 활용하세요.</div>', unsafe_allow_html=True)

else:
    st.error("데이터를 불러올 수 없습니다. 사이드바에서 새로고침을 눌러주세요.")
