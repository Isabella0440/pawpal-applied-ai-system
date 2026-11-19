"""Run repeatable planner scenarios with python3 -m src.evaluate."""

from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task
from src.agent import CarePlanner
from src.prompts import MEDICAL_REDIRECT, NO_EVIDENCE, NO_SLOT
from src.retriever import Retriever


def main():
    planner = CarePlanner(Retriever())
    owner = Owner("Demo owner")
    dog = Pet("Bella", "Dog")
    cat = Pet("Luna", "Cat")
    for pet in (dog, cat):
        owner.add_pet(pet)
    scheduler = Scheduler(owner)
    day = date(2026, 11, 19)
    cat.add_task(Task("Existing appointment", "17:00", day, 20))

    cases = [
        (dog, "walk", time(18), "dog-walk", "17:20"),
        (cat, "enrichment", time(18), "cat-play", "17:20"),
        (cat, "fix my router", time(18), NO_EVIDENCE, None),
        (dog, "medication dose", time(18), MEDICAL_REDIRECT, None),
        (dog, "walk", time(17, 25), NO_SLOT, None),
    ]
    for pet, focus, end, expected, expected_time in cases:
        result = planner.plan(focus, pet, scheduler, day, time(17), end)
        if expected_time:
            assert result.proposal is not None, result.message
            assert result.proposal.guide.id == expected
            assert result.proposal.start.strftime("%H:%M") == expected_time
            output = f"{result.proposal.guide.activity} at {expected_time} ({expected})"
        else:
            assert result.proposal is None
            assert result.message == expected
            output = result.message
        print(f"{pet.species} / {focus} -> {output}")

    preview = planner.plan("walk", dog, scheduler, day, time(17), time(18)).proposal
    assert preview is not None and not dog.tasks
    blocker = Task("New appointment", "17:20", day, 10)
    cat.add_task(blocker)
    assert not planner.add_approved(preview, dog, scheduler)
    cat.remove_task(blocker)
    assert planner.add_approved(preview, dog, scheduler)
    assert not planner.add_approved(preview, dog, scheduler)
    assert not scheduler.detect_conflicts()
    print("Approval -> schedule updated once, with stale previews blocked")
    print("6 scenarios passed.")


if __name__ == "__main__":
    main()
