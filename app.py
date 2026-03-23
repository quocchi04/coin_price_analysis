import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px

# --- ĐOẠN MỒI THÔNG MINH ---
# 1. Nếu chưa có file service_account.json (thường là trên Cloud)
if not os.path.exists("service_account.json"):
    # 2. Thử tìm trong Secrets (Chỉ có trên Streamlit Cloud mới có cái này)
    try:
        if "GCP_SERVICE_ACCOUNT" in st.secrets:
            st.info("🔄 Đang khởi tạo cấu hình từ Cloud...")
            secret_data = st.secrets["GCP_SERVICE_ACCOUNT"]
            
            # Chuyển đổi dữ liệu từ Secrets sang Dictionary
            if isinstance(secret_data, str):
                secret_dict = json.loads(secret_data)
            else:
                secret_dict = dict(secret_data)
                
            # Tạo file json tạm thời để các module khác sử dụng
            with open("service_account.json", "w") as f:
                json.dump(secret_dict, f)
    except Exception as e:
        pass

from src.untils.drive import get_data
from src.Prediction.coin_prediction import show as run_prediction
from src.alert.crypto_alert import writing_alert, alert as run_alert_check
from src.alert.del_alert import read_json_from_gcs, write_json_to_gcs 

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
    "🎯 Dự báo giá",
    "🔔 Thiết lập Cảnh báo",
    "⚙️ Hệ thống"
])

# --- 1. TRANG CHỦ & 2. PHÂN TÍCH ---
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
    st.header("🔍 Các mô hình phân tích dữ liệu")
    sub_menu = st.tabs(["Xu hướng", "Xếp hạng", "Tương quan", "Gom cụm DBSCAN", "Gom cụm KMeans", "Mô hình nến", "Phân tích chung"])
    with sub_menu[0]: coin_trend.show(df)
    with sub_menu[1]: coin_ranking.show(df)
    with sub_menu[2]: correlation_analysis.show(df)
    with sub_menu[3]: dbscan_clustering.show(df)
    with sub_menu[4]: KMean_clustering.show(df)
    with sub_menu[5]: pattern_matching.show(df)
    with sub_menu[6]: coin_analysis.show(df)

# --- 3. DỰ BÁO GIÁ ---
elif menu == "🎯 Dự báo giá":
    st.header("🎯 Dự báo thị trường bằng Trí tuệ nhân tạo")
    
    # Tạo các Tab lựa chọn
    tab_prediction, tab_market_trend = st.tabs(["🎯 Dự báo cụ thể (Coin)", "📊 Xu hướng tổng quát (Market)"])
    
    # --- TAB 1: DỰ BÁO TỪNG ĐỒNG COIN (XGBoost) ---
    with tab_prediction:
        st.subheader("1️⃣ Dự báo giá ngắn hạn (Khung 1h)")
        st.info("Sử dụng mô hình XGBoost để dự báo mức giá cụ thể của từng đồng coin trong thời gian 1 giờ.")
        
        if df is not None:
            all_available_coins = sorted(df['id'].unique())
            target = st.selectbox("Chọn đồng Coin muốn dự báo:", all_available_coins, key="predict_box")
            
            if st.button("🚀 Kích hoạt AI Dự báo"):
                with st.spinner(f"Đang phân tích dữ liệu của {target}..."):
                    p, report = run_prediction(target, df)
                    st.success(f"Dự báo hoàn tất cho {target.upper()}!")
                    
                    c1, c2 = st.columns(2)
                    with c1: 
                        st.metric("Giá dự báo (1h tới)", f"${p:,.2f}")
                    with c2: 
                        with st.expander("Xem thông số kỹ thuật (Report)"):
                            st.code(report)

    # --- TAB 2: XU HƯỚNG THỊ TRƯỜNG CHUNG (Random Forest) ---
    with tab_market_trend:
        st.subheader("2️⃣ Phân tích xu hướng toàn thị trường")
        st.write("Mô hình Random Forest phân tích hơn 400 đồng coin để đưa ra tín hiệu chung.")
        
        json_path = "Data/ml_results.json" 
        
        if not os.path.exists(json_path):
            st.warning("⚠️ Chưa tìm thấy dữ liệu mô hình. Vui lòng chạy file 'price_trend_prediction.py' để huấn luyện.")
        else:
            with open(json_path, "r", encoding="utf-8") as f:
                ml_data = json.load(f)
            
            # Hiển thị Tín hiệu (Sentiment)
            sentiment = ml_data.get("market_sentiment", "N/A")
            ratio = ml_data.get("up_ratio", 0) * 100
            
            if sentiment == "TĂNG":
                st.success(f"🚀 **TÍN HIỆU: BULLISH ({sentiment})**")
                st.write(f"Dự báo có **{ratio:.1f}%** số lượng coin sẽ tăng giá.")
            else:
                st.error(f"📉 **TÍN HIỆU: BEARISH ({sentiment})**")
                st.write(f"Dự báo có **{100-ratio:.1f}%** số lượng coin sẽ có xu hướng giảm.")

            st.divider()

            # Hiển thị các chỉ số kỹ thuật của mô hình
            col_acc, col_empty = st.columns([1, 2])
            with col_acc:
                st.metric(label="Độ chính xác (Accuracy)", value=f"{ml_data['accuracy']:.2%}")

            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                df_imp = pd.DataFrame({
                    "Chỉ số": ml_data["features"],
                    "Độ quan trọng": ml_data["importances"]
                }).sort_values(by="Độ quan trọng", ascending=True)
                
                fig_imp = px.bar(df_imp, x="Độ quan trọng", y="Chỉ số", orientation='h',
                                 title="Tầm quan trọng của các chỉ số",
                                 color="Độ quan trọng", color_continuous_scale="Viridis")
                fig_imp.update_layout(height=350)
                st.plotly_chart(fig_imp, use_container_width=True)

            with col_chart2:
                x_labels = ['Đoán Giảm', 'Đoán Tăng']
                y_labels = ['Thực tế Giảm', 'Thực tế Tăng']
                fig_heat = px.imshow(ml_data["confusion_matrix"], x=x_labels, y=y_labels, 
                                     text_auto=True, color_continuous_scale='YlGnBu',
                                     title="Ma trận nhầm lẫn (Confusion Matrix)")
                fig_heat.update_layout(height=350)
                st.plotly_chart(fig_heat, use_container_width=True)
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