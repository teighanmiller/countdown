import streamlit as st


def render():
    st.markdown("## COUNTDOWN", help=None)
    st.markdown("### The AI-Powered Game Show")
    st.markdown("---")
    st.markdown(
        "A hidden theme connects every round. Guess it at the end for bonus points."
    )

    col1, col2 = st.columns(2)
    with col1:
        p1 = st.text_input("Player 1 Name", placeholder="Alice", key="p1_input")
    with col2:
        p2 = st.text_input("Player 2 Name", placeholder="Bob", key="p2_input")

    st.markdown("#### Theme Difficulty")
    difficulty = st.radio(
        "How obscure should the hidden theme be?",
        options=["easy", "medium", "hard"],
        format_func=lambda x: {
            "easy": "Easy — broad theme (e.g. 'Animals')",
            "medium": "Medium — specific theme (e.g. 'The Olympics')",
            "hard": "Hard — niche theme (e.g. 'Apollo 13 mission')",
        }[x],
        horizontal=True,
        key="difficulty_input",
    )

    st.markdown("---")
    if st.button("Start Game", type="primary", use_container_width=True):
        if not p1.strip() or not p2.strip():
            st.error("Both players need a name to start.")
            return

        st.session_state.players = [p1.strip(), p2.strip()]
        st.session_state.difficulty = difficulty
        st.session_state.pop("_generation_ready", None)
        st.session_state.screen = "loading"
        st.rerun()
