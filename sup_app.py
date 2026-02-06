import streamlit as st
import pandas as pd
import random

# --- ページ設定 ---
st.set_page_config(page_title="慶應ボード決め", page_icon="🏄‍♂️")

st.title("🏄‍慶應ボード決め")
st.markdown("""
名前と回数を入れて実行可能
""")
st.markdown("""1.実力を反映：練習回数をベーススコアとする""")
st.markdown("""2.正規分布による揺らぎ：練習回数に平均0の「ガウス分布」に従う運要素を加える""")

# --- サイドバー：設定 ---
st.sidebar.header("設定")

# 運要素（シグマ）の調整
luck_sigma = st.sidebar.slider(
    "運の強さ (標準偏差 σ)",
    min_value=0.0,
    max_value=20.0,
    value=5.0,
    step=0.500,
    help="値を大きくすると、練習回数が少ない人でも逆転しやすくなります。"
)

st.sidebar.info(f"現在の設定: 練習回数の差が **{luck_sigma * 2:.1f}回** 以内なら、運で逆転可能です。")

# --- メインエリア：データ入力 ---
st.subheader("メンバーと練習回数の入力")
st.caption("下の表は直接編集できます。行を追加・削除して人数を調整してください。")

# 初期の空データ（または例）
default_data = pd.DataFrame(
    [
        {"名前": "メンバーA", "練習回数": 50},
        {"名前": "メンバーB", "練習回数": 45},
        {"名前": "メンバーC", "練習回数": 30},
        {"名前": "メンバーD", "練習回数": 10},
    ]
)

# 編集可能なデータフレームを表示 (num_rows="dynamic"で行の追加削除が可能)
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
        
       



