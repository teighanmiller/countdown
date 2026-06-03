from __future__ import annotations

import random
import re

from lib.claude_client import chat_json
from lib.dictionary import is_valid_word
from lib.solver import solve
from lib.validator import evaluate_expression
from lib.wikipedia_rag import fetch_and_embed, retrieve

DIFFICULTY_PROMPT = {
    "easy": "Choose a broad, well-known theme (e.g. 'Animals', 'Sports', 'Food', 'Music', 'Weather', 'Travel') — but do NOT reuse these exact examples; pick something fresh. Clues should be obvious.",
    "medium": "Choose a moderately specific theme (e.g. 'The Olympic Games', 'Dinosaurs', 'Classic Rock'). Clues should be inferrable.",
    "hard": "Choose a narrow, niche theme (e.g. 'Michael Jordan's 1996 season', 'The Apollo 13 mission', 'Led Zeppelin's IV album'). Clues should be subtle.",
}

THEME_SYSTEM = """You are a game show producer for Countdown, an AI-powered word and number game.
Your task is to pick a theme for today's game.
Respond with ONLY a JSON object — no markdown, no explanation."""

GAME_SYSTEM = """You are a creative game show producer for Countdown, an AI-powered word and number game.
You are building a complete themed game session. All letter sets and number puzzles must be connected to the hidden theme.
The player knows a theme exists but not what it is.
Respond with ONLY a JSON object — no markdown, no explanation."""


def _scramble(word: str) -> str:
    chars = list(word.upper())
    for _ in range(10):
        random.shuffle(chars)
        if "".join(chars) != word.upper():
            break
    return "".join(chars)


def _validate_letter_round(round_data: dict) -> bool:
    optimal = round_data.get("optimalWord", "").upper()
    return 7 <= len(optimal) <= 9 and is_valid_word(optimal)


def _has_longer_word(letters: list[str], min_len: int) -> bool:
    """Return True if any valid dictionary word longer than min_len can be formed from letters."""
    from collections import Counter
    from lib.dictionary import all_words
    avail = Counter(l.upper() for l in letters)
    for w in all_words():
        if len(w) <= min_len:
            continue
        needed = Counter(w)
        if all(avail[ch] >= cnt for ch, cnt in needed.items()):
            return True
    return False


def _pad_letters(word: str) -> list[str]:
    """Pad word to 9 letters with safe letters that don't allow any longer valid word."""
    letters = list(word.upper())
    needed = 9 - len(letters)
    if needed <= 0:
        return letters

    candidates = list("BCDFGHJKLMNPQRSTVWXYZ")
    for _ in range(needed):
        random.shuffle(candidates)
        for c in candidates:
            if not _has_longer_word(letters + [c], len(word)):
                letters.append(c)
                break
        else:
            letters.append(random.choice(list(word.upper())))
    return letters


def _validate_number_round(round_data: dict) -> bool:
    available = round_data.get("available", [])
    target = round_data.get("target")
    solution = round_data.get("solutionPath", "")
    if len(available) != 6 or not target or not solution:
        return False
    valid, result, _ = evaluate_expression(solution, available)
    if valid and result == target:
        return True
    # Fall back to solver verification
    solvable, found_expr = solve(available, target)
    if solvable:
        round_data["solutionPath"] = found_expr
    return solvable


def generate_theme(difficulty: str, today: str) -> dict:
    """Step 1: Pick a theme. Returns {theme, wikipedia_query, themeCategory}."""
    diff_desc = DIFFICULTY_PROMPT[difficulty]
    user = f"""Today is {today}. {diff_desc}

Return a JSON object with exactly these keys:
{{
  "theme": "<specific theme name>",
  "wikipedia_query": "<best Wikipedia search query for this theme>",
  "themeCategory": "<broad category shown to players, e.g. 'History', 'Science', 'Pop Culture'>"
}}"""
    return chat_json(THEME_SYSTEM, user, max_tokens=256)


def generate_game_session(
    theme_data: dict, wiki_context: list[str], difficulty: str
) -> dict:
    """Step 2: Generate full game session grounded in Wikipedia context."""
    theme = theme_data["theme"]
    category = theme_data.get("themeCategory", "General Knowledge")
    context_block = "\n\n".join(
        f"[Wikipedia excerpt {i+1}]:\n{c}" for i, c in enumerate(wiki_context)
    )

    difficulty_word_guidance = {
        "easy": (
            "Choose optimalWords that are COMMON, EVERYDAY English words players will recognise immediately once unscrambled — "
            "things like STARFISH, CALENDAR, FOOTBALL, MOUNTAIN. No specialist vocabulary, scientific names, or archaic words."
        ),
        "medium": "Choose optimalWords clearly connected to the theme but needing some knowledge to place — recognisable once seen, but not the first word that comes to mind.",
        "hard": "Choose optimalWords with subtle or indirect thematic connections that only an expert would spot. Obscure but valid dictionary words are fine.",
    }[difficulty]

    user = f"""Theme: {theme}
Category shown to players: {category}
Difficulty: {difficulty}

Wikipedia context (use this to ground all facts and numbers):
{context_block}

Generate a complete Countdown game session as JSON with exactly this structure:
{{
  "theme": "{theme}",
  "themeCategory": "{category}",
  "letterRounds": [
    {{
      "optimalWord": "<a valid English dictionary word, 7-9 letters, with a strong thematic connection — see word guidance below>",
      "themeConnection": "<1 sentence explaining the connection, revealed at end>"
    }},
    ... (3 total letter rounds, each with a DIFFERENT optimalWord)
  ],
  "numberRounds": [
    {{
      "available": [<6 integers: small numbers 1-10, large numbers only from 25/50/75/100>],
      "target": <integer from Wikipedia context that is meaningfully associated with the theme>,
      "solutionPath": "<arithmetic expression that equals target using only the available numbers, each at most once>",
      "themeConnection": "<1 sentence: why this number relates to the theme>"
    }},
    ... (3 total number rounds)
  ],
  "conundrum": {{
    "word": "<9-letter word — the single most iconic word associated with the theme>",
    "themeConnection": "<1 sentence explaining the connection>"
  }},
  "commentary": {{
    "intro": "<1-2 sentences: tell players a hidden theme connects all 7 rounds and they should try to spot it. Do NOT hint at the subject matter at all.>",
    "afterRounds": ["<witty 1-sentence comment purely about the players' gameplay — no thematic content whatsoever>", ... (exactly 6 strings)],
    "themeReveal": "<dramatic 2-3 sentence reveal of the theme with a fun fact from the Wikipedia context>",
    "winMessage": "<fun 1-sentence congratulations for the winner, use {{winner}} as placeholder>"
  }}
}}

Word guidance for letter rounds: {difficulty_word_guidance}

Hard rules:
- 'optimalWord' must be exactly 7, 8, or 9 letters — prefer 8 or 9 where possible
- 'optimalWord' must be a real English dictionary word (no proper nouns, no abbreviations)
- Number round 'available' must be exactly 6 integers; large numbers ONLY from the set {{25, 50, 75, 100}}
- 'solutionPath' must evaluate exactly to 'target' using only +, -, *, / and the available numbers (each at most once)
- Conundrum 'word' must be exactly 9 letters and a real English dictionary word
- 'afterRounds' must contain exactly 6 strings — one per round
- CRITICAL commentary rule: 'intro' and every 'afterRounds' string must contain ZERO thematic content. No subject hints, no topic words, no category clues. Pure gameplay commentary only. Players are guessing the theme themselves."""

    return chat_json(GAME_SYSTEM, user, max_tokens=2048)


def _sanitize_commentary(session: dict) -> dict:
    """Strip any mention of the theme from commentary shown before the reveal."""
    theme = session.get("theme", "")
    if not theme:
        return session

    # Build a set of words to watch for (theme words longer than 3 chars)
    theme_words = {w.lower() for w in theme.split() if len(w) > 3}
    commentary = session.get("commentary", {})

    def _redact(text: str) -> str:
        if not text:
            return text
        lower = text.lower()
        # If the full theme phrase appears, replace with a generic line
        if theme.lower() in lower:
            return "What a round! Keep your eyes on those letters and numbers."
        # If any prominent theme word appears, replace that sentence
        for word in theme_words:
            if word in lower:
                return "Excellent play — stay focused, the best is yet to come!"
        return text

    commentary["intro"] = _redact(commentary.get("intro", ""))
    commentary["afterRounds"] = [_redact(c) for c in commentary.get("afterRounds", [])]
    session["commentary"] = commentary
    return session


def _repair_session(session: dict, attempts: int = 2) -> dict:
    """Validate and fix invalid rounds in the session."""
    for lr in session.get("letterRounds", []):
        word = lr.get("optimalWord", "").upper()
        if not (7 <= len(word) <= 9 and is_valid_word(word)):
            word = "TELESCOPE"
        lr["optimalWord"] = word
        padded = _pad_letters(word)
        random.shuffle(padded)
        lr["letters"] = padded

    for i, nr in enumerate(session.get("numberRounds", [])):
        if not _validate_number_round(nr):
            available = nr.get("available", [25, 50, 75, 100, 6, 3])
            solvable, expr = solve(available, nr.get("target", 100))
            if solvable:
                session["numberRounds"][i]["solutionPath"] = expr
            else:
                session["numberRounds"][i]["target"] = 100
                session["numberRounds"][i]["solutionPath"] = "100"
                session["numberRounds"][i]["available"] = [25, 50, 75, 100, 6, 3]

    conundrum = session.get("conundrum", {})
    word = conundrum.get("word", "")
    if len(word) != 9 or not is_valid_word(word):
        session["conundrum"]["word"] = "TELESCOPE"
    session["conundrum"]["scrambled"] = _scramble(session["conundrum"]["word"])
    return session


def _find_valid_word_for_letters(letters: list[str]) -> tuple[bool, str]:
    """Try to find the longest valid word formable from the given letters."""
    from collections import Counter
    from lib.dictionary import all_words

    avail = Counter(l.upper() for l in letters)
    best = ""
    for word in all_words():
        needed = Counter(word)
        if all(avail[ch] >= cnt for ch, cnt in needed.items()):
            if len(word) > len(best):
                best = word
    return bool(best), best


def build_game(difficulty: str, today: str) -> dict:
    """Full two-step generation pipeline. Returns validated game session."""
    # Step 1: theme
    theme_data = generate_theme(difficulty, today)

    # Step 2: fetch Wikipedia + embed
    chunks, embeddings = fetch_and_embed(theme_data["wikipedia_query"])
    context = retrieve(
        f"numeric facts, key events, and important words related to {theme_data['theme']}",
        chunks,
        embeddings,
        top_k=5,
    )

    # Step 3: generate full session with Wikipedia context
    session = generate_game_session(theme_data, context, difficulty)
    session = _repair_session(session)
    session = _sanitize_commentary(session)

    # Store wiki assets for theme-guess scoring later
    session["_wiki_chunks"] = chunks
    session["_wiki_embeddings"] = embeddings.tolist()

    return session
