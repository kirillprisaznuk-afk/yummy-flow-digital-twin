"""Stable decimal context even when a caller changes its own context."""

from collections.abc import Callable
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from fractions import Fraction
from functools import wraps


def calculation[**P, R](function: Callable[P, R]) -> Callable[P, R]:
    @wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        with localcontext(Context(prec=28, rounding=ROUND_HALF_EVEN)):
            return function(*args, **kwargs)

    return wrapped


def as_decimal(value: Fraction) -> Decimal:
    """Convert an exact rate/quantity only at the Decimal result boundary."""
    return Decimal(value.numerator) / Decimal(value.denominator)
