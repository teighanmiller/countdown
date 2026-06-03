import time

import streamlit as st

from lib.validator import check_word_from_letters

SOLVE_SECONDS = 30
ANSWER_SECONDS = 10
TOTAL_SECONDS = SOLVE_SECONDS + ANSWER_SECONDS


@st.fragment(run_every=1)
def _timer_fragment():
    start_key = st.session_state.get("_active_start_key")
    if not start_key or start_key not in st.session_state:
        return

    e = time.time() - st.session_state[start_key]
    prev_phase = st.session_state.get("timer_phase", "solve")
    new_phase = "answer" if e >= SOLVE_SECONDS else "solve"

    if new_phase != prev_phase:
        st.session_state.timer_phase = new_phase
        st.rerun(scope="app")
        return

    if e >= TOTAL_SECONDS:
        st.rerun(scope="app")
        return

    if new_phase == "solve":
        remaining = max(0, SOLVE_SECONDS - int(e))
        st.markdown(
            f"<div style='font-size:3rem;font-weight:bold;color:#FFD700;text-align:center;'>{remaining}</div>"
            f"<div style='text-align:center;color:#aaa;margin-top:0.2rem;'>seconds to think</div>",
            unsafe_allow_html=True,
        )
    else:
        remaining = max(0, TOTAL_SECONDS - int(e))
        color = "#ff4444" if remaining <= 5 else "#ff8800"
        st.markdown(
            f"<div style='font-size:3rem;font-weight:bold;color:{color};text-align:center;'>{remaining}</div>"
            f"<div style='text-align:center;color:{color};font-weight:bold;margin-top:0.2rem;'>⚡ Type your answer now!</div>",
            unsafe_allow_html=True,
        )


def _round_index() -> int:
    r = st.session_state.current_round
    return r // 2


def render():
    game = st.session_state.game
    r_idx = _round_index()
    round_data = game["letterRounds"][r_idx]
    letters = round_data["letters"]
    phase = st.session_state.round_phase
    p1, p2 = st.session_state.players
    current_player = p1 if phase == "p1" else p2
    round_num = st.session_state.current_round + 1

    start_key = f"round_start_letter_{r_idx}_{phase}"
    if start_key not in st.session_state:
        st.session_state[start_key] = time.time()
        st.session_state.timer_phase = "solve"
    st.session_state._active_start_key = start_key

    elapsed = time.time() - st.session_state[start_key]

    if elapsed >= TOTAL_SECONDS:
        word = st.session_state.get(f"letter_word_{r_idx}_{phase}", "")
        _handle_submission(word.strip(), letters, r_idx, phase, p1, p2, round_data, game, auto=True)
        return

    in_answer_phase = st.session_state.get("timer_phase", "solve") == "answer"

    st.header(f"Round {round_num} — Letters", anchor=False)
    st.markdown(f"**{current_player}'s turn**")
    st.markdown("---")

    cols = st.columns(9)
    for i, col in enumerate(cols):
        col.markdown(
            f"<div style='font-size:2.5rem;font-weight:bold;text-align:center;"
            f"background:#16213e;border:2px solid #FFD700;border-radius:8px;"
            f"padding:0.3rem;'>{letters[i].upper()}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")
    _timer_fragment()
    st.markdown("")

    if in_answer_phase:
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
    else:
        st.info("Work out your answer — input unlocks when the timer reaches 0.")


def _handle_submission(word, letters, r_idx, phase, p1, p2, round_data, game, auto=False):
    if word:
        valid, reason = check_word_from_letters(word, letters)
        if not valid:
            if not auto:
                st.error(f"Invalid: {reason}")
                return
            word = ""
        score = len(word) if word else 0
    else:
        score = 0

    if phase == "p1":
        st.session_state.p1_answer = {"word": word.upper() if word else "—", "score": score}
        st.session_state.round_phase = "handoff_p2"
        st.rerun()
    else:
        st.session_state.p2_answer = {"word": word.upper() if word else "—", "score": score}
        _score_round(r_idx, p1, p2, round_data, game)


def render_handoff():
    p2 = st.session_state.players[1]

    st.header("Hand the device to Player 2", anchor=False)
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
