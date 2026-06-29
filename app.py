import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px

# Streamlit yêu cầu set_page_config nằm trước mọi lệnh hiển thị UI.
st.set_page_config(page_title="Crypto Full Analytics", layout="wide")

# --- ĐOẠN MỒI THÔNG MINH: TẠO service_account.json TỪ STREAMLIT SECRETS ---
def bootstrap_service_account():
    """Tạo file service_account.json tạm thời trên Streamlit Cloud nếu chưa có."""
    if os.path.exists("service_account.json"):
        return

    try:
        if "GCP_SERVICE_ACCOUNT" not in st.secrets:
            return

        secret_data = st.secrets["GCP_SERVICE_ACCOUNT"]
        if isinstance(secret_data, str):
            secret_dict = json.loads(secret_data)
        else:
            secret_dict = dict(secret_data)

        with open("service_account.json", "w", encoding="utf-8") as f:
            json.dump(secret_dict, f)
    except Exception as e:
        # Không cho app chết ngay ở bước khởi tạo; lỗi thật sẽ được hiện ở lúc tải dữ liệu.
        st.sidebar.warning(f"Không khởi tạo được service_account.json: {e}")


bootstrap_service_account()

from src.untils.drive import get_data
from src.Prediction.coin_prediction import show as run_prediction
from src.alert.crypto_alert import alert as run_alert_check
from src.alert.del_alert import read_json_from_gcs, write_json_to_gcs
from src.analysis import coin_trend, coin_ranking, correlation_analysis
from src.analysis import dbscan_clustering, KMean_clustering, pattern_matching, coin_analysis

# --- CSS TÙY CHỈNH ---
st.markdown(
    """
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

REQUIRED_COLUMNS = ["id", "time_collected", "current_price_usd"]
NUMERIC_COLUMNS = [
    "current_price_usd",
    "market_cap",
    "price_change_24h",
    "total_volume",
    "circulating_supply",
    "total_supply",
]


def clean_market_df(raw_df):
    """Làm sạch DataFrame tải từ Drive để tránh lỗi lọc df[df['id'] == selected]."""
    if raw_df is None:
        return pd.DataFrame()

    try:
        df = pd.DataFrame(raw_df).copy()
    except Exception:
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    # Chuẩn hóa tên cột và loại cột trùng tên.
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.duplicated()].copy()

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"File dữ liệu thiếu cột bắt buộc: {missing}")
        st.write("Các cột hiện có:", list(df.columns))
        return pd.DataFrame()

    # Ép toàn bộ cột về object/NumPy thường để tránh lỗi Arrow/ExtensionArray khi filter trên Cloud.
    clean_dict = {}
    for col in df.columns:
        clean_dict[col] = df[col].to_numpy(copy=True)
    df = pd.DataFrame(clean_dict)

    df["id"] = df["id"].astype(str).str.strip().str.lower()
    df["time_collected"] = pd.to_datetime(df["time_collected"], errors="coerce")

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["id", "time_collected"])
    df = df[df["id"].ne("") & df["id"].str.lower().ne("nan")]
    df = df.sort_values(["id", "time_collected"], kind="mergesort").reset_index(drop=True)

    return df


def load_market_data():
    """Tải dữ liệu từ Drive và trả về DataFrame đã làm sạch."""
    try:
        raw_df = get_data()
        return clean_market_df(raw_df)
    except Exception as e:
        st.error(f"Không tải được dữ liệu từ Drive: {e}")
        return pd.DataFrame()


def get_coin_options(df):
    if df is None or df.empty or "id" not in df.columns:
        return []
    return sorted(df["id"].dropna().astype(str).unique().tolist())


def get_coin_frame(df, coin_id):
    if df is None or df.empty or not coin_id:
        return pd.DataFrame()
    return (
        df.loc[df["id"].astype(str).str.lower().eq(str(coin_id).lower())]
        .copy()
        .sort_values("time_collected", kind="mergesort")
        .reset_index(drop=True)
    )


def money(value, decimals=2):
    if pd.isna(value):
        return "N/A"
    try:
        return f"${float(value):,.{decimals}f}"
    except Exception:
        return "N/A"


def safe_module_show(module_name, show_func, df):
    """Không để một module phân tích lỗi làm sập toàn bộ app."""
    if df is None or df.empty:
        st.warning("Chưa có dữ liệu để phân tích.")
        return
    try:
        show_func(df.copy())
    except Exception as e:
        st.error(f"Module '{module_name}' đang gặp lỗi: {e}")
        with st.expander("Xem lỗi kỹ thuật"):
            st.code(str(e))


def save_alert_config(mail, coin, breakout, breakdown):
    """Lưu cảnh báo trực tiếp, không gọi lại get_data() để tránh crash khi chỉ cần ghi ngưỡng."""
    try:
        data = read_json_from_gcs()
    except Exception:
        data = []

    if not isinstance(data, list):
        data = []

    new_coin_config = {coin: {"breakout": float(breakout), "breakdown": float(breakdown)}}

    found_user = False
    for user in data:
        if user.get("mail") == mail:
            found_user = True
            coins = user.setdefault("coins", [])
            found_coin = False
            for item in coins:
                if coin in item:
                    item[coin] = new_coin_config[coin]
                    found_coin = True
                    break
            if not found_coin:
                coins.append(new_coin_config)
            break

    if not found_user:
        data.append({"mail": mail, "coins": [new_coin_config]})

    write_json_to_gcs(data)


# --- LOAD DATA THỊ TRƯỜNG ---
if "df" not in st.session_state:
    with st.spinner("Đang tải dữ liệu từ Cloud..."):
        st.session_state.df = load_market_data()
else:
    # Làm sạch lại để tránh session giữ DataFrame cũ/lỗi sau khi deploy code mới.
    st.session_state.df = clean_market_df(st.session_state.df)

df = st.session_state.df
coins = get_coin_options(df)
data_ready = df is not None and not df.empty and len(coins) > 0

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📊 MENU HỆ THỐNG")

if data_ready:
    latest_time = df["time_collected"].max()
    st.sidebar.success(f"Đã tải {len(df):,} dòng dữ liệu")
    st.sidebar.caption(f"Snapshot mới nhất: {latest_time}")
else:
    st.sidebar.error("Chưa tải được dữ liệu hợp lệ")

menu = st.sidebar.selectbox(
    "Chọn Module:",
    [
        "🏠 Trang chủ & Tổng quan",
        "📈 Phân tích chuyên sâu",
        "🎯 Dự báo giá",
        "🔔 Thiết lập Cảnh báo",
        "⚙️ Hệ thống",
    ],
)

# --- 1. TRANG CHỦ & TỔNG QUAN ---
if menu == "🏠 Trang chủ & Tổng quan":
    st.header("💎 Theo dõi thị trường")

    if not data_ready:
        st.error("Không có dữ liệu hợp lệ để hiển thị. Hãy kiểm tra file CSV trên Drive hoặc bấm Đồng bộ dữ liệu mới nhất ở mục Hệ thống.")
        st.stop()

    selected = st.selectbox("Chọn Coin:", coins, index=coins.index("bitcoin") if "bitcoin" in coins else 0)
    c_df = get_coin_frame(df, selected)

    if c_df.empty:
        st.warning(f"Không tìm thấy dữ liệu cho coin: {selected}")
        st.stop()

    col1, col2 = st.columns([3, 1])
    with col1:
        fig = px.area(
            c_df,
            x="time_collected",
            y="current_price_usd",
            title=f"Biến động giá {selected}",
        )
        fig.update_layout(xaxis_title="Thời gian", yaxis_title="Giá USD")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        latest_row = c_df.iloc[-1]
        st.metric("Giá hiện tại", money(latest_row.get("current_price_usd"), 2))
        st.metric("Vốn hóa", money(latest_row.get("market_cap"), 0))
        if "price_change_24h" in c_df.columns:
            change_24h = latest_row.get("price_change_24h")
            st.metric("Biến động 24h", "N/A" if pd.isna(change_24h) else f"{float(change_24h):+.2f}%")
        st.write("Dữ liệu mới nhất lúc:", latest_row.get("time_collected"))

# --- 2. PHÂN TÍCH CHUYÊN SÂU ---
elif menu == "📈 Phân tích chuyên sâu":
    st.header("🔍 Các mô hình phân tích dữ liệu")

    if not data_ready:
        st.warning("Chưa có dữ liệu để chạy các mô hình phân tích.")
        st.stop()

    sub_menu = st.tabs([
        "Xu hướng",
        "Xếp hạng",
        "Tương quan",
        "Gom cụm DBSCAN",
        "Gom cụm KMeans",
        "Mô hình nến",
        "Phân tích chung",
    ])
    with sub_menu[0]:
        safe_module_show("Xu hướng", coin_trend.show, df)
    with sub_menu[1]:
        safe_module_show("Xếp hạng", coin_ranking.show, df)
    with sub_menu[2]:
        safe_module_show("Tương quan", correlation_analysis.show, df)
    with sub_menu[3]:
        safe_module_show("DBSCAN", dbscan_clustering.show, df)
    with sub_menu[4]:
        safe_module_show("KMeans", KMean_clustering.show, df)
    with sub_menu[5]:
        safe_module_show("Mô hình nến", pattern_matching.show, df)
    with sub_menu[6]:
        safe_module_show("Phân tích chung", coin_analysis.show, df)

# --- 3. DỰ BÁO GIÁ ---
elif menu == "🎯 Dự báo giá":
    st.header("🎯 Dự báo thị trường bằng Trí tuệ nhân tạo")

    if not data_ready:
        st.warning("Chưa có dữ liệu để dự báo.")
        st.stop()

    tab_prediction, tab_market_trend = st.tabs(["🎯 Dự báo cụ thể (Coin)", "📊 Xu hướng tổng quát (Market)"])

    with tab_prediction:
        st.subheader("1️⃣ Dự báo giá ngắn hạn (Khung 1h)")
        st.info("Sử dụng mô hình XGBoost để dự báo mức giá cụ thể của từng đồng coin trong thời gian 1 giờ.")

        target = st.selectbox("Chọn đồng Coin muốn dự báo:", coins, key="predict_box")

        if st.button("🚀 Kích hoạt AI Dự báo"):
            with st.spinner(f"Đang phân tích dữ liệu của {target}..."):
                try:
                    p, report = run_prediction(target, df.copy())
                    if p is None:
                        st.warning(report)
                    else:
                        st.success(f"Dự báo hoàn tất cho {target.upper()}!")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.metric("Giá dự báo (1h tới)", money(p, 2))
                        with c2:
                            with st.expander("Xem thông số kỹ thuật (Report)"):
                                st.code(report)
                except Exception as e:
                    st.error(f"Không chạy được mô hình dự báo: {e}")

    with tab_market_trend:
        st.subheader("2️⃣ Phân tích xu hướng toàn thị trường")
        st.write("Mô hình Random Forest phân tích hơn 400 đồng coin để đưa ra tín hiệu chung.")

        json_path = os.path.join("Data", "ml_results.json")

        if not os.path.exists(json_path):
            st.warning("⚠️ Chưa tìm thấy dữ liệu mô hình. Vui lòng chạy file 'price_trend_prediction.py' để huấn luyện.")
        else:
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    ml_data = json.load(f)

                sentiment = ml_data.get("market_sentiment", "N/A")
                ratio = float(ml_data.get("up_ratio", 0)) * 100

                if sentiment == "TĂNG":
                    st.success(f"🚀 **TÍN HIỆU: BULLISH ({sentiment})**")
                    st.write(f"Dự báo có **{ratio:.1f}%** số lượng coin sẽ tăng giá.")
                else:
                    st.error(f"📉 **TÍN HIỆU: BEARISH ({sentiment})**")
                    st.write(f"Dự báo có **{100 - ratio:.1f}%** số lượng coin sẽ có xu hướng giảm.")

                st.divider()
                col_acc, _ = st.columns([1, 2])
                with col_acc:
                    st.metric(label="Độ chính xác (Accuracy)", value=f"{float(ml_data.get('accuracy', 0)):.2%}")

                col_chart1, col_chart2 = st.columns(2)

                with col_chart1:
                    df_imp = pd.DataFrame({
                        "Chỉ số": ml_data.get("features", []),
                        "Độ quan trọng": ml_data.get("importances", []),
                    }).sort_values(by="Độ quan trọng", ascending=True)
                    if not df_imp.empty:
                        fig_imp = px.bar(
                            df_imp,
                            x="Độ quan trọng",
                            y="Chỉ số",
                            orientation="h",
                            title="Tầm quan trọng của các chỉ số",
                            color="Độ quan trọng",
                            color_continuous_scale="Viridis",
                        )
                        fig_imp.update_layout(height=350)
                        st.plotly_chart(fig_imp, use_container_width=True)

                with col_chart2:
                    matrix = ml_data.get("confusion_matrix", [[0, 0], [0, 0]])
                    x_labels = ["Đoán Giảm", "Đoán Tăng"]
                    y_labels = ["Thực tế Giảm", "Thực tế Tăng"]
                    fig_heat = px.imshow(
                        matrix,
                        x=x_labels,
                        y=y_labels,
                        text_auto=True,
                        color_continuous_scale="YlGnBu",
                        title="Ma trận nhầm lẫn (Confusion Matrix)",
                    )
                    fig_heat.update_layout(height=350)
                    st.plotly_chart(fig_heat, use_container_width=True)
            except Exception as e:
                st.error(f"Không đọc được Data/ml_results.json: {e}")

# --- 4. THIẾT LẬP CẢNH BÁO ---
elif menu == "🔔 Thiết lập Cảnh báo":
    st.header("🔔 Quản lý danh sách cảnh báo")

    with st.expander("➕ Thêm cảnh báo mới"):
        list_coins = coins if data_ready else ["bitcoin", "ethereum"]
        with st.form("new_alert"):
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])
            new_id = c1.selectbox("Chọn đồng Coin:", list_coins)

            coin_df = get_coin_frame(df, new_id)
            if not coin_df.empty and "current_price_usd" in coin_df.columns:
                current_p = coin_df["current_price_usd"].dropna().iloc[-1] if not coin_df["current_price_usd"].dropna().empty else 0.0
            else:
                current_p = 0.0

            breakout_p = c2.number_input(
                f"Ngưỡng TRÊN (Hiện tại: {current_p:,.0f}):",
                value=float(current_p * 1.05) if current_p else 0.0,
            )
            breakdown_p = c3.number_input(
                "Ngưỡng DƯỚI:",
                value=float(current_p * 0.95) if current_p else 0.0,
            )
            new_email = c4.text_input("Email nhận thông báo:")

            if st.form_submit_button("Lưu vào hệ thống"):
                if not new_email:
                    st.error("Vui lòng nhập Email!")
                elif breakout_p <= breakdown_p:
                    st.error("Ngưỡng TRÊN phải lớn hơn ngưỡng DƯỚI.")
                else:
                    try:
                        save_alert_config(mail=new_email.strip(), coin=new_id, breakout=breakout_p, breakdown=breakdown_p)
                        st.success(f"✅ Đã lưu cảnh báo cho {new_id}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Không lưu được cảnh báo: {e}")

    st.subheader("Danh sách cảnh báo hiện có")
    try:
        data_json = read_json_from_gcs()

        if data_json:
            display_list = []
            for user in data_json:
                user_email = user.get("mail", "N/A")
                for coin_dict in user.get("coins", []):
                    for c_name, v in coin_dict.items():
                        display_list.append({
                            "Email": user_email,
                            "Coin": c_name,
                            "Vượt ngưỡng (Trên)": money(v.get("breakout", 0), 2),
                            "Thủng ngưỡng (Dưới)": money(v.get("breakdown", 0), 2),
                        })
            if display_list:
                st.table(pd.DataFrame(display_list))
            else:
                st.info("Chưa có cảnh báo nào trong danh sách.")
        else:
            st.info("Danh sách trống.")
    except Exception as e:
        st.error(f"Lỗi khi đọc dữ liệu cảnh báo: {e}")

    st.divider()
    st.subheader("🚀 Kiểm tra & Gửi Mail")
    col_btn1, col_btn2 = st.columns(2)

    if col_btn1.button("🔥 Chạy kiểm tra giá ngay lập tức"):
        with st.spinner("Hệ thống đang quét giá trên Cloud..."):
            try:
                run_alert_check()
                st.success("Quá trình quét hoàn tất!")
            except Exception as e:
                st.error(f"Không chạy được kiểm tra cảnh báo: {e}")

    if col_btn2.button("🗑️ Xóa toàn bộ danh sách"):
        try:
            write_json_to_gcs([])
            st.warning("Đã xóa sạch danh sách cảnh báo.")
            st.rerun()
        except Exception as e:
            st.error(f"Không xóa được danh sách cảnh báo: {e}")

# --- 5. HỆ THỐNG ---
elif menu == "⚙️ Hệ thống":
    st.header("⚙️ Quản trị hệ thống")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Đồng bộ dữ liệu mới nhất"):
            with st.spinner("Đang tải lại dữ liệu từ Drive..."):
                st.session_state.df = load_market_data()
            st.success("Đã cập nhật dữ liệu mới nhất từ Drive!")
            st.rerun()

    with c2:
        if st.button("🧹 Xóa cache dữ liệu trong phiên"):
            st.session_state.pop("df", None)
            st.success("Đã xóa cache trong phiên. App sẽ tải lại dữ liệu.")
            st.rerun()

    st.divider()
    st.subheader("Tình trạng dữ liệu")
    if data_ready:
        st.write("Số dòng:", len(df))
        st.write("Số coin:", len(coins))
        st.write("Thời gian mới nhất:", df["time_collected"].max())
        st.write("Các cột:", list(df.columns))
        st.dataframe(df.tail(20), use_container_width=True)
    else:
        st.warning("Không có dữ liệu hợp lệ trong phiên hiện tại.")
