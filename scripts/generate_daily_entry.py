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


def build_prompt(topic: str, day_number: int, questions_per_day: int, context: str) -> str:
    return f"""You are generating generic interview preparation content, grounded
by (but not narrated as) the background below. Do not invent metrics,
dates, or outcomes. Never use real employer or product names — only the
anonymized Company/Project placeholders in the grounding facts, and only
where a concrete example genuinely helps.

GROUNDING FACTS:
{context}

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


def generate_entry(topic: str, context: str, questions_per_day: int, api_key: str) -> None:
    topic_dir = CONTENT_DIR / topic
    topic_dir.mkdir(parents=True, exist_ok=True)

    day_number = next_day_number(topic_dir)
    prompt = build_prompt(topic, day_number, questions_per_day, context)

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

    for topic in topics_for_today(config):
        generate_entry(topic, context, config["questions_per_day"], api_key)


if __name__ == "__main__":
    main()
