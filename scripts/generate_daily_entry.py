#!/usr/bin/env python3
"""Generate one day's interview Q&A entry for the topic whose turn it is today.

Rotation, start date, and questions-per-day are configured in topics.json.
Grounding facts (real projects/roles) live in docs/project-context.md and are
sent to the model on every run so answers stay tied to actual experience.

Requires ANTHROPIC_API_KEY in the environment. Run from the repo root:
    python3 scripts/generate_daily_entry.py
"""
import datetime
import json
import os
import re
import sys
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
CONTEXT_FILE = REPO_ROOT / "docs" / "project-context.md"
CONFIG_FILE = REPO_ROOT / "scripts" / "topics.json"
MODEL = "claude-sonnet-5"


def load_config() -> dict:
    return json.loads(CONFIG_FILE.read_text())


def topic_for_today(config: dict) -> str:
    start = datetime.date.fromisoformat(config["start_date"])
    today = datetime.date.today()
    days_elapsed = (today - start).days
    rotation = config["rotation"]
    return rotation[days_elapsed % len(rotation)]


def next_day_number(topic_dir: Path) -> int:
    existing = [
        int(m.group(1))
        for f in topic_dir.glob("day-*.md")
        if (m := re.match(r"day-(\d+)\.md", f.name))
    ]
    return max(existing, default=0) + 1


def build_prompt(topic: str, day_number: int, questions_per_day: int, context: str) -> str:
    return f"""You are generating interview preparation content for a real engineer
based strictly on the grounding facts below. Do not invent experience,
metrics, or projects that are not in the grounding facts.

GROUNDING FACTS:
{context}

TASK:
Generate {questions_per_day} interview questions and model answers for the
topic "{topic}", suitable for day {day_number} of an ongoing study log.
Vary difficulty (include at least one deep technical question and one
behavioral/experience question if the topic allows). Where an answer draws
on experience, it must map to a specific project or role from the grounding
facts. Follow-up questions an interviewer might ask should be included per
entry.

OUTPUT FORMAT (markdown, follow exactly):

# {topic} — Day {day_number}

## Q1: <question>
**Answer:** <answer>
**Possible follow-ups:** <one or two follow-up questions>

## Q2: <question>
...continue through Q{questions_per_day}...
"""


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY is not set")

    config = load_config()
    topic = topic_for_today(config)
    topic_dir = CONTENT_DIR / topic
    topic_dir.mkdir(parents=True, exist_ok=True)

    day_number = next_day_number(topic_dir)
    context = CONTEXT_FILE.read_text()
    prompt = build_prompt(topic, day_number, config["questions_per_day"], context)

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    entry_text = response.content[0].text

    out_path = topic_dir / f"day-{day_number}.md"
    out_path.write_text(entry_text)
    print(f"Wrote {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
