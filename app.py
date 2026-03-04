import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# ページ設定
st.set_page_config(page_title="昭和CMバズ・レーダー", layout="wide")
st.title("📺 1980年代CM バズ・レーダー")

# DB読み込み
def load_data():
    conn = sqlite3.connect("buzz_radar.db")
    query = "SELECT * FROM videos ORDER BY buzz_ratio DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

try:
    df = load_data()
    
    # --- サイドバー：フィルタリング ---
    st.sidebar.header("Filter")
    min_ratio = st.sidebar.slider("最小バズ倍率 (views/subs)", 0.0, float(df["buzz_ratio"].max()), 1.0)
    filtered_df = df[df["buzz_ratio"] >= min_ratio]

    # --- メイン指標 ---
    col1, col2, col3 = st.columns(3)
    col1.metric("総収集件数", f"{len(df)} 件")
    col2.metric("今回のターゲット", f"{len(filtered_df)} 件")
    col3.metric("最高バズ倍率", f"{df['buzz_ratio'].max()} 倍")

    # --- グラフ：バズの分布 ---
    st.subheader("📈 バズり倍率の分布")
    fig = px.scatter(filtered_df, x="sub_count", y="view_count", size="buzz_ratio", 
                     hover_name="title", color="buzz_ratio",
                     log_x=True, title="登録者数 vs 再生数（円の大きさがバズり度）")
    st.plotly_chart(fig, use_container_width=True)

    # --- データテーブル ---
    st.subheader("🔍 発掘リスト")
    
    # URLをクリッカブルにする
    display_df = filtered_df.copy()
    display_df['url'] = "https://www.youtube.com/watch?v=" + display_df['video_id']
    
    st.dataframe(
        display_df[['buzz_ratio', 'title', 'channel_title', 'view_count', 'sub_count', 'url']],
        column_config={
            "url": st.column_config.LinkColumn("YouTube Link"),
            "buzz_ratio": st.column_config.NumberColumn("バズ倍率", format="%.2f 倍"),
            "view_count": "再生数",
            "sub_count": "登録者数"
        },
        hide_index=True,
    )

except Exception as e:
    st.error(f"データの読み込みに失敗したよ。まだDBがないか、中身が空かも？: {e}")
    st.info("リサーチ用のスクリプトを先に動かして、buzz_radar.db を作ってみて！")

