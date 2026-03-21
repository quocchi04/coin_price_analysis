import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px

from src.untils.drive import get_data
from src.Prediction.coin_prediction import show as run_prediction
from src.alert.crypto_alert import writing_alert, alert as run_alert_check

from src.analysis import coin_trend
from src.analysis import coin_ranking
from src.analysis import correlation_analysis
from src.analysis import dbscan_clustering
from src.analysis import KMean_clustering
from src.analysis import pattern_matching
from src.analysis import coin_analysis

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
    "📈 Phân tích chuyên sâu",
    "🎯 Dự báo giá (XGBoost)",
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
elif menu == "📈 Phân tích chuyên sâu":
    st.header("🔍 Các mô hình phân tích dữ liệu")
    sub_menu = st.tabs([
        "Xu hướng", "Xếp hạng", "Tương quan", 
        "Gom cụm DBSCAN", "Gom cụm KMeans", "Mô hình nến", "Phân tích chung"
    ])
    with sub_menu[0]:
        st.subheader("Phân tích xu hướng (Coin Trend)")
        st.info("Phân tích xu hướng giá và volume để xác định các coin có tiềm năng tăng trưởng mạnh.")
        coin_trend.show(df)
    with sub_menu[1]:
        st.subheader("Phân tích xếp hạng (Coin Ranking)")
        st.info("Phân tích và xếp hạng các coin dựa trên nhiều yếu tố như tăng trưởng giá, volume, vốn hóa...")
        coin_ranking.show(df)
    with sub_menu[2]:
        st.subheader("Phân tích tương quan (Correlation Analysis)")
        st.info("Phân tích mối quan hệ giữa các coin để tìm ra những cặp coin có xu hướng di chuyển cùng nhau.")
        correlation_analysis.show(df)
    with sub_menu[3]:
        st.subheader("Gom cụm DBSCAN")
        st.write("Phân tích các nhóm coin có đặc tính giống nhau bằng thuật toán DBSCAN.")
        dbscan_clustering.show(df)
    with sub_menu[4]:
        st.subheader("Gom cụm KMeans")
        st.write("Phân tích các nhóm coin có đặc tính giống nhau bằng thuật toán KMeans.")
        KMean_clustering.show(df)
    with sub_menu[5]:
        st.subheader("Nhận dạng hình thái (Pattern Matching)")
        st.write("Phân tích các mẫu nến phổ biến để dự đoán xu hướng giá.")
        pattern_matching.show(df)
    with sub_menu[6]:
        st.subheader("Phân tích chung")
        st.write("Phân tích tổng hợp các yếu tố để đưa ra cái nhìn toàn diện về thị trường.")
        coin_analysis.show(df)
# --- 3. DỰ BÁO GIÁ ---
elif menu == "🎯 Dự báo giá (XGBoost)":
    st.header("🎯 Dự báo tương lai (Khung 1h)")
    
    # 🛑 BƯỚC QUAN TRỌNG: Lấy danh sách coin từ dữ liệu thật
    if df is not None:
        # Lấy tất cả các 'id' duy nhất và sắp xếp theo thứ tự ABC
        all_available_coins = sorted(df['id'].unique())
        
        # Tạo Selectbox hiển thị danh sách coin thật
        target = st.selectbox("Chọn đồng Coin muốn dự báo:", all_available_coins)
        
        # Tạo nút bấm để user kích hoạt mô hình
        if st.button("🚀 Kích hoạt AI Dự báo"):
            # Thêm hiệu ứng loading spinner để user không bị chán khi đợi
            with st.spinner(f"AI đang phân tích dữ liệu {target} bằng XGBoost..."):
                # Gọi hàm dự báo từ file coin_prediction.py
                p, report = run_prediction(target, df)
                
                # Hiển thị thông báo thành công màu xanh lá
                st.success(f"Dự báo hoàn tất cho {target.upper()}!")
                
                # Tạo 2 cột để hiển thị kết quả đẹp mắt hơn
                col1, col2 = st.columns(2)
                with col1:
                    # Hiển thị giá dự báo bằng số lớn
                    st.metric("Giá dự báo (1h tới)", f"${p:,.2f}")
                with col2:
                    st.info("Thông số kỹ thuật mô hình:")
                    st.code(report) # Giữ lại phần report chi tiết bằng st.code
    else:
        # Trường hợp user chưa load được dữ liệu
        st.error("Chưa có dữ liệu. Vui lòng kiểm tra lại Google Drive hoặc file config.")

elif menu == "🔔 Thiết lập Cảnh báo":
    st.header("🔔 Quản lý danh sách cảnh báo")
    
    # 1. GIAO DIỆN THÊM MỚI
    with st.expander("➕ Thêm cảnh báo mới"):
        # Lấy danh sách ID coin từ dữ liệu thật
        list_coins = sorted(df['id'].unique()) if df is not None else ["bitcoin", "ethereum"]
        
        with st.form("new_alert"):
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])
            
            new_id = c1.selectbox("Chọn đồng Coin:", list_coins)
            
            # Lấy giá hiện tại để gợi ý cho người dùng
            current_p = 0.0
            if df is not None:
                current_p = df[df['id'] == new_id]['current_price_usd'].iloc[0]
            
            # Cho phép nhập 2 ngưỡng: Breakout (Vượt trên) và Breakdown (Thủng dưới)
            breakout_p = c2.number_input(f"Ngưỡng TRÊN (Hiện tại: {current_p:,.0f}):", value=float(current_p * 1.05))
            breakdown_p = c3.number_input(f"Ngưỡng DƯỚI:", value=float(current_p * 0.95))
            new_email = c4.text_input("Email nhận thông báo:")
            
            if st.form_submit_button("Lưu vào hệ thống"):
                if new_email:
                    # GỌI HÀM TỪ FILE CRYPTO_ALERT.PY
                    writing_alert(mail=new_email, coin=new_id, breakout=breakout_p, breakdown=breakdown_p)
                    st.success(f"✅ Đã lưu cảnh báo cho {new_id}!")
                    st.rerun()
                else:
                    st.error("Vui lòng nhập Email!")

    # 2. HIỂN THỊ DANH SÁCH (Đọc từ file JSON để hiện bảng)
    st.subheader("Danh sách cảnh báo hiện có")
    ALERT_FILE = "alert_list.json"
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, 'r', encoding='utf-8') as f:
            data_json = json.load(f)
        
        if data_json:
            # Chuyển đổi cấu trúc JSON phức tạp sang DataFrame để hiển thị đẹp
            display_list = []
            for user in data_json:
                for coin_dict in user['coins']:
                    for c_name, v in coin_dict.items():
                        display_list.append({
                            "Email": user['mail'],
                            "Coin": c_name,
                            "Vượt ngưỡng (Trên)": f"${v['breakout']:,.2f}",
                            "Thủng ngưỡng (Dưới)": f"${v['breakdown']:,.2f}"
                        })
            st.table(pd.DataFrame(display_list))
        else:
            st.write("Chưa có cảnh báo nào.")
    
    # 3. NÚT KÍCH HOẠT GỬI MAIL (TEST)
    st.divider()
    st.subheader("🚀 Kiểm tra & Gửi Mail")
    col_btn1, col_btn2 = st.columns(2)
    
    if col_btn1.button("🔥 Chạy kiểm tra giá ngay lập tức"):
        with st.spinner("Hệ thống đang quét giá và đối chiếu..."):
            # GỌI HÀM alert() TRONG FILE CRYPTO_ALERT.PY
            run_alert_check() 
            st.success("Quá trình quét hoàn tất! Kiểm tra Terminal để xem log gửi mail.")
            st.info("Nếu giá chạm ngưỡng, mail sẽ được gửi đến hòm thư của bạn.")

    if col_btn2.button("🗑️ Xóa toàn bộ danh sách"):
        if os.path.exists(ALERT_FILE):
            with open(ALERT_FILE, 'w') as f:
                json.dump([], f)
            st.rerun()
# --- 5. HỆ THỐNG ---
elif menu == "⚙️ Hệ thống":
    st.header("⚙️ Quản trị hệ thống")
    if st.button("🔄 Đồng bộ Google Drive ngay bây giờ"):
        from src.untils.upload_to_drive import upload_to_drive
        upload_to_drive()
        st.success("Đồng bộ hoàn tất!")