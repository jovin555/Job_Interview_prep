#!/usr/bin/env python3
"""Generate today's interview Q&A entry for every topic in the rotation.

Topics and questions-per-day are configured in topics.json. Grounding facts
(real projects/roles) live in docs/project-context.md and are sent to the
model on every run so answers stay tied to actual experience.

Requires DEEPSEEK_API_KEY in the environment. Run from the repo root:
    python3 scripts/generate_daily_entry.py
"""
import json
import os
import re
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
CONTEXT_FILE = REPO_ROOT / "docs" / "project-context.md"
CONFIG_FILE = REPO_ROOT / "scripts" / "topics.json"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


def load_config() -> dict:
    return json.loads(CONFIG_FILE.read_text())


def topics_for_today(config: dict) -> list[str]:
    override = os.environ.get("TOPIC_OVERRIDE")
    if override:
        if override not in config["rotation"]:
            sys.exit(f"TOPIC_OVERRIDE {override!r} is not in the rotation list")
        return [override]
    return config["rotation"]


def next_day_number(topic_dir: Path) -> int:
    existing = [
        int(m.group(1))
        for f in topic_dir.glob("day-*.md")
        if (m := re.match(r"day-(\d+)\.md", f.name))
    ]
    return max(existing, default=0) + 1


def prior_questions(topic_dir: Path) -> list[str]:
    questions = []
    for f in sorted(topic_dir.glob("day-*.md")):
        for line in f.read_text().splitlines():
            if m := re.match(r"## Q\d+: (.+)", line):
                questions.append(m.group(1).strip())
    return questions


def build_prompt(
    topic: str,
    day_number: int,
    questions_per_day: int,
    context: str,
    already_asked: list[str],
    topic_hints: list[str],
) -> str:
    already_asked_block = ""
    if already_asked:
        listed = "\n".join(f"- {q}" for q in already_asked)
        already_asked_block = f"""

ALREADY ASKED (do not repeat or closely rephrase any of these — pick
genuinely different scenarios/angles on the topic):
{listed}
"""

    topic_hints_block = ""
    if topic_hints:
        listed = "\n".join(f"- {h}" for h in topic_hints)
        topic_hints_block = f"""

TOPIC FOCUS AREAS (draw from across these over the life of the log — don't
cover the same one or two every day; rotate through the others as prior
days accumulate):
{listed}
"""

    return f"""You are generating generic interview preparation content, grounded
by (but not narrated as) the background below. Do not invent metrics,
dates, or outcomes. Never use real employer or product names — only the
anonymized Company/Project placeholders in the grounding facts, and only
where a concrete example genuinely helps.

GROUNDING FACTS:
{context}
{already_asked_block}{topic_hints_block}
TASK:
Generate {questions_per_day} interview questions and model answers for the
topic "{topic}", suitable for day {day_number} of an ongoing study log.
Vary difficulty (include at least one deep technical question and one
behavioral question if the topic allows). Phrase questions generically
("How would you approach/debug/handle X?"), not as "Tell me about a time
you achieved X" or "Describe a time when you...". Answers should read as
sound reasoning and best practice a strong candidate would give — not a
personal-achievement story with claimed results. Follow-up questions an
interviewer might ask should be included per entry.

OUTPUT FORMAT (markdown, follow exactly):

# {topic} — Day {day_number}

## Q1: <question>
**Answer:** <answer>
**Possible follow-ups:** <one or two follow-up questions>

## Q2: <question>
...continue through Q{questions_per_day}...
"""


def generate_entry(
    topic: str,
    context: str,
    questions_per_day: int,
    api_key: str,
    topic_hints: list[str],
) -> None:
    topic_dir = CONTENT_DIR / topic
    topic_dir.mkdir(parents=True, exist_ok=True)

    day_number = next_day_number(topic_dir)
    already_asked = prior_questions(topic_dir)
    prompt = build_prompt(
        topic, day_number, questions_per_day, context, already_asked, topic_hints
    )

    response = requests.post(
        DEEPSEEK_API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 4096,
        },
        timeout=120,
    )
    response.raise_for_status()
    entry_text = response.json()["choices"][0]["message"]["content"]

    out_path = topic_dir / f"day-{day_number}.md"
    out_path.write_text(entry_text)
    print(f"Wrote {out_path.relative_to(REPO_ROOT)}")


def main() -> None:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        sys.exit("DEEPSEEK_API_KEY is not set")

    config = load_config()
    context = CONTEXT_FILE.read_text()
    topic_hints = config.get("topic_hints", {})

    for topic in topics_for_today(config):
        generate_entry(
            topic, context, config["questions_per_day"], api_key, topic_hints.get(topic, [])
        )


if __name__ == "__main__":
    main()
