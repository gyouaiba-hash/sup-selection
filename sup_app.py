import streamlit as st
import pandas as pd
import random

# --- 1. スプレッドシートの設定 (Spreadsheet settings) ---
# 「アプリ書き出し用」シートのURL末尾は必ず「gid=数字」にする
SHEET_URL = "https://docs.google.com/spreadsheets/d/1LLgMdsiORF8LBCtN_8BHGUdms_TpbXuwki4DFn03Amo/export?format=csv&gid=0"

if "sigma_value" not in st.session_state:
    st.session_state.sigma_value = 2.0

st.set_page_config(page_title="ボード", page_icon="🏄‍♂️")
st.title("慶應ボード決め")

# --- 2. データ読み込み処理 (Data loading) ---
@st.cache_data(ttl=30)
def load_spreadsheet_data():
    if "google.com" not in SHEET_URL or "【" in SHEET_URL:
        return pd.DataFrame([
            {"名前": "メンバーA", "性別": "男子", "練習回数": 10},
            {"名前": "メンバーB", "性別": "女子", "練習回数": 8}
        ])
    
    try:
        df = pd.read_csv(SHEET_URL)
        
        # 名前、性別、練習回数の3つの列があるかチェック (Check columns)
        required_cols = ["名前", "性別", "練習回数"]
        if all(col in df.columns for col in required_cols):
            df = df.dropna(subset=["名前"])
            df["練習回数"] = pd.to_numeric(df["練習回数"], errors='coerce').fillna(0).astype(int)
            return df[required_cols].reset_index(drop=True)
        else:
            st.error(f"列が見つからない。現在の列: {list(df.columns)}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"読み込み失敗: {e}")
        return pd.DataFrame()

# 全データを読み込む
all_data = load_spreadsheet_data()

# --- 3. 性別選択 (Gender selection) ---
st.subheader("性別選択")
selection_type = st.radio(
    "",["全員", "男子", "女子"],
    horizontal=True
)

# 選択に合わせてデータをフィルタリング (Filtering)
if selection_type == "全員":
    filtered_data = all_data
else:
    # 選択された性別（男子 or 女子）と一致する行だけを抽出
    filtered_data = all_data[all_data["性別"] == selection_type]

# --- 4. データ表示・編集 (Data editor) ---
st.subheader(f"メンバーと練習回数の確認（{selection_type}）")
edited_df = st.data_editor(
    filtered_data,
    num_rows="dynamic",
    column_config={
        "練習回数": st.column_config.NumberColumn(
            "練習回数", min_value=0, step=1, format="%d 回"
        )
    },
    use_container_width=True
)

# 除外（欠席）されたメンバーをグレーエリアに表示
excluded_members = filtered_data[~filtered_data["名前"].isin(edited_df["名前"])]
if not excluded_members.empty:
    st.markdown("---")
    st.caption("⬇️ 除外・欠席中のメンバー")
    # グレーっぽい背景にするための設定
    st.dataframe(
        excluded_members[["名前", "練習回数"]], 
        hide_index=True, 
        use_container_width=True
    )
    st.info("👆 間違えて消した場合は、上の表の空行に「名前」と「回数」を打ち直せば復活します。")

# --- 5. 統計量の計算 (Stats calculation) ---
st.sidebar.header("設定")

# 【追加機能】休んでいる人を含むかどうかの選択
st.sidebar.markdown("### 統計の対象")
include_excluded = st.sidebar.checkbox("除外・欠席者を含めて計算", value=False)

# 統計に使用するデータの切り替え
stats_target = filtered_data if include_excluded else edited_df
target_label = "（欠席者込み）" if include_excluded else "（出席者のみ）"

if not stats_target.empty:
    current_mean = stats_target["練習回数"].mean()
    current_sd = stats_target["練習回数"].std()
    current_sd = 0.0 if pd.isna(current_sd) else current_sd
    ideal_sigma = max(0.5, current_sd * 0.5)
else:
    current_mean, current_sd, ideal_sigma = 0.0, 0.0, 2.0

# 1. 統計情報の表示
st.sidebar.markdown(f"### データ統計 {target_label}")
st.sidebar.info(f"""
- **平均**: {current_mean:.1f} 回
- **標準偏差**: {current_sd:.1f}
""")
st.sidebar.caption("※標準偏差が大きい＝格差が激しい")

st.sidebar.markdown("---")

# 2. ボタンとスライダーの設定
st.sidebar.markdown("### 運要素(σ)の調整")
st.sidebar.caption(f"理想値 (SD×0.5): **{ideal_sigma:.1f}**")

# ボタンを押したら理想値をセット
if st.sidebar.button("理想のσの値を設定する"):
    st.session_state.sigma_value = float(ideal_sigma)
    st.rerun() # 画面を更新してスライダーに反映

# スライダー
luck_sigma = st.sidebar.slider(
    "運の強さ (σ)",
    min_value=0.0,
    max_value=10.0,
    step=0.1,
    key="sigma_value", 
    help="値を大きくすると、下剋上が起きやすくなる"
)

# 逆転可能ラインの計算（σの2倍）
reversal_range = luck_sigma * 2.0

st.sidebar.warning(f"""**現在の設定：**練習回数の差が**{reversal_range: .1f}回**以内なら運で逆転可能""")

# --- 6. 抽選実行 (Run lottery) ---
if st.button("抽選実行", type="primary"):
    if edited_df.empty:
        st.error("抽選対象のデータがないです")
    else:
        results = []
        for _, row in edited_df.iterrows():
            luck = random.gauss(0, luck_sigma)
            results.append({
                "名前": row["名前"],
                "性別": row["性別"],
                "練習回数": row["練習回数"],
                "運 (Luck)": luck,
                "最終スコア (Score)": row["練習回数"] + luck
            })
        
        # スコア順に並び替え
        result_df = pd.DataFrame(results).sort_values(by="最終スコア (Score)", ascending=False).reset_index(drop=True)
        result_df.index = result_df.index + 1
        result_df.index.name = "順位 (Rank)"
        
        st.success(f"{selection_type}の抽選結果")
        display_df = result_df.copy()
        display_df["運 (Luck)"] = display_df["運 (Luck)"].map('{:+.1f}'.format)
        display_df["最終スコア (Score)"] = display_df["最終スコア (Score)"].map('{:.1f}'.format)
        st.table(display_df)

