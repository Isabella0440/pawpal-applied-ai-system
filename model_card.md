# PawPal+ AI Care Planner Model Card

## Intended use

PawPal+ helps a dog or cat owner schedule a routine care activity in a time window they choose. It uses a local TF-IDF vector space model to rank individual care guides by cosine similarity. The planner turns the highest-ranked guide that meets the cutoff into a one-time task and finds the earliest slot that fits across the owner's pending tasks.

## Data and output

The knowledge base contains eight project-authored examples for dog care, cat care, and shared routines. Each entry includes topic words, a stable source ID, a task title, guidance, and an estimated duration. The response uses the guide's text directly. The system requires no API key, hosted model, or generative LLM. The activity log shows the retrieval score, validation outcome, and proposal status for the current preview. It lives in the Streamlit session.

## Guardrails and evaluation

| Scenario | Expected behavior |
| --- | --- |
| Dog owner requests a walk and 17:00–17:20 is booked | Suggest a leash walk at 17:20 |
| Cat owner requests enrichment | Select the cat play guide |
| Owner asks for router repair | Return a no-match message |
| Owner asks for a medication dose | Redirect to a veterinarian |
| Requested window ends at 17:25 and only five minutes are free | Explain that the activity does not fit |
| Another task occupies the proposed slot after preview | Reject approval until the owner previews a new slot |

Run `python3 -m src.evaluate` to repeat these scenarios locally. The approval scenario also checks that preview leaves the schedule untouched and that repeated approval cannot add a duplicate.

## Limitations

The retriever depends on vocabulary overlap. Paraphrases may fail to match, and a mixed request may match only one topic. The similarity cutoff is a heuristic. Medical keyword checks are incomplete and can block benign wording. The small guide set limits coverage. Estimated durations are for schedule planning. Existing tasks and the preview log are session-local.

## AI collaboration

I used AI to help turn my Week 8 plan into a working feature in the existing PawPal+ app. I kept the existing scheduler as the source for pending tasks so manual entries and planner suggestions work with the same schedule. I carried the approval step from my original plan into the app. The planner previews the task first and checks the schedule again when I approve it, since a slot can be taken after the preview.

I kept the guidance tied to the local care guides so I can see where each suggestion came from. The evaluation checks a dog walk and cat enrichment, along with cases where the planner should stop. The approval test adds a competing task after preview and checks that the planner catches the conflict before adding anything.
