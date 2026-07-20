# Job Interview Prep — Daily Interview Log

Daily interview-question log for a Senior Embedded Systems / Hardware Engineer
job search. Static site built with Quartz 5, auto-deployed to GitHub Pages,
content auto-generated daily via GitHub Actions + DeepSeek API.

**Site:** https://jovin555.github.io/Job_Interview_prep/
**Repo:** jovin555/Job_Interview_prep (public)

## How daily generation works

- `.github/workflows/daily-log.yml` runs on cron `0 11 * * *` (11:00 UTC daily),
  plus `workflow_dispatch` for manual runs.
- It calls `scripts/generate_daily_entry.py`, which now generates a NEW
  `content/<topic>/day-N.md` for **every** topic in `scripts/topics.json` on
  every run (not a one-topic-per-day rotation — that was the original design
  but was changed; see "Design history" below).
- `TOPIC_OVERRIDE=<topic>` env var (or the workflow's `topic` dispatch input)
  restricts a run to a single topic — useful for backfill/re-running one topic.
- After generation, the workflow commits and pushes `content/`.
- `.github/workflows/deploy-site.yml` triggers on push to `main` and on
  `daily-log.yml` completion, builds Quartz, deploys to Pages.
- Requires a `DEEPSEEK_API_KEY` repo secret (not stored locally/in this repo).

**If content looks stale/missing:** check `git log` / `gh run list
--workflow=daily-log.yml` before assuming it's broken — a common false alarm
is the local clone just being behind `origin/main` (`git pull`). Another is a
new topic's `day-N.md` files existing under `content/` but not being linked
from `content/index.md` (the homepage listing is a manually maintained list,
NOT auto-generated from `scripts/topics.json` — keep them in sync manually).

## Content rules (critical — see `docs/project-context.md`)

1. **Anonymized only.** `docs/project-context.md` (the grounding-facts file
   fed to the LLM) uses placeholders — Company A-F for employers, Project
   W/X/Y/Z for products — instead of real names. Real name and real
   employer/product names must NEVER appear in generated content, since it's
   committed to a public repo. If you ever see a real name leak into
   `content/`, the likely cause is `docs/project-context.md` itself having a
   real name (fix the source) or the LLM ignoring the anonymization rule.
2. **Generic framing, not personal-achievement stories.** Questions are
   phrased "How would you approach/handle/debug X?" not "Tell me about a
   time you achieved X." Answers describe sound reasoning/best practice, not
   "I did X and achieved Y%" with invented metrics. This was an explicit
   user preference — real interview answers with fabricated-sounding
   specifics were considered worse than honest, generic, well-reasoned ones.
3. **Target-role topics** (`high-speed-digital-fpga`, `embedded-linux-bsp`,
   `risk-requirements-traceability`) are topics NOT in the real employment
   history — they were added because they recur in job descriptions
   currently being applied to (Teledyne, Thornhill Medical, Sterling
   Industries, Miovision — see `/home/eva/workspace/Job_search/`). These must
   be answered as pure general knowledge, never attached to any
   Company/Project placeholder.

## Topics (11, all regenerated daily)

`hardware-design`, `firmware`, `medical-devices`, `protocols`,
`space-rad-hard`, `tools`, `behavioral-leadership`,
`debugging-failure-analysis`, `high-speed-digital-fpga`,
`embedded-linux-bsp`, `risk-requirements-traceability`.

## Design history / decisions made

- **Original design** (one topic/day, 8-day rotation) was silently working
  as designed but looked broken because the user's local clone was behind
  `origin/main`. Investigated via `gh run list`/`gh run view --log` before
  concluding it was fine.
- **Changed to all-topics-daily** on 2026-07-20 per explicit user request
  (wanted the site "updated every day with the day's content" for every
  topic, not one at a time).
- **Added 3 target-role topics** same day, sourced from JDs in
  `/home/eva/workspace/Job_search/` (Teledyne, Thornhill, Sterling
  Industries, Miovision) — confirmed with user before adding.
- **Anonymized `docs/project-context.md`** and rewrote the generation
  prompt/rules for generic framing, same day, after user flagged real names
  leaking into generated `content/` files (the earlier "Anonymize company
  project names" commit only fixed already-generated day-1 files, not the
  grounding-facts source, so the leak recurred in day-2).
- **Wiped and regenerated all existing content** (day-1/day-2 files) same
  day rather than patch old files, since old entries had both real-name
  leaks and personal-achievement framing that predated both fixes.

## Related project

`/home/eva/workspace/Job_search/` — the user's actual job search workspace:
resume versions, JDs per company, application tracker (`applications.csv`),
interview prep notes. `docs/project-context.md` in this repo should be kept
in sync with `Job_search/Job_details/Role_Descriptions_by_Organization.md`
(real employment history) if that ever changes — but always re-anonymize
before it lands in `content/`.
