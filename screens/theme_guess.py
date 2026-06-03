import streamlit as st

from lib.wikipedia_rag import similarity

_SCORE_THRESHOLDS = [
    (0.90, 10),
    (0.70, 7),
    (0.50, 4),
    (0.30, 2),
    (0.00, 0),
]

_TEMPERATURE = [
    (10, "🔥 On fire! You're extremely close."),
    (7,  "♨️  Very warm — you're on the right track."),
    (4,  "🌤️  Lukewarm — loosely connected."),
    (2,  "❄️  Cold — not quite there."),
    (0,  "🧊 Ice cold — way off!"),
]


def _pts_from_similarity(sim: float) -> int:
    for threshold, pts in _SCORE_THRESHOLDS:
        if sim >= threshold:
            return pts
    return 0


def _temperature_label(pts: int) -> str:
    for score, label in _TEMPERATURE:
        if pts >= score:
            return label
    return _TEMPERATURE[-1][1]


def render():
    game = st.session_state.game
    theme = game["theme"]
    p1, p2 = st.session_state.players
    phase = st.session_state.get("theme_guess_phase", "p1")

    st.markdown("## Theme Guess Round")
    st.markdown(
        f"**Category:** {game.get('themeCategory', 'General Knowledge')} — "
        "What's the hidden theme connecting all rounds?"
    )
    st.markdown("You'll find out how close you are right away, but the full reveal comes later.")
    st.markdown("---")

    if phase == "p1":
        _render_guess(p1, "theme_p1_guess", "theme_p1_score")
    elif phase == "handoff_p2":
        st.markdown(f"## Hand the device to {p2}")
        st.markdown(f"**{p2}**, it's your turn to guess the theme!")
        if st.button(f"I'm {p2} — I'm ready", type="primary", use_container_width=True):
            st.session_state.theme_guess_phase = "p2"
            st.rerun()
    elif phase == "p2":
        _render_guess(p2, "theme_p2_guess", "theme_p2_score")
    elif phase == "done":
        _show_scores(p1, p2, theme)


def _render_guess(player: str, input_key: str, score_key: str):
    theme = st.session_state.game["theme"]
    phase_key = "theme_guess_phase"

    st.markdown(f"**{player}**, what's your guess?")
    guess = st.text_input("Your guess", key=input_key, placeholder="e.g. The Space Race")

    if st.button("Submit Guess", type="primary", use_container_width=True):
        if not guess.strip():
            st.error("Please enter a guess.")
            return

        sim = similarity(guess.strip(), theme)
        pts = _pts_from_similarity(sim)

        if input_key == "theme_p1_guess":
            st.session_state.scores[0] += pts
            st.session_state.theme_p1_score = pts
            st.session_state.theme_p1_guess_text = guess.strip()
            st.session_state[phase_key] = "handoff_p2"
        else:
            st.session_state.scores[1] += pts
            st.session_state.theme_p2_score = pts
            st.session_state.theme_p2_guess_text = guess.strip()
            st.session_state[phase_key] = "done"

        st.rerun()


def _show_scores(p1: str, p2: str, theme: str):
    p1_pts = st.session_state.get("theme_p1_score", 0)
    p2_pts = st.session_state.get("theme_p2_score", 0)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{p1}**")
        st.markdown(f"Guess: *{st.session_state.get('theme_p1_guess_text', '—')}*")
        st.markdown(f"Score: **{p1_pts}/10**")
        st.info(_temperature_label(p1_pts))
    with col2:
        st.markdown(f"**{p2}**")
        st.markdown(f"Guess: *{st.session_state.get('theme_p2_guess_text', '—')}*")
        st.markdown(f"Score: **{p2_pts}/10**")
        st.info(_temperature_label(p2_pts))

    s1, s2 = st.session_state.scores
    st.markdown("---")
    st.markdown(f"**Scoreboard: {p1} {s1} — {s2} {p2}**")
    st.markdown("The theme will be revealed after the final round...")

    if st.button("Final Showdown →", type="primary", use_container_width=True):
        st.session_state.screen = "conundrum"
        st.rerun()
