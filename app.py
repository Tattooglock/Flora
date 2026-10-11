import streamlit as st
import pandas as pd
import sqlite3
import os
import html
import calendar as cal_mod
from datetime import datetime, date, timedelta
import plotly.express as px

# --- 🌸 НАЛАШТУВАННЯ ---
st.set_page_config(page_title="🌷 Квітковий Календар", page_icon="🌸", layout="wide")

# Якщо на Railway підключений Volume з mount path /data — база лежить там (не губиться при деплої)
DATA_DIR = "/data" if os.path.isdir("/data") else "."
DB_NAME = os.path.join(DATA_DIR, "florist_db.sqlite")
ARCHIVE_DIR = os.path.join(DATA_DIR, "Місячні_Звіти")

custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
.stApp { background: linear-gradient(135deg, #fdf6f0 0%, #f9e4e1 50%, #f4d4d8 100%); }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #8b4a5e !important; text-align: center; font-weight: 600 !important; }
h1 { font-size: 2.8rem !important; background: linear-gradient(120deg, #d4758c, #b85c7a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem !important; }
p, li, label, span { font-family: 'Inter', sans-serif !important; color: #5a3e4b !important; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #f9e4e1 0%, #f4d4d8 100%) !important; border-right: 2px solid #e8b4bc !important; }
section[data-testid="stSidebar"] .stRadio label { font-size: 1.05rem !important; padding: 10px 15px !important; border-radius: 12px !important; margin: 4px 0 !important; transition: all 0.3s ease !important; }
section[data-testid="stSidebar"] .stRadio label:hover { background-color: #ffffff80 !important; transform: translateX(5px); }
.stButton > button { background: linear-gradient(135deg, #d4758c 0%, #b85c7a 100%) !important; color: white !important; border: none !important; border-radius: 25px !important; padding: 0.6rem 2rem !important; font-family: 'Inter', sans-serif !important; font-weight: 500 !important; letter-spacing: 0.5px !important; box-shadow: 0 4px 15px rgba(212, 117, 140, 0.3) !important; transition: all 0.3s ease !important; }
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(212, 117, 140, 0.5) !important; background: linear-gradient(135deg, #b85c7a 0%, #9d4a66 100%) !important; }
[data-testid="stMetric"] { background: linear-gradient(135deg, #ffffff 0%, #fff5f7 100%) !important; border: 1px solid #f4d4d8 !important; border-radius: 20px !important; padding: 20px !important; box-shadow: 0 4px 15px rgba(212, 117, 140, 0.1) !important; transition: transform 0.3s ease !important; }
[data-testid="stMetric"]:hover { transform: translateY(-5px) !important; box-shadow: 0 8px 25px rgba(212, 117, 140, 0.2) !important; }
[data-testid="stMetricLabel"] { color: #8b4a5e !important; font-weight: 500 !important; font-size: 0.95rem !important; }
[data-testid="stMetricValue"] { color: #d4758c !important; font-family: 'Playfair Display', serif !important; font-weight: 700 !important; font-size: 2rem !important; }
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input, .stTimeInput input { background-color: #ffffff !important; border: 1.5px solid #f4d4d8 !important; border-radius: 12px !important; padding: 10px 15px !important; color: #5a3e4b !important; transition: all 0.3s ease !important; }
.stTextInput input:focus, .stTextArea textarea:focus { border-color: #d4758c !important; box-shadow: 0 0 0 3px rgba(212, 117, 140, 0.15) !important; }
.stSelectbox div[data-baseweb="select"] > div { background-color: #ffffff !important; border: 1.5px solid #f4d4d8 !important; border-radius: 12px !important; }
.streamlit-expanderHeader { background: linear-gradient(90deg, #fff5f7 0%, #ffffff 100%) !important; border: 1px solid #f4d4d8 !important; border-radius: 15px !important; padding: 12px 20px !important; font-family: 'Playfair Display', serif !important; color: #8b4a5e !important; font-weight: 600 !important; }
[data-testid="stDataFrame"] { border-radius: 15px !important; overflow: hidden !important; box-shadow: 0 4px 15px rgba(212, 117, 140, 0.1) !important; }
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 🔒 ПАРОЛЬ (задається змінною APP_PASSWORD на Railway; якщо не задана — без пароля) ---
APP_PASSWORD = os.environ.get("APP_PASSWORD")
if APP_PASSWORD and not st.session_state.get("auth_ok"):
    st.markdown("<h1>🌸 Вхід</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Пароль", type="password")
    if pwd:
        if pwd == APP_PASSWORD:
            st.session_state["auth_ok"] = True
            st.rerun()
        else:
            st.error("Невірний пароль")
    st.stop()

# --- 🌷 HEADER ---
st.markdown("""
<div style="text-align: center; padding: 20px 0 30px 0;">
    <div style="font-size: 3rem; margin-bottom: 10px;">🌸 🌷 🌹 🌺 🌸</div>
    <h1 style="margin: 0;">Квітковий Календар</h1>
    <p style="font-style: italic; color: #8b4a5e; font-size: 1.1rem; margin-top: 5px;">
        ✨ Твій затишний простір для квіткової магії ✨
    </p>
    <div style="font-size: 2rem; margin-top: 10px;">🌺 🌹 🌷 🌸 🌺</div>
</div>
""", unsafe_allow_html=True)

# --- 🌹 БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_name TEXT, phone TEXT, description TEXT,
                  price REAL, cost REAL, order_date TEXT, order_time TEXT,
                  status TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reminders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_name TEXT, event_type TEXT, event_date TEXT,
                  description TEXT, phone TEXT)''')
    conn.commit()
    conn.close()

init_db()
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# --- 🌼 МЕНЮ ---
st.sidebar.markdown("## 🌸 Меню")
page = st.sidebar.radio(" ", [
    "🌷 Статистика місяця",
    "📊 Графіки та аналітика",
    "🌹 Календар замовлень",
    "💐 Нове замовлення",
    "🎂 Нагадування",
    "🌺 Пошук та клієнти",
    "🌻 Архів місяців"
], label_visibility="collapsed")

conn = sqlite3.connect(DB_NAME)

# --- 📊 СТАТИСТИКА ---
if page == "🌷 Статистика місяця":
    st.markdown("### 📊 Статистика поточного місяця")
    st.markdown("---")

    today = date.today()
    current_month = today.strftime("%Y-%m")

    df = pd.read_sql_query("SELECT * FROM orders WHERE order_date LIKE ?", conn, params=(current_month + "%",))

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("<div style='text-align:center; font-size:2rem;'>💐</div>", unsafe_allow_html=True)
        st.metric("Замовлень", len(df))
    with col2:
        st.markdown("<div style='text-align:center; font-size:2rem;'>💰</div>", unsafe_allow_html=True)
        st.metric("Дохід", f"{df['price'].sum():.2f} грн")
    with col3:
        st.markdown("<div style='text-align:center; font-size:2rem;'>🌱</div>", unsafe_allow_html=True)
        st.metric("Витрати", f"{df['cost'].sum():.2f} грн")
    with col4:
        st.markdown("<div style='text-align:center; font-size:2rem;'>✨</div>", unsafe_allow_html=True)
        st.metric("Чистий прибуток", f"{(df['price'].sum() - df['cost'].sum()):.2f} грн")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🎂 Найближчі події")

    reminders_df = pd.read_sql_query("SELECT * FROM reminders ORDER BY event_date ASC", conn)

    if not reminders_df.empty:
        today_str = today.strftime("%Y-%m-%d")
        upcoming = reminders_df[reminders_df['event_date'] >= today_str].head(5)

        if not upcoming.empty:
            for _, reminder in upcoming.iterrows():
                event_date = datetime.strptime(reminder['event_date'], "%Y-%m-%d").date()  # FIX: .date()
                days_until = (event_date - today).days

                if days_until == 0:
                    alert = "🔴 СЬОГОДНІ!"
                elif days_until <= 3:
                    alert = f"🟡 Через {days_until} дні"
                elif days_until <= 7:
                    alert = f"🟢 Через {days_until} днів"
                else:
                    alert = f"⚪ Через {days_until} днів"

                st.markdown(f"""
                <div style="background: linear-gradient(90deg, #fff5f7 0%, #ffffff 100%);
                            padding: 15px 20px; border-radius: 12px; margin: 8px 0;
                            border-left: 4px solid #d4758c;">
                    <div style="font-weight: 600; color: #8b4a5e;">
                        {alert} • {html.escape(str(reminder['event_date']))}
                    </div>
                    <div style="color: #5a3e4b; margin-top: 5px;">
                        🎂 <strong>{html.escape(str(reminder['client_name']))}</strong> - {html.escape(str(reminder['event_type']))}
                    </div>
                    <div style="color: #8b4a5e; font-size: 0.9rem; margin-top: 3px;">
                        {html.escape(str(reminder['description'] or ''))}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🌷 Немає найближчих подій")
    else:
        st.info("🎂 Додай нагадування про дні народження клієнтів!")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🌸 Останні замовлення")

    if not df.empty:
        st.dataframe(df[['client_name', 'order_date', 'order_time', 'price', 'status']],
                     use_container_width=True, hide_index=True)
    else:
        st.info("🌷 Цього місяця ще немає замовлень. Час творити красу!")

# --- 📈 ГРАФІКИ ---
elif page == "📊 Графіки та аналітика":
    st.markdown("### 📊 Графіки та аналітика")
    st.markdown("<p style='text-align:center; font-style:italic;'>Візуалізація твоїх успіхів ✨</p>", unsafe_allow_html=True)
    st.markdown("---")

    period = st.selectbox("🗓 Оберіть період", ["Поточний місяць", "Останні 3 місяці", "Весь час"])

    if period == "Поточний місяць":
        current_month = date.today().strftime("%Y-%m")
        df = pd.read_sql_query("SELECT * FROM orders WHERE order_date LIKE ?", conn, params=(current_month + "%",))
    elif period == "Останні 3 місяці":
        three_months_ago = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")
        df = pd.read_sql_query("SELECT * FROM orders WHERE order_date >= ?", conn, params=(three_months_ago,))
    else:
        df = pd.read_sql_query("SELECT * FROM orders", conn)

    if not df.empty:
        st.markdown("#### 💰 Динаміка доходів по днях")
        df['order_date'] = pd.to_datetime(df['order_date'])
        daily_income = df.groupby('order_date')['price'].sum().reset_index()

        fig1 = px.line(daily_income, x='order_date', y='price', title='Доходи по днях',
                       labels={'order_date': 'Дата', 'price': 'Дохід (грн)'})
        fig1.update_traces(line_color='#d4758c', line_width=3)
        fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                           font_family='Inter', title_font_family='Playfair Display')
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("#### 📋 Розподіл замовлень по статусах")
        col1, col2 = st.columns(2)

        with col1:
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['Статус', 'Кількість']
            fig2 = px.pie(status_counts, values='Кількість', names='Статус',
                          color_discrete_sequence=['#d4758c', '#f4d4d8', '#b85c7a', '#e8b4bc', '#9d4a66'])
            fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_family='Inter')
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            st.markdown("#### 🏆 Топ клієнтів за доходами")
            top_clients = df.groupby('client_name')['price'].sum().nlargest(5).reset_index()
            fig3 = px.bar(top_clients, x='price', y='client_name', orientation='h',
                          color='price', color_continuous_scale=['#f4d4d8', '#d4758c'])
            fig3.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                               font_family='Inter', xaxis_title='Дохід (грн)', yaxis_title='')
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("#### 💎 Прибутковість по днях")
        df['profit'] = df['price'] - df['cost']
        daily_profit = df.groupby('order_date')['profit'].sum().reset_index()
        fig4 = px.bar(daily_profit, x='order_date', y='profit', title='Чистий прибуток по днях',
                      labels={'order_date': 'Дата', 'profit': 'Прибуток (грн)'})
        fig4.update_traces(marker_color='#b85c7a')
        fig4.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                           font_family='Inter', title_font_family='Playfair Display')
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("🌷 Немає даних для відображення графіків")

# --- 📅 КАЛЕНДАР (НОВИЙ) ---
elif page == "🌹 Календар замовлень":
    MONTHS_UA = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
                 "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]
    DAYS_UA = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]

    st.markdown("### 📅 Календар замовлень")
    st.markdown("---")

    if "cal_year" not in st.session_state:
        st.session_state.cal_year = date.today().year
        st.session_state.cal_month = date.today().month

    nav1, nav2, nav3 = st.columns([1, 3, 1])
    if nav1.button("◀", use_container_width=True, key="cal_prev"):
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1
    if nav3.button("▶", use_container_width=True, key="cal_next"):
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1

    y = st.session_state.cal_year
    m = st.session_state.cal_month
    nav2.markdown(f"<h3 style='margin:0'>{MONTHS_UA[m-1]} {y}</h3>", unsafe_allow_html=True)

    month_str = f"{y}-{m:02d}"
    orders_df = pd.read_sql_query(
        "SELECT * FROM orders WHERE order_date LIKE ? ORDER BY order_time ASC",
        conn, params=(month_str + "%",))
    all_rem = pd.read_sql_query("SELECT * FROM reminders", conn)

    by_day = {}
    for _, r in orders_df.iterrows():
        d = int(r["order_date"][8:10])
        by_day.setdefault(d, {"orders": [], "events": []})["orders"].append(r)

    for _, r in all_rem.iterrows():
        try:
            ev = datetime.strptime(r["event_date"], "%Y-%m-%d").date()
        except Exception:
            continue
        recurring = r["event_type"] != "Інше"
        if ev.month == m and (recurring or ev.year == y):
            by_day.setdefault(ev.day, {"orders": [], "events": []})["events"].append(r)

    today = date.today()
    th = "".join(f"<th style='padding:6px;color:#8b4a5e;font-size:0.8rem'>{d}</th>" for d in DAYS_UA)
    rows_html = ""
    for week in cal_mod.monthcalendar(y, m):
        rows_html += "<tr>"
        for d in week:
            if d == 0:
                rows_html += "<td style='background:#ffffff40;border-radius:10px'></td>"
                continue
            info = by_day.get(d)
            is_today = (d == today.day and m == today.month and y == today.year)
            bg = "#ffe3ea" if is_today else "#ffffff"
            border = "2px solid #d4758c" if is_today else "1px solid #f4d4d8"
            badges = ""
            if info:
                if info["orders"]:
                    badges += f"<div style='font-size:0.75rem;color:#d4758c;font-weight:600'>💐{len(info['orders'])}</div>"
                if info["events"]:
                    badges += f"<div style='font-size:0.75rem'>🎂{len(info['events'])}</div>"
            rows_html += (
                f"<td style='background:{bg};border:{border};border-radius:10px;"
                f"height:64px;vertical-align:top;padding:4px;text-align:left'>"
                f"<div style='font-weight:600;color:#8b4a5e;font-size:0.85rem'>{d}</div>{badges}</td>"
            )
        rows_html += "</tr>"

    st.markdown(
        f"<table style='width:100%;border-collapse:separate;border-spacing:4px;table-layout:fixed'>"
        f"<tr>{th}</tr>{rows_html}</table>",
        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    busy_days = sorted(by_day.keys())
    if busy_days:
        default_idx = busy_days.index(today.day) if (today.year == y and today.month == m and today.day in busy_days) else 0
        chosen = st.selectbox("🔎 Подивитись день", busy_days, index=default_idx,
                              format_func=lambda d: f"{d} {MONTHS_UA[m-1].lower()}")
        info = by_day[chosen]

        for ev in info["events"]:
            st.markdown(
                f"<div style='background:#fff9e6;padding:12px 16px;border-radius:12px;margin:6px 0;border-left:4px solid #ffc107'>"
                f"🎂 <strong>{html.escape(str(ev['client_name']))}</strong> — {html.escape(str(ev['event_type']))}"
                f"{' • 📱 ' + html.escape(str(ev['phone'])) if ev['phone'] else ''}<br>"
                f"<span style='font-size:0.9rem'>{html.escape(str(ev['description'] or ''))}</span></div>",
                unsafe_allow_html=True)

        status_emoji = {"Нове": "🆕", "В роботі": "🌱", "Готове": "✅", "Видано": "🎁", "Оплачено": "💎"}
        for o in info["orders"]:
            st.markdown(
                f"<div style='background:linear-gradient(90deg,#fff5f7,#fff);padding:12px 16px;border-radius:12px;"
                f"margin:6px 0;border-left:4px solid #d4758c'>"
                f"<strong>{status_emoji.get(o['status'], '🌸')} {html.escape(str(o['order_time']))} • {html.escape(str(o['client_name']))}</strong><br>"
                f"🌷 <em>{html.escape(str(o['description'] or ''))}</em><br>"
                f"<span style='color:#d4758c;font-weight:600'>💰 {o['price']} грн • {html.escape(str(o['status']))}</span></div>",
                unsafe_allow_html=True)
    else:
        st.info("🌷 У цьому місяці поки нічого немає")

# --- ➕ НОВЕ ЗАМОВЛЕННЯ ---
elif page == "💐 Нове замовлення":
    st.markdown("### 💐 Нове замовлення")
    st.markdown("<p style='text-align:center; font-style:italic;'>Створи нову квіткову історію ✨</p>", unsafe_allow_html=True)
    st.markdown("---")

    with st.form("new_order_form"):
        st.markdown("#### 👤 Клієнт")
        c1, c2 = st.columns(2)
        name = c1.text_input("Ім'я клієнта 🌸")
        phone = c2.text_input("Телефон 📱")

        st.markdown("#### 📅 Дата і час")
        c3, c4 = st.columns(2)
        o_date = c3.date_input("Дата 🌷", value=date.today())
        o_time = c4.time_input("Час 🕐")

        st.markdown("#### 🌹 Деталі букета")
        desc = st.text_area("Опис (які квіти, привід, склад, побажання)")

        st.markdown("#### 💰 Фінанси")
        c5, c6 = st.columns(2)
        price = c5.number_input("Ціна для клієнта (грн)", min_value=0.0, step=50.0)
        cost = c6.number_input("Собівартість (грн)", min_value=0.0, step=50.0)

        st.markdown("#### 📝 Додатково")
        status = st.selectbox("Статус", ["Нове", "В роботі", "Готове", "Видано", "Оплачено"])
        notes = st.text_input("Нотатки (день народження, особливі побажання)")

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🌸 Зберегти замовлення", use_container_width=True)

        if submitted and name:
            c = conn.cursor()
            c.execute("INSERT INTO orders (client_name, phone, description, price, cost, order_date, order_time, status, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (name, phone, desc, price, cost, o_date.strftime("%Y-%m-%d"),
                       o_time.strftime("%H:%M"), status, notes))
            conn.commit()
            st.success(f"🌷 Замовлення для {name} успішно додано! ✨")

# --- 🎂 НАГАДУВАННЯ ---
elif page == "🎂 Нагадування":
    st.markdown("### 🎂 Нагадування та важливі дати")
    st.markdown("<p style='text-align:center; font-style:italic;'>Не забудь про важливі події клієнтів 🌸</p>", unsafe_allow_html=True)
    st.markdown("---")

    with st.form("new_reminder_form"):
        st.markdown("#### ➕ Додати нове нагадування")

        c1, c2 = st.columns(2)
        client_name = c1.text_input("Ім'я клієнта 🌸")
        phone = c2.text_input("Телефон 📱")

        c3, c4 = st.columns(2)
        event_type = c3.selectbox("Тип події 🎉", ["День народження", "Річниця", "Ювілей", "Інше"])
        event_date = c4.date_input("Дата події 📅", value=date.today())

        description = st.text_area("Опис (напр. 'Любить півонії', 'Чоловік дарує щороку')")

        submitted = st.form_submit_button("🌸 Зберегти нагадування", use_container_width=True)

        if submitted and client_name:
            c = conn.cursor()
            c.execute("INSERT INTO reminders (client_name, event_type, event_date, description, phone) VALUES (?, ?, ?, ?, ?)",
                      (client_name, event_type, event_date.strftime("%Y-%m-%d"), description, phone))
            conn.commit()
            st.success(f"🎂 Нагадування для {client_name} додано! ✨")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📋 Всі нагадування")

    reminders_df = pd.read_sql_query("SELECT * FROM reminders ORDER BY event_date ASC", conn)

    if not reminders_df.empty:
        today = date.today()

        for _, reminder in reminders_df.iterrows():
            event_date = datetime.strptime(reminder['event_date'], "%Y-%m-%d").date()
            days_until = (event_date - today).days

            if days_until < 0:
                alert = "⚪ Минуло"
                bg_color = "#f5f5f5"
            elif days_until == 0:
                alert = "🔴 СЬОГОДНІ!"
                bg_color = "#ffebee"
            elif days_until <= 3:
                alert = f"🟡 Через {days_until} дні"
                bg_color = "#fff9e6"
            elif days_until <= 7:
                alert = f"🟢 Через {days_until} днів"
                bg_color = "#e8f5e9"
            else:
                alert = f"⚪ Через {days_until} днів"
                bg_color = "#ffffff"

            phone_html = f"• 📱 {html.escape(str(reminder['phone']))}" if reminder['phone'] else ""
            desc_html = html.escape(str(reminder['description'])) if reminder['description'] else "Без опису"

            st.markdown(f"""
            <div style="background: {bg_color};
                        padding: 15px 20px; border-radius: 12px; margin: 8px 0;
                        border-left: 4px solid #d4758c;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 600; color: #8b4a5e; font-size: 1.1rem;">
                        {alert} • {html.escape(str(reminder['event_date']))}
                    </div>
                    <div style="color: #d4758c; font-weight: 600;">
                        🎂 {html.escape(str(reminder['event_type']))}
                    </div>
                </div>
                <div style="color: #5a3e4b; margin-top: 8px; font-size: 1.05rem;">
                    👤 <strong>{html.escape(str(reminder['client_name']))}</strong> {phone_html}
                </div>
                <div style="color: #8b4a5e; font-size: 0.95rem; margin-top: 5px;">
                    {desc_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🎂 Поки що немає нагадувань. Додай перше!")

# --- 🔍 ПОШУК ---
elif page == "🌺 Пошук та клієнти":
    st.markdown("### 🔍 Глобальний пошук")
    st.markdown("<p style='text-align:center; font-style:italic;'>Знайди будь-яку квіткову історію 🌸</p>", unsafe_allow_html=True)
    st.markdown("---")

    search_term = st.text_input("🔎 Введіть ім'я, телефон або опис квітів...")
    if search_term:
        like = f"%{search_term}%"
        df = pd.read_sql_query(
            "SELECT * FROM orders WHERE client_name LIKE ? OR phone LIKE ? OR description LIKE ? OR notes LIKE ?",
            conn, params=(like, like, like, like))
        if not df.empty:
            st.success(f"🌸 Знайдено {len(df)} замовлень")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("🌷 Нічого не знайдено. Спробуй інший запит!")

# --- 📁 АРХІВ ---
elif page == "🌻 Архів місяців":
    st.markdown("### 📁 Архівація місяців")
    st.markdown("<p style='text-align:center; font-style:italic;'>Збережи квіткову історію місяця 🌺</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Останні 12 місяців — підлаштовується під поточну дату
    months = []
    d = date.today().replace(day=1)
    for _ in range(12):
        months.append(d.strftime("%Y-%m"))
        d = (d - timedelta(days=1)).replace(day=1)

    selected_month = st.selectbox("🗓 Оберіть місяць для архівації", months)

    if st.button("🌸 Створити папку та зберегти звіт", use_container_width=True):
        month_name = selected_month.replace("-", "_")
        folder_path = os.path.join(ARCHIVE_DIR, month_name)
        os.makedirs(folder_path, exist_ok=True)

        df = pd.read_sql_query("SELECT * FROM orders WHERE order_date LIKE ?", conn, params=(selected_month + "%",))
        df.to_excel(os.path.join(folder_path, "Замовлення.xlsx"), index=False)

        stats_text = f"🌸 Статистика за {selected_month} 🌸\n\n"
        stats_text += f"💐 Всього замовлень: {len(df)}\n"
        stats_text += f"💰 Загальний дохід: {df['price'].sum():.2f} грн\n"
        stats_text += f"🌱 Витрати: {df['cost'].sum():.2f} грн\n"
        stats_text += f"✨ Чистий прибуток: {df['price'].sum() - df['cost'].sum():.2f} грн\n"

        with open(os.path.join(folder_path, "Статистика.txt"), "w", encoding="utf-8") as f:
            f.write(stats_text)

        st.success(f"🌷 Звіт за {selected_month} збережено! ✨")

        with open(os.path.join(folder_path, "Замовлення.xlsx"), "rb") as f:
            st.download_button("📥 Завантажити Excel", f, file_name=f"Замовлення_{selected_month}.xlsx")

conn.close()

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 20px; color: #8b4a5e; font-style: italic;">
    🌸 Зроблено з любов'ю для найкращої флористки 🌸
</div>
""", unsafe_allow_html=True)
