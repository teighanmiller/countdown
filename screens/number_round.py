import streamlit as st
import streamlit.components.v1 as components

from lib.validator import evaluate_expression

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
    """Which number round (0, 1, 2)?"""
    r = st.session_state.current_round
    return r // 2


def _score_expr(result: int, target: int) -> int:
    diff = abs(result - target)
    if diff == 0:
        return 10
    if diff <= 5:
        return 7
    if diff <= 10:
        return 5
    return 0


def render():
    game = st.session_state.game
    r_idx = _round_index()
    round_data = game["numberRounds"][r_idx]
    available = round_data["available"]
    target = round_data["target"]
    phase = st.session_state.round_phase
    p1, p2 = st.session_state.players
    current_player = p1 if phase == "p1" else p2
    round_num = st.session_state.current_round + 1

    st.markdown(f"## Round {round_num} — Numbers")
    st.markdown(f"**{current_player}'s turn**")
    st.markdown("---")

    st.markdown(
        f"<div style='font-size:3.5rem;font-weight:bold;text-align:center;color:#FFD700;'>{target}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='text-align:center;color:#aaa;margin-bottom:1rem;'>Target</div>", unsafe_allow_html=True)

    # Number chips
    cols = st.columns(6)
    for i, col in enumerate(cols):
        col.markdown(
            f"<div style='font-size:1.8rem;font-weight:bold;text-align:center;"
            f"background:#16213e;border:2px solid #888;border-radius:8px;"
            f"padding:0.3rem;'>{available[i]}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")
    components.html(_TIMER_HTML.format(secs=TIMER_SECONDS), height=80)

    st.markdown("**Enter an expression using the numbers above (each at most once). Use +, -, *, /**")
    st.markdown("*Example: `75 * 4 + 25 - 3`*")

    expr_input = st.text_input(
        "Your expression", key=f"num_expr_{r_idx}_{phase}", placeholder="e.g. 75 + 25"
    )

    col_submit, col_pass = st.columns([2, 1])
    with col_submit:
        submitted = st.button("Submit", type="primary", use_container_width=True)
    with col_pass:
        passed = st.button("Pass (can't solve)", use_container_width=True)

    if submitted or passed:
        expr = expr_input.strip() if submitted else ""
        _handle_submission(expr, available, target, r_idx, phase, p1, p2, round_data, game)


def _handle_submission(expr, available, target, r_idx, phase, p1, p2, round_data, game):
    if expr:
        valid, result, reason = evaluate_expression(expr, available)
        if not valid:
            st.error(f"Invalid expression: {reason}")
            return
        pts = _score_expr(result, target)
        answer = {"expr": expr, "result": result, "score": pts}
    else:
        answer = {"expr": "—", "result": None, "score": 0}

    if phase == "p1":
        st.session_state.p1_answer = answer
        st.session_state.round_phase = "handoff_p2"
        st.rerun()
    else:
        st.session_state.p2_answer = answer
        _score_round(r_idx, p1, p2, round_data, game)


def render_handoff():
    p2 = st.session_state.players[1]

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
        "type": "number",
        "round": r_idx + 1,
        "available": round_data["available"],
        "target": round_data["target"],
        "solution": round_data["solutionPath"],
        "p1": p1_ans,
        "p2": p2_ans,
        "commentary": commentary,
    })

    st.session_state.round_phase = "scoring"
    st.session_state.screen = "round_result"
    st.rerun()
