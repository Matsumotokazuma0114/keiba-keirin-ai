
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="競輪 妙味分析AI",
    page_icon="🚴",
    layout="wide"
)

st.title("🚴 競輪 妙味分析AI")
st.caption("出走表・ライン・脚質・競走得点・オッズを使った参考分析ツール")

st.warning(
    "現在は入力データから参考スコアを算出する試作版です。"
    "実際の競走結果で予測精度を検証したモデルではなく、"
    "的中や利益を保証するものではありません。"
)

st.sidebar.header("レース設定")
race_name = st.sidebar.text_input(
    "開催場・レース番号",
    placeholder="例：防府 10R"
)
bank_style = st.sidebar.selectbox(
    "バンク・展開の傾向",
    ["標準", "先行有利", "捲り有利", "直線長め"]
)

st.subheader("① 出走表を入力")

st.write(
    "選手名、ライン、競走得点、直近3連対率、オッズなどを入力してね。"
    "選手名が空欄の行は分析から除外されるよ。"
)

columns = [
    "車番", "選手名", "ライン", "脚質",
    "競走得点", "直近3連対率(%)",
    "先行力(1-5)", "番手力(1-5)", "単勝オッズ"
]

initial_data = pd.DataFrame({
    "車番": list(range(1, 8)),
    "選手名": [""] * 7,
    "ライン": [""] * 7,
    "脚質": ["自在"] * 7,
    "競走得点": [90.0] * 7,
    "直近3連対率(%)": [30.0] * 7,
    "先行力(1-5)": [3] * 7,
    "番手力(1-5)": [3] * 7,
    "単勝オッズ": [5.0] * 7
})

uploaded_file = st.file_uploader(
    "CSVから出走表を読み込む（任意）",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        uploaded_data = pd.read_csv(uploaded_file)
        missing_columns = [
            col for col in columns
            if col not in uploaded_data.columns
        ]

        if missing_columns:
            st.error(
                "CSVの列名が指定形式と一致しないよ。"
                "必要な列：" + "、".join(columns)
            )
            raw_data = initial_data.copy()
        else:
            raw_data = uploaded_data[columns].copy()
            st.success("CSVを読み込んだよ。")
    except Exception as e:
        st.error(f"CSVを読み込めなかったよ：{e}")
        raw_data = initial_data.copy()
else:
    raw_data = initial_data.copy()

edited_data = st.data_editor(
    raw_data,
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    key="riders_editor",
    column_config={
        "車番": st.column_config.NumberColumn(
            "車番", min_value=1, max_value=9, step=1
        ),
        "選手名": st.column_config.TextColumn("選手名"),
        "ライン": st.column_config.TextColumn(
            "ライン", help="例：123のラインなら同じ番号を入力"
        ),
        "脚質": st.column_config.SelectboxColumn(
            "脚質",
            options=["先行", "捲り", "追込", "自在", "番手"]
        ),
        "競走得点": st.column_config.NumberColumn(
            "競走得点", min_value=0.0, max_value=150.0
        ),
        "直近3連対率(%)": st.column_config.NumberColumn(
            "直近3連対率(%)", min_value=0.0, max_value=100.0
        ),
        "先行力(1-5)": st.column_config.NumberColumn(
            "先行力(1-5)", min_value=1, max_value=5, step=1
        ),
        "番手力(1-5)": st.column_config.NumberColumn(
            "番手力(1-5)", min_value=1, max_value=5, step=1
        ),
        "単勝オッズ": st.column_config.NumberColumn(
            "単勝オッズ", min_value=0.0, max_value=9999.0
        )
    }
)

st.caption(
    "※ CSVを使う場合も、上に表示された列名と同じ形式にしてね。"
)

st.divider()
st.subheader("② 分析設定")

st.write(
    "スコアは競走得点・直近成績・ライン人数・脚質傾向から算出するよ。"
)

analyze = st.button(
    "🔎 レースを分析する",
    type="primary",
    use_container_width=True
)

if analyze:
    data = edited_data.copy()

    data["選手名"] = data["選手名"].fillna("").astype(str).str.strip()
    data = data[data["選手名"] != ""].copy()

    if len(data) < 2:
        st.error("選手名を2人以上入力してね。")
    else:
        numeric_columns = [
            "車番", "競走得点", "直近3連対率(%)",
            "先行力(1-5)", "番手力(1-5)", "単勝オッズ"
        ]

        for col in numeric_columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

        data = data.dropna(subset=["車番", "競走得点", "直近3連対率(%)"])
        data = data[
            (data["競走得点"] >= 0)
            & (data["直近3連対率(%)"].between(0, 100))
        ].copy()

        if len(data) < 2:
            st.error("有効な選手データを2人以上入力してね。")
        else:
            data["ライン"] = data["ライン"].fillna("").astype(str).str.strip()
            data["脚質"] = data["脚質"].fillna("自在").astype(str)
            data["先行力(1-5)"] = data["先行力(1-5)"].fillna(3).clip(1, 5)
            data["番手力(1-5)"] = data["番手力(1-5)"].fillna(3).clip(1, 5)

            # ライン人数
            valid_line = data["ライン"].ne("")
            line_counts = data.loc[valid_line, "ライン"].value_counts()
            data["ライン人数"] = data["ライン"].map(line_counts).fillna(1)

            # 各項目を0～1程度の範囲にそろえる
            points_min = data["競走得点"].min()
            points_max = data["競走得点"].max()

            if points_max > points_min:
                points_score = (
                    (data["競走得点"] - points_min)
                    / (points_max - points_min)
                )
            else:
                points_score = pd.Series(0.5, index=data.index)

            recent_score = data["直近3連対率(%)"] / 100
            line_score = data["ライン人数"] / max(data["ライン人数"].max(), 1)

            # バンク傾向は仮の加点。実測データに基づく補正ではない
            style_bonus = {
                "標準": {
                    "先行": 0.50, "捲り": 0.50, "追込": 0.50,
                    "自在": 0.50, "番手": 0.50
                },
                "先行有利": {
                    "先行": 1.00, "番手": 0.75, "自在": 0.60,
                    "捲り": 0.45, "追込": 0.40
                },
                "捲り有利": {
                    "捲り": 1.00, "自在": 0.75, "先行": 0.45,
                    "番手": 0.50, "追込": 0.50
                },
                "直線長め": {
                    "追込": 1.00, "番手": 0.75, "自在": 0.65,
                    "捲り": 0.55, "先行": 0.40
                }
            }

            data["脚質評価"] = (
                data["脚質"]
                .map(style_bonus[bank_style])
                .fillna(0.50)
            )

            # 仮の総合スコア
            data["総合スコア"] = (
                points_score * 0.40
                + recent_score * 0.35
                + line_score * 0.15
                + data["脚質評価"] * 0.10
            )

            # スコア比を参考確率として表示（校正済みの勝率ではない）
            total_score = data["総合スコア"].sum()

            if total_score <= 0:
                data["参考確率(%)"] = 100 / len(data)
            else:
                data["参考確率(%)"] = (
                    data["総合スコア"] / total_score * 100
                )

            data["期待回収率(%)"] = np.where(
                data["単勝オッズ"].notna() & (data["単勝オッズ"] > 0),
                data["参考確率(%)"] / 100 * data["単勝オッズ"] * 100,
                np.nan
            )

            data["妙味判定"] = np.where(
                data["期待回収率(%)"].isna(),
                "オッズ未入力",
                np.where(
                    data["期待回収率(%)"] > 100,
                    "参考値上は妙味あり",
                    "参考値上は妙味薄め"
                )
            )

            data = data.sort_values(
                "総合スコア", ascending=False
            ).reset_index(drop=True)

            data.insert(0, "評価順位", range(1, len(data) + 1))

            st.divider()
            st.subheader("③ 分析結果")

            if race_name:
                st.markdown(f"### {race_name}")

            first = data.iloc[0]
            st.metric(
                "スコア1位",
                f"{int(first['車番'])}番 {first['選手名']}",
                f"参考確率 {first['参考確率(%)']:.1f}%"
            )

            st.caption(
                "参考確率は入力項目のスコアを正規化した数値で、"
                "実際の的中確率を保証しないよ。"
            )

            display_columns = [
                "評価順位", "車番", "選手名", "ライン", "脚質",
                "競走得点", "直近3連対率(%)", "ライン人数",
                "参考確率(%)", "単勝オッズ", "期待回収率(%)", "妙味判定"
            ]

            results = data[display_columns].copy()
            results["参考確率(%)"] = results["参考確率(%)"].round(1)
            results["期待回収率(%)"] = results["期待回収率(%)"].round(1)
            st.dataframe(results, hide_index=True, use_container_width=True)

            st.subheader("④ スコア比較")
            chart_data = data.set_index("選手名")[["総合スコア"]]
            st.bar_chart(chart_data)

            st.subheader("⑤ 分析メモ")
            st.write(
                f"- 分析対象：{len(data)}人\n"
                f"- 設定したバンク傾向：{bank_style}\n"
                "- ライン人数は入力したライン欄の文字列が同じ選手を集計\n"
                "- 選手の欠場、当日の状態、風、並びの信頼性などは未取得"
            )

            csv = results.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 分析結果をCSVで保存",
                data=csv,
                file_name="keirin_analysis.csv",
                mime="text/csv",
                use_container_width=True
            )

st.divider()
st.caption(
    "今後の拡張候補：出走表・オッズの自動取得、"
    "バンク別成績、選手の直近成績、展開・ライン分析、"
    "過去レースによる予測精度の検証。"
)
