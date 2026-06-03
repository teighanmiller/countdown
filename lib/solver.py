"""
Countdown numbers solver.
Tries all ways to combine up to 6 numbers with +,-,*,/ to reach a target.
Commutative-pair deduplication keeps this under ~0.3s for typical targets.
"""
from __future__ import annotations


def _solve(nums: list[float], exprs: list[str], target: int) -> str | None:
    for val, expr in zip(nums, exprs):
        if val == target:
            return expr

    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            a, b, ea, eb = nums[i], nums[j], exprs[i], exprs[j]
            rest_n = [nums[k] for k in range(n) if k != i and k != j]
            rest_e = [exprs[k] for k in range(n) if k != i and k != j]

            candidates: list[tuple[float, str]] = []

            # Commutative: try once each
            candidates.append((a + b, f"({ea} + {eb})"))
            candidates.append((a * b, f"({ea} * {eb})"))

            # Non-commutative: try both orders, skip non-positive/non-integer results
            for x, y, xe, ye in [(a, b, ea, eb), (b, a, eb, ea)]:
                if x > y:
                    candidates.append((x - y, f"({xe} - {ye})"))
                if y != 0 and x % y == 0:
                    candidates.append((x / y, f"({xe} / {ye})"))

            for val, expr in candidates:
                if val <= 0:
                    continue
                result = _solve([val] + rest_n, [expr] + rest_e, target)
                if result is not None:
                    return result
    return None


def solve(available: list[int], target: int) -> tuple[bool, str]:
    """Return (solvable, expression_string)."""
    nums = [float(n) for n in available]
    exprs = [str(n) for n in available]
    result = _solve(nums, exprs, target)
    if result is None:
        return False, ""
    if result.startswith("(") and result.endswith(")"):
        result = result[1:-1]
    return True, result
