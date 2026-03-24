import random
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SmartSafe DENSO Production Dashboard",
    layout="wide"
)

REFRESH_INTERVAL = 2  # seconds — native rerun, no extra package needed

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
MAX_ALERTS  = 20
DB_PATH     = Path("smartsafe_history.db")

# -------------------------
# DATABASE LAYER
# -------------------------
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sensor_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,
                line_key    TEXT NOT NULL,
                helmet      INTEGER,
                distance    INTEGER,
                vibration   INTEGER,
                temperature INTEGER,
                risk        INTEGER,
                status      TEXT,
                action      TEXT,
                reasons     TEXT,
                solutions   TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ts     ON sensor_events(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_line   ON sensor_events(line_key)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON sensor_events(status)")


def insert_event(timestamp: str, line_key: str, record: dict):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO sensor_events
                (timestamp, line_key, helmet, distance, vibration, temperature,
                 risk, status, action, reasons, solutions)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            timestamp, line_key,
            1 if record["helmet"] == "YES" else 0,
            record["distance"], record["vibration"], record["temperature"],
            record["risk"], record["status"], record["action"],
            record["reasons"], record["solutions"]
        ))


def query_history(line_keys: list, days: int) -> pd.DataFrame:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    ph = ",".join("?" * len(line_keys))
    with get_db() as conn:
        rows = conn.execute(f"""
            SELECT timestamp, line_key, helmet, distance, vibration, temperature,
                   risk, status, action, reasons
            FROM sensor_events
            WHERE timestamp >= ? AND line_key IN ({ph})
            ORDER BY timestamp
        """, [since] + line_keys).fetchall()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def query_alert_summary(line_keys: list, days: int) -> pd.DataFrame:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    ph = ",".join("?" * len(line_keys))
    with get_db() as conn:
        rows = conn.execute(f"""
            SELECT line_key, status,
                   COUNT(*)   AS count,
                   AVG(risk)  AS avg_risk,
                   MAX(risk)  AS max_risk
            FROM sensor_events
            WHERE timestamp >= ? AND line_key IN ({ph})
              AND status IN ('WARNING','HIGH RISK')
            GROUP BY line_key, status
            ORDER BY line_key, status
        """, [since] + line_keys).fetchall()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def query_hourly_heatmap(line_key: str, days: int) -> pd.DataFrame:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        rows = conn.execute("""
            SELECT CAST(strftime('%H','timestamp') AS INTEGER) AS hour,
                   CAST(strftime('%w','timestamp') AS INTEGER) AS dow,
                   AVG(risk) AS avg_risk
            FROM sensor_events
            WHERE timestamp >= ? AND line_key = ?
            GROUP BY hour, dow
            ORDER BY hour, dow
        """, [since, line_key]).fetchall()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def query_rolling_risk(line_keys: list, days: int) -> pd.DataFrame:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    ph = ",".join("?" * len(line_keys))
    with get_db() as conn:
        rows = conn.execute(f"""
            SELECT strftime('%Y-%m-%d', timestamp) AS date,
                   line_key,
                   AVG(risk) AS avg_risk,
                   MAX(risk) AS max_risk,
                   SUM(CASE WHEN status='HIGH RISK' THEN 1 ELSE 0 END) AS high_risk_count
            FROM sensor_events
            WHERE timestamp >= ? AND line_key IN ({ph})
            GROUP BY date, line_key
            ORDER BY date
        """, [since] + line_keys).fetchall()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def query_anomaly_events(line_keys: list, days: int) -> pd.DataFrame:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    ph = ",".join("?" * len(line_keys))
    with get_db() as conn:
        rows = conn.execute(f"""
            SELECT timestamp, line_key, risk, status, reasons
            FROM sensor_events
            WHERE timestamp >= ? AND line_key IN ({ph})
              AND status = 'HIGH RISK'
            ORDER BY timestamp DESC
            LIMIT 200
        """, [since] + line_keys).fetchall()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def get_db_stats() -> dict:
    with get_db() as conn:
        total  = conn.execute("SELECT COUNT(*) FROM sensor_events").fetchone()[0]
        oldest = conn.execute("SELECT MIN(timestamp) FROM sensor_events").fetchone()[0]
    size_kb = DB_PATH.stat().st_size / 1024 if DB_PATH.exists() else 0
    return {"total": total, "oldest": oldest, "size_kb": size_kb}


init_db()

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.title("Demo Control")
demo_mode = st.sidebar.toggle("Demo Mode (Fixed Scenario)", value=True)

fixed_risk = {}
if demo_mode:
    st.sidebar.markdown("### Set Risk per Line")
    defaults = {"Line 1": 30, "Line 2": 0, "Line 3": 50, "Line 4": 75}
    for line in LINE_CONFIG:
        fixed_risk[line] = st.sidebar.slider(
            f"{line} Risk", min_value=0, max_value=100,
            value=defaults[line], step=1
        )

st.sidebar.divider()
st.sidebar.markdown("### Database Info")
stats = get_db_stats()
st.sidebar.metric("Total records", f"{stats['total']:,}")
if stats["oldest"]:
    st.sidebar.caption(f"Oldest: {stats['oldest'][:10]}")
st.sidebar.caption(f"DB size: {stats['size_kb']:.1f} KB")

# -------------------------
# HELPERS
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


def decision_logic(risk):
    risk = clamp_risk(risk)
    if risk > 80:
        return "HIGH RISK", "STOP MACHINE"
    if risk > 50:
        return "WARNING",   "CHECK SYSTEM"
    return "SAFE",          "NORMAL OPERATION"


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


# -------------------------
# RANDOM DATA GENERATORS
# -------------------------
def generate_random_data_by_line(line_key):
    if line_key == "Line 1":
        return {"helmet": random.choice([True, False]),
                "distance": random.randint(15, 80),
                "vibration": random.randint(10, 60),
                "temperature": random.randint(25, 45)}
    if line_key == "Line 2":
        return {"helmet": random.choice([True, False]),
                "distance": random.randint(20, 90),
                "vibration": random.randint(5, 40),
                "temperature": random.randint(30, 65)}
    if line_key == "Line 3":
        return {"helmet": random.choice([True, False]),
                "distance": random.randint(10, 70),
                "vibration": random.randint(25, 90),
                "temperature": random.randint(28, 55)}
    return {"helmet": random.choice([True, False]),
            "distance": random.randint(15, 85),
            "vibration": random.randint(10, 75),
            "temperature": random.randint(35, 80)}


def calculate_risk_by_line(d, line_key):
    risk, reasons = 0, []
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


# -------------------------
# DEMO FIXED SCENARIO
# -------------------------
def demo_fixed_data_by_risk(risk, line_key):
    risk = clamp_risk(risk)

    if risk <= 50:
        maps = {
            "Line 1": {"helmet": True, "distance": 65, "vibration": 22, "temperature": 34},
            "Line 2": {"helmet": True, "distance": 70, "vibration": 18, "temperature": 42},
            "Line 3": {"helmet": True, "distance": 55, "vibration": 35, "temperature": 40},
            "Line 4": {"helmet": True, "distance": 60, "vibration": 30, "temperature": 48},
        }
        return maps[line_key], ["Normal operating condition"], ["ระบบอยู่ในเกณฑ์ปกติ ให้ติดตามต่อเนื่อง"]

    if risk <= 80:
        maps = {
            "Line 1": ({"helmet": False, "distance": 28, "vibration": 45, "temperature": 38},
                       ["No helmet detected", "Worker too close to machine"]),
            "Line 2": ({"helmet": True,  "distance": 45, "vibration": 25, "temperature": 66},
                       ["High operating temperature"]),
            "Line 3": ({"helmet": True,  "distance": 25, "vibration": 78, "temperature": 44},
                       ["Worker too close to machine", "High machine vibration"]),
            "Line 4": ({"helmet": False, "distance": 40, "vibration": 50, "temperature": 67},
                       ["No helmet detected", "High operating temperature"]),
        }
        d, reasons = maps[line_key]
        return d, reasons, ai_solution_by_line(reasons, line_key)

    maps = {
        "Line 1": ({"helmet": False, "distance": 18, "vibration": 55, "temperature": 42},
                   ["No helmet detected", "Worker too close to machine"]),
        "Line 2": ({"helmet": False, "distance": 35, "vibration": 30, "temperature": 75},
                   ["No helmet detected", "High operating temperature"]),
        "Line 3": ({"helmet": False, "distance": 15, "vibration": 85, "temperature": 49},
                   ["No helmet detected", "Worker too close to machine", "High machine vibration"]),
        "Line 4": ({"helmet": False, "distance": 22, "vibration": 72, "temperature": 78},
                   ["No helmet detected", "Worker too close to machine",
                    "High machine vibration", "High operating temperature"]),
    }
    d, reasons = maps[line_key]
    return d, reasons, ai_solution_by_line(reasons, line_key)


# -------------------------
# SESSION STATE INIT
# -------------------------
if "line_history" not in st.session_state:
    st.session_state.line_history = {line: [] for line in LINE_CONFIG}
if "line_alerts" not in st.session_state:
    st.session_state.line_alerts = {line: [] for line in LINE_CONFIG}
if "last_saved_minute" not in st.session_state:
    st.session_state.last_saved_minute = ""
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "live"

# -------------------------
# GENERATE CURRENT DATA + PERSIST
# -------------------------
current_line_data = {}
now            = datetime.now()
now_str        = now.strftime("%Y-%m-%d %H:%M:%S")
current_minute = now.strftime("%Y-%m-%d %H:%M")
should_save    = (current_minute != st.session_state.last_saved_minute)

for line_key in LINE_CONFIG:
    if demo_mode:
        risk = clamp_risk(fixed_risk[line_key])
        d, reasons, solutions = demo_fixed_data_by_risk(risk, line_key)
    else:
        d = generate_random_data_by_line(line_key)
        risk, reasons = calculate_risk_by_line(d, line_key)
        solutions = ai_solution_by_line(reasons, line_key)

    risk = clamp_risk(risk)
    status, action = decision_logic(risk)

    record = {
        "time":        now.strftime("%H:%M:%S"),
        "helmet":      "YES" if d["helmet"] else "NO",
        "distance":    d["distance"],
        "vibration":   d["vibration"],
        "temperature": d["temperature"],
        "risk":        risk,
        "status":      status,
        "action":      action,
        "reasons":     ", ".join(reasons) if reasons else "No active risk detected",
        "solutions":   " | ".join(solutions),
    }

    safe_append_limited(st.session_state.line_history[line_key], record, MAX_HISTORY)

    if should_save:
        insert_event(now_str, line_key, record)

    if status in ("WARNING", "HIGH RISK"):
        new_alert = {k: record[k] for k in ("time", "risk", "status", "reasons", "action")}
        hist = st.session_state.line_alerts[line_key]
        if (not hist
                or hist[-1]["reasons"] != new_alert["reasons"]
                or hist[-1]["status"]  != new_alert["status"]):
            safe_append_limited(hist, new_alert, MAX_ALERTS)

    current_line_data[line_key] = {
        "data": d, "risk": risk, "reasons": reasons,
        "status": status, "action": action, "solutions": solutions,
    }

if should_save:
    st.session_state.last_saved_minute = current_minute

# -------------------------
# HEADER
# -------------------------
st.title("SmartSafe Co-Pilot Dashboard")
st.caption("DENSO-style production safety monitoring — real-time + historical analysis")

if demo_mode:
    st.info("Demo Mode ON — risk, sensor values and AI fixes are scenario-driven.")

# -------------------------
# OVERVIEW CARDS
# -------------------------
st.subheader("Overview")
ov_cols = st.columns(4, gap="medium")
for i, line_key in enumerate(LINE_CONFIG):
    with ov_cols[i]:
        info    = LINE_CONFIG[line_key]
        line_now = current_line_data[line_key]
        d       = line_now["data"]
        with st.container(border=True):
            l, r = st.columns([2, 1])
            with l:
                st.markdown(f"**{line_key}**")
                st.write(info["name"])
            with r:
                st.metric("Risk", line_now["risk"])
            st.caption(info["description"])
            c1, c2 = st.columns(2)
            c1.write(f"Helmet: {'YES' if d['helmet'] else 'NO'}")
            c2.write(f"Temp: {d['temperature']} °C")
            render_status_box(line_now["status"])

# -------------------------
# TABS
# -------------------------
tab_labels = ["Overview All"] + list(LINE_CONFIG.keys()) + ["📊 Historical Analysis"]
tabs = st.tabs(tab_labels)

# ── Tab 0 : Overview All ────────────────────────────────────────────────────
with tabs[0]:
    st.session_state.active_tab = "live"
    st.subheader("All Production Lines Summary")

    rows = []
    for lk, info in LINE_CONFIG.items():
        ln = current_line_data[lk]
        d  = ln["data"]
        rows.append({
            "Line": lk, "Process": info["name"],
            "Helmet": "YES" if d["helmet"] else "NO",
            "Distance (cm)": d["distance"], "Vibration": d["vibration"],
            "Temperature (°C)": d["temperature"],
            "Risk": ln["risk"], "Status": ln["status"], "Action": ln["action"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Risk Comparison")
    rc = pd.DataFrame({
        "Line": list(LINE_CONFIG.keys()),
        "Risk Score": [clamp_risk(current_line_data[lk]["risk"]) for lk in LINE_CONFIG],
    }).set_index("Line")
    st.line_chart(rc, use_container_width=True)

# ── Tabs 1-4 : Per-line ─────────────────────────────────────────────────────
for idx, line_key in enumerate(LINE_CONFIG, start=1):
    with tabs[idx]:
        st.session_state.active_tab = "live"
        info     = LINE_CONFIG[line_key]
        line_now = current_line_data[line_key]
        d        = line_now["data"]
        risk     = clamp_risk(line_now["risk"])
        reasons  = line_now["reasons"]
        status   = line_now["status"]
        action   = line_now["action"]
        solutions = line_now["solutions"]

        st.subheader(f"{line_key} — {info['name']}")
        st.caption(info["description"])

        c1, c2, c3 = st.columns(3, gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("### Worker Status")
                st.metric("Helmet",   "YES" if d["helmet"] else "NO")
                st.metric("Distance", f"{d['distance']} cm")
        with c2:
            with st.container(border=True):
                st.markdown("### Machine Status")
                st.metric("Vibration",   d["vibration"])
                st.metric("Temperature", f"{d['temperature']} °C")
        with c3:
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
                for r in (reasons if reasons else ["No active risk detected"]):
                    st.write(f"- {r}")
        with right:
            with st.container(border=True):
                st.markdown("### AI Recommended Fix")
                for s in solutions:
                    st.info(s)

        with st.container(border=True):
            st.markdown("### Risk Trend")
            df_rt = pd.DataFrame(st.session_state.line_history[line_key])
            if "risk" in df_rt.columns and not df_rt.empty:
                df_rt["risk"] = df_rt["risk"].apply(clamp_risk)
                st.line_chart(df_rt[["risk"]], use_container_width=True)
            else:
                st.info("ยังไม่มีข้อมูลกราฟ")

        with st.container(border=True):
            st.markdown("### Recent Alerts")
            alerts = st.session_state.line_alerts[line_key]
            if alerts:
                for alert in reversed(alerts[-5:]):
                    msg = (f"[{alert['time']}] {alert['status']} | "
                           f"Score {clamp_risk(alert['risk'])} | "
                           f"{alert['reasons']} | Action: {alert['action']}")
                    if alert["status"] == "HIGH RISK":
                        st.error(msg)
                    else:
                        st.warning(msg)
            else:
                st.info("ยังไม่มีประวัติการแจ้งเตือน")

# ── Tab 5 : Historical Analysis ──────────────────────────────────────────────
with tabs[5]:
    st.session_state.active_tab = "historical"
    st.subheader("📊 Historical Analysis")
    st.caption("วิเคราะห์ข้อมูลย้อนหลังจากฐานข้อมูล SQLite")

    ctrl1, ctrl2, _ = st.columns([1, 1, 2])
    with ctrl1:
        period_label = st.selectbox(
            "ช่วงเวลา",
            options=["7 วัน", "1 เดือน", "4 เดือน", "8 เดือน", "1 ปี"],
            index=0,
        )
    with ctrl2:
        selected_lines = st.multiselect(
            "เลือกไลน์",
            options=list(LINE_CONFIG.keys()),
            default=list(LINE_CONFIG.keys()),
        )

    period_map = {
        "7 วัน": 7, "1 เดือน": 30,
        "4 เดือน": 120, "8 เดือน": 240, "1 ปี": 365,
    }
    days = period_map[period_label]

    if not selected_lines:
        st.warning("กรุณาเลือกอย่างน้อย 1 ไลน์")
    else:
        df_hist = query_history(selected_lines, days)

        if df_hist.empty:
            st.info(
                f"ยังไม่มีข้อมูลในช่วง {period_label} ที่เลือก\n\n"
                "ระบบบันทึก 1 ครั้ง/นาที — รอให้ระบบทำงานสักครู่แล้วลองใหม่ครับ"
            )
        else:
            df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])

            # ── 1. Daily risk trend ─────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### แนวโน้มความเสี่ยงรายวัน (Daily Risk Trend)")

            df_daily = query_rolling_risk(selected_lines, days)
            if not df_daily.empty:
                pivot_avg = df_daily.pivot_table(
                    index="date", columns="line_key", values="avg_risk"
                ).ffill()
                st.line_chart(pivot_avg, use_container_width=True)

                pivot_high = df_daily.pivot_table(
                    index="date", columns="line_key", values="high_risk_count"
                ).fillna(0)
                st.caption("จำนวน HIGH RISK events ต่อวัน")
                st.bar_chart(pivot_high, use_container_width=True)

            # ── 2. Alert summary ────────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### สรุป Alert (Alert Summary)")

            df_summary = query_alert_summary(selected_lines, days)
            if not df_summary.empty:
                df_summary["avg_risk"] = df_summary["avg_risk"].round(1)
                df_summary.columns = ["Line", "Status", "Count", "Avg Risk", "Max Risk"]
                st.dataframe(df_summary, use_container_width=True, hide_index=True)

                m_cols = st.columns(len(selected_lines))
                for i, lk in enumerate(selected_lines):
                    sub = df_summary[df_summary["Line"] == lk]
                    total = int(sub["Count"].sum()) if not sub.empty else 0
                    with m_cols[i]:
                        st.metric(lk, f"{total} alerts")
            else:
                st.success("ไม่มี alert ในช่วงเวลาที่เลือก ✅")

            # ── 3. Shift / hour heatmap ─────────────────────────────────────
            st.markdown("---")
            st.markdown("#### Shift Heatmap — ชั่วโมงที่มีความเสี่ยงสูง")

            hm_line = st.selectbox(
                "เลือกไลน์สำหรับ heatmap", options=selected_lines, key="hm_line"
            )
            df_hm = query_hourly_heatmap(hm_line, days)

            if not df_hm.empty:
                dow_labels = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"]
                df_hm["dow_label"] = df_hm["dow"].map(lambda x: dow_labels[int(x)])

# ✅ แก้แล้ว — guard None และ NaN
lambda x: dow_labels[int(x)] if x is not None and str(x) != "nan" else "?"
                pivot_hm = (
                    df_hm.pivot_table(index="hour", columns="dow_label", values="avg_risk")
                    .reindex(columns=dow_labels)
                    .fillna(0)
                )
                st.dataframe(
                    pivot_hm.style.background_gradient(cmap="RdYlGn_r", vmin=0, vmax=100),
                    use_container_width=True,
                )
                st.caption(
                    "สี: เขียว = ปลอดภัย / แดง = ความเสี่ยงสูง | "
                    "แถว = ชั่วโมง (0–23), คอลัมน์ = วันในสัปดาห์"
                )
            else:
                st.info("ยังไม่มีข้อมูลสำหรับ heatmap")

            # ── 4. Anomaly events ───────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### 🚨 Anomaly Events (HIGH RISK incidents)")

            df_anomaly = query_anomaly_events(selected_lines, days)
            if not df_anomaly.empty:
                st.metric("HIGH RISK events ทั้งหมด", len(df_anomaly))
                st.dataframe(
                    df_anomaly.rename(columns={
                        "timestamp": "เวลา", "line_key": "ไลน์",
                        "risk": "Risk Score", "status": "Status", "reasons": "สาเหตุ",
                    }),
                    use_container_width=True, hide_index=True,
                )
            else:
                st.success("ไม่มี HIGH RISK events ในช่วงเวลาที่เลือก ✅")

            # ── 5. Export ───────────────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### Export ข้อมูล")

            e1, e2 = st.columns(2)
            with e1:
                st.download_button(
                    label="⬇️ Download raw CSV",
                    data=df_hist.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"smartsafe_history_{period_label.replace(' ','_')}.csv",
                    mime="text/csv",
                )
            with e2:
                if not df_summary.empty:
                    st.download_button(
                        label="⬇️ Download Alert Summary CSV",
                        data=df_summary.to_csv(index=False).encode("utf-8-sig"),
                        file_name=f"smartsafe_alerts_{period_label.replace(' ','_')}.csv",
                        mime="text/csv",
                    )

            # ── 6. Predictive 7-day rolling score ──────────────────────────
            st.markdown("---")
            st.markdown("#### 📈 Predictive Risk Score (7-day rolling average)")
            st.caption("ค่าเฉลี่ย rolling 7 วัน — บ่งชี้แนวโน้มความเสี่ยงล่วงหน้าเบื้องต้น")

            df_pred = query_rolling_risk(selected_lines, days)
            if not df_pred.empty:
                df_pred["date"] = pd.to_datetime(df_pred["date"])
                pred_frames = []
                for lk in selected_lines:
                    sub = (
                        df_pred[df_pred["line_key"] == lk]
                        .sort_values("date")
                        .set_index("date")
                    )
                    sub[f"rolling_{lk}"] = sub["avg_risk"].rolling(7, min_periods=1).mean()
                    pred_frames.append(sub[[f"rolling_{lk}"]])
                if pred_frames:
                    st.line_chart(
                        pd.concat(pred_frames, axis=1).ffill(),
                        use_container_width=True,
                    )

# -------------------------
# AUTO-REFRESH (end of script)
# Pauses 2 s then triggers a full rerun — native Streamlit, no extra libs.
# Skipped when user is on the Historical tab to avoid interrupting analysis.
# -------------------------
if st.session_state.get("active_tab", "live") != "historical":
    time.sleep(REFRESH_INTERVAL)
    st.rerun()
