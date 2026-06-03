import ast
import operator
from collections import Counter

from lib.dictionary import is_valid_word

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def check_word_from_letters(word: str, letters: list[str]) -> tuple[bool, str]:
    """Return (valid, reason). Word must be formable from letters and in the dictionary."""
    word_up = word.upper()
    available = Counter(l.upper() for l in letters)
    needed = Counter(word_up)
    for ch, count in needed.items():
        if available[ch] < count:
            return False, f"'{ch}' not available enough times in the letter set"
    if not is_valid_word(word_up):
        return False, f"'{word}' is not a recognised word"
    return True, "ok"


def _eval_node(node: ast.expr, used: list[int], available: list[int]) -> float:
    if isinstance(node, ast.Constant):
        if node.value not in available:
            raise ValueError(f"{node.value} not in available numbers")
        idx = available.index(node.value)
        used.append(available.pop(idx))
        return float(node.value)
    if isinstance(node, ast.BinOp):
        op_fn = _OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError("Only +, -, *, / are allowed")
        left = _eval_node(node.left, used, available)
        right = _eval_node(node.right, used, available)
        if isinstance(node.op, ast.Div) and right == 0:
            raise ValueError("Division by zero")
        return op_fn(left, right)
    raise ValueError("Unsupported expression")


def evaluate_expression(expr: str, available: list[int]) -> tuple[bool, int | None, str]:
    """
    Safely evaluate an arithmetic expression using only numbers from available.
    Returns (valid, result, reason).
    """
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as e:
        return False, None, f"Syntax error: {e}"

    pool = list(available)
    used: list[int] = []
    try:
        result = _eval_node(tree.body, used, pool)
    except ValueError as e:
        return False, None, str(e)

    if result != int(result) or result < 0:
        return False, None, "Result must be a positive integer"

    return True, int(result), "ok"
