"""SSOT — 2025 federal tax constants. No magic numbers anywhere else."""
from __future__ import annotations

from decimal import Decimal
from typing import Literal

YEAR = 2025

FilingStatus = Literal["single", "mfj", "mfs", "hoh", "qss"]

STANDARD_DEDUCTION: dict[str, Decimal] = {
    "single": Decimal("15750"),
    "mfj":    Decimal("31500"),
    "mfs":    Decimal("15750"),
    "hoh":    Decimal("23625"),
    "qss":    Decimal("31500"),
}

DEPENDENT_OF_ANOTHER_FLOOR = Decimal("1350")
DEPENDENT_OF_ANOTHER_EARNED_BUMP = Decimal("450")

BRACKETS: dict[str, list[tuple[Decimal, Decimal]]] = {
    "single": [
        (Decimal("0"),       Decimal("0.10")),
        (Decimal("11925"),   Decimal("0.12")),
        (Decimal("48475"),   Decimal("0.22")),
        (Decimal("103350"),  Decimal("0.24")),
        (Decimal("197300"),  Decimal("0.32")),
        (Decimal("250525"),  Decimal("0.35")),
        (Decimal("626350"),  Decimal("0.37")),
    ],
    "mfj": [
        (Decimal("0"),       Decimal("0.10")),
        (Decimal("23850"),   Decimal("0.12")),
        (Decimal("96950"),   Decimal("0.22")),
        (Decimal("206700"),  Decimal("0.24")),
        (Decimal("394600"),  Decimal("0.32")),
        (Decimal("501050"),  Decimal("0.35")),
        (Decimal("751600"),  Decimal("0.37")),
    ],
    "mfs": [
        (Decimal("0"),       Decimal("0.10")),
        (Decimal("11925"),   Decimal("0.12")),
        (Decimal("48475"),   Decimal("0.22")),
        (Decimal("103350"),  Decimal("0.24")),
        (Decimal("197300"),  Decimal("0.32")),
        (Decimal("250525"),  Decimal("0.35")),
        (Decimal("375800"),  Decimal("0.37")),
    ],
    "hoh": [
        (Decimal("0"),       Decimal("0.10")),
        (Decimal("17000"),   Decimal("0.12")),
        (Decimal("64850"),   Decimal("0.22")),
        (Decimal("103350"),  Decimal("0.24")),
        (Decimal("197300"),  Decimal("0.32")),
        (Decimal("250500"),  Decimal("0.35")),
        (Decimal("626350"),  Decimal("0.37")),
    ],
    "qss": [
        (Decimal("0"),       Decimal("0.10")),
        (Decimal("23850"),   Decimal("0.12")),
        (Decimal("96950"),   Decimal("0.22")),
        (Decimal("206700"),  Decimal("0.24")),
        (Decimal("394600"),  Decimal("0.32")),
        (Decimal("501050"),  Decimal("0.35")),
        (Decimal("751600"),  Decimal("0.37")),
    ],
}

TAX_TABLE_CEILING = Decimal("100000")
TAX_TABLE_RANGE = Decimal("50")
TAX_TABLE_MIDPOINT_OFFSET = Decimal("25")
