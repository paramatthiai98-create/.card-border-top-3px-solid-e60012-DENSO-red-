import streamlit as st
import random
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

st.set_page_config(
    page_title="SmartSafe DENSO Production Dashboard",
    layout="wide"
)

st_autorefresh(interval=2000, key="datarefresh")

# -------------------------
# STYLE
# -------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #03101f 0%, #06172b 100%);
    color: #f8fafc;
}
.block-container {
    max-width: 96rem;
    padding-top: 1rem;
    padding-bottom: 1rem;
}
.main-title {
    font-size: 2.35rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 0.15rem;
}
.sub-title {
    color: #b6c2cf;
    margin-bottom: 1.2rem;
    font-size: 1rem;
}
.card {
    background: linear-gradient(180deg, rgba(7,20,40,0.98), rgba(5,17,34,0.98));
    border: 1px solid rgba(255,255,255,0.08);
    border-top: 3px solid #e60012;
    border-radius: 22px;
    padding: 22px;
    margin-bottom: 16px;
    box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset;
}
.card-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 1rem;
}
.label {
    font-size: 0.95rem;
    color: #9fb0c3;
    margin-bottom: 0.25rem;
}
.big-value {
    font-size: 2.45rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.1;
    margin-bottom: 0.9rem;
}
.big-sub-value {
    font-size: 1.9rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.15;
    margin-bottom: 0.8rem;
}
.info-line {
    font-size: 1rem;
    color: #e5e7eb;
    margin: 0.35rem 0;
}
.panel {
    background: rgba(8, 20, 38, 0.97);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 22px;
    padding: 18px 20px;
    margin-bottom: 16px;
}
.section-title {
    font-size: 1.28rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 0.85rem;
}
.alert-main {
    border-radius: 18px;
    padding: 18px 20px;
    font-weight: 700;
    font-size: 1.05rem;
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 16px;
}
.alert-safe {
    background: rgba(22,163,74,0.16);
    color: #bbf7d0;
}
.alert-warning {
    background: rgba(245,158,11,0.18);
    color: #fde68a;
}
.alert-risk {
    background: rgba(239,68,68,0.18);
    color: #fecaca;
}
.fix-box {
    background: rgba(59,130,246,0.12);
    border: 1px solid rgba(59,130,246,0.28);
    border-radius: 16px;
    padding: 14px 16px;
    margin-bottom: 10px;
    color: #dbeafe;
    font-size: 1rem;
}
.small-alert {
    border-radius: 14px;
    padding: 12px 14px;
    font-size: 0.97rem;
    margin-bottom: 10px;
    border: 1px solid rgba(255,255,255,0.08);
}
.small-warning {
    background: rgba(245,158,11,0.12);
    color: #fde68a;
}
.small-risk {
    background: rgba(239,68,68,0.14);
    color: #fecaca;
}
.status-chip {
    display: inline-block;
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 0.84rem;
    font-weight: 800;
    margin-bottom: 1rem;
}
.status-safe {
    background: rgba(22,163,74,0.18);
    color: #86efac;
    border: 1px solid rgba(22,163,74,0.32);
}
.status-warning {
    background: rgba(245,158,11,0.18);
    color: #fcd34d;
    border: 1px solid rgba(245,158,11,0.32);
}
.status-risk {
    background: rgba(239,68,68,0.18);
    color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.32);
}
.line-caption {
    color: #cbd5e1;
    font-size: 0.96rem;
    margin-top: -0.2rem;
    margin-bottom: 0.8rem;
}
.overview-box {
    background: linear-gradient(180deg, rgba(9,24,46,0.97), rgba(6,18,34,0.98));
    border: 1px solid rgba(255,255,255,0.08);
    border-top: 4px solid #e60012;
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 12px;
    min-height: 168px;
    box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset;
}
.overview-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 10px;
}
.overview-line {
    font-size: 1.1rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.2;
}
.overview-process {
    font-size: 1rem;
    font-weight: 700;
    color: #e5e7eb;
    line-height: 1.2;
    margin-top: 2px;
}
.overview-desc {
    color: #94a3b8;
    font-size: 0.88rem;
    line-height: 1.45;
    margin-top: 6px;
    min-height: 40px;
}
.overview-risk-wrap {
    text-align: right;
    min-width: 78px;
}
.overview-risk-label {
    color: #94a3b8;
    font-size: 0.76rem;
    margin-bottom: 2px;
}
.overview-risk-value {
    color: #ffffff;
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1;
}
.overview-footer {
    margin-top: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
}
.overview-mini {
    color: #cbd5e1;
    font-size: 0.88rem;
}
button[data-baseweb="tab"] {
    font-weight: 700 !important;
    font-size: 0.98rem !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# LINE CONFIG
# -------------------------
LINE_CONFIG = {
    "Line 1": {
        "name": "Sensor Assembly",
        "description": "Temperature / Pressure / Oxygen Sensor Assembly Line"
    },
    "Line 2": {
        "name": "ECU Production",
        "description": "Electronic Control Unit and PCB Assembly Line"
    },
    "Line 3": {
        "name": "Fuel Injector",
        "description": "Fuel System / Injector Precision Manufacturing Line"
    },
    "Line 4": {
        "name": "EV Components",
        "description": "Battery / Motor / Power Electronics Assembly Line"
    }
}

# -------------------------
# DATA / LOGIC
# -------------------------
def generate_data_by_line(line_key: str):
    if line_key == "Line 1":
        return {
            "helmet": random.choice([True, False]),
            "distance": random.randint(15, 80),
            "vibration": random.randint(10, 60),
            "temperature": random.randint(25, 45)
        }
    elif line_key == "Line 2":
        return {
            "helmet": random.choice([True, False]),
            "distance": random.randint(20, 90),
            "vibration": random.randint(5, 40),
            "temperature": random.randint(30, 65)
        }
    elif line_key == "Line 3":
        return {
            "helmet": random.choice([True, False]),
            "distance": random.randint(10, 70),
            "vibration": random.randint(25, 90),
            "temperature": random.randint(28, 55)
        }
    else:
        return {
            "helmet": random.choice([True, False]),
            "distance": random.randint(15, 85),
            "vibration": random.randint(10, 75),
            "temperature": random.randint(35, 80)
        }


def calculate_risk_by_line(d, line_key: str):
    risk = 0
    reasons = []

    if not d["helmet"]:
        risk += 40 if line_key == "Line 4" else 30
        reasons.append("No helmet detected")

    if d["distance"] < 30:
        risk += 45 if line_key == "Line 3" else 40
        reasons.append("Worker too close to machine")

    if d["vibration"] > 70:
        risk += 45 if line_key == "Line 3" else 35
        reasons.append("High machine vibration")

    if d["temperature"] > 60:
        if line_key in ["Line 2", "Line 4"]:
            risk += 35
            reasons.append("High operating temperature")
        elif d["temperature"] > 70:
            risk += 20
            reasons.append("High operating temperature")

    return min(risk, 100), reasons


def decision_logic(risk):
    if risk > 80:
        return "HIGH RISK", "STOP MACHINE"
    elif risk > 50:
        return "WARNING", "CHECK SYSTEM"
    return "SAFE", "NORMAL OPERATION"


def ai_solution_by_line(reasons, line_key: str):
    solutions = []

    if "No helmet detected" in reasons:
        solutions.append("ให้พนักงานสวมหมวกนิรภัยก่อนเข้าพื้นที่ปฏิบัติงาน")
        if line_key == "Line 1":
            solutions.append("เพิ่มจุดตรวจ PPE ก่อนเข้าพื้นที่ประกอบเซนเซอร์")
        elif line_key == "Line 4":
            solutions.append("เพิ่มมาตรการ PPE เข้มงวดในพื้นที่ EV / High Voltage")
        else:
            solutions.append("ติดตั้งระบบตรวจจับ PPE อัตโนมัติ")

    if "Worker too close to machine" in reasons:
        if line_key == "Line 3":
            solutions.append("เพิ่มระยะปลอดภัยจากเครื่องจักรความเร็วสูงในไลน์หัวฉีด")
        else:
            solutions.append("เพิ่มระยะปลอดภัยระหว่างคนงานกับเครื่องจักร")
        solutions.append("กำหนดเขต safe zone ให้ชัดเจน")

    if "High machine vibration" in reasons:
        if line_key == "Line 3":
            solutions.append("ตรวจสอบเครื่องจักร precision machining และ fixture ทันที")
        else:
            solutions.append("ตรวจสอบการสั่นสะเทือนของเครื่องจักรทันที")
        solutions.append("หยุดเครื่องเพื่อตรวจเช็กความผิดปกติ")
        solutions.append("วางแผนบำรุงรักษาเชิงป้องกัน")

    if "High operating temperature" in reasons:
        if line_key == "Line 2":
            solutions.append("ตรวจสอบระบบระบายความร้อนใน ECU/PCB line")
            solutions.append("ควบคุมอุณหภูมิพื้นที่ผลิตอิเล็กทรอนิกส์")
        elif line_key == "Line 4":
            solutions.append("ตรวจสอบอุณหภูมิในพื้นที่ EV Components ทันที")
            solutions.append("แยกพื้นที่ความร้อนสูงและเพิ่มระบบระบายอากาศ")
        else:
            solutions.append("ตรวจสอบอุณหภูมิการทำงานของอุปกรณ์")

    if not solutions:
        solutions.append("ระบบอยู่ในเกณฑ์ปกติ ให้ติดตามต่อเนื่อง")

    return solutions


def render_status_chip(status):
    if status == "HIGH RISK":
        return '<span class="status-chip status-risk">HIGH RISK</span>'
    elif status == "WARNING":
        return '<span class="status-chip status-warning">WARNING</span>'
    return '<span class="status-chip status-safe">SAFE</span>'


# -------------------------
# SESSION STATE
# -------------------------
if "line_history" not in st.session_state:
    st.session_state.line_history = {line: [] for line in LINE_CONFIG.keys()}

if "line_alerts" not in st.session_state:
    st.session_state.line_alerts = {line: [] for line in LINE_CONFIG.keys()}

# -------------------------
# GENERATE DATA FOR ALL LINES
# -------------------------
current_line_data = {}

for line_key in LINE_CONFIG.keys():
    d = generate_data_by_line(line_key)
    risk, reasons = calculate_risk_by_line(d, line_key)
    status, action = decision_logic(risk)
    solutions = ai_solution_by_line(reasons, line_key)

    record = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "helmet": "YES" if d["helmet"] else "NO",
        "distance": d["distance"],
        "vibration": d["vibration"],
        "temperature": d["temperature"],
        "risk": risk,
        "status": status,
        "action": action,
        "reasons": ", ".join(reasons) if reasons else "No active risk detected",
        "solutions": " | ".join(solutions)
    }

    st.session_state.line_history[line_key].append(record)
    if len(st.session_state.line_history[line_key]) > 100:
        st.session_state.line_history[line_key] = st.session_state.line_history[line_key][-100:]

    if status in ["WARNING", "HIGH RISK"]:
        new_alert = {
            "time": record["time"],
            "risk": record["risk"],
            "status": record["status"],
            "reasons": record["reasons"],
            "action": record["action"]
        }

        alert_history = st.session_state.line_alerts[line_key]
        if (
            len(alert_history) == 0
            or alert_history[-1]["reasons"] != new_alert["reasons"]
            or alert_history[-1]["status"] != new_alert["status"]
        ):
            alert_history.append(new_alert)

    if len(st.session_state.line_alerts[line_key]) > 20:
        st.session_state.line_alerts[line_key] = st.session_state.line_alerts[line_key][-20:]

    current_line_data[line_key] = {
        "data": d,
        "risk": risk,
        "reasons": reasons,
        "status": status,
        "action": action,
        "solutions": solutions
    }

# -------------------------
# HEADER
# -------------------------
st.markdown('<div class="main-title">SmartSafe Co-Pilot Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">DENSO-style production safety monitoring across 4 lines</div>', unsafe_allow_html=True)

# -------------------------
# OVERVIEW
# -------------------------
st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)

cols = st.columns(4)

for i, line in enumerate(LINE_CONFIG):
    with cols[i]:
        info = LINE_CONFIG[line]
        d = current_data[line]["data"]
        risk = current_data[line]["risk"]
        status = current_data[line]["status"]

        st.markdown(f"### {line}")
        st.markdown(f"**{info['name']}**")

        st.write(info["description"])

        st.metric("Risk", risk)

        col1, col2 = st.columns(2)
        col1.write(f"Helmet: {'YES' if d['helmet'] else 'NO'}")
        col2.write(f"Temp: {d['temperature']} °C")

        if status == "SAFE":
            st.success("SAFE")
        elif status == "WARNING":
            st.warning("WARNING")
        else:
            st.error("HIGH RISK")

# -------------------------
# TABS
# -------------------------
tab_names = ["Overview All"] + list(LINE_CONFIG.keys())
tabs = st.tabs(tab_names)

with tabs[0]:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">All Production Lines Summary</div>', unsafe_allow_html=True)

    summary_rows = []
    for line_key, line_info in LINE_CONFIG.items():
        line_now = current_line_data[line_key]
        d = line_now["data"]
        summary_rows.append({
            "Line": line_key,
            "Process": line_info["name"],
            "Helmet": "YES" if d["helmet"] else "NO",
            "Distance (cm)": d["distance"],
            "Vibration": d["vibration"],
            "Temperature (°C)": d["temperature"],
            "Risk": line_now["risk"],
            "Status": line_now["status"],
            "Action": line_now["action"]
        })

    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    risk_compare = pd.DataFrame({
        "Line": list(LINE_CONFIG.keys()),
        "Risk Score": [current_line_data[line]["risk"] for line in LINE_CONFIG.keys()]
    }).set_index("Line")

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Risk Comparison</div>', unsafe_allow_html=True)
    st.line_chart(risk_compare, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

for idx, line_key in enumerate(LINE_CONFIG.keys(), start=1):
    with tabs[idx]:
        line_info = LINE_CONFIG[line_key]
        line_now = current_line_data[line_key]
        d = line_now["data"]
        risk = line_now["risk"]
        reasons = line_now["reasons"]
        status = line_now["status"]
        action = line_now["action"]
        solutions = line_now["solutions"]

        st.markdown(f'<div class="section-title">{line_key} - {line_info["name"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="line-caption">{line_info["description"]}</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3, gap="large")

        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Worker Status</div>', unsafe_allow_html=True)
            st.markdown('<div class="label">Helmet</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="big-value">{"YES" if d["helmet"] else "NO"}</div>', unsafe_allow_html=True)
            st.markdown('<div class="label">Distance</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="big-sub-value">{d["distance"]} cm</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Machine Status</div>', unsafe_allow_html=True)
            st.markdown('<div class="label">Vibration</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="big-value">{d["vibration"]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="label">Temperature</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="big-sub-value">{d["temperature"]} °C</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Risk Analysis</div>', unsafe_allow_html=True)
            st.markdown('<div class="label">Risk Score</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="big-value">{risk}</div>', unsafe_allow_html=True)
            st.markdown(render_status_chip(status), unsafe_allow_html=True)
            st.progress(risk / 100)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">Live Alert</div>', unsafe_allow_html=True)

        if status == "HIGH RISK":
            st.markdown(
                f'<div class="alert-main alert-risk">🚨 {line_key}: HIGH RISK - {", ".join(reasons)}</div>',
                unsafe_allow_html=True
            )
        elif status == "WARNING":
            st.markdown(
                f'<div class="alert-main alert-warning">⚠️ {line_key}: WARNING - {", ".join(reasons)}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="alert-main alert-safe">✅ {line_key}: SAFE - No active critical risk</div>',
                unsafe_allow_html=True
            )

        left, right = st.columns([1, 1.15], gap="large")

        with left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">AI Decision Support</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-line">Recommended Action: <b>{action}</b></div>', unsafe_allow_html=True)

            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Explainable AI</div>', unsafe_allow_html=True)
            if reasons:
                for r in reasons:
                    st.markdown(f'<div class="info-line">• {r}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="info-line">• No active risk detected</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with right:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">AI Recommended Fix</div>', unsafe_allow_html=True)
            for s in solutions:
                st.markdown(f'<div class="fix-box">• {s}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Risk Trend</div>', unsafe_allow_html=True)
        df = pd.DataFrame(st.session_state.line_history[line_key])
        st.line_chart(df[["risk"]], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Recent Alerts</div>', unsafe_allow_html=True)

        if st.session_state.line_alerts[line_key]:
            for alert in reversed(st.session_state.line_alerts[line_key][-5:]):
                if alert["status"] == "HIGH RISK":
                    st.markdown(
                        f'<div class="small-alert small-risk">[{alert["time"]}] HIGH RISK | Score {alert["risk"]} | {alert["reasons"]} | Action: {alert["action"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="small-alert small-warning">[{alert["time"]}] WARNING | Score {alert["risk"]} | {alert["reasons"]} | Action: {alert["action"]}</div>',
                        unsafe_allow_html=True
                    )
        else:
            st.info("ยังไม่มีประวัติการแจ้งเตือน")

        st.markdown('</div>', unsafe_allow_html=True)
