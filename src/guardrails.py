"""Check planner scope and proposed task times."""

from datetime import datetime, timedelta
import re

from src.prompts import MEDICAL_REDIRECT

MEDICAL_TERMS = re.compile(
    r"\b(?:meds?|medical|medications?|dos(?:e|es|age)|diagnos\w*|treatments?|"
    r"poison\w*|toxic|chok\w*|bleed\w*|vomit\w*|injur\w*|pain\w*|"
    r"sick\w*|symptoms?|diarrh\w*|seizures?|limp\w*|emergency|"
    r"antibiotics?|insulin|pills?|drugs?|wounds?|letharg\w*|"
    r"infect\w*|allerg\w*|breath\w*|diabet\w*|heartworms?)\b",
    re.IGNORECASE,
)


def check_request(focus, pet, start, end):
    if not 1 <= len(focus.strip()) <= 200:
        return "Enter a care focus between 1 and 200 characters."
    if MEDICAL_TERMS.search(focus):
        return MEDICAL_REDIRECT
    if pet.species.casefold() not in {"dog", "cat"}:
        return "The care planner currently supports dogs and cats."
    if start >= end:
        return "Choose an end time after the start time on the same day."
    return ""


def pending_intervals(scheduler):
    intervals = []
    for task in scheduler.filter_tasks(completed=False):
        if task.duration <= 0:
            continue
        start = datetime.combine(task.due_date, datetime.strptime(task.time, "%H:%M").time())
        intervals.append((start, start + timedelta(minutes=task.duration)))
    return intervals


def available(start, end, intervals):
    return start < end and all(
        end <= busy_start or start >= busy_end for busy_start, busy_end in intervals
    )
