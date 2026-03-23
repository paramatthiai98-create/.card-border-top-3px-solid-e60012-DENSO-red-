import streamlit as st
import random
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from textwrap import dedent

st.set_page_config(page_title="SmartSafe DENSO Dashboard", layout="wide")

st_autorefresh(interval=2000, key="refresh")

# -------------------------
# STYLE
# -------------------------
st.markdown("""
<style>
.stApp {background:#06172b;color:white;}
.main-title {font-size:2rem;font-weight:800;}
.sub-title {color:#94a3b8;margin-bottom:15px;}

.overview-box {
    background:#081a33;
    border-radius:16px;
    padding:16px;
    border-top:4px solid #e60012;
}
.overview-top {
    display:flex;justify-content:space-between;
}
.overview-line {font-weight:800;font-size:1.1rem;}
.overview-process {color:#e5e7eb;}
.overview-risk-value {font-size:1.8rem;font-weight:800;}
.overview-desc {color:#94a3b8;margin-top:6px;}
.overview-footer {margin-top:10px;display:flex;justify-content:space-between;}
.status-chip {padding:6px 12px;border-radius:999px;font-weight:700;}
.status-safe {background:green;}
.status-warning {background:orange;}
.status-risk {background:red;}
</style>
""", unsafe_allow_html=True)

# -------------------------
# LINE CONFIG
# -------------------------
LINE_CONFIG = {
    "Line 1": {"name":"Sensor Assembly","description":"Temperature / Pressure / Oxygen Sensor Assembly Line"},
    "Line 2": {"name":"ECU Production","description":"Electronic Control Unit and PCB Assembly Line"},
    "Line 3": {"name":"Fuel Injector","description":"Fuel System / Injector Precision Manufacturing Line"},
    "Line 4": {"name":"EV Components","description":"Battery / Motor / Power Electronics Assembly Line"},
}

# -------------------------
# DATA
# -------------------------
def generate_data():
    return {
        "helmet": random.choice([True, False]),
        "distance": random.randint(10,80),
        "vibration": random.randint(10,90),
        "temperature": random.randint(25,80)
    }

def calculate_risk(d):
    risk = 0
    if not d["helmet"]: risk += 30
    if d["distance"] < 30: risk += 40
    if d["vibration"] > 70: risk += 30
    if d["temperature"] > 60: risk += 30
    return min(risk,100)

def get_status(r):
    if r>80: return "HIGH RISK"
    if r>50: return "WARNING"
    return "SAFE"

def chip(s):
    if s=="HIGH RISK": return '<span class="status-chip status-risk">HIGH</span>'
    if s=="WARNING": return '<span class="status-chip status-warning">WARN</span>'
    return '<span class="status-chip status-safe">SAFE</span>'

# -------------------------
# GENERATE DATA
# -------------------------
current_data = {}
for line in LINE_CONFIG:
    d = generate_data()
    risk = calculate_risk(d)
    status = get_status(risk)

    current_data[line] = {
        "data": d,
        "risk": risk,
        "status": status
    }

# -------------------------
# HEADER
# -------------------------
st.markdown('<div class="main-title">SmartSafe Co-Pilot Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">DENSO Production Monitoring</div>', unsafe_allow_html=True)

# -------------------------
# OVERVIEW (FIXED)
# -------------------------
st.markdown("### Overview")

cols = st.columns(4)

for i, line in enumerate(LINE_CONFIG):
    with cols[i]:
        info = LINE_CONFIG[line]
        d = current_data[line]["data"]
        risk = current_data[line]["risk"]
        status = current_data[line]["status"]

        html = dedent(f"""
        <div class="overview-box">
            <div class="overview-top">
                <div>
                    <div class="overview-line">{line}</div>
                    <div class="overview-process">{info['name']}</div>
                </div>
                <div>
                    <div>Risk</div>
                    <div class="overview-risk-value">{risk}</div>
                </div>
            </div>

            <div class="overview-desc">{info['description']}</div>

            <div class="overview-footer">
                <div>
                    Helmet: <b>{"YES" if d["helmet"] else "NO"}</b><br>
                    Temp: <b>{d["temperature"]} °C</b>
                </div>
                <div>
                    {chip(status)}
                </div>
            </div>
        </div>
        """).strip()

        st.markdown(html, unsafe_allow_html=True)

# -------------------------
# TABS
# -------------------------
tabs = st.tabs(["Overview All","Line 1","Line 2","Line 3","Line 4"])

# SUMMARY TAB
with tabs[0]:
    rows=[]
    for line in LINE_CONFIG:
        d=current_data[line]["data"]
        rows.append({
            "Line":line,
            "Helmet": "YES" if d["helmet"] else "NO",
            "Temp":d["temperature"],
            "Risk":current_data[line]["risk"]
        })
    st.dataframe(pd.DataFrame(rows))

# LINE DETAIL
for idx,line in enumerate(LINE_CONFIG, start=1):
    with tabs[idx]:
        d=current_data[line]["data"]
        risk=current_data[line]["risk"]
        status=current_data[line]["status"]

        st.write("###", line)
        st.write("Helmet:", "YES" if d["helmet"] else "NO")
        st.write("Distance:", d["distance"])
        st.write("Temp:", d["temperature"])
        st.write("Risk:", risk)
        st.write("Status:", status)

        df=pd.DataFrame([current_data[line]["risk"] for _ in range(10)], columns=["risk"])
        st.line_chart(df)
