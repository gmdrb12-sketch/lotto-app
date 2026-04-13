import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import time
from collections import Counter

# 페이지 설정
st.set_page_config(page_title="Lotto Analysis Pro (10회 안정버전)", page_icon="🍀", layout="centered")

# 디자인 설정 (아이폰 최적화)
st.markdown("""
    <style>
    .lotto-ball {
        display: inline-block; width: 40px; height: 40px; line-height: 40px;
        text-align: center; border-radius: 50%; font-weight: bold; font-size: 16px;
        margin: 3px; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    .ball-1 { background: #fbc02d; color: #333; }
    .ball-11 { background: #1976d2; }
    .ball-21 { background: #d32f2f; }
    .ball-31 { background: #616161; }
    .ball-41 { background: #388e3c; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background: #6200ee; color: white; border: none; }
    .card { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

def render_balls(numbers):
    html = '<div style="display: flex; flex-wrap: wrap; justify-content: center;">'
    for n in numbers:
        if n <= 10: cls = "ball-1"
        elif n <= 20: cls = "ball-11"
        elif n <= 30: cls = "ball-21"
        elif n <= 40: cls = "ball-31"
        else: cls = "ball-41"
        html += f'<div class="lotto-ball {cls}">{n:02d}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# --- 슈퍼KTS 10회차 실시간 스크래핑 (가장 빠르고 안정적) ---
@st.cache_data(ttl=3600)
def fetch_data_10_draws():
    # 사용자가 처음 제공했던 10회차 URL로 복구
    url = "https://superkts.com/lotto/recent/10"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        balls = soup.select('.ball_645')
        
        all_draws = []
        temp = []
        for b in balls:
            temp.append(int(b.get_text()))
            if len(temp) == 6:
                all_draws.append(temp)
                temp = []
        return all_draws, None
    except Exception as e:
        return None, str(e)

# --- 통계적 조합 필터링 엔진 ---
def validate_combination(combination):
    # 합계(Sum) 필터: 100 ~ 170 사이만 통과
    total = sum(combination)
    if not (100 <= total <= 170):
        return False
        
    # 홀짝(Even/Odd) 필터: 2:4, 3:3, 4:2 비율만 통과
    evens = len([n for n in combination if n % 2
