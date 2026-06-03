# Countdown — AI-Powered Game Show

A two-player, pass-the-device web adaptation of the UK game show *Countdown*. An AI agent generates the entire game session around a **hidden theme** before play begins — every letter set, every number puzzle, and the final conundrum word are thematically connected. Players know a theme exists and try to deduce it. At the end, they guess for bonus points scored by semantic similarity.

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

## How It Works

### Game Structure
1. **Setup** — Enter player names and choose theme difficulty (Easy / Medium / Hard)
2. **3 × Letter rounds** — Find the longest word from 9 AI-curated letters (30s each, pass-device)
3. **3 × Number rounds** — Hit a target number using arithmetic on 6 AI-chosen numbers (30s each, pass-device)
4. **Theme guess** — Each player guesses the hidden theme; scored by semantic similarity (0–10 pts)
5. **Conundrum** — Unscramble a 9-letter thematic word for 10 pts; tied games repeat up to 3×
6. **Results** — Full theme reveal with explanations for how each round connected

### AI Usage (`gpt-4.1-nano` via OpenAI API)

**Step 1 — Theme selection:** A small call picks a theme at the right specificity for the chosen difficulty.

**Step 2 — Wikipedia RAG + game generation:** The Wikipedia article for the theme is fetched, chunked into ~200-word passages, and embedded with `sentence-transformers` (`all-MiniLM-L6-v2`). The top 5 most relevant passages are retrieved and injected into a second call that generates the full game — letter sets, number targets, the conundrum word, and all commentary — grounded in real Wikipedia text.

**Theme guess scoring:** Player guesses are embedded with the same sentence transformer and compared to the actual theme via cosine similarity. Score bands: ≥0.90 = 10pts, ≥0.70 = 7pts, ≥0.50 = 4pts, ≥0.30 = 2pts.

### Data

| Source | Role |
|---|---|
| `data/sowpods.txt` (270k words) | Word validation for letter rounds |
| Wikipedia (via `wikipedia` Python package) | Live article text fetched per game — grounds all AI-generated facts and commentary |
| `sentence-transformers` (`all-MiniLM-L6-v2`) | Embeds Wikipedia passages for retrieval; also powers theme guess semantic scoring |

Wikipedia is continuously updated, so the game content is genuinely dynamic — a game about an ongoing topic will reflect the latest article text.

### Dynamic Behavior

Every game is unique: the AI selects a fresh theme each session, pulling the current version of its Wikipedia article. Difficulty controls how obscure the theme is (broad categories on Easy, niche topics on Hard), so the game adapts to the players' knowledge level. Because Wikipedia reflects real-world events as they happen, a game themed around an ongoing topic will use up-to-date facts.

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

## Tech Stack

- **Python 3.12** + **uv** for dependency management
- **Streamlit** — UI and deployment
- **OpenAI Python SDK** — `gpt-4.1-nano` for game generation and theme selection
- **sentence-transformers** — local embeddings (`all-MiniLM-L6-v2`)
- **wikipedia** — live article fetching
- **numpy** — cosine similarity
