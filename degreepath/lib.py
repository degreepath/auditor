from __future__ import annotations
from typing import List
from decimal import Decimal


def grade_from_str(s: str) -> Decimal:
    grades = {
        "A+": "4.30",
        "A": "4.00",
        "A-": "3.70",
        "B+": "3.30",
        "B": "3.00",
        "B-": "2.70",
        "C+": "2.30",
        "C": "2.00",
        "C-": "1.70",
        "D+": "1.30",
        "D": "1.00",
        "D-": "0.70",
        "F": "0.00",
    }

    return Decimal(grades.get(s, "0.00"))


def expand_subjects(subjects: List[str]):
    shorthands = {
        "AS": "ASIAN",
        "BI": "BIO",
        "CH": "CHEM",
        "ES": "ENVST",
        "PS": "PSCI",
        "RE": "REL",
    }

    for subject in subjects:
        for code in subject.split("/"):
            yield shorthands.get(code, code)
