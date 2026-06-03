import random

import streamlit as st
import streamlit.components.v1 as components

MAX_ATTEMPTS = 3

_TIMER_HTML = """
<div style="font-size:3rem;font-weight:bold;color:#FFD700;text-align:center;" id="t">30</div>
<script>
  var t = 30;
  var el = document.getElementById('t');
  var iv = setInterval(function() {{
    t--;
    el.textContent = t;
    if (t <= 0) {{ clearInterval(iv); el.textContent = "⏰"; el.style.color = "#ff4444"; }}
  }}, 1000);
</script>
"""


def _rescramble(word: str) -> str:
    chars = list(word.upper())
    for _ in range(20):
        random.shuffle(chars)
        if "".join(chars) != word.upper():
            break
    return "".join(chars)


def render():
    game = st.session_state.game
    conundrum = game["conundrum"]
    word = conundrum["word"].upper()
    attempt = st.session_state.conundrum_attempt
    p1, p2 = st.session_state.players
    s1, s2 = st.session_state.scores

    # Generate or retrieve scramble for this attempt
    scramble_key = f"conundrum_scramble_{attempt}"
    if scramble_key not in st.session_state:
        st.session_state[scramble_key] = _rescramble(word)
    scrambled = st.session_state[scramble_key]

    st.header("Final Showdown — The Conundrum", anchor=False)
    if attempt > 0:
        st.markdown(f"*Attempt {attempt + 1} of {MAX_ATTEMPTS} — scores are tied!*")
    st.markdown("Both players work together (or race each other).")
    st.markdown("First to unscramble wins the round. **10 points** to the winner.")
    st.markdown("---")

    # Scrambled word display
    cols = st.columns(9)
    for i, col in enumerate(cols):
        col.markdown(
            f"<div style='font-size:2.5rem;font-weight:bold;text-align:center;"
            f"background:#16213e;border:2px solid #FFD700;border-radius:8px;"
            f"padding:0.3rem;'>{scrambled[i]}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")
    components.html(_TIMER_HTML, height=80)

    st.markdown(f"**Scoreboard: {p1} {s1} — {s2} {p2}**")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        g1 = st.text_input(f"{p1}'s answer", key=f"con_p1_{attempt}", placeholder="Unscramble it...")
        b1 = st.button(f"{p1} submits", key=f"con_b1_{attempt}", use_container_width=True)
    with col2:
        g2 = st.text_input(f"{p2}'s answer", key=f"con_p2_{attempt}", placeholder="Unscramble it...")
        b2 = st.button(f"{p2} submits", key=f"con_b2_{attempt}", use_container_width=True)

    if b1 and g1.strip().upper() == word:
        st.session_state.scores[0] += 10
        st.session_state.conundrum_winner = p1
        st.session_state.screen = "results"
        st.rerun()
    elif b2 and g2.strip().upper() == word:
        st.session_state.scores[1] += 10
        st.session_state.conundrum_winner = p2
        st.session_state.screen = "results"
        st.rerun()
    elif b1 or b2:
        st.error("Not quite! Keep trying.")

    if st.button("Nobody got it — move on", use_container_width=True):
        next_attempt = attempt + 1
        if next_attempt >= MAX_ATTEMPTS or s1 != s2:
            st.session_state.conundrum_winner = None
            st.session_state.screen = "results"
            st.rerun()
        else:
            st.session_state.conundrum_attempt = next_attempt
            st.rerun()
