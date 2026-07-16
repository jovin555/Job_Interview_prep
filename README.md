# Job Interview Prep — Daily Interview Log

A daily interview-question log for a Senior Embedded Systems / Hardware
Engineer role, covering medical device hardware/firmware, IEC60601
compliance, and embedded systems design. Structured after
[jovin555/firmware-daily-log](https://github.com/jovin555/firmware-daily-log).

Each day, one topic (rotating through the list below) gets 5 new interview
Q&A entries, generated from a grounding-facts file (`docs/project-context.md`)
so answers stay tied to real project experience rather than invented details.

**Daily log:** [`content/`](content/) — latest seeded entry:
[`content/hardware-design/day-1.md`](content/hardware-design/day-1.md)

## Structure

```
content/<topic>/day-N.md   — 5 Q&A per file, one file per topic per rotation turn
docs/project-context.md    — grounding facts (roles, projects) fed to the generator
real-interview-log/        — actual questions encountered in real interviews
scripts/
  topics.json               — rotation order, start date, questions/day
  generate_daily_entry.py   — generation script (called by the GitHub Action)
.github/workflows/
  daily-log.yml              — daily cron: generates + commits the day's entry
```

## Topics (8-day rotation)

1. `hardware-design` — mixed-signal & high-speed PCB, power supply design
2. `firmware` — Embedded C, Zephyr RTOS, MicroPython
3. `medical-devices` — sensor integration, product testing, IEC60601/regulatory
4. `protocols` — I2C, SPI, UART, RS485, CAN-FD, USB 2.0
5. `space-rad-hard` — radiation-hardened design, STM32, hot-swap protection
6. `tools` — Altium, Cadence Allegro, KiCad, Keil, MPLAB
7. `behavioral-leadership` — STAR-format leadership/ownership stories
8. `debugging-failure-analysis` — 8D root cause, bench debugging, test coverage

## Automation

A GitHub Actions workflow runs daily, determines whose turn it is in the
rotation (based on `scripts/topics.json`), calls the Anthropic API with
`docs/project-context.md` as grounding context, and commits the new
`content/<topic>/day-N.md` file.

Requires an `ANTHROPIC_API_KEY` repo secret to be set before the workflow can
run.

## Manual use

```bash
export ANTHROPIC_API_KEY=sk-...
pip install anthropic
python3 scripts/generate_daily_entry.py
```

## Status

Local scaffold — not yet pushed to GitHub. Repo is intended to be **private**.
Note: GitHub Pages on a private repository requires a paid GitHub plan
(Pro/Team/Enterprise); confirm before wiring up the Quartz publishing step.
