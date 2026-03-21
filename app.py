import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px

# Import các module của bạn
from src.untils.drive import get_data
from src.Prediction.coin_prediction import show as run_prediction
# (Giả sử các file analysis của bạn có hàm main hoặc show tương tự)
# from src.analysis.coin_analysis import show_analysis 

st.set_page_config(page_title="Crypto Full Analytics", layout="wide")

# --- CSS TÙY CHỈNH ---
st.markdown("""<style> .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; } </style>""", unsafe_allow_html=True)

# --- LOAD DATA ---
if 'df' not in st.session_state:
    st.session_state.df = get_data()
df = st.session_state.df

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📊 MENU HỆ THỐNG")
menu = st.sidebar.selectbox("Chọn Module:", [
    "🏠 Trang chủ & Tổng quan",
    "📈 Phân tích chuyên sâu (7 Modules)",
    "🤖 Dự báo giá (XGBoost)",
    "🔔 Thiết lập Cảnh báo",
    "⚙️ Hệ thống"
])

# --- 1. TRANG CHỦ ---
if menu == "🏠 Trang chủ & Tổng quan":
    st.header("💎 Theo dõi thị trường")
    if df is not None:
        coins = df['id'].unique()
        selected = st.selectbox("Chọn Coin:", coins)
        c_df = df[df['id'] == selected].sort_values('time_collected')
        
        col1, col2 = st.columns([3, 1])
        with col1:
            fig = px.area(c_df, x='time_collected', y='current_price_usd', title=f"Biến động giá {selected}")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.metric("Giá hiện tại", f"${c_df['current_price_usd'].iloc[-1]:,.2f}")
            st.metric("Vốn hóa", f"${c_df['market_cap'].iloc[-1]:,.0f}")
            st.write("Dữ liệu mới nhất lúc:", c_df['time_collected'].iloc[-1])

# --- 2. 7 MODULES PHÂN TÍCH (Analysis) ---
elif menu == "📈 Phân tích chuyên sâu (7 Modules)":
    st.header("🔍 Các mô hình phân tích dữ liệu")
    sub_menu = st.tabs([
        "Xu hướng (Trend)", "Xếp hạng", "Tương quan", 
        "Gom cụm DBSCAN", "Gom cụm KMeans", "Mô hình nến", "Phân tích chung"
    ])
    
    with sub_menu[0]:
        st.subheader("Phân tích xu hướng (Coin Trend)")
        st.info("Module này đang sử dụng file: `src/analysis/coin_trend.py`")
        # Gọi hàm từ file tương ứng: coin_trend.show(df)
        
    with sub_menu[3]:
        st.subheader("Gom cụm DBSCAN")
        st.write("Phân tích các nhóm coin có đặc tính giống nhau bằng thuật toán DBSCAN.")
        # Gọi hàm từ file: dbscan_clustering.py

# --- 3. DỰ BÁO GIÁ ---
elif menu == "🤖 Dự báo giá (XGBoost)":
    st.header("🤖 Dự báo tương lai (1h)")
    target = st.selectbox("Chọn Coin:", ["bitcoin", "ethereum", "solana"])
    if st.button("Chạy mô hình XGBoost"):
        p, report = run_prediction(target, df)
        st.code(report)

# --- 4. THIẾT LẬP CẢNH BÁO (Sửa lỗi không hoạt động) ---
elif menu == "🔔 Thiết lập Cảnh báo":
    st.header("🔔 Quản lý danh sách cảnh báo")
    ALERT_FILE = "alert_list.json"
    
    # Đọc file hiện tại
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, 'r') as f:
            alerts = json.load(f)
    else:
        alerts = []

    # Giao diện thêm mới
    with st.expander("➕ Thêm cảnh báo mới"):
        with st.form("new_alert"):
            c1, c2, c3 = st.columns(3)
            new_id = c1.text_input("ID Coin (vd: bitcoin):")
            new_price = c2.number_input("Giá mục tiêu:", value=60000.0)
            new_email = c3.text_input("Email nhận:")
            if st.form_submit_button("Lưu vào hệ thống"):
                alerts.append({"id": new_id, "price_threshold": new_price, "email": new_email})
                with open(ALERT_FILE, 'w') as f:
                    json.dump(alerts, f, indent=4)
                st.success("Đã cập nhật file alert_list.json!")
                st.rerun()

    # Hiển thị danh sách đang chạy
    st.subheader("Danh sách cảnh báo hiện có")
    if alerts:
        alert_df = pd.DataFrame(alerts)
        st.table(alert_df)
        if st.button("🗑️ Xóa tất cả cảnh báo"):
            if os.path.exists(ALERT_FILE): os.remove(ALERT_FILE)
            st.rerun()
    else:
        st.write("Chưa có cảnh báo nào được thiết lập.")

# --- 5. HỆ THỐNG ---
elif menu == "⚙️ Hệ thống":
    st.header("⚙️ Quản trị hệ thống")
    if st.button("🔄 Đồng bộ Google Drive ngay bây giờ"):
        from src.untils.upload_to_drive import upload_to_drive
        upload_to_drive()
        st.success("Đồng bộ hoàn tất!")