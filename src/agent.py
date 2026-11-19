"""Retrieve, assess, validate, and present a reviewable care task."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from pawpal_system import Task
from src.guardrails import available, check_request, pending_intervals
from src.prompts import NO_EVIDENCE, NO_SLOT
from src.retriever import CareGuide


@dataclass(frozen=True)
class Proposal:
    guide: CareGuide
    start: datetime

    @property
    def end(self):
        return self.start + timedelta(minutes=self.guide.minutes)


@dataclass(frozen=True)
class PlanResult:
    message: str
    trace: tuple[str, ...]
    proposal: Proposal | None = None


class CarePlanner:
    def __init__(self, retriever):
        self.retriever = retriever

    def plan(self, focus, pet, scheduler, day, start_time, end_time):
        start = datetime.combine(day, start_time.replace(second=0, microsecond=0))
        end = datetime.combine(day, end_time.replace(second=0, microsecond=0))
        error = check_request(focus, pet, start, end)
        if error:
            return PlanResult(error, ("Input validation: blocked",))

        matches = self.retriever.retrieve(focus, pet.species)
        if not matches:
            return PlanResult(NO_EVIDENCE, ("Input validation: passed", "Retrieval: no relevant guide"))

        guide, score = matches[0]
        trace = (
            "Input validation: passed",
            f"Retrieval: {guide.id} (cosine similarity {score:.2f})",
            f"Assessment: {guide.minutes}-minute, one-time task",
        )
        intervals = pending_intervals(scheduler)
        candidate = start
        for busy_start, busy_end in intervals:
            if candidate + timedelta(minutes=guide.minutes) <= busy_start:
                break
            candidate = max(candidate, busy_end)

        proposal = Proposal(guide, candidate)
        if proposal.end > end or not available(proposal.start, proposal.end, intervals):
            return PlanResult(NO_SLOT, (*trace, "Schedule validation: no slot"))
        return PlanResult(
            guide.guidance, (*trace, "Schedule validation: passed", "Awaiting approval"), proposal
        )

    def add_approved(self, proposal, pet, scheduler):
        if not any(registered is pet for registered in scheduler.owner.pets):
            return False
        if proposal.guide.species not in (pet.species.casefold(), "all"):
            return False
        if not available(proposal.start, proposal.end, pending_intervals(scheduler)):
            return False
        if any(
            task.description == proposal.guide.activity
            and task.due_date == proposal.start.date()
            and task.time == proposal.start.strftime("%H:%M")
            for task in pet.tasks
        ):
            return False

        pet.add_task(Task(
            description=proposal.guide.activity,
            due_date=proposal.start.date(),
            time=proposal.start.strftime("%H:%M"),
            duration=proposal.guide.minutes,
        ))
        return True
