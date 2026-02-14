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
        df = pd.DataFrame([
            {"名前": "メンバーA", "性別": "男子", "練習回数": 10},
            {"名前": "メンバーB", "性別": "女子", "練習回数": 8}
        ])
    else:
        try:
            df = pd.read_csv(SHEET_URL)
            df = df.dropna(subset=["名前"])
            df["練習回数"] = pd.to_numeric(df["練習回数"], errors='coerce').fillna(0).astype(int)
        except Exception as e:
            st.error(f"読み込み失敗: {e}")
            return pd.DataFrame()

    # 【重要】初期状態で全員「参加」にチェックを入れる列を追加
    if "名前" in df.columns:
        df.insert(0, "対象", True)
        return df.reset_index(drop=True)
    return pd.DataFrame()

# 全データを読み込む
all_data = load_spreadsheet_data()

# --- 3. 性別選択 (Gender selection) ---
st.subheader("性別選択")
selection_type = st.radio(
    "",["全員", "男子", "女子"],
    horizontal=True
)

# 性別フィルター
if selection_type == "全員":
    display_data = all_data
else:
    display_data = all_data[all_data["性別"] == selection_type]

# --- 4. データ表示・編集 (Data editor) ---
st.subheader(f"メンバーと練習回数の確認（{selection_type}）")
st.caption("チェックを外すと、統計と抽選から除外される")

# チェックボックス形式のテーブル
edited_df = st.data_editor(
    display_data,
    num_rows="fixed", # 名前が消えないよう固定
    column_config={
        "対象": st.column_config.CheckboxColumn(
            "対象",
            help="抽選に含める場合はチェック",
            default=True,
        ),
        "練習回数": st.column_config.NumberColumn(
            "練習回数", min_value=0, step=1, format="%d 回"
        ),
        "名前": st.column_config.TextColumn("名前", disabled=True), # 名前は編集不可に
        "性別": st.column_config.TextColumn("性別", disabled=True)
    },
    use_container_width=True,
    hide_index=True
)

# 「対象」にチェックが入っている人のみを抽出
active_df = edited_df[edited_df["対象"] == True]

# --- 5. 統計量の計算 (Stats calculation) ---
st.sidebar.header("設定")

# 統計対象の選択
st.sidebar.markdown("### 統計の対象")
include_all = st.sidebar.checkbox("チェック無しのメンバーも含めて計算", value=False)

stats_target = edited_df if include_all else active_df
target_label = "（全員）" if include_all else "（対象のみ）"

if not stats_target.empty:
    current_mean = stats_target["練習回数"].mean()
    current_sd = stats_target["練習回数"].std()
    current_sd = 0.0 if pd.isna(current_sd) else current_sd
    ideal_sigma = max(0.5, current_sd * 0.5)
else:
    current_mean, current_sd, ideal_sigma = 0.0, 0.0, 2.0

st.sidebar.markdown(f"### データ統計 {target_label}")
st.sidebar.info(f"- **平均**: {current_mean:.1f} 回\n- **標準偏差**: {current_sd:.1f}")
st.sidebar.caption("※標準偏差が大きい＝格差が激しい")
st.sidebar.markdown("---")

st.sidebar.markdown("### 運要素(σ)の調整")
st.sidebar.caption(f"理想値 (SD×0.5): **{ideal_sigma:.1f}**")

if st.sidebar.button("理想のσの値を設定する"):
    st.session_state.sigma_value = float(ideal_sigma)
    st.rerun()

luck_sigma = st.sidebar.slider(
    "運の強さ (σ)",
    min_value=0.0,
    max_value=10.0,
    step=0.1,
    key="sigma_value"
)

reversal_range = luck_sigma * 2.0
st.sidebar.warning(f"**現在の設定：** 差が **{reversal_range:.1f}回** 以内なら逆転可能")

# --- 6. 抽選実行 (Run lottery) ---
if st.button("抽選実行", type="primary"):
    if active_df.empty:
        st.error("抽選対象が選択されていません")
    else:
        results = []
        for _, row in active_df.iterrows():
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
        
        st.success(f"{selection_type}（対象：{len(active_df)}名）の抽選結果")
        display_res = result_df.copy()
        display_res["運"] = display_res["運"].map('{:+.1f}'.format)
        display_res["最終スコア"] = display_res["最終スコア"].map('{:.1f}'.format)
        st.table(display_res)
