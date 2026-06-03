import streamlit as st


def render():
    game = st.session_state.game
    p1, p2 = st.session_state.players

    st.markdown("## The game is ready!")
    st.markdown(f"**Category:** {game.get('themeCategory', 'General Knowledge')}")
    st.markdown("---")
    st.info(game["commentary"]["intro"])
    st.markdown(
        """
**How to play:**
- 3 letter rounds + 3 number rounds
- Each round: Player 1 goes first, then pass the device to Player 2
- After all rounds: guess the hidden theme for bonus points
- Final showdown: unscramble a 9-letter mystery word
"""
    )
    st.markdown("---")
    st.markdown(f"**{p1}** vs **{p2}** — good luck!")

    if st.button("Let's go!", type="primary", use_container_width=True):
        st.session_state.screen = "letter"
        st.rerun()
