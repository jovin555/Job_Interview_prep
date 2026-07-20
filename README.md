# Job Interview Prep — Daily Interview Log

A daily interview-question log for a Senior Embedded Systems / Hardware
Engineer role, covering medical device hardware/firmware, IEC60601
compliance, and embedded systems design. Structured after
[jovin555/firmware-daily-log](https://github.com/jovin555/firmware-daily-log).

Every day, all topics below each get 5 new interview Q&A entries, generated
from a grounding-facts file (`docs/project-context.md`) so answers stay tied
to real project experience rather than invented details.

**Daily log site:** https://jovin555.github.io/Job_Interview_prep/

**Daily log (source):** [`content/`](content/) — latest seeded entry:
[`content/hardware-design/day-1.md`](content/hardware-design/day-1.md)

## Structure

```
content/<topic>/day-N.md   — 5 Q&A per file, one new file per topic per day
docs/project-context.md    — grounding facts (roles, projects) fed to the generator
real-interview-log/        — actual questions encountered in real interviews
scripts/
  topics.json               — topic list, questions/day
  generate_daily_entry.py   — generation script (called by the GitHub Action)
.github/workflows/
  daily-log.yml              — daily cron: generates + commits the day's entry
  deploy-site.yml            — builds the Quartz site and deploys to GitHub Pages
quartz/, quartz.ts, quartz.config.yaml — Quartz 5 static site generator
```

## Topics (11, all updated daily)

1. `hardware-design` — mixed-signal & high-speed PCB, power supply design
2. `firmware` — Embedded C, Zephyr RTOS, MicroPython
3. `medical-devices` — sensor integration, product testing, IEC60601/regulatory
4. `protocols` — I2C, SPI, UART, RS485, CAN-FD, USB 2.0
5. `space-rad-hard` — radiation-hardened design, STM32, hot-swap protection
6. `tools` — Altium, Cadence Allegro, KiCad, Keil, MPLAB
7. `behavioral-leadership` — STAR-format leadership/ownership stories
8. `debugging-failure-analysis` — 8D root cause, bench debugging, test coverage
9. `high-speed-digital-fpga` — FPGAs, DDR, clock distribution, SI/PI at high
   frequency (target-role topic, general knowledge — see
   `docs/project-context.md`)
10. `embedded-linux-bsp` — Linux BSP, drivers, multi-board bring-up,
    Yocto/Buildroot (target-role topic, general knowledge)
11. `risk-requirements-traceability` — ISO 14971, DFMEA, SRS/ICDs,
    traceability matrices (target-role topic, general knowledge)

Topics 9-11 were added from recurring themes in job descriptions currently
being applied to (Teledyne, Thornhill Medical, Sterling Industries,
Miovision) that aren't part of the real employment history — see the
"Target-role topics" section of `docs/project-context.md` for how those
answers are kept honest about what's actual experience vs. general
knowledge.

## Automation

A GitHub Actions workflow runs daily, calls the DeepSeek API once per topic
(based on `scripts/topics.json`) with `docs/project-context.md` as grounding
context, and commits a new `content/<topic>/day-N.md` file for every topic.

Requires a `DEEPSEEK_API_KEY` repo secret to be set before the workflow can
run. The workflow can also be triggered manually (`workflow_dispatch`) with
an optional `topic` input to generate just that one topic instead of all of
them — useful for backfilling or re-running a single topic.

## Manual use

```bash
export DEEPSEEK_API_KEY=sk-...
pip install requests
python3 scripts/generate_daily_entry.py
# or override the topic:
TOPIC_OVERRIDE=firmware python3 scripts/generate_daily_entry.py
```

## Publishing

Built with [Quartz 5](https://quartz.jzhao.xyz/), same generator as the
reference repo. `deploy-site.yml` builds `content/` and deploys to GitHub
Pages on every push to `main`. To preview locally:

```bash
npm ci
npx quartz plugin install
npx quartz build --serve
```

## Status

Public repo, pushed to GitHub. Pages requires enabling "GitHub Actions" as
the Pages source in repo Settings before `deploy-site.yml` can publish.
