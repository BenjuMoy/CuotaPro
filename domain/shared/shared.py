from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class PeriodBalance:
    month: int
    year: int
    amount: int


VALID_TEACHERS = {"Asuncion", "Daniela", "Florencia", "Kiana", "Romina", "Silvia"}
VALID_SCHOOL_YEARS = {
    "",
    "Kindergarden",
    "1 EP",
    "2 EP",
    "3 EP",
    "4 EP",
    "5 EP",
    "6 EP",
    "1 ES",
    "2 ES",
    "3 ES",
    "4 ES",
    "5 ES",
    "6 ES",
}
VALID_BOOKS = {
    "",
    "Power Up Start P. 1",
    "Power Up Start P. 2",
    "Learn With Us 1",
    "Power Up 1",
    "Power Up 2",
    "Own It 1",
    "Gateway A1",
    "Gateway A2",
    "Gateway B1",
    "Gateway B2",
    "Gold. Exp. FCE",
    "Gold. Exp. CAE",
    "Insight Elem.",
    "Insight Pre. Int.",
    "Insight Int.",
}
VALID_COURSES = {
    "",
    "Kids 1",
    "Kids 2",
    "Kids 3",
    "Junior 1",
    "Junior 2",
    "Junior 3",
    "Senior 1",
    "Senior 2",
    "Senior 3",
    "Senior 4",
    "Senior 5",
    "Senior 6",
    "Adults 1",
    "Adults 2",
    "Adults 3",
    "Adults 4",
}


class MovementType(str, Enum):
    FEE = "FEE"
    PAYMENT = "PAYMENT"
    REVERSED = "REVERSED"
