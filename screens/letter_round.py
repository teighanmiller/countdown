import time

import streamlit as st
import streamlit.components.v1 as components

from lib.validator import check_word_from_letters
from lib.wikipedia_rag import preload_model

SOLVE_SECONDS = 30
ANSWER_SECONDS = 10
TOTAL_SECONDS = SOLVE_SECONDS + ANSWER_SECONDS


def _countdown_html(total_remaining: int) -> str:
    if total_remaining > ANSWER_SECONDS:
        init_num = total_remaining - ANSWER_SECONDS
        init_color = "#FFD700"
        init_msg = "seconds to think"
        init_msg_color = "#aaa"
    elif total_remaining > 0:
        init_num = total_remaining
        init_color = "#ff4444" if total_remaining <= 5 else "#ff8800"
        init_msg = "⚡ Type your answer now!"
        init_msg_color = init_color
    else:
        init_num = "⏰"
        init_color = "#ff4444"
        init_msg = "Time’s up — submit what you have!"
        init_msg_color = "#ff4444"

    return f"""
<div style="text-align:center;padding:0.25rem 0;">
  <div style="font-size:3rem;font-weight:bold;color:{init_color};line-height:1;" id="lr_t">{init_num}</div>
  <div style="margin-top:0.3rem;font-weight:bold;color:{init_msg_color};" id="lr_m">{init_msg}</div>
</div>
<script>
(function(){{
  var rem={total_remaining};
  var el=document.getElementById('lr_t');
  var ml=document.getElementById('lr_m');
  if(!el||!ml)return;
  var iv=setInterval(function(){{
    rem--;
    if(rem<0){{clearInterval(iv);return;}}
    if(rem>{ANSWER_SECONDS}){{
      el.textContent=rem-{ANSWER_SECONDS};
      el.style.color='#FFD700';
      ml.textContent='seconds to think';
      ml.style.color='#aaa';
    }}else if(rem>0){{
      var c=rem<=5?'#ff4444':'#ff8800';
      el.textContent=rem;
      el.style.color=c;
      ml.textContent='⚡ Type your answer now!';
      ml.style.color=c;
    }}else{{
      el.textContent='⏰';
      el.style.color='#ff4444';
      ml.textContent='Time’s up — submit what you have!';
      ml.style.color='#ff4444';
    }}
  }},1000);
}})();
</script>
"""


@st.fragment(run_every=5)
def _auto_submit_watcher():
    if st.session_state.get("screen") != "letter":
        return
    if st.session_state.get("round_phase") not in ("p1", "p2"):
        return
    start_key = st.session_state.get("_active_start_key")
    if not start_key or start_key not in st.session_state:
        return
    if time.time() - st.session_state[start_key] >= TOTAL_SECONDS:
        st.rerun()


def _round_index() -> int:
    return st.session_state.current_round // 2


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
        if not st.session_state.get("_model_preload_started"):
            st.session_state._model_preload_started = True
            preload_model()
    st.session_state._active_start_key = start_key

    elapsed = time.time() - st.session_state[start_key]
    if elapsed >= TOTAL_SECONDS:
        word = st.session_state.get(f"letter_word_{r_idx}_{phase}", "")
        _handle_submission(word.strip(), letters, r_idx, phase, p1, p2, round_data, game, auto=True)
        return

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
    total_remaining = max(0, int(TOTAL_SECONDS - elapsed))
    components.html(_countdown_html(total_remaining), height=90)
    st.markdown("")

    word_input = st.text_input(
        "Your word", key=f"letter_word_{r_idx}_{phase}", placeholder="Type here when ready..."
    )
    col_submit, col_pass = st.columns([2, 1])
    with col_submit:
        submitted = st.button("Submit Word", type="primary", use_container_width=True)
    with col_pass:
        passed = st.button("Pass (no word)", use_container_width=True)

    if submitted or passed:
        word = word_input.strip() if submitted else ""
        _handle_submission(word, letters, r_idx, phase, p1, p2, round_data, game)

    _auto_submit_watcher()


def render_handoff():
    p2 = st.session_state.players[1]

    st.header("Hand the device to Player 2", anchor=False)
    st.markdown(f"**{p2}**, it's your turn. Don't let Player 1 peek!")
    st.markdown("---")
    if st.button(f"I'm {p2} — I'm ready", type="primary", use_container_width=True):
        st.session_state.round_phase = "p2"
        st.rerun()


def _handle_submission(word, letters, r_idx, phase, p1, p2, round_data, game, auto=False):
    if word:
        valid, _ = check_word_from_letters(word, letters)
        score = len(word) if valid else 0
    else:
        score = 0

    if phase == "p1":
        st.session_state.p1_answer = {"word": word.upper() if word else "—", "score": score}
        st.session_state.round_phase = "handoff_p2"
        st.rerun()
    else:
        st.session_state.p2_answer = {"word": word.upper() if word else "—", "score": score}
        _score_round(r_idx, p1, p2, round_data, game)


def _score_round(r_idx, p1, p2, round_data, game):
    p1_ans = st.session_state.p1_answer
    p2_ans = st.session_state.p2_answer
    s1, s2 = p1_ans["score"], p2_ans["score"]

    if s1 > 0:
        st.session_state.scores[0] += s1
    if s2 > 0:
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
