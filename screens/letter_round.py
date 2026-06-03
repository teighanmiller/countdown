import streamlit as st
import streamlit.components.v1 as components

from lib.validator import check_word_from_letters

TIMER_SECONDS = 30

_TIMER_HTML = """
<div style="font-size:3rem;font-weight:bold;color:#FFD700;text-align:center;" id="t">{secs}</div>
<script>
  var t = {secs};
  var el = document.getElementById('t');
  var iv = setInterval(function() {{
    t--;
    el.textContent = t;
    if (t <= 0) {{ clearInterval(iv); el.textContent = "⏰"; el.style.color = "#ff4444"; }}
  }}, 1000);
</script>
"""


def _round_index() -> int:
    """Which letter round are we on (0, 1, 2)?"""
    r = st.session_state.current_round
    # Rounds 0,2,4 are letter rounds (0-indexed among all 6 rounds)
    # Letter round index = r // 2
    return r // 2


def render():
    game = st.session_state.game
    r_idx = _round_index()
    round_data = game["letterRounds"][r_idx]
    letters = round_data["letters"]
    phase = st.session_state.round_phase
    p1, p2 = st.session_state.players
    current_player = p1 if phase == "p1" else p2
    round_num = st.session_state.current_round + 1  # display as 1-based overall round

    st.markdown(f"## Round {round_num} — Letters")
    st.markdown(f"**{current_player}'s turn**")
    st.markdown("---")

    # Letter tiles
    cols = st.columns(9)
    for i, col in enumerate(cols):
        col.markdown(
            f"<div style='font-size:2.5rem;font-weight:bold;text-align:center;"
            f"background:#16213e;border:2px solid #FFD700;border-radius:8px;"
            f"padding:0.3rem;'>{letters[i].upper()}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")
    components.html(_TIMER_HTML.format(secs=TIMER_SECONDS), height=80)

    st.markdown("**Make the longest word you can from these letters.**")
    word_input = st.text_input(
        "Your word", key=f"letter_word_{r_idx}_{phase}", placeholder="Type here..."
    )

    col_submit, col_pass = st.columns([2, 1])
    with col_submit:
        submitted = st.button("Submit Word", type="primary", use_container_width=True)
    with col_pass:
        passed = st.button("Pass (no word)", use_container_width=True)

    if submitted or passed:
        word = word_input.strip() if submitted else ""
        _handle_submission(word, letters, r_idx, phase, p1, p2, round_data, game)


def _handle_submission(word, letters, r_idx, phase, p1, p2, round_data, game):
    if word:
        valid, reason = check_word_from_letters(word, letters)
        if not valid:
            st.error(f"Invalid: {reason}")
            return
        score = len(word)
    else:
        valid, score = True, 0

    if phase == "p1":
        st.session_state.p1_answer = {"word": word.upper() if word else "—", "score": score}
        st.session_state.round_phase = "handoff_p2"
        st.rerun()
    else:
        st.session_state.p2_answer = {"word": word.upper() if word else "—", "score": score}
        _score_round(r_idx, p1, p2, round_data, game)


def render_handoff():
    p2 = st.session_state.players[1]
    p1_ans = st.session_state.p1_answer
    r_idx = _round_index()
    letters = st.session_state.game["letterRounds"][r_idx]["letters"]

    st.markdown("## Hand the device to Player 2")
    st.markdown(f"**{p2}**, it's your turn. Don't let Player 1 peek!")
    st.markdown("---")
    if st.button(f"I'm {p2} — I'm ready", type="primary", use_container_width=True):
        st.session_state.round_phase = "p2"
        st.rerun()


def _score_round(r_idx, p1, p2, round_data, game):
    p1_ans = st.session_state.p1_answer
    p2_ans = st.session_state.p2_answer
    s1, s2 = p1_ans["score"], p2_ans["score"]

    if s1 > s2:
        st.session_state.scores[0] += s1
    elif s2 > s1:
        st.session_state.scores[1] += s2
    else:
        st.session_state.scores[0] += s1
        st.session_state.scores[1] += s2

    overall_round = st.session_state.current_round
    after_rounds = game["commentary"].get("afterRounds", [])
    commentary = after_rounds[overall_round] if overall_round < len(after_rounds) else ""

    st.session_state.round_results.append({
        "type": "letter",
        "round": r_idx + 1,
        "letters": round_data["letters"],
        "optimal": round_data["optimalWord"],
        "p1": p1_ans,
        "p2": p2_ans,
        "commentary": commentary,
    })

    st.session_state.round_phase = "scoring"
    st.session_state.screen = "round_result"
    st.rerun()
