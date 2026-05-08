import re
from dataclasses import dataclass

from domain.shared.exceptions import AppValidationError
from domain.shared.shared import (
    VALID_BOOKS,
    VALID_COURSES,
    VALID_SCHOOL_YEARS,
    VALID_TEACHERS,
)

NAME_PATTERN = re.compile(r"^[A-Za-zÁÉÍÓÚÜáéíóúüÑñ\s\-]+$")

# TODO this
PHONE_PATTERN = re.compile(r"^[0-9+\-\s]+$")


@dataclass(frozen=True)
class StudentName:
    first_name: str
    last_name: str

    def __post_init__(self):
        if not (1 <= len(self.first_name) <= 50):
            raise AppValidationError("Invalid first name length")
        if not (1 <= len(self.last_name) <= 50):
            raise AppValidationError("Invalid last name length")
        if not NAME_PATTERN.match(self.first_name):
            raise AppValidationError("Invalid first name")
        if not NAME_PATTERN.match(self.last_name):
            raise AppValidationError("Invalid last name")


@dataclass(frozen=True)
class PhoneNumber:
    value: str

    def __post_init__(self):
        if not (1 <= len(self.value) <= 20):
            raise AppValidationError("Invalid phone number")

    @classmethod
    def optional(cls, value: str | None):
        if not value:
            return None
        return cls(value)

    @classmethod
    def from_persistence(cls, value: str):
        obj = cls.__new__(cls)
        object.__setattr__(obj, "value", value)
        return obj


@dataclass(frozen=True)
class MonthlyFee:
    amount: int

    def __post_init__(self):
        if not (1 <= self.amount <= 500000):
            raise AppValidationError("Invalid monthly fee")

    @classmethod
    def from_persistence(cls, amount: str):
        obj = cls.__new__(cls)
        object.__setattr__(obj, "amount", amount)
        return obj


@dataclass(frozen=True)
class Teacher:
    name: str

    def __post_init__(self):
        if self.name not in VALID_TEACHERS:
            raise AppValidationError("Profesor invalido")

    @classmethod
    def from_persistence(cls, name: str):
        obj = cls.__new__(cls)
        object.__setattr__(obj, "name", name)
        return obj


@dataclass(frozen=True)
class SchoolYear:
    value: str

    def __post_init__(self):
        if self.value not in VALID_SCHOOL_YEARS:
            raise AppValidationError("Año escolar invalido")

    @classmethod
    def from_persistence(cls, value: str):
        obj = cls.__new__(cls)
        object.__setattr__(obj, "value", value)
        return obj


@dataclass(frozen=True)
class Book:
    title: str

    def __post_init__(self):
        if self.title not in VALID_BOOKS:
            raise AppValidationError("Libro invalido")

    @classmethod
    def from_persistence(cls, title: str):
        obj = cls.__new__(cls)
        object.__setattr__(obj, "title", title)
        return obj


@dataclass(frozen=True)
class Course:
    name: str

    def __post_init__(self):
        if self.name not in VALID_COURSES:
            raise AppValidationError("curso invalido")

    @classmethod
    def from_persistence(cls, name: str):
        obj = cls.__new__(cls)
        object.__setattr__(obj, "name", name)
        return obj
