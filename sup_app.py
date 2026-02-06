import streamlit as st
import pandas as pd
import random

# スライダーの値を記憶するための「箱」を作る
if "sigma_value" not in st.session_state:
    st.session_state.sigma_value = 2.0

# --- ページ設定 ---
st.set_page_config(page_title="慶應ボード決め", page_icon="🏄‍♂️")

st.title("慶應ボード決め")
st.markdown("""
名前と回数を入れて実行可能
""")
st.markdown("""1. 実力を反映：練習回数をベーススコアとする""")
st.markdown("""2. 正規分布による揺らぎ：練習回数に平均0の「ガウス分布」に従う運要素を加える""")

# --- 【重要】先にデータ入力エリアを作る（ここを上に移動しました） ---
st.subheader("メンバーと練習回数の入力")
st.caption("下の表は直接編集可能)           

# 初期の空データ（または例）
default_data = pd.DataFrame(
    [
        {"名前": "メンバーA", "練習回数": 50},
        {"名前": "メンバーB", "練習回数": 45},
        {"名前": "メンバーC", "練習回数": 30},
        {"名前": "メンバーD", "練習回数": 10},
    ]
)

# 編集可能なデータフレームを表示
edited_df = st.data_editor(
    default_data,
    num_rows="dynamic",
    column_config={
        "練習回数": st.column_config.NumberColumn(
            "練習回数",
            min_value=0,
            step=1,
            format="%d 回"
        )
    },
    use_container_width=True
)

# --- 統計量の計算（表を作った後に計算する） ---
if not edited_df.empty:
    current_mean = edited_df["練習回数"].mean()
    current_sd = edited_df["練習回数"].std()
    
    # データが少なくて計算できない場合の処理
    if pd.isna(current_sd):
        current_sd = 0.0
    
    # 理想のσ（標準偏差 × 0.5）
    ideal_sigma = max(0.5, current_sd * 0.5)
else:
    current_mean = 0.0
    current_sd = 0.0
    ideal_sigma = 2.0

# --- サイドバー：設定（計算が終わってから表示する） ---
st.sidebar.header("設定")

# 1. 統計情報の表示
st.sidebar.markdown("### データ統計")
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

# --- 抽選ボタンと結果表示 ---
if st.button("抽選", type="primary"):
    if edited_df.empty:
        st.error("メンバーを入力してください！")
    else:
        # 計算ロジック
        results = []
        
        # 毎回ランダムな結果を出すためのループ
        for index, row in edited_df.iterrows():
            name = row["名前"]
            practice = row["練習回数"]
            
            # ガウシアンノイズ（運）を生成
            luck_score = random.gauss(0, luck_sigma)
            final_score = practice + luck_score
            
            results.append({
                "名前": name,
                "練習回数": practice,
                "運": luck_score,
                "最終スコア": final_score
            })
        
        # 結果をデータフレーム化してソート
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values(by="最終スコア", ascending=False).reset_index(drop=True)
        
        # 順位カラムを追加（1から開始）
        result_df.index = result_df.index + 1
        result_df.index.name = "順位"
        
        # --- 結果表示 ---
        st.success("結果は以下の通りです")
        
        # 表示用に桁数を整える
        display_df = result_df.copy()
        display_df["運"] = display_df["運"].map('{:+.1f}'.format)
        display_df["最終スコア"] = display_df["最終スコア"].map('{:.1f}'.format)
        
        st.table(display_df)
