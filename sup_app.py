import streamlit as st
import pandas as pd
import random

# --- 1. スプレッドシートの設定 ---
# 「1ヶ月間の回数」シートを表示した状態のURLをコピーし、末尾を /export?format=csv&gid=... に書き換えてね
SHEET_URL = "https://docs.google.com/spreadsheets/d/1LLgMdsiORF8LBCtN_8BHGUdms_TpbXuwki4DFn03Amo/export?format=csv&gid=0"

# スライダーの値を記憶するための「箱」を作る
if "sigma_value" not in st.session_state:
    st.session_state.sigma_value = 2.0

# --- ページ設定 ---
st.set_page_config(page_title="慶應ボード決め", page_icon="🏄‍♂️")

st.title("🏄‍慶應ボードセレクション")
st.markdown("スプレッドシートから練習回数を自動取得します。")
st.markdown("1. 実力を反映：練習回数をベーススコアとする")
st.markdown("2. 正規分布による揺らぎ：練習回数に平均0の「ガウス分布」に従う運要素を加える")

# --- 2. データ読み込み処理 ---
@st.cache_data(ttl=30) # 30秒キャッシュ（頻繁にシートを更新する場合に便利）
def load_spreadsheet_data():
    if "google.com" not in SHEET_URL or "【" in SHEET_URL:
        # URLが未設定ならダミーを表示
        return pd.DataFrame([{"名前": "メンバーA", "練習回数": 10}, {"名前": "メンバーB", "練習回数": 8}])
    
    try:
        # 【修正ポイント】skiprows=3 を削除。1行目から読み込む設定に変更
        df = pd.read_csv(SHEET_URL)
        
        # 列名が正しく読み込めているかチェック
        if "名前" in df.columns and "練習回数" in df.columns:
            # 名前が空の行（IMPORTRANGEの余白など）を除去
            df = df.dropna(subset=["名前"])
            # 練習回数を数値に変換（エラーは0にする）
            df["練習回数"] = pd.to_numeric(df["練習回数"], errors='coerce').fillna(0).astype(int)
            
            return df[["名前", "練習回数"]].reset_index(drop=True)
        else:
            # デバッグ用に読み込んだ列名を表示
            st.error(f"列が見つかりません。現在の列名: {list(df.columns)}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"データの読み込みに失敗しました。URLを確認してください。")
        return pd.DataFrame()

# --- データ表示・編集エリア ---
st.subheader("メンバーと練習回数の確認")
st.caption("スプレッドシート「1ヶ月間の回数」から自動取得中。")

default_data = load_spreadsheet_data()

edited_df = st.data_editor(
    default_data,
    num_rows="dynamic",
    column_config={
        "練習回数": st.column_config.NumberColumn(
            "練習回数", min_value=0, step=1, format="%d 回"
        )
    },
    use_container_width=True
)

# --- 統計量の計算 ---
if not edited_df.empty:
    current_mean = edited_df["練習回数"].mean()
    current_sd = edited_df["練習回数"].std()
    current_sd = 0.0 if pd.isna(current_sd) else current_sd
    ideal_sigma = max(0.5, current_sd * 0.5)
else:
    current_mean, current_sd, ideal_sigma = 0.0, 0.0, 2.0

# --- サイドバー：設定 ---
st.sidebar.header("設定")
st.sidebar.markdown("### データ統計")
st.sidebar.info(f"- **平均**: {current_mean:.1f} 回\n- **標準偏差**: {current_sd:.1f}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 運要素(σ)の調整")
st.sidebar.caption(f"理想値 (SD×0.5): **{ideal_sigma:.1f}**")

if st.sidebar.button("理想のσの値を設定する"):
    st.session_state.sigma_value = float(ideal_sigma)
    st.rerun()

luck_sigma = st.sidebar.slider(
    "運の強さ (σ)", min_value=0.0, max_value=10.0, step=0.1, key="sigma_value"
)

reversal_range = luck_sigma * 2.0
st.sidebar.warning(f"**現在の設定：** 差が **{reversal_range:.1f}回** 以内なら逆転可能")

# --- 抽選ボタンと結果表示 ---
if st.button("抽選実行", type="primary"):
    if edited_df.empty:
        st.error("データがありません！")
    else:
        results = []
        for _, row in edited_df.iterrows():
            luck = random.gauss(0, luck_sigma)
            results.append({
                "名前": row["名前"],
                "練習回数": row["練習回数"],
                "運": luck,
                "最終スコア": row["練習回数"] + luck
            })
        
        result_df = pd.DataFrame(results).sort_values(by="最終スコア", ascending=False).reset_index(drop=True)
        result_df.index = result_df.index + 1
        result_df.index.name = "順位"
        
        st.success("結果発表！")
        display_df = result_df.copy()
        display_df["運"] = display_df["運"].map('{:+.1f}'.format)
        display_df["最終スコア"] = display_df["最終スコア"].map('{:.1f}'.format)
        st.table(display_df)
