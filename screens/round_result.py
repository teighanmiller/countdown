import streamlit as st


def render():
    result = st.session_state.round_results[-1]
    p1, p2 = st.session_state.players
    s1, s2 = st.session_state.scores
    r_type = result["type"]

    if r_type == "letter":
        st.header(f"Letter Round {result['round']} — Results", anchor=False)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{p1}**")
            st.markdown(f"Word: `{result['p1']['word']}`")
            st.markdown(f"Score this round: **{result['p1']['score']} pts**")
        with col2:
            st.markdown(f"**{p2}**")
            st.markdown(f"Word: `{result['p2']['word']}`")
            st.markdown(f"Score this round: **{result['p2']['score']} pts**")
        st.markdown(f"The word was: **{result['optimal']}** ({len(result['optimal'])} letters)")
    else:
        st.header(f"Number Round {result['round']} — Results", anchor=False)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{p1}**")
            st.markdown(f"Expression: `{result['p1']['expr']}`")
            r1 = result["p1"]["result"]
            st.markdown(f"Result: **{r1 if r1 is not None else '—'}**")
            st.markdown(f"Score this round: **{result['p1']['score']} pts**")
        with col2:
            st.markdown(f"**{p2}**")
            st.markdown(f"Expression: `{result['p2']['expr']}`")
            r2 = result["p2"]["result"]
            st.markdown(f"Result: **{r2 if r2 is not None else '—'}**")
            st.markdown(f"Score this round: **{result['p2']['score']} pts**")
        st.markdown(f"Target: **{result['target']}** | One solution: `{result['solution']}`")

    st.markdown("---")
    if result.get("commentary"):
        st.info(f"🎙️ {result['commentary']}")

    st.markdown(f"**Scoreboard: {p1} {s1} — {s2} {p2}**")
    st.markdown("---")

    # Advance to next round
    current = st.session_state.current_round
    total_rounds = 6  # 3 letter + 3 number

    if st.button("Next Round →", type="primary", use_container_width=True):
        st.session_state.current_round = current + 1
        st.session_state.round_phase = "p1"
        st.session_state.p1_answer = None
        st.session_state.p2_answer = None

        if current + 1 >= total_rounds:
            st.session_state.screen = "theme_guess"
        else:
            next_round = current + 1
            # Even overall rounds (0,2,4) → letter; Odd (1,3,5) → number
            st.session_state.screen = "letter" if next_round % 2 == 0 else "number"
        st.rerun()
