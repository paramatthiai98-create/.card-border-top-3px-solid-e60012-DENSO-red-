import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="SmartSafe Co-Pilot Dashboard",
    layout="wide"
)

# =========================================================
# AUTO REFRESH
# =========================================================
REFRESH_MS = 2000
st_autorefresh(interval=REFRESH_MS, key="datarefresh")

# =========================================================
# CONFIG
# =========================================================
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

MAX_SESSION_HISTORY = 100
MAX_SESSION_ALERTS = 20
DB_PATH = Path("smartsafe_history.db")

RANGE_OPTIONS = {
    "7 วัน": 7,
    "30 วัน": 30,
    "4 เดือน": 120,
    "8 เดือน": 240,
    "1 ปี": 365
}

# =========================================================
# DATABASE
# =========================================================
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        created_date TEXT NOT NULL,
        created_hour TEXT NOT NULL,
        line_key TEXT NOT NULL,
        process_name TEXT NOT NULL,
        helmet TEXT NOT NULL,
        distance REAL NOT NULL,
        vibration REAL NOT NULL,
        temperature REAL NOT NULL,
        risk INTEGER NOT NULL,
        status TEXT NOT NULL,
        action TEXT NOT NULL,
        reasons TEXT NOT NULL,
        solutions TEXT NOT NULL,
        is_demo INTEGER NOT NULL DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_history_line_time
    ON history(line_key, created_at)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_history_time
    ON history(created_at)
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alert_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        line_key TEXT NOT NULL,
        risk INTEGER NOT NULL,
        status TEXT NOT NULL,
        reasons TEXT NOT NULL,
        action TEXT NOT NULL,
        is_demo INTEGER NOT NULL DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_alert_line_time
    ON alert_log(line_key, created_at)
    """)

    conn.commit()
    conn.close()

init_db()

# =========================================================
# HELPERS
# =========================================================
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

def decision_logic(risk):
    risk = clamp_risk(risk)
    if risk > 80:
        return "HIGH RISK", "STOP MACHINE"
    if risk > 50:
        return "WARNING", "CHECK SYSTEM"
    return "SAFE", "NORMAL OPERATION"

def render_status_box(status):
    if status == "SAFE":
        st.success(status)
    elif status == "WARNING":
        st.warning(status)
    else:
        st.error(status)

def render_live_alert(line_key, status, reasons):
    if status == "HIGH RISK":
        st.error(f"🚨 {line_key}: HIGH RISK - {', '.join(reasons)}")
    elif status == "WARNING":
        st.warning(f"⚠️ {line_key}: WARNING - {', '.join(reasons)}")
    else:
        st.success(f"✅ {line_key}: SAFE - No active critical risk")

def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def current_hour_str():
    return datetime.now().strftime("%H:00")

def cutoff_datetime(days):
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")

# =========================================================
# DATA GENERATION
# =========================================================
def generate_random_data_by_line(line_key):
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

def ai_pattern_recommendation(df_line: pd.DataFrame, line_key: str):
    if df_line.empty:
        return "ยังไม่มีข้อมูลย้อนหลังเพียงพอ"

    msg = []
    high_count = int((df_line["status"] == "HIGH RISK").sum())
    warning_count = int((df_line["status"] == "WARNING").sum())
    avg_risk = float(df_line["risk"].mean())

    if high_count >= 10:
        msg.append("พบ HIGH RISK ซ้ำหลายครั้ง ควรทำ root cause analysis และกำหนด owner รายไลน์")
    if warning_count >= 20:
        msg.append("พบ WARNING สะสมจำนวนมาก ควรเปิด preventive review รายกะ")
    if avg_risk >= 60:
        msg.append("ค่าเฉลี่ยความเสี่ยงค่อนข้างสูง ควรเพิ่ม inspection frequency")

    helmet_no_rate = (df_line["helmet"] == "NO").mean() if len(df_line) else 0
    if helmet_no_rate >= 0.25:
        msg.append("พบอัตราไม่สวม PPE สูง ควรเพิ่ม PPE checkpoint ก่อนเข้าไลน์")

    if (df_line["vibration"] > 70).mean() >= 0.20:
        msg.append("พบ vibration สูงซ้ำ ควรวางแผน preventive maintenance")

    if (df_line["temperature"] > 60).mean() >= 0.20:
        msg.append("พบอุณหภูมิสูงซ้ำ ควรตรวจสอบระบบระบายความร้อนและ ventilation")

    if not msg:
        return f"{line_key}: แนวโน้มย้อนหลังยังอยู่ในเกณฑ์ควบคุมได้ ให้ติดตามต่อเนื่อง"

    return f"{line_key}: " + " | ".join(msg[:3])

# =========================================================
# DEMO FIXED SCENARIO
# =========================================================
def demo_fixed_data_by_risk(risk, line_key):
    risk = clamp_risk(risk)

    if risk <= 50:
        if line_key == "Line 1":
            d = {"helmet": True, "distance": 65, "vibration": 22, "temperature": 34}
            reasons = ["Normal operating condition"]
        elif line_key == "Line 2":
            d = {"helmet": True, "distance": 70, "vibration": 18, "temperature": 42}
            reasons = ["Normal operating condition"]
        elif line_key == "Line 3":
            d = {"helmet": True, "distance": 55, "vibration": 35, "temperature": 40}
            reasons = ["Normal operating condition"]
        else:
            d = {"helmet": True, "distance": 60, "vibration": 30, "temperature": 48}
            reasons = ["Normal operating condition"]

        solutions = ["ระบบอยู่ในเกณฑ์ปกติ ให้ติดตามต่อเนื่อง"]
        return d, reasons, solutions

    if risk <= 80:
        if line_key == "Line 1":
            d = {"helmet": False, "distance": 28, "vibration": 45, "temperature": 38}
            reasons = ["No helmet detected", "Worker too close to machine"]
        elif line_key == "Line 2":
            d = {"helmet": True, "distance": 45, "vibration": 25, "temperature": 66}
            reasons = ["High operating temperature"]
        elif line_key == "Line 3":
            d = {"helmet": True, "distance": 25, "vibration": 78, "temperature": 44}
            reasons = ["Worker too close to machine", "High machine vibration"]
        else:
            d = {"helmet": False, "distance": 40, "vibration": 50, "temperature": 67}
            reasons = ["No helmet detected", "High operating temperature"]

        solutions = ai_solution_by_line(reasons, line_key)
        return d, reasons, solutions

    if line_key == "Line 1":
        d = {"helmet": False, "distance": 18, "vibration": 55, "temperature": 42}
        reasons = ["No helmet detected", "Worker too close to machine"]
    elif line_key == "Line 2":
        d = {"helmet": False, "distance": 35, "vibration": 30, "temperature": 75}
        reasons = ["No helmet detected", "High operating temperature"]
    elif line_key == "Line 3":
        d = {"helmet": False, "distance": 15, "vibration": 85, "temperature": 49}
        reasons = ["No helmet detected", "Worker too close to machine", "High machine vibration"]
    else:
        d = {"helmet": False, "distance": 22, "vibration": 72, "temperature": 78}
        reasons = ["No helmet detected", "Worker too close to machine", "High machine vibration", "High operating temperature"]

    solutions = ai_solution_by_line(reasons, line_key)
    return d, reasons, solutions

# =========================================================
# DB WRITE / READ
# =========================================================
def insert_history_record(record: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history (
            created_at, created_date, created_hour, line_key, process_name,
            helmet, distance, vibration, temperature, risk, status, action,
            reasons, solutions, is_demo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["created_at"],
        record["created_date"],
        record["created_hour"],
        record["line_key"],
        record["process_name"],
        record["helmet"],
        record["distance"],
        record["vibration"],
        record["temperature"],
        record["risk"],
        record["status"],
        record["action"],
        record["reasons"],
        record["solutions"],
        record["is_demo"]
    ))
    conn.commit()
    conn.close()

def insert_alert_record(record: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO alert_log (
            created_at, line_key, risk, status, reasons, action, is_demo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        record["created_at"],
        record["line_key"],
        record["risk"],
        record["status"],
        record["reasons"],
        record["action"],
        record["is_demo"]
    ))
    conn.commit()
    conn.close()

def read_history(days: int, line_key: str | None = None):
    conn = get_conn()
    cutoff = cutoff_datetime(days)
    if line_key and line_key != "All Lines":
        query = """
            SELECT * FROM history
            WHERE created_at >= ? AND line_key = ?
            ORDER BY created_at ASC
        """
        df = pd.read_sql_query(query, conn, params=(cutoff, line_key))
    else:
        query = """
            SELECT * FROM history
            WHERE created_at >= ?
            ORDER BY created_at ASC
        """
        df = pd.read_sql_query(query, conn, params=(cutoff,))
    conn.close()
    return df

def read_recent_alerts(line_key: str, limit: int = 5):
    conn = get_conn()
    query = """
        SELECT created_at, risk, status, reasons, action
        FROM alert_log
        WHERE line_key = ?
        ORDER BY created_at DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(line_key, limit))
    conn.close()
    return df

def read_total_counts():
    conn = get_conn()
    cur = conn.cursor()
    total_history = cur.execute("SELECT COUNT(*) FROM history").fetchone()[0]
    total_alerts = cur.execute("SELECT COUNT(*) FROM alert_log").fetchone()[0]
    conn.close()
    return total_history, total_alerts

def delete_older_than(days: int):
    cutoff = cutoff_datetime(days)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM history WHERE created_at < ?", (cutoff,))
    cur.execute("DELETE FROM alert_log WHERE created_at < ?", (cutoff,))
    conn.commit()
    deleted = conn.total_changes
    conn.close()
    return deleted

# =========================================================
# SESSION STATE
# =========================================================
if "line_history" not in st.session_state:
    st.session_state.line_history = {line: [] for line in LINE_CONFIG.keys()}

if "line_alerts" not in st.session_state:
    st.session_state.line_alerts = {line: [] for line in LINE_CONFIG.keys()}

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("Control Panel")

demo_mode = st.sidebar.toggle("Demo Mode (Fixed Scenario)", value=True)

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

st.sidebar.markdown("---")
history_range_label = st.sidebar.selectbox(
    "Historical Range",
    list(RANGE_OPTIONS.keys()),
    index=2
)
history_days = RANGE_OPTIONS[history_range_label]

selected_history_line = st.sidebar.selectbox(
    "Historical Line Filter",
    ["All Lines"] + list(LINE_CONFIG.keys()),
    index=0
)

st.sidebar.markdown("---")
retention_days = st.sidebar.selectbox(
    "Data Retention",
    [30, 90, 180, 365, 730],
    index=3
)

if st.sidebar.button("Clean Old Data"):
    deleted_rows = delete_older_than(retention_days)
    st.sidebar.success(f"ลบข้อมูลเก่าแล้ว {deleted_rows} รายการ")

# =========================================================
# GENERATE CURRENT DATA + SAVE TO DB
# =========================================================
current_line_data = {}

for line_key in LINE_CONFIG.keys():
    if demo_mode:
        risk = clamp_risk(fixed_risk[line_key])
        d, reasons, solutions = demo_fixed_data_by_risk(risk, line_key)
    else:
        d = generate_random_data_by_line(line_key)
        risk, reasons = calculate_risk_by_line(d, line_key)
        solutions = ai_solution_by_line(reasons, line_key)

    risk = clamp_risk(risk)
    status, action = decision_logic(risk)
    ts = now_iso()

    record = {
        "created_at": ts,
        "created_date": today_str(),
        "created_hour": current_hour_str(),
        "line_key": line_key,
        "process_name": LINE_CONFIG[line_key]["name"],
        "helmet": "YES" if d["helmet"] else "NO",
        "distance": d["distance"],
        "vibration": d["vibration"],
        "temperature": d["temperature"],
        "risk": risk,
        "status": status,
        "action": action,
        "reasons": ", ".join(reasons) if reasons else "No active risk detected",
        "solutions": " | ".join(solutions),
        "is_demo": 1 if demo_mode else 0
    }

    insert_history_record(record)

    session_record = {
        "time": ts,
        "helmet": record["helmet"],
        "distance": record["distance"],
        "vibration": record["vibration"],
        "temperature": record["temperature"],
        "risk": record["risk"],
        "status": record["status"],
        "action": record["action"],
        "reasons": record["reasons"],
        "solutions": record["solutions"]
    }
    safe_append_limited(st.session_state.line_history[line_key], session_record, MAX_SESSION_HISTORY)

    if status in ["WARNING", "HIGH RISK"]:
        new_alert = {
            "created_at": ts,
            "line_key": line_key,
            "risk": risk,
            "status": status,
            "reasons": record["reasons"],
            "action": action,
            "is_demo": 1 if demo_mode else 0
        }

        alert_history = st.session_state.line_alerts[line_key]
        should_append = (
            len(alert_history) == 0
            or alert_history[-1]["reasons"] != new_alert["reasons"]
            or alert_history[-1]["status"] != new_alert["status"]
        )
        if should_append:
            safe_append_limited(alert_history, new_alert, MAX_SESSION_ALERTS)
            insert_alert_record(new_alert)

    current_line_data[line_key] = {
        "data": d,
        "risk": risk,
        "reasons": reasons,
        "status": status,
        "action": action,
        "solutions": solutions
    }

# =========================================================
# HEADER
# =========================================================
st.title("SmartSafe Co-Pilot Dashboard")
st.caption("DENSO-style production safety monitoring across 4 lines with SQLite historical storage")

if demo_mode:
    st.info("Demo Mode is ON: Risk, sensor values, reasons, and AI fixes are fixed by scenario.")

total_history, total_alerts = read_total_counts()
h1, h2, h3, h4 = st.columns(4)
h1.metric("Total History Rows", f"{total_history:,}")
h2.metric("Total Alert Rows", f"{total_alerts:,}")
h3.metric("Selected Range", history_range_label)
h4.metric("Refresh", f"{REFRESH_MS/1000:.0f}s")

# =========================================================
# OVERVIEW
# =========================================================
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

# =========================================================
# HISTORICAL DATA LOAD
# =========================================================
hist_df = read_history(history_days, selected_history_line)

if not hist_df.empty:
    hist_df["created_at"] = pd.to_datetime(hist_df["created_at"])
    hist_df["risk"] = hist_df["risk"].apply(clamp_risk)

# =========================================================
# TABS
# =========================================================
tab_names = ["Overview All"] + list(LINE_CONFIG.keys()) + ["Historical Analytics"]
tabs = st.tabs(tab_names)

# =========================================================
# TAB 0 - OVERVIEW ALL
# =========================================================
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

# =========================================================
# LINE TABS
# =========================================================
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
            st.markdown("### Session Risk Trend")
            df = pd.DataFrame(st.session_state.line_history[line_key])

            if "risk" in df.columns and not df.empty:
                df["risk"] = df["risk"].apply(clamp_risk)
                st.line_chart(df[["risk"]], use_container_width=True)
            else:
                st.info("ยังไม่มีข้อมูลกราฟ")

        with st.container(border=True):
            st.markdown(f"### Recent Alerts from SQLite ({history_range_label})")
            recent_alerts_df = read_recent_alerts(line_key, limit=5)

            if not recent_alerts_df.empty:
                for _, alert in recent_alerts_df.iterrows():
                    safe_risk = clamp_risk(alert["risk"])
                    msg = (
                        f"[{alert['created_at']}] {alert['status']} | "
                        f"Score {safe_risk} | {alert['reasons']} | "
                        f"Action: {alert['action']}"
                    )
                    if alert["status"] == "HIGH RISK":
                        st.error(msg)
                    else:
                        st.warning(msg)
            else:
                st.info("ยังไม่มีประวัติการแจ้งเตือน")

# =========================================================
# HISTORICAL ANALYTICS TAB
# =========================================================
with tabs[-1]:
    st.subheader("Historical Analytics")
    st.caption(f"ช่วงเวลาที่เลือก: {history_range_label} | Line: {selected_history_line}")

    if hist_df.empty:
        st.warning("ยังไม่มีข้อมูลย้อนหลังในช่วงเวลาที่เลือก")
    else:
        top1, top2, top3, top4 = st.columns(4)
        top1.metric("Rows", f"{len(hist_df):,}")
        top2.metric("Avg Risk", f"{hist_df['risk'].mean():.1f}")
        top3.metric("HIGH RISK", int((hist_df["status"] == "HIGH RISK").sum()))
        top4.metric("WARNING", int((hist_df["status"] == "WARNING").sum()))

        st.markdown("### Historical Trend")
        trend_df = (
            hist_df
            .assign(created_date_only=hist_df["created_at"].dt.date)
            .groupby(["created_date_only", "line_key"], as_index=False)
            .agg(
                avg_risk=("risk", "mean"),
                max_risk=("risk", "max"),
                alerts=("status", lambda s: int((s.isin(["WARNING", "HIGH RISK"])).sum()))
            )
        )

        if selected_history_line == "All Lines":
            pivot_avg = trend_df.pivot(index="created_date_only", columns="line_key", values="avg_risk")
            st.line_chart(pivot_avg, use_container_width=True)
        else:
            one_line = trend_df[trend_df["line_key"] == selected_history_line].set_index("created_date_only")
            st.line_chart(one_line[["avg_risk", "max_risk"]], use_container_width=True)

        a1, a2 = st.columns(2)

        with a1:
            st.markdown("### Risk by Line")
            risk_line_df = (
                hist_df.groupby("line_key", as_index=False)
                .agg(
                    avg_risk=("risk", "mean"),
                    max_risk=("risk", "max"),
                    records=("id", "count")
                )
                .sort_values("avg_risk", ascending=False)
                .set_index("line_key")
            )
            st.bar_chart(risk_line_df[["avg_risk", "max_risk"]], use_container_width=True)

        with a2:
            st.markdown("### Alert Distribution")
            alert_dist_df = (
                hist_df[hist_df["status"].isin(["WARNING", "HIGH RISK"])]
                .groupby(["line_key", "status"], as_index=False)
                .size()
            )
            if not alert_dist_df.empty:
                alert_pivot = alert_dist_df.pivot(index="line_key", columns="status", values="size").fillna(0)
                st.bar_chart(alert_pivot, use_container_width=True)
            else:
                st.info("ยังไม่มี WARNING/HIGH RISK ในช่วงเวลานี้")

        b1, b2 = st.columns(2)

        with b1:
            st.markdown("### Top Reasons")
            reason_series = (
                hist_df["reasons"]
                .str.split(", ")
                .explode()
                .dropna()
            )
            reason_df = (
                reason_series.value_counts()
                .reset_index()
            )
            reason_df.columns = ["Reason", "Count"]
            st.dataframe(reason_df.head(10), use_container_width=True, hide_index=True)

        with b2:
            st.markdown("### Hourly Hotspot")
            hourly_df = hist_df.copy()
            hourly_df["hour"] = hourly_df["created_at"].dt.hour
            hourly_summary = (
                hourly_df.groupby("hour", as_index=False)
                .agg(
                    avg_risk=("risk", "mean"),
                    alerts=("status", lambda s: int((s.isin(["WARNING", "HIGH RISK"])).sum()))
                )
                .set_index("hour")
            )
            st.line_chart(hourly_summary, use_container_width=True)

        st.markdown("### Safety Score by Line")
        safety_df = hist_df.groupby("line_key", as_index=False).agg(
            avg_risk=("risk", "mean"),
            helmet_yes_rate=("helmet", lambda s: round((s == "YES").mean() * 100, 2)),
            high_risk_count=("status", lambda s: int((s == "HIGH RISK").sum())),
            warning_count=("status", lambda s: int((s == "WARNING").sum()))
        )
        safety_df["safety_score"] = (
            100
            - safety_df["avg_risk"]
            - (safety_df["high_risk_count"] * 0.5)
            - (safety_df["warning_count"] * 0.2)
            + (safety_df["helmet_yes_rate"] * 0.1)
        ).clip(lower=0, upper=100).round(1)

        st.dataframe(
            safety_df.sort_values("safety_score", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### Pattern-based AI Insight")
        insight_lines = []
        for lk in hist_df["line_key"].unique():
            df_line = hist_df[hist_df["line_key"] == lk].copy()
            insight_lines.append(ai_pattern_recommendation(df_line, lk))
        for msg in insight_lines:
            st.info(msg)

        st.markdown("### Raw Historical Data")
        display_df = hist_df.copy()
        display_df["created_at"] = display_df["created_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv_data = to_csv_bytes(display_df)
        st.download_button(
            "Download Historical CSV",
            data=csv_data,
            file_name=f"smartsafe_history_{selected_history_line.replace(' ', '_').lower()}_{history_days}d.csv",
            mime="text/csv"
        )
