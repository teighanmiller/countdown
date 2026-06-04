# Countdown — AI-Powered Game Show

A two-player, pass-the-device web adaptation of the UK game show *Countdown*. An AI agent generates the entire game session around a **hidden theme** before play begins — every letter set, every number puzzle, and the final conundrum word are thematically connected. Players know a theme exists and try to deduce it across 7 rounds, then guess it directly for bonus points.

**Designed for** word and puzzle fans — whether they grew up watching Countdown or are encountering the format for the first time.

## Live Demo

🔗 **[Play it here](https://countdown-ai.streamlit.app)**

## How to Run Locally

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/teighanmiller/countdown.git
cd countdown
uv sync
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

Add your API key to `.streamlit/secrets.toml` (create this file — it's gitignored):
```toml
OPENAI_API_KEY = "sk-..."
```

Run the app:
```bash
streamlit run app.py
```

## Deploying to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select your repo
3. Set `app.py` as the main file
4. Add `OPENAI_API_KEY` under **Advanced settings → Secrets**
5. Deploy — that's it

---

## System Write-Up

### Why This Design

The core design challenge was making AI feel *load-bearing*, not decorative. Any game could add an AI chatbot — the goal here was to make a game that structurally *cannot exist* without generative AI. The solution: AI generates the entire session before play begins, weaving a hidden theme through every puzzle. Players don't know the theme; deducing it from the letter sets and number targets is the meta-game that runs alongside the official Countdown rules.

### How AI Is Used (`gpt-4.1-nano` via OpenAI API)

AI drives three distinct functions, each serving the experience rather than just being present:

**1 — Theme selection:** A lightweight call picks a theme calibrated to the chosen difficulty. Easy = broad topics anyone knows (Animals, Weather); Hard = narrow, niche subjects (a specific athlete's record-breaking season, a single album). Difficulty doesn't just change which words appear — it changes *what knowledge the game tests*.

**2 — Wikipedia RAG + game generation:** The Wikipedia article for the theme is fetched live, chunked into ~200-word passages, and embedded with `sentence-transformers` (`all-MiniLM-L6-v2`). The top 5 most relevant passages are retrieved and injected into a second AI call that generates the complete game — letter sets, number targets (drawn from real facts in the article), the conundrum word, and all round commentary — grounded in verifiable Wikipedia text. This RAG step is what makes the number targets meaningful: they're real figures (years, statistics, counts) rather than arbitrary numbers.

**3 — Theme guess scoring:** At the end of play, both players guess the hidden theme in writing. Their guesses are embedded with the same sentence transformer and compared to the actual theme via cosine similarity. This means a guess of "The Beatles" scores highly against a theme of "The Fab Four" — capturing semantic closeness, not just exact match. Score bands: ≥0.90 = 10pts, ≥0.70 = 7pts, ≥0.50 = 4pts, ≥0.30 = 2pts.

### How Data Is Used

| Source | Role |
|---|---|
| `data/sowpods.txt` (270k words) | Word validation for all letter rounds — checked as a Python `set` for O(1) lookup |
| Wikipedia (via `wikipedia` Python package) | Live article text fetched per game — grounds all facts, targets, and commentary in real-world content |
| `sentence-transformers` (`all-MiniLM-L6-v2`) | Runs locally; embeds Wikipedia passages for retrieval and powers theme-guess semantic scoring |

The SOWPODS list (the official Scrabble dictionary) is the dataset that makes letter rounds fair: the game only awards points for real words, validated against 270,000 entries in under a millisecond.

### Dynamic Behavior

Every game is different by construction. There are three sources of variation:

1. **Difficulty controls specificity** — Easy themes produce puzzles testing general knowledge; Hard themes test niche expertise. The AI is explicitly prompted to match theme obscurity to difficulty level, so the game adapts meaningfully to who's playing.

2. **Wikipedia is live** — The article for a theme is fetched fresh at game time, not cached. A game about an ongoing topic (a current athlete, a recent film) will reflect the latest article text. The same theme can produce a measurably different game on a different day if the article has been updated — number targets, key facts, and commentary all flow from the retrieved passages.

3. **Randomness within constraints** — Letter padding and scrambling are randomised per session; the AI is instructed to avoid repeating example themes, so repeated plays trend toward novel topics.

### Game Structure

1. **Setup** — Enter player names and choose difficulty (Easy / Medium / Hard)
2. **3 × Letter rounds** — Find the longest valid word from 9 AI-curated letters (30s to think, 10s to answer; pass-device between players)
3. **3 × Number rounds** — Hit a thematic target number using arithmetic on 6 available numbers (same timing; targets are real facts from Wikipedia)
4. **Theme guess** — Both players write their best guess at the hidden theme; scored by semantic similarity
5. **Conundrum** — Unscramble a 9-letter thematic word; first correct answer wins 10 pts. If scores are tied and nobody solves it, the word is rescrambled and replayed — up to 3 attempts (fully implemented)
6. **Results** — Final scores, theme reveal, and AI-generated explanation of how each round connected to the theme

### Key Architectural Decisions

**Session-state routing over multi-page Streamlit** — All navigation is driven by `st.session_state.screen`. This keeps the app a single deployable file with no URL routing complexity, while giving full control over transitions and pass-device handoffs.

**Two-step generation with RAG** — Splitting theme selection (cheap, fast) from full game generation (expensive, RAG-grounded) means the theme can be validated before committing to the full generation cost, and the Wikipedia context keeps the AI's output factually anchored rather than hallucinated.

**Local embeddings** — Using `sentence-transformers` locally (rather than an embedding API) keeps latency low for both RAG retrieval and theme-guess scoring, and avoids a second paid API dependency.

**Fragment-based timers** — Streamlit's `@st.fragment(run_every=1)` drives the round countdown. The timer fragment owns the full answer-phase UI (input + buttons) to avoid full-app reruns mid-round, which would cause visible grey-screen flashes.

### Tools Used

- **Python 3.12** + **uv** — dependency management
- **Streamlit** — UI framework and deployment target (Streamlit Community Cloud)
- **OpenAI Python SDK** — `gpt-4.1-nano` for theme selection and game generation
- **sentence-transformers** (`all-MiniLM-L6-v2`) — local embeddings for RAG and semantic scoring
- **wikipedia** Python package — live article fetching
- **numpy** — cosine similarity computation

## Project Structure

```
app.py                 # Streamlit entry point — screen router
screens/               # One module per game screen
  setup.py             # Player names + difficulty
  loading.py           # Game generation with live progress
  intro.py             # Theme category announcement
  letter_round.py      # Letter round UI + pass-device flow
  number_round.py      # Number round UI + pass-device flow
  round_result.py      # Post-round score + commentary
  theme_guess.py       # Semantic similarity theme guessing
  conundrum.py         # Final scrambled word
  results.py           # Scores + theme reveal + debrief
lib/
  llm_client.py        # OpenAI API wrapper (gpt-4.1-nano)
  game_generator.py    # Two-step generation pipeline
  wikipedia_rag.py     # Fetch → chunk → embed → retrieve
  dictionary.py        # SOWPODS word set loader
  validator.py         # Word + arithmetic expression validation
  solver.py            # Countdown numbers solver (fallback validation)
data/
  sowpods.txt          # English word list (270k words)
```
