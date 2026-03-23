import random
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="SmartSafe DENSO Production Dashboard",
    layout="wide"
)

# รีเฟรชทุก 2 วินาที
st_autorefresh(interval=2000, key="datarefresh")

# -------------------------
# CONFIG
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

MAX_HISTORY = 100
MAX_ALERTS = 20

# -------------------------
# SIDEBAR DEMO CONTROL
# -------------------------
st.sidebar.title("Demo Control")

demo_mode = st.sidebar.toggle("Demo Mode (Fix Risk from UI)", value=True)

fixed_risk = {}
if demo_mode:
    st.sidebar.markdown("### Set Risk per Line")
    for line in LINE_CONFIG.keys():
        default_value = 30
        if line == "Line 2":
            default_value = 0
        elif line == "Line 3":
            default_value = 50
        elif line == "Line 4":
            default_value = 75

        fixed_risk[line] = st.sidebar.slider(
            f"{line} Risk",
            min_value=0,
            max_value=100,
            value=default_value,
            step=1
        )

# -------------------------
# SAFETY HELPERS
# -------------------------
def clamp_risk(value):
    try:
        value = int(round(float(value)))
    except Exception:
        return 0
    return max(0, min(value, 100))


def progress_value_from_risk(risk):
    return clamp_risk(risk) / 100.0


def safe_append_limited(items, value, max_len):
    items.append(value)
    if len(items) > max_len:
        del items[:-max_len]

# -------------------------
# DATA GENERATION
# -------------------------
def generate_data_by_line(line_key):
    if line_key == "Line 1":
        return {
            "helmet": random.choice([True, False]),
            "distance": random.randint(15, 80),
            "vibration": random.randint(10, 60),
            "temperature": random.randint(25, 45)
        }
    if line_key == "Line 2":
        return {
            "helmet": random.choice([True, False]),
            "distance": random.randint(20, 90),
            "vibration": random.randint(5, 40),
            "temperature": random.randint(30, 65)
        }
    if line_key == "Line 3":
        return {
            "helmet": random.choice([True, False]),
            "distance": random.randint(10, 70),
            "vibration": random.randint(25, 90),
            "temperature": random.randint(28, 55)
        }
    return {
        "helmet": random.choice([True, False]),
        "distance": random.randint(15, 85),
        "vibration": random.randint(10, 75),
        "temperature": random.randint(35, 80)
    }


def calculate_risk_by_line(d, line_key):
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

    return clamp_risk(risk), reasons


def decision_logic(risk):
    risk = clamp_risk(risk)
    if risk > 80:
        return "HIGH RISK", "STOP MACHINE"
    if risk > 50:
        return "WARNING", "CHECK SYSTEM"
    return "SAFE", "NORMAL OPERATION"


def ai_solution_by_line(reasons, line_key):
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

# -------------------------
# RENDER HELPERS
# -------------------------
def render_status_box(status):
    if status == "SAFE":
        st.success(status)
    elif status == "WARNING":
        st.warning(status)
    else:
        st.error(status)


def render_live_alert(line_key, status, reasons):
    if status == "HIGH RISK":
        st.error(f"🚨 {line_key}: HIGH RISK - {', '.join(reasons) if reasons else 'Risk level overridden by demo mode'}")
    elif status == "WARNING":
        st.warning(f"⚠️ {line_key}: WARNING - {', '.join(reasons) if reasons else 'Risk level overridden by demo mode'}")
    else:
        st.success(f"✅ {line_key}: SAFE - No active critical risk")

# -------------------------
# SESSION STATE
# -------------------------
if "line_history" not in st.session_state:
    st.session_state.line_history = {line: [] for line in LINE_CONFIG.keys()}

if "line_alerts" not in st.session_state:
    st.session_state.line_alerts = {line: [] for line in LINE_CONFIG.keys()}

# -------------------------
# GENERATE CURRENT DATA
# -------------------------
current_line_data = {}

for line_key in LINE_CONFIG.keys():
   d = generate_data_by_line(line_key)
calc_risk, reasons = calculate_risk_by_line(d, line_key)

if demo_mode:
    risk = clamp_risk(fixed_risk[line_key])
    reasons, solutions = demo_reason_and_solution_by_risk(risk, line_key)
else:
    risk = calc_risk
    solutions = ai_solution_by_line(reasons, line_key)

status, action = decision_logic(risk)

    record = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "helmet": "YES" if d["helmet"] else "NO",
        "distance": d["distance"],
        "vibration": d["vibration"],
        "temperature": d["temperature"],
        "risk": clamp_risk(risk),
        "status": status,
        "action": action,
        "reasons": ", ".join(reasons) if reasons else "No active risk detected",
        "solutions": " | ".join(solutions)
    }

    safe_append_limited(st.session_state.line_history[line_key], record, MAX_HISTORY)

    if status in ["WARNING", "HIGH RISK"]:
        new_alert = {
            "time": record["time"],
            "risk": record["risk"],
            "status": record["status"],
            "reasons": record["reasons"],
            "action": record["action"]
        }

        alert_history = st.session_state.line_alerts[line_key]
        should_append = (
            len(alert_history) == 0
            or alert_history[-1]["reasons"] != new_alert["reasons"]
            or alert_history[-1]["status"] != new_alert["status"]
        )
        if should_append:
            safe_append_limited(alert_history, new_alert, MAX_ALERTS)

    current_line_data[line_key] = {
        "data": d,
        "risk": clamp_risk(risk),
        "reasons": reasons,
        "status": status,
        "action": action,
        "solutions": solutions
    }

# -------------------------
# HEADER
# -------------------------
st.title("SmartSafe Co-Pilot Dashboard")
st.caption("DENSO-style production safety monitoring across 4 lines")

if demo_mode:
    st.info("Demo Mode is ON: Risk Score of each line is controlled from the sidebar sliders.")

# -------------------------
# OVERVIEW
# -------------------------
st.subheader("Overview")

overview_cols = st.columns(4, gap="medium")

for i, line_key in enumerate(LINE_CONFIG.keys()):
    with overview_cols[i]:
        line_info = LINE_CONFIG[line_key]
        line_now = current_line_data[line_key]
        d = line_now["data"]

        with st.container(border=True):
            left, right = st.columns([2, 1])
            with left:
                st.markdown(f"**{line_key}**")
                st.write(line_info["name"])
            with right:
                st.metric("Risk", line_now["risk"])

            st.caption(line_info["description"])

            c1, c2 = st.columns(2)
            c1.write(f"Helmet: {'YES' if d['helmet'] else 'NO'}")
            c2.write(f"Temp: {d['temperature']} °C")

            render_status_box(line_now["status"])

# -------------------------
# TABS
# -------------------------
tab_names = ["Overview All"] + list(LINE_CONFIG.keys())
tabs = st.tabs(tab_names)

with tabs[0]:
    st.subheader("All Production Lines Summary")

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

    st.subheader("Risk Comparison")
    risk_compare = pd.DataFrame({
        "Line": list(LINE_CONFIG.keys()),
        "Risk Score": [clamp_risk(current_line_data[line]["risk"]) for line in LINE_CONFIG.keys()]
    }).set_index("Line")
    st.line_chart(risk_compare, use_container_width=True)

for idx, line_key in enumerate(LINE_CONFIG.keys(), start=1):
    with tabs[idx]:
        line_info = LINE_CONFIG[line_key]
        line_now = current_line_data[line_key]
        d = line_now["data"]
        risk = clamp_risk(line_now["risk"])
        reasons = line_now["reasons"]
        status = line_now["status"]
        action = line_now["action"]
        solutions = line_now["solutions"]

        st.subheader(f"{line_key} - {line_info['name']}")
        st.caption(line_info["description"])

        col1, col2, col3 = st.columns(3, gap="large")

        with col1:
            with st.container(border=True):
                st.markdown("### Worker Status")
                st.metric("Helmet", "YES" if d["helmet"] else "NO")
                st.metric("Distance", f"{d['distance']} cm")

        with col2:
            with st.container(border=True):
                st.markdown("### Machine Status")
                st.metric("Vibration", d["vibration"])
                st.metric("Temperature", f"{d['temperature']} °C")

        with col3:
            with st.container(border=True):
                st.markdown("### Risk Analysis")
                st.metric("Risk Score", risk)
                render_status_box(status)
                st.progress(progress_value_from_risk(risk))

        st.subheader("Live Alert")
        render_live_alert(line_key, status, reasons)

        left, right = st.columns([1, 1.15], gap="large")

        with left:
            with st.container(border=True):
                st.markdown("### AI Decision Support")
                st.write(f"Recommended Action: **{action}**")

                st.markdown("### Explainable AI")
                if reasons:
                    for r in reasons:
                        st.write(f"- {r}")
                else:
                    st.write("- No active risk detected")

        with right:
            with st.container(border=True):
                st.markdown("### AI Recommended Fix")
                for s in solutions:
                    st.info(s)

        with st.container(border=True):
            st.markdown("### Risk Trend")
            df = pd.DataFrame(st.session_state.line_history[line_key])

            if "risk" in df.columns and not df.empty:
                df["risk"] = df["risk"].apply(clamp_risk)
                st.line_chart(df[["risk"]], use_container_width=True)
            else:
                st.info("ยังไม่มีข้อมูลกราฟ")

        with st.container(border=True):
            st.markdown("### Recent Alerts")
            if st.session_state.line_alerts[line_key]:
                for alert in reversed(st.session_state.line_alerts[line_key][-5:]):
                    safe_risk = clamp_risk(alert["risk"])
                    msg = (
                        f"[{alert['time']}] {alert['status']} | "
                        f"Score {safe_risk} | {alert['reasons']} | "
                        f"Action: {alert['action']}"
                    )
                    if alert["status"] == "HIGH RISK":
                        st.error(msg)
                    else:
                        st.warning(msg)
            else:
                st.info("ยังไม่มีประวัติการแจ้งเตือน")
