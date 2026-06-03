import streamlit as st


def render():
    game = st.session_state.game
    p1, p2 = st.session_state.players
    s1, s2 = st.session_state.scores
    theme = game["theme"]
    p1_guess = st.session_state.get("theme_p1_guess_text", "—")
    p2_guess = st.session_state.get("theme_p2_guess_text", "—")
    winner = st.session_state.get("conundrum_winner")

    st.markdown("## Game Over!")
    st.markdown("---")

    # Winner announcement
    if s1 > s2:
        st.success(f"🏆 {p1} wins with {s1} points!")
    elif s2 > s1:
        st.success(f"🏆 {p2} wins with {s2} points!")
    else:
        st.info(f"It's a tie! Both players scored {s1} points.")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(p1, f"{s1} pts")
    with col2:
        st.metric(p2, f"{s2} pts")

    if winner:
        st.markdown(f"**Conundrum solved by {winner}!**")

    # Win message from Claude
    win_msg_template = game["commentary"].get("winMessage", "")
    if s1 > s2:
        win_msg = win_msg_template.replace("{winner}", p1)
    elif s2 > s1:
        win_msg = win_msg_template.replace("{winner}", p2)
    else:
        win_msg = "A tie — equally matched opponents!"
    if win_msg:
        st.info(f"🎙️ {win_msg}")

    st.markdown("---")

    # Theme reveal
    st.markdown("## The Hidden Theme Was...")
    st.markdown(
        f"<div style='font-size:2.5rem;font-weight:bold;text-align:center;"
        f"color:#FFD700;padding:1rem;background:#16213e;border-radius:12px;'>{theme}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.markdown(game["commentary"].get("themeReveal", ""))

    st.markdown("---")
    st.markdown("### How the theme was hidden in each round")
    letter_rounds = game.get("letterRounds", [])
    number_rounds = game.get("numberRounds", [])
    conundrum = game.get("conundrum", {})

    for i, lr in enumerate(letter_rounds):
        st.markdown(f"**Letter Round {i+1}** — `{lr['optimalWord']}`: {lr.get('themeConnection', '')}")
    for i, nr in enumerate(number_rounds):
        st.markdown(f"**Number Round {i+1}** — `{nr['target']}`: {nr.get('themeConnection', '')}")
    st.markdown(f"**Conundrum** — `{conundrum.get('word', '')}`: {conundrum.get('themeConnection', '')}")

    st.markdown("---")
    st.markdown("### Your theme guesses")
    st.markdown(f"**{p1}** guessed: *{p1_guess}*")
    st.markdown(f"**{p2}** guessed: *{p2_guess}*")

    st.markdown("---")
    if st.button("Play Again", type="primary", use_container_width=True):
        _GAME_KEYS = {
            "game", "scores", "round_results", "current_round", "round_phase",
            "p1_answer", "p2_answer", "conundrum_attempt", "conundrum_winner",
            "theme_guess_phase", "theme_p1_score", "theme_p2_score",
            "theme_p1_guess_text", "theme_p2_guess_text",
            "players", "difficulty", "screen", "_generation_ready",
        }
        for key in _GAME_KEYS:
            st.session_state.pop(key, None)
        st.rerun()
