from __future__ import annotations

import threading
import uuid
from datetime import date

from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

# ── server-side session store ─────────────────────────────────────────────────

_SESSIONS: dict[str, dict] = {}


class _SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        sid = request.cookies.get("_sid")
        if not sid or sid not in _SESSIONS:
            sid = str(uuid.uuid4())
            _SESSIONS[sid] = {}
        request.state.session = _SESSIONS[sid]
        response = await call_next(request)
        response.set_cookie("_sid", sid, httponly=True, samesite="lax", max_age=86400)
        return response


# ── app setup ─────────────────────────────────────────────────────────────────

app = FastAPI()
app.add_middleware(_SessionMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── background game generation ────────────────────────────────────────────────

_JOBS: dict[str, dict] = {}


def _run_game(job_id: str, difficulty: str) -> None:
    from lib.game_generator import build_game

    def _step(msg: str):
        _JOBS[job_id]["messages"].append(msg)

    try:
        game = build_game(difficulty, str(date.today()), on_progress=_step)
        game.pop("_wiki_chunks", None)
        game.pop("_wiki_embeddings", None)
        _JOBS[job_id]["game"] = game
        _JOBS[job_id]["status"] = "done"
    except Exception as exc:
        _JOBS[job_id]["error"] = str(exc)
        _JOBS[job_id]["status"] = "error"


# ── helpers ───────────────────────────────────────────────────────────────────


def _sess(request: Request) -> dict:
    return request.state.session


def _t(request: Request, name: str, ctx: dict | None = None):
    """Shorthand for TemplateResponse with the Starlette 1.x (request-first) API."""
    return templates.TemplateResponse(request, name, ctx or {})


def _round_type(current_round: int) -> str:
    return "letter" if current_round % 2 == 0 else "number"


def _round_index(current_round: int) -> int:
    return current_round // 2


def _score_word(word: str, letters: list[str]) -> tuple[str, int]:
    from lib.validator import check_word_from_letters

    word = word.upper()
    valid, _ = check_word_from_letters(word, letters)
    return (word if valid else f"(invalid: {word})", len(word) if valid else 0)


def _score_expr(expr: str, available: list[int], target: int) -> tuple[str, int]:
    from lib.validator import evaluate_expression

    valid, value, _ = evaluate_expression(expr, available)
    if not valid or value is None:
        return (f"(invalid: {expr})", 0)
    diff = abs(value - target)
    if diff == 0:
        score = 10
    elif diff <= 5:
        score = 7
    elif diff <= 10:
        score = 5
    else:
        score = 0
    return (expr, score)


def _temperature_label(sim: float) -> str:
    if sim >= 0.90:
        return "On fire!"
    elif sim >= 0.70:
        return "Warm"
    elif sim >= 0.50:
        return "Lukewarm"
    elif sim >= 0.30:
        return "Cold"
    else:
        return "Ice cold"


# ── setup ─────────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def page_setup(request: Request):
    return _t(request, "setup.html", {"error": None})


@app.post("/setup")
async def handle_setup(
    request: Request,
    p1: str = Form(...),
    p2: str = Form(...),
    difficulty: str = Form(default="medium"),
):
    p1, p2 = p1.strip(), p2.strip()
    if not p1 or not p2:
        return _t(request, "setup.html", {"error": "Both player names are required."})

    job_id = str(uuid.uuid4())
    _JOBS[job_id] = {"status": "running", "messages": [], "game": None, "error": None}

    s = _sess(request)
    s.clear()
    s.update(
        players=[p1, p2],
        difficulty=difficulty,
        job_id=job_id,
        scores=[0, 0],
        current_round=0,
        round_phase="p1",
        round_results=[],
        theme_guess_phase="p1",
    )

    threading.Thread(target=_run_game, args=(job_id, difficulty), daemon=True).start()
    return RedirectResponse("/loading", status_code=303)


# ── loading ───────────────────────────────────────────────────────────────────


@app.get("/loading", response_class=HTMLResponse)
async def page_loading(request: Request):
    if "job_id" not in _sess(request):
        return RedirectResponse("/", status_code=303)
    return _t(request, "loading.html")


@app.get("/loading/poll", response_class=HTMLResponse)
async def poll_loading(request: Request):
    s = _sess(request)
    job_id = s.get("job_id")
    if not job_id or job_id not in _JOBS:
        return HTMLResponse('<p class="error">Session error. <a href="/">Start over</a></p>')

    job = _JOBS[job_id]

    if job["status"] == "done":
        s["game"] = job["game"]
        del _JOBS[job_id]
        return HTMLResponse("", headers={"HX-Redirect": "/intro"})

    if job["status"] == "error":
        msg = job["error"]
        del _JOBS[job_id]
        return HTMLResponse(
            f'<p class="error">Generation failed: {msg}</p>'
            '<br><a href="/" class="btn">Try Again</a>'
        )

    msgs = job["messages"]
    rows = "\n".join(f'<div class="progress-step">{m}</div>' for m in msgs)
    return HTMLResponse(rows or '<div class="progress-step">Starting...</div>')


# ── intro ─────────────────────────────────────────────────────────────────────


@app.get("/intro", response_class=HTMLResponse)
async def page_intro(request: Request):
    s = _sess(request)
    if "game" not in s:
        return RedirectResponse("/", status_code=303)
    game = s["game"]
    return _t(request, "intro.html", {
        "players": s["players"],
        "category": game.get("themeCategory", "General Knowledge"),
        "intro": game.get("commentary", {}).get("intro", ""),
    })


@app.post("/start")
async def handle_start(request: Request):
    if "game" not in _sess(request):
        return RedirectResponse("/", status_code=303)
    _sess(request)["round_phase"] = "p1"
    return RedirectResponse("/round", status_code=303)


# ── rounds ────────────────────────────────────────────────────────────────────


@app.get("/round", response_class=HTMLResponse)
async def page_round(request: Request):
    s = _sess(request)
    if "game" not in s:
        return RedirectResponse("/", status_code=303)

    game = s["game"]
    current_round = s["current_round"]
    phase = s.get("round_phase", "p1")
    players = s["players"]
    rtype = _round_type(current_round)
    ridx = _round_index(current_round)

    if phase == "handoff":
        return _t(request, "handoff.html", {
            "player": players[1],
            "ready_url": "/round/ready",
            "round_num": current_round + 1,
        })

    current_player = players[0] if phase == "p1" else players[1]

    if rtype == "letter":
        rd = game["letterRounds"][ridx]
        return _t(request, "letter_round.html", {
            "player": current_player,
            "round_num": current_round + 1,
            "letters": rd["letters"],
        })
    else:
        rd = game["numberRounds"][ridx]
        return _t(request, "number_round.html", {
            "player": current_player,
            "round_num": current_round + 1,
            "numbers": rd["available"],
            "target": rd["target"],
        })


@app.post("/round/submit")
async def submit_round(request: Request, answer: str = Form(default="")):
    s = _sess(request)
    if "game" not in s:
        return RedirectResponse("/", status_code=303)

    game = s["game"]
    current_round = s["current_round"]
    phase = s.get("round_phase", "p1")
    rtype = _round_type(current_round)
    ridx = _round_index(current_round)
    players = s["players"]
    answer = answer.strip()

    if rtype == "letter":
        rd = game["letterRounds"][ridx]
        display, score = _score_word(answer, rd["letters"]) if answer else ("—", 0)
        result = {"word": display, "score": score}
    else:
        rd = game["numberRounds"][ridx]
        display, score = _score_expr(answer, rd["available"], rd["target"]) if answer else ("—", 0)
        result = {"expr": display, "score": score}

    if phase == "p1":
        s["p1_answer"] = result
        s["round_phase"] = "handoff"
        return RedirectResponse("/round", status_code=303)

    # p2 completes the round
    s["p2_answer"] = result
    p1, p2 = s["p1_answer"], result
    s["scores"][0] += p1.get("score", 0)
    s["scores"][1] += p2.get("score", 0)

    after = game.get("commentary", {}).get("afterRounds", [])
    commentary = after[current_round] if current_round < len(after) else ""

    s["round_results"].append({
        "type": rtype,
        "round_num": current_round + 1,
        "p1": {**p1, "name": players[0]},
        "p2": {**p2, "name": players[1]},
        "optimal": rd.get("optimalWord") or rd.get("solutionPath", ""),
        "connection": rd.get("themeConnection", ""),
        "commentary": commentary,
    })
    return RedirectResponse("/round-result", status_code=303)


@app.post("/round/ready")
async def round_ready(request: Request):
    _sess(request)["round_phase"] = "p2"
    return RedirectResponse("/round", status_code=303)


# ── round result ──────────────────────────────────────────────────────────────


@app.get("/round-result", response_class=HTMLResponse)
async def page_round_result(request: Request):
    s = _sess(request)
    if not s.get("round_results"):
        return RedirectResponse("/", status_code=303)
    return _t(request, "round_result.html", {
        "result": s["round_results"][-1],
        "scores": s["scores"],
        "players": s["players"],
    })


@app.post("/round-result/next")
async def next_round(request: Request):
    s = _sess(request)
    s["current_round"] += 1
    s["round_phase"] = "p1"
    s.pop("p1_answer", None)
    s.pop("p2_answer", None)

    if s["current_round"] > 5:
        s["theme_guess_phase"] = "p1"
        return RedirectResponse("/theme-guess", status_code=303)
    return RedirectResponse("/round", status_code=303)


# ── theme guess ───────────────────────────────────────────────────────────────


@app.get("/theme-guess", response_class=HTMLResponse)
async def page_theme_guess(request: Request):
    s = _sess(request)
    if "game" not in s:
        return RedirectResponse("/", status_code=303)

    phase = s.get("theme_guess_phase", "p1")

    if phase == "done":
        return RedirectResponse("/conundrum", status_code=303)

    if phase == "handoff":
        return _t(request, "handoff.html", {
            "player": s["players"][1],
            "ready_url": "/theme-guess/ready",
        })

    if phase in ("p1_result", "p2_result"):
        is_p1 = phase == "p1_result"
        return _t(request, "theme_result.html", {
            "player": s["players"][0 if is_p1 else 1],
            "guess": s.get("theme_p1_guess" if is_p1 else "theme_p2_guess", ""),
            "score": s.get("theme_p1_score" if is_p1 else "theme_p2_score", 0),
            "temperature": _temperature_label(
                s.get("theme_p1_sim" if is_p1 else "theme_p2_sim", 0.0)
            ),
            "is_last": not is_p1,
        })

    current_player = s["players"][0 if phase == "p1" else 1]
    return _t(request, "theme_guess.html", {
        "player": current_player,
        "category": s["game"].get("themeCategory", "General Knowledge"),
    })


@app.post("/theme-guess/submit")
async def submit_theme_guess(request: Request, guess: str = Form(default="")):
    s = _sess(request)
    if "game" not in s:
        return RedirectResponse("/", status_code=303)

    from lib.wikipedia_rag import similarity

    theme = s["game"].get("theme", "")
    guess = guess.strip()
    phase = s.get("theme_guess_phase", "p1")
    sim = float(similarity(guess, theme)) if guess else 0.0
    score = 10 if sim >= 0.90 else 7 if sim >= 0.70 else 4 if sim >= 0.50 else 2 if sim >= 0.30 else 0

    if phase == "p1":
        s.update(theme_p1_guess=guess, theme_p1_score=score, theme_p1_sim=sim)
        s["scores"][0] += score
        s["theme_guess_phase"] = "p1_result"
    else:
        s.update(theme_p2_guess=guess, theme_p2_score=score, theme_p2_sim=sim)
        s["scores"][1] += score
        s["theme_guess_phase"] = "p2_result"

    return RedirectResponse("/theme-guess", status_code=303)


@app.post("/theme-guess/next")
async def theme_guess_next(request: Request):
    s = _sess(request)
    transitions = {"p1_result": "handoff", "p2_result": "done"}
    s["theme_guess_phase"] = transitions.get(s.get("theme_guess_phase", ""), "p1")
    return RedirectResponse("/theme-guess", status_code=303)


@app.post("/theme-guess/ready")
async def theme_guess_ready(request: Request):
    _sess(request)["theme_guess_phase"] = "p2"
    return RedirectResponse("/theme-guess", status_code=303)


# ── conundrum ─────────────────────────────────────────────────────────────────


@app.get("/conundrum", response_class=HTMLResponse)
async def page_conundrum(request: Request):
    s = _sess(request)
    if "game" not in s:
        return RedirectResponse("/", status_code=303)
    con = s["game"].get("conundrum", {})
    return _t(request, "conundrum.html", {
        "scrambled": con.get("scrambled", "").upper(),
        "players": s["players"],
        "attempt": s.get("conundrum_attempt", 0),
        "winner": s.get("conundrum_winner"),
    })


@app.post("/conundrum/submit")
async def submit_conundrum(
    request: Request,
    p1_answer: str = Form(default=""),
    p2_answer: str = Form(default=""),
):
    s = _sess(request)
    if "game" not in s:
        return RedirectResponse("/", status_code=303)

    word = s["game"].get("conundrum", {}).get("word", "").upper()
    players = s["players"]
    p1a, p2a = p1_answer.strip().upper(), p2_answer.strip().upper()

    if p1a == word or p2a == word:
        winner = players[0] if p1a == word else players[1]
        s["conundrum_winner"] = winner
        s["scores"][players.index(winner)] += 10
        return RedirectResponse("/results", status_code=303)

    attempt = s.get("conundrum_attempt", 0) + 1
    s["conundrum_attempt"] = attempt
    if attempt >= 3:
        s["conundrum_winner"] = None
        return RedirectResponse("/results", status_code=303)
    return RedirectResponse("/conundrum", status_code=303)


# ── results ───────────────────────────────────────────────────────────────────


@app.get("/results", response_class=HTMLResponse)
async def page_results(request: Request):
    s = _sess(request)
    if "game" not in s:
        return RedirectResponse("/", status_code=303)

    game = s["game"]
    scores, players = s["scores"], s["players"]

    if scores[0] > scores[1]:
        winner = players[0]
    elif scores[1] > scores[0]:
        winner = players[1]
    else:
        winner = None

    win_msg = (
        game.get("commentary", {})
        .get("winMessage", "{winner} wins!")
        .replace("{winner}", winner or "Both players")
    )

    return _t(request, "results.html", {
        "players": players,
        "scores": scores,
        "winner": winner,
        "win_message": win_msg,
        "game": game,
        "round_results": s.get("round_results", []),
        "theme_p1_guess": s.get("theme_p1_guess", ""),
        "theme_p2_guess": s.get("theme_p2_guess", ""),
        "theme_p1_score": s.get("theme_p1_score", 0),
        "theme_p2_score": s.get("theme_p2_score", 0),
        "conundrum_winner": s.get("conundrum_winner"),
    })


@app.post("/play-again")
async def play_again(request: Request):
    _sess(request).clear()
    return RedirectResponse("/", status_code=303)
