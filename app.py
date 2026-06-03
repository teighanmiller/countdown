import streamlit as st

st.set_page_config(
    page_title="Countdown",
    page_icon="⏱️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Lazy imports keep startup fast
def _screen():
    return st.session_state.get("screen", "setup")


screen = _screen()

if screen == "setup":
    from screens.setup import render
    render()

elif screen == "loading":
    from screens.loading import render
    render()

elif screen == "intro":
    from screens.intro import render
    render()

elif screen == "letter":
    from screens.letter_round import render, render_handoff
    phase = st.session_state.get("round_phase", "p1")
    if phase == "handoff_p2":
        render_handoff()
    else:
        render()

elif screen == "number":
    from screens.number_round import render, render_handoff
    phase = st.session_state.get("round_phase", "p1")
    if phase == "handoff_p2":
        render_handoff()
    else:
        render()

elif screen == "round_result":
    from screens.round_result import render
    render()

elif screen == "theme_guess":
    if "theme_guess_phase" not in st.session_state:
        st.session_state.theme_guess_phase = "p1"
    from screens.theme_guess import render
    render()

elif screen == "conundrum":
    from screens.conundrum import render
    render()

elif screen == "results":
    from screens.results import render
    render()

else:
    st.error(f"Unknown screen: {screen}")
    if st.button("Return to start"):
        st.session_state.clear()
        st.rerun()
