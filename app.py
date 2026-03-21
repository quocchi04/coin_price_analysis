import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
# ĐOẠN MỒI: Tự động tạo file json từ Secrets của Streamlit
if "GCP_SERVICE_ACCOUNT" in st.secrets:
    secret_data = st.secrets["GCP_SERVICE_ACCOUNT"]
    # Nếu secret là chuỗi (string), ta chuyển nó về dict
    if isinstance(secret_data, str):
        secret_dict = json.loads(secret_data)
    else:
        secret_dict = dict(secret_data)
        
    with open("service_account.json", "w") as f:
        json.dump(secret_dict, f)
# Import các hàm xử lý GCS thay vì file local
from src.untils.drive import get_data
from src.Prediction.coin_prediction import show as run_prediction
from src.alert.crypto_alert import writing_alert, alert as run_alert_check
from src.alert.del_alert import read_json_from_gcs, write_json_to_gcs # Thêm cái này

# Các module phân tích khác của bạn
from src.analysis import coin_trend, coin_ranking, correlation_analysis
from src.analysis import dbscan_clustering, KMean_clustering, pattern_matching, coin_analysis

st.set_page_config(page_title="Crypto Full Analytics", layout="wide")

# --- CSS TÙY CHỈNH ---
st.markdown("""<style> .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; } </style>""", unsafe_allow_html=True)

# --- LOAD DATA THỊ TRƯỜNG ---
if 'df' not in st.session_state:
    with st.spinner("Đang tải dữ liệu từ Cloud..."):
        st.session_state.df = get_data()
df = st.session_state.df

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📊 MENU HỆ THỐNG")
menu = st.sidebar.selectbox("Chọn Module:", [
    "🏠 Trang chủ & Tổng quan",
    "📈 Phân tích chuyên sâu",
    "🎯 Dự báo giá (XGBoost)",
    "🔔 Thiết lập Cảnh báo",
    "⚙️ Hệ thống"
])

# --- 1. TRANG CHỦ & 2. PHÂN TÍCH (Giữ nguyên logic của bạn) ---
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

elif menu == "📈 Phân tích chuyên sâu":
    # ... (Phần Tabs phân tích giữ nguyên như code cũ của bạn) ...
    st.header("🔍 Các mô hình phân tích dữ liệu")
    sub_menu = st.tabs(["Xu hướng", "Xếp hạng", "Tương quan", "Gom cụm DBSCAN", "Gom cụm KMeans", "Mô hình nến", "Phân tích chung"])
    with sub_menu[0]: coin_trend.show(df)
    with sub_menu[1]: coin_ranking.show(df)
    with sub_menu[2]: correlation_analysis.show(df)
    with sub_menu[3]: dbscan_clustering.show(df)
    with sub_menu[4]: KMean_clustering.show(df)
    with sub_menu[5]: pattern_matching.show(df)
    with sub_menu[6]: coin_analysis.show(df)

# --- 3. DỰ BÁO GIÁ (Giữ nguyên) ---
elif menu == "🎯 Dự báo giá (XGBoost)":
    st.header("🎯 Dự báo tương lai (Khung 1h)")
    if df is not None:
        all_available_coins = sorted(df['id'].unique())
        target = st.selectbox("Chọn đồng Coin muốn dự báo:", all_available_coins)
        if st.button("🚀 Kích hoạt AI Dự báo"):
            with st.spinner(f"AI đang phân tích {target}..."):
                p, report = run_prediction(target, df)
                st.success(f"Dự báo hoàn tất cho {target.upper()}!")
                col1, col2 = st.columns(2)
                with col1: st.metric("Giá dự báo (1h tới)", f"${p:,.2f}")
                with col2: st.info("Thông số kỹ thuật:"); st.code(report)

# --- 4. THIẾT LẬP CẢNH BÁO (PHẦN QUAN TRỌNG NHẤT CẦN SỬA) ---
elif menu == "🔔 Thiết lập Cảnh báo":
    st.header("🔔 Quản lý danh sách cảnh báo")
    
    with st.expander("➕ Thêm cảnh báo mới"):
        list_coins = sorted(df['id'].unique()) if df is not None else ["bitcoin", "ethereum"]
        with st.form("new_alert"):
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])
            new_id = c1.selectbox("Chọn đồng Coin:", list_coins)
            
            current_p = df[df['id'] == new_id]['current_price_usd'].iloc[-1] if df is not None else 0.0
            
            breakout_p = c2.number_input(f"Ngưỡng TRÊN (Hiện tại: {current_p:,.0f}):", value=float(current_p * 1.05))
            breakdown_p = c3.number_input(f"Ngưỡng DƯỚI:", value=float(current_p * 0.95))
            new_email = c4.text_input("Email nhận thông báo:")
            
            if st.form_submit_button("Lưu vào hệ thống"):
                if new_email:
                    # Ghi trực tiếp lên Cloud
                    writing_alert(mail=new_email, coin=new_id, breakout=breakout_p, breakdown=breakdown_p)
                    st.success(f"✅ Đã lưu cảnh báo cho {new_id} lên Cloud!")
                    st.rerun()
                else:
                    st.error("Vui lòng nhập Email!")

    st.subheader("Danh sách cảnh báo hiện có (Đồng bộ từ Cloud)")
    try:
        # ĐỌC TỪ CLOUD THAY VÌ FILE LOCAL
        data_json = read_json_from_gcs()
        
        if data_json:
            display_list = []
            for user in data_json:
                # Dùng .get để tránh lỗi nếu cấu trúc json bị lệch
                user_email = user.get('mail', 'N/A')
                for coin_dict in user.get('coins', []):
                    for c_name, v in coin_dict.items():
                        display_list.append({
                            "Email": user_email,
                            "Coin": c_name,
                            "Vượt ngưỡng (Trên)": f"${v.get('breakout', 0):,.2f}",
                            "Thủng ngưỡng (Dưới)": f"${v.get('breakdown', 0):,.2f}"
                        })
            if display_list:
                st.table(pd.DataFrame(display_list))
            else:
                st.info("Chưa có cảnh báo nào trong danh sách.")
        else:
            st.info("Danh sách trống.")
    except Exception as e:
        st.error(f"Lỗi khi đọc dữ liệu từ Cloud: {e}")
    
    st.divider()
    st.subheader("🚀 Kiểm tra & Gửi Mail")
    col_btn1, col_btn2 = st.columns(2)
    
    if col_btn1.button("🔥 Chạy kiểm tra giá ngay lập tức"):
        with st.spinner("Hệ thống đang quét giá trên Cloud..."):
            run_alert_check() 
            st.success("Quá trình quét hoàn tất!")

    if col_btn2.button("🗑️ Xóa toàn bộ danh sách"):
        # Ghi đè danh sách rỗng lên Cloud
        write_json_to_gcs([])
        st.warning("Đã xóa sạch danh sách trên Cloud.")
        st.rerun()

elif menu == "⚙️ Hệ thống":
    st.header("⚙️ Quản trị hệ thống")
    if st.button("🔄 Đồng bộ dữ liệu mới nhất"):
        st.session_state.df = get_data()
        st.success("Đã cập nhật dữ liệu mới nhất từ Drive!")
        st.rerun()