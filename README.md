# Countdown — AI-Powered Game Show

A two-player web adaptation of the UK game show *Countdown*. Before play begins, an AI agent picks a secret theme and builds the entire game around it — every letter set, every number target, and the final conundrum word are thematically connected. Players try to deduce the theme across 7 rounds, then guess it directly for bonus points.

**[Play it here →](https://your-deployment-url.com)**

---

## Running Locally

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/teighanmiller/countdown.git
cd countdown
uv sync
source .venv/bin/activate
```

Create a `.env` file in the project root:
```
OPENAI_API_KEY=sk-...
```

```bash
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

## Deploying

Standard ASGI app — Railway, Render, and Fly.io all work out of the box. Set `OPENAI_API_KEY` as an environment variable and use this start command:

```
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```

`--workers 1` is required since sessions are held in memory.

---

## Write-Up

### What it is

Countdown is a British game show where two contestants race to find long words from a random set of letters and hit target numbers using arithmetic. This version adds a hidden theme that connects every puzzle in a session — the letters and numbers aren't just random, they're chosen because they relate to something. Players don't know the theme until the end, and guessing it correctly is worth points.

The whole thing is designed for two people on one device, passing it back and forth — hence the handoff screens between each player's turn.

### How AI is used

AI is load-bearing here, not decorative. The game literally cannot exist without it — there's no pre-generated content, no template-filling. Every session is created from scratch.

It works in two steps. First, a small call to `gpt-4.1-nano` picks a theme matched to the chosen difficulty — broad and familiar on Easy (Animals, Weather), narrow and specific on Hard (a single album, a specific athlete's season). Then a second, larger call generates the complete game: the optimal words for each letter round, the number targets, the conundrum word, and all the commentary. That second call is grounded in real Wikipedia content (more on that below), which is what makes the number targets meaningful rather than arbitrary.

At the end, both players type a free-text guess at the theme. Rather than checking for an exact match, their guesses are embedded with `sentence-transformers` and scored by cosine similarity against the real theme. "The Fab Four" gets nearly full marks against "The Beatles." This makes the guessing round genuinely playable — you get credit for being in the right area even if you don't nail the exact phrasing.

### How data is used

Two datasets drive the game:

**SOWPODS** (270,000 words) — the official international Scrabble dictionary. Every word a player submits in a letter round is validated against this list. It's loaded as a Python `set` at startup so lookups are O(1). Without it, the game has no fair way to judge whether a word is real.

**Wikipedia** — fetched live for each game. Once the theme is chosen, the relevant Wikipedia article is pulled, chunked into ~200-word passages, and embedded locally. The top 5 most relevant passages are retrieved and injected into the game generation prompt. This is what grounds the number targets in real facts — a game about the Apollo 13 mission uses actual mission statistics as targets, not made-up numbers. Because articles are fetched fresh every time, a game about an ongoing topic will reflect the latest version of that article.

### Dynamic behavior

No two games are the same. The theme is picked fresh each time and the AI is instructed to avoid repeating examples. Wikipedia is fetched live so a game about a current event can change day-to-day as articles are updated. Difficulty meaningfully changes the experience — not just which words appear, but what knowledge domain the whole game tests. A Hard game about a specific album requires a different kind of thinking than an Easy game about Weather.

### Architectural decisions

The app is built on **FastAPI + HTMX** with Jinja2 templates. Navigation is standard POST-redirect-GET; timers are plain JavaScript `setInterval`. There are no WebSockets anywhere, which keeps the app simple and eliminates the reconnection issues that come with persistent connections. Sessions live server-side in a dict (UUID cookie), which handles the pass-the-device flow cleanly — both players' state is on the server, not split across two browsers.

Game generation runs in a background thread. The loading screen polls `/loading/poll` via HTMX every 2 seconds; when the game is ready, the server returns an `HX-Redirect` header and the page moves on automatically.

The generation pipeline is split in two deliberately: a cheap theme-selection call first, then an expensive generation call only once the theme is validated. Wikipedia retrieval uses local `sentence-transformers` embeddings rather than an API, which keeps latency low and avoids a second paid dependency.

### Tools

Python 3.12, uv, FastAPI, Jinja2, HTMX, uvicorn, OpenAI Python SDK (`gpt-4.1-nano`), sentence-transformers (`all-MiniLM-L6-v2`), wikipedia, numpy.

---

## Project Structure

```
main.py          — FastAPI routes, session management, scoring logic
lib/
  game_generator.py   — two-step AI generation pipeline
  llm_client.py       — OpenAI wrapper
  wikipedia_rag.py    — fetch, chunk, embed, retrieve
  validator.py        — word and expression validation
  solver.py           — numbers round solver (used to verify AI solutions)
  dictionary.py       — SOWPODS loader
templates/       — Jinja2 templates, one per screen
static/          — CSS (dark gold theme)
data/
  sowpods.txt    — 270k-word English dictionary
```
