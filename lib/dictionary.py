from pathlib import Path

_WORD_FILE = Path(__file__).parent.parent / "data" / "sowpods.txt"

_words: set[str] | None = None


def _load() -> set[str]:
    global _words
    if _words is None:
        _words = {w.strip().upper() for w in _WORD_FILE.read_text().splitlines() if w.strip()}
    return _words


def is_valid_word(word: str) -> bool:
    return word.upper() in _load()


def all_words() -> set[str]:
    return _load()
