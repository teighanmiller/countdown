from datetime import date

import streamlit as st

from lib.game_generator import build_game


def render():
    p1, p2 = st.session_state.players[0], st.session_state.players[1]

    st.header("Generating your game...", anchor=False)
    st.markdown(f"Picking a hidden theme for **{p1}** vs **{p2}**.")

    # First pass: render the loading UI and flush it to the browser, then rerun to start generation.
    if not st.session_state.get("_generation_ready"):
        st.session_state._generation_ready = True
        st.info("Fetching Wikipedia context and building your themed game — this takes about 15 seconds...")
        st.rerun()
        return

    with st.spinner("Building game..."):
        today = date.today().isoformat()
        try:
            session = build_game(st.session_state.difficulty, today)
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
