
import streamlit as st

st.set_page_config(
    page_title="競馬・競輪 妙味分析AI",
    page_icon="🎯",
    layout="centered"
)

st.title("🎯 競馬・競輪 妙味分析AI")
st.write("自分の勝率評価とオッズの差から、買い目の妙味を分析します。")

sport = st.radio("競技", ["競馬", "競輪"], horizontal=True)

name = st.text_input("馬名・選手名・買い目")
odds = st.number_input("現在のオッズ", min_value=1.0, value=5.0, step=0.1)
prob = st.slider("自分が考える的中確率（%）", 1, 99, 25)

if st.button("妙味を分析する"):
    p = prob / 100
    fair_odds = 1 / p
    ev = odds * p
    edge = (ev - 1) * 100

    st.subheader("分析結果")
    st.write(f"対象：{name if name else '未入力'}")
    st.metric("自分の評価オッズ", f"{fair_odds:.2f}倍")
    st.metric("期待回収率", f"{ev * 100:.1f}%")
    st.metric("期待値の差", f"{edge:+.1f}%")

    if ev > 1:
        st.success("理論上はプラス期待値です。確率評価の精度に注意してください。")
    elif ev < 1:
        st.warning("理論上はマイナス期待値です。")
    else:
        st.info("理論上は損益分岐点です。")

st.caption("※入力した的中確率が正しいと仮定した計算です。的中を保証するものではありません。")
