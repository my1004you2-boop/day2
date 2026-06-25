import streamlit as st
import pandas as pd
import altair as alt
import requests
from datetime import datetime

st.set_page_config(page_title="수강생 취업 현황 대시보드", layout="wide")

# --- 커스텀 CSS ---
st.markdown("""
<style>
    .stApp { background-color: #F5F7FA; }

    .dashboard-header {
        background: linear-gradient(135deg, #4F8EF7 0%, #6C63FF 100%);
        border-radius: 16px;
        padding: 32px 40px;
        margin-bottom: 28px;
        color: white;
    }
    .dashboard-header h1 { font-size: 2.2rem; font-weight: 800; margin: 0 0 6px 0; color: white; }
    .dashboard-header p { font-size: 1rem; margin: 0; opacity: 0.85; color: white; }

    .kpi-card {
        background: white;
        border-radius: 14px;
        padding: 24px 28px;
        box-shadow: 0 2px 12px rgba(79,142,247,0.10);
        text-align: center;
    }
    .kpi-label { font-size: 0.85rem; color: #7A8599; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 8px; }
    .kpi-value { font-size: 2rem; font-weight: 800; color: #1E2A3A; }
    .kpi-value span { font-size: 1.1rem; color: #4F8EF7; margin-right: 4px; }

    .section-card { background: white; border-radius: 14px; padding: 24px 28px; box-shadow: 0 2px 12px rgba(79,142,247,0.08); margin-bottom: 24px; }
    .section-title { font-size: 1.1rem; font-weight: 700; color: #1E2A3A; margin-bottom: 18px; }

    .stDataFrame { border-radius: 10px; overflow: hidden; }
    section[data-testid="stSidebar"] { background: #FFFFFF; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    .upload-box {
        background: white;
        border-radius: 14px;
        padding: 32px;
        box-shadow: 0 2px 12px rgba(79,142,247,0.08);
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)

# --- 헤더 ---
st.markdown("""
<div class="dashboard-header">
    <h1>🎓 수강생 취업 현황 대시보드</h1>
    <p>수강생 기본정보와 취업현황 파일을 업로드하면 자동으로 분석합니다</p>
</div>
""", unsafe_allow_html=True)

# --- 서울 날씨 ---
@st.cache_data(ttl=600)
def fetch_seoul_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=37.5665&longitude=126.9780"
        "&current=temperature_2m,weathercode"
        "&hourly=temperature_2m"
        "&forecast_days=1"
        "&timezone=Asia%2FSeoul"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def weathercode_to_label(code):
    if code == 0:
        return "맑음 ☀️"
    elif code in (1, 2, 3):
        return "구름 ⛅"
    elif code in range(51, 68):
        return "비 🌧️"
    elif code in range(71, 78):
        return "눈 🌨️"
    elif code in range(80, 83):
        return "소나기 🌦️"
    elif code in range(95, 100):
        return "뇌우 ⛈️"
    return "—"

try:
    weather_data = fetch_seoul_weather()
    current_temp = weather_data["current"]["temperature_2m"]
    current_code = weather_data["current"]["weathercode"]
    weather_label = weathercode_to_label(current_code)

    hourly_times = weather_data["hourly"]["time"]          # ["2024-06-25T00:00", ...]
    hourly_temps = weather_data["hourly"]["temperature_2m"]
    now_hour = datetime.now().hour
    df_hourly = pd.DataFrame({
        "시간": [f"{i:02d}시" for i in range(24)],
        "기온(°C)": hourly_temps[:24],
        "_hour": list(range(24)),
    })

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🌡️ 서울 오늘 날씨 (Open-Meteo)</div>', unsafe_allow_html=True)

    w_col1, w_col2 = st.columns([1, 3], gap="large")
    with w_col1:
        st.markdown(f"""
        <div class="kpi-card" style="margin-top:8px;">
            <div class="kpi-label">현재 기온</div>
            <div class="kpi-value" style="font-size:2.6rem;">{current_temp}°</div>
            <div style="font-size:1rem; color:#7A8599; margin-top:6px;">{weather_label}</div>
        </div>
        """, unsafe_allow_html=True)

    with w_col2:
        line = (
            alt.Chart(df_hourly)
            .mark_line(point=True, color="#4F8EF7", strokeWidth=2.5)
            .encode(
                x=alt.X("시간:N", sort=None, axis=alt.Axis(title=None, labelFontSize=11)),
                y=alt.Y("기온(°C):Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="°C")),
                tooltip=["시간:N", alt.Tooltip("기온(°C):Q", format=".1f")],
            )
        )
        now_rule = (
            alt.Chart(pd.DataFrame({"_hour": [now_hour]}))
            .mark_rule(color="#F76F6F", strokeDash=[4, 3], strokeWidth=2)
            .encode(x=alt.X("_hour:O"))
        )
        # now_rule uses ordinal position — use a simpler approach: highlight current hour bar
        highlight = df_hourly[df_hourly["_hour"] == now_hour]
        dot = (
            alt.Chart(highlight)
            .mark_point(size=120, color="#F76F6F", filled=True)
            .encode(
                x=alt.X("시간:N", sort=None),
                y=alt.Y("기온(°C):Q"),
                tooltip=["시간:N", alt.Tooltip("기온(°C):Q", format=".1f")],
            )
        )
        st.altair_chart((line + dot).properties(height=220).configure_view(strokeWidth=0).configure_axis(grid=False), use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.warning(f"날씨 정보를 불러오지 못했습니다: {e}")

# --- 파일 업로드 ---
st.markdown('<div class="upload-box">', unsafe_allow_html=True)
col_up1, col_up2 = st.columns(2)
with col_up1:
    st.markdown("#### 📋 수강생 기본정보 업로드")
    file1 = st.file_uploader("수강생_기본정보.xlsx", type=["xlsx", "xls"], key="file1")
with col_up2:
    st.markdown("#### 💼 수강생 취업현황 업로드")
    file2 = st.file_uploader("수강생_취업현황.xlsx", type=["xlsx", "xls"], key="file2")
st.markdown('</div>', unsafe_allow_html=True)

if not (file1 and file2):
    st.info("두 파일을 모두 업로드하면 대시보드가 표시됩니다.")
    st.stop()

# --- 데이터 로드 & 머지 ---
df_info = pd.read_excel(file1)
df_jobs = pd.read_excel(file2)

df = pd.merge(df_info, df_jobs, on="수강생ID", how="left")

# 날짜 컬럼 정리
df["등록일"] = pd.to_datetime(df["등록일"], errors="coerce")
df["취업일"] = pd.to_datetime(df["취업일"], errors="coerce")

# --- 사이드바 필터 ---
with st.sidebar:
    st.markdown("## 🔍 필터")

    campuses = ["전체"] + sorted(df["캠퍼스"].dropna().unique().tolist())
    selected_campus = st.selectbox("캠퍼스", campuses)

    courses = ["전체"] + sorted(df["수강과정"].dropna().unique().tolist())
    selected_course = st.selectbox("수강과정", courses)

    statuses = ["전체"] + sorted(df["취업상태"].dropna().unique().tolist())
    selected_status = st.selectbox("취업상태", statuses)

filtered = df.copy()
if selected_campus != "전체":
    filtered = filtered[filtered["캠퍼스"] == selected_campus]
if selected_course != "전체":
    filtered = filtered[filtered["수강과정"] == selected_course]
if selected_status != "전체":
    filtered = filtered[filtered["취업상태"] == selected_status]

# --- KPI 계산 ---
total_students = len(filtered)
completed = (filtered["수료여부"] == "수료").sum()
completion_rate = round(completed / total_students * 100, 1) if total_students else 0

employed = (filtered["취업상태"] == "취업완료").sum()
employment_rate = round(employed / total_students * 100, 1) if total_students else 0

avg_salary = filtered.loc[filtered["취업상태"] == "취업완료", "연봉(만원)"].mean()
avg_salary_str = f"{avg_salary:,.0f}" if pd.notna(avg_salary) else "—"

avg_coaching = filtered["커리어코칭횟수"].mean()
avg_coaching_str = f"{avg_coaching:.1f}" if pd.notna(avg_coaching) else "—"

# --- KPI 카드 ---
k1, k2, k3, k4 = st.columns(4)
kpi_data = [
    (k1, "총 수강생 수", f"{total_students:,}", "명"),
    (k2, "수료율", f"{completion_rate}", "%"),
    (k3, "취업률", f"{employment_rate}", "%"),
    (k4, "평균 연봉", avg_salary_str, "만원"),
]
for col, label, value, unit in kpi_data:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}<span style="font-size:1rem;color:#7A8599;"> {unit}</span></div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 차트 행 1: 취업상태 분포 + 캠퍼스별 취업률 ---
left, right = st.columns(2, gap="large")

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 취업상태 분포</div>', unsafe_allow_html=True)

    status_counts = filtered["취업상태"].value_counts().reset_index()
    status_counts.columns = ["취업상태", "인원수"]

    color_map = {"취업완료": "#4F8EF7", "구직중": "#F7A24F", "취업포기": "#F76F6F", "취업준비중": "#6C63FF"}
    chart = (
        alt.Chart(status_counts)
        .mark_arc(innerRadius=60, outerRadius=120)
        .encode(
            theta=alt.Theta("인원수:Q"),
            color=alt.Color("취업상태:N", scale=alt.Scale(
                domain=list(color_map.keys()),
                range=list(color_map.values())
            )),
            tooltip=["취업상태:N", "인원수:Q"],
        )
        .properties(height=280)
    )
    st.altair_chart(chart, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🏫 캠퍼스별 취업률</div>', unsafe_allow_html=True)

    campus_stats = (
        filtered.groupby("캠퍼스")
        .apply(lambda x: round((x["취업상태"] == "취업완료").sum() / len(x) * 100, 1), include_groups=False)
        .reset_index()
    )
    campus_stats.columns = ["캠퍼스", "취업률(%)"]

    chart2 = (
        alt.Chart(campus_stats)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("캠퍼스:N", axis=alt.Axis(title=None, labelFontSize=13)),
            y=alt.Y("취업률(%):Q", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(title="취업률 (%)")),
            color=alt.Color("캠퍼스:N", legend=None,
                scale=alt.Scale(scheme="blues")),
            tooltip=["캠퍼스:N", alt.Tooltip("취업률(%):Q", format=".1f")],
        )
        .properties(height=280)
        .configure_view(strokeWidth=0)
        .configure_axis(grid=False)
    )
    st.altair_chart(chart2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 차트 행 2: 수강과정별 평균 연봉 + 희망직군 분포 ---
left2, right2 = st.columns(2, gap="large")

with left2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💰 수강과정별 평균 연봉 (취업완료자)</div>', unsafe_allow_html=True)

    employed_df = filtered[filtered["취업상태"] == "취업완료"]
    if not employed_df.empty:
        salary_by_course = (
            employed_df.groupby("수강과정")["연봉(만원)"]
            .mean()
            .round(0)
            .reset_index()
            .sort_values("연봉(만원)", ascending=False)
        )
        salary_by_course.columns = ["수강과정", "평균연봉(만원)"]

        chart3 = (
            alt.Chart(salary_by_course)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("평균연봉(만원):Q", axis=alt.Axis(title="평균 연봉 (만원)")),
                y=alt.Y("수강과정:N", sort="-x", axis=alt.Axis(title=None)),
                color=alt.value("#4F8EF7"),
                tooltip=["수강과정:N", alt.Tooltip("평균연봉(만원):Q", format=",.0f")],
            )
            .properties(height=280)
            .configure_view(strokeWidth=0)
            .configure_axis(grid=False)
        )
        st.altair_chart(chart3, use_container_width=True)
    else:
        st.info("취업완료 데이터가 없습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

with right2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎯 희망직군 분포</div>', unsafe_allow_html=True)

    job_counts = filtered["희망직군"].value_counts().reset_index()
    job_counts.columns = ["희망직군", "인원수"]

    if not job_counts.empty:
        chart4 = (
            alt.Chart(job_counts)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("인원수:Q", axis=alt.Axis(title="인원수")),
                y=alt.Y("희망직군:N", sort="-x", axis=alt.Axis(title=None)),
                color=alt.value("#6C63FF"),
                tooltip=["희망직군:N", "인원수:Q"],
            )
            .properties(height=280)
            .configure_view(strokeWidth=0)
            .configure_axis(grid=False)
        )
        st.altair_chart(chart4, use_container_width=True)
    else:
        st.info("희망직군 데이터가 없습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 머지된 데이터 테이블 ---
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📋 수강생 전체 데이터 (머지 결과)</div>', unsafe_allow_html=True)

display_cols = ["수강생ID", "이름", "성별", "나이", "수강과정", "캠퍼스", "수료여부",
                "취업상태", "희망직군", "취업기업", "연봉(만원)", "커리어코칭횟수"]
display_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[display_cols].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
    height=400,
)
st.markdown('</div>', unsafe_allow_html=True)
