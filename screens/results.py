import streamlit as st


def render():
    game = st.session_state.game
    p1, p2 = st.session_state.players
    s1, s2 = st.session_state.scores
    theme = game["theme"]
    p1_guess = st.session_state.get("theme_p1_guess_text", "—")
    p2_guess = st.session_state.get("theme_p2_guess_text", "—")
    winner = st.session_state.get("conundrum_winner")

    st.header("Game Over!", anchor=False)
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
    st.header("The Hidden Theme Was...", anchor=False)
    st.markdown(
        f"<div style='font-size:2.5rem;font-weight:bold;text-align:center;"
        f"color:#FFD700;padding:1rem;background:#16213e;border-radius:12px;'>{theme}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.markdown(game["commentary"].get("themeReveal", ""))

    st.markdown("---")
    st.subheader("How the theme was hidden in each round", anchor=False)
    letter_rounds = game.get("letterRounds", [])
    number_rounds = game.get("numberRounds", [])
    conundrum = game.get("conundrum", {})

    for i, lr in enumerate(letter_rounds):
        st.markdown(f"**Letter Round {i+1}** — `{lr['optimalWord']}`: {lr.get('themeConnection', '')}")
    for i, nr in enumerate(number_rounds):
        st.markdown(f"**Number Round {i+1}** — `{nr['target']}`: {nr.get('themeConnection', '')}")
    st.markdown(f"**Conundrum** — `{conundrum.get('word', '')}`: {conundrum.get('themeConnection', '')}")

    st.markdown("---")
    st.subheader("Your theme guesses", anchor=False)
    st.markdown(f"**{p1}** guessed: *{p1_guess}*")
    st.markdown(f"**{p2}** guessed: *{p2_guess}*")

    st.markdown("---")
    if st.button("Play Again", type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()
