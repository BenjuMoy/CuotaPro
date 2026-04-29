from dataclasses import dataclass


@dataclass(frozen=True)
class PeriodBalance:
    month: int
    year: int
    amount: int
