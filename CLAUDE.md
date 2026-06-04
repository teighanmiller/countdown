# Countdown — Project Notes for Claude

## What This Is
A two-player, pass-the-device web adaptation of the UK game show *Countdown*, built with Python + FastAPI + HTMX. An AI agent generates the entire game session around a hidden theme before play begins.

## Running the App
```bash
uv venv          # create env (Python 3.12)
uv pip install -r requirements.txt
source .venv/bin/activate
uvicorn main:app --reload
```
App runs at http://localhost:8000

## Environment Variables
- `OPENAI_API_KEY` — required. Set in a `.env` file or shell environment variable.

## LLM
`gpt-4.1-nano` via the OpenAI Python SDK (`openai`). Client is in `lib/llm_client.py` — `chat()` and `chat_json()` are the only two callsites; swapping models means changing `MODEL_ID` there.

## Key Architecture Decisions

### Screen Routing
`app.py` reads `st.session_state.screen` and delegates to the matching module in `screens/`. No actual Streamlit multi-page — all routing is via session state.

### Game Generation (two-step)
1. Small Claude call → picks theme + wikipedia query string
2. `lib/wikipedia_rag.py` fetches article, chunks, embeds with `sentence-transformers`
3. Full Claude call with top-5 retrieved Wikipedia passages as context → complete game JSON

### Word Validation
- `data/sowpods.txt` loaded as a Python `set` at import time in `lib/dictionary.py`
- Multiset letter check + SOWPODS lookup happen in `lib/validator.py`

### Numbers Solver
- `lib/solver.py` — recursive solver that tries all permutations/operator combos
- Used to validate Claude's number round solution paths before serving the session

### Semantic Similarity (theme guess round)
- `sentence-transformers` (`all-MiniLM-L6-v2`) encodes both the theme and player guesses
- Cosine similarity → points on a 0–10 scale (≥0.90 = 10pts, 0.70 = 7pts, etc.)
- Score shown immediately as a "temperature" hint without revealing the theme

## Game Flow
1. Setup (player names + difficulty: easy/medium/hard)
2. 3× Letter rounds (pass device, 30s timer, find longest word)
3. 3× Number rounds (pass device, 30s timer, arithmetic expression to hit target)
4. Theme guess (semantic similarity scoring)
5. Conundrum (scrambled 9-letter thematic word, first to answer wins)
6. Results + theme reveal + AI debrief

## Deployment
Streamlit Community Cloud — connect GitHub repo, set `OPENAI_API_KEY` in secrets, done.

## Dependencies
See `requirements.txt`. Key: `openai`, `streamlit`, `sentence-transformers`, `wikipedia`, `numpy`.
