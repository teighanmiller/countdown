from datetime import date

import streamlit as st

from lib.game_generator import build_game


def render():
    p1, p2 = st.session_state.players[0], st.session_state.players[1]

    st.header("Generating your game...", anchor=False)
    st.markdown(f"Preparing a themed game for **{p1}** vs **{p2}**.")

    if not st.session_state.get("_generation_ready"):
        st.session_state._generation_ready = True
        st.rerun()
        return

    progress_placeholder = st.empty()
    steps: list[tuple[str, str]] = []

    def on_progress(msg: str):
        if steps:
            steps[-1] = ("✅", steps[-1][1])
        steps.append(("⏳", msg))
        _render_steps()

    def _render_steps():
        lines = [f"{icon} {text}" for icon, text in steps]
        progress_placeholder.markdown("\n\n".join(lines))

    today = date.today().isoformat()
    try:
        session = build_game(st.session_state.difficulty, today, on_progress=on_progress)
        if steps:
            steps[-1] = ("✅", steps[-1][1])
        _render_steps()
    except Exception as e:
        st.error(f"Game generation failed: {e}")
        if st.button("Try again"):
            st.session_state.pop("_generation_ready", None)
            st.session_state.screen = "setup"
            st.rerun()
        return

    st.session_state.game = session
    st.session_state.scores = [0, 0]
    st.session_state.round_results = []
    st.session_state.current_round = 0
    st.session_state.round_phase = "p1"
    st.session_state.p1_answer = None
    st.session_state.p2_answer = None
    st.session_state.conundrum_attempt = 0
    st.session_state.conundrum_winner = None
    st.session_state.theme_guess_phase = "p1"
    st.session_state.theme_p1_score = None
    st.session_state.theme_p2_score = None
    st.session_state.theme_p1_guess_text = None
    st.session_state.theme_p2_guess_text = None
    st.session_state.screen = "intro"
    st.rerun()
