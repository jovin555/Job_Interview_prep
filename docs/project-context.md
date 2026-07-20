# Project & Experience Context

This file is the ground truth fed to the LLM when generating new Q&A entries.
It exists so generated answers stay grounded in real experience instead of
inventing plausible-sounding but false details. Update it whenever new
projects, roles, or details should be reflected in future entries.

This file uses anonymized placeholders for employers and projects
(Company A/B/C/..., Project W/X/Y/Z) instead of real names, so that
generated Q&A content — which gets committed to a public repo — never
leaks real employer or product names. The mapping is fixed below and must
stay consistent across entries; never substitute a real name back in.

## Profile
Senior Embedded Systems Engineer, 10+ years, specializing in Medical IoT
devices: mixed-signal & high-speed PCB design, firmware (Zephyr RTOS,
Embedded C, MicroPython), IEC60601 regulatory compliance, Class II medical
device hardware, radiation-hardened space electronics.

## Core Competencies
- Hardware: mixed-signal & high-speed circuit design, power supply design,
  PCB layout & review
- Firmware/software: Embedded C, Zephyr RTOS, MicroPython
- Compliance: IEC60601 medical standards, regulatory testing, Health Canada
  standards
- Protocols: I2C, SPI, UART, RS485, CAN-FD, USB 2.0
- Tools: Altium Designer, Cadence Allegro, KiCad, Keil uVision, MPLAB IDE

## Employment History
- **Company A** (medical device manufacturer) — Electronics Design
  Engineering Specialist, Oct 2020–Jul 2026. Led hardware design for Class II
  medical devices with high-accuracy sensor integration; optimized PCB
  layouts/decoupling to cut signal noise 15%; ran 8D root-cause
  investigations for critical medical device failures.
- **Company C** (contractor via Company D, medical imaging/monitoring OEM) —
  Lead Engineer, Apr 2019–Apr 2020. Managed medical product development,
  executed regulatory testing phases.
- **Company E** (engineering services) — Senior Engineer, Aug 2017–Feb 2019.
  Medical product prototypes, translated client requirements into circuit
  designs.
- **Company B** (photonics/laser electronics) — Embedded Hardware Engineer,
  May 2013–Aug 2017. Circuits for high-power laser products and fiber
  amplifiers; board-level debugging/testing and client technical support.
- **Company F** (industrial electronics) — Junior Engineer, May 2011–Aug
  2013. Industrial product development, Embedded C, PCB design in Eagle CAD.

## Key Projects
- **Project X** — intelligent respiratory device to clear mucus and monitor
  patient technique. Pressure sensors for flow capture, RGB LED feedback,
  Li-ion power management for 7 days continuous use.
- **Project Y** — maternal/infant care system. Continuous uterine
  contraction monitoring during labor; companion unit records contraction
  values, maternal heart rate, and fetal heart rate. IEC 60601 testing
  performed; resolved circuit design issues found during testing.
- **Project Z** — portable control/sensor box for life-support procedures
  (ECMO/PCPS-type). Motor speed control, biological parameter monitoring
  (temperature/pressure), wireless comms for real-time monitoring/logging
  via tablet.
- **Project W** (high-reliability fiber amplifier) — radiation-hardened
  (50K rad-hard) hardware for space-qualified booster modules. STM32
  microcontrollers with external DAC/ADC, hot-swap protection, also used in
  industrial laser-cutting applications.

## Education
- Post-graduate diploma — Advanced Embedded System Design
- Bachelor's degree — Electronics and Communication

## Target-role topics (general knowledge, not claimed hands-on experience)
These topics were added because they recur in job descriptions currently
being applied to, but are NOT part of the employment history above. Answers
here must be framed as general/theoretical knowledge or "how I would
approach it," never as "I did X at [company]" — do not attach them to any
project or role above.
- **High-speed digital & FPGA design** — FPGAs, DDR memory interfaces, clock
  generation/distribution, board-to-board interconnects, signal/power
  integrity at high frequency, EMI/EMC for high-speed digital.
- **Embedded Linux & BSP** — Linux kernel/driver basics, board support
  packages, multi-board/multi-processor bring-up, Yocto/Buildroot, ARM/x64
  cross-compilation.
- **Risk management & requirements traceability** — ISO 14971 risk
  management, DFMEA, SRS/architecture diagrams, ICDs, traceability matrices,
  as distinct from the IEC 60601/DHF compliance work already covered under
  medical-devices.

## Generation rules for the LLM
1. Questions and answers must be generic, not personal-achievement stories.
   Phrase questions as "How would you approach/handle/debug X?" rather than
   "Tell me about a time you achieved X" or "Describe a time when you...".
   Answers describe sound reasoning, trade-offs, and best practice — not
   "I did X and achieved Y%".
2. Do not invent specific metrics, dates, or outcomes ("reduced noise by
   15%", "passed on the next attempt") even when loosely referencing the
   kind of work in the background above — reference it only as the general
   type of system/problem (e.g. "in a battery-powered medical sensor
   device"), never as a claimed personal result.
3. Never use real employer or product names — only the anonymized
   Company A/B/C/... and Project W/X/Y/Z placeholders defined above, and
   only when a concrete example genuinely clarifies the answer. Most
   answers don't need to name a placeholder at all.
4. For the target-role topics listed below, answer purely as general
   technical/theoretical knowledge — do not tie them to any
   company/project placeholder above at all.
5. Behavioral/leadership questions should still be answerable in an
   interview (a general framework or approach — e.g. how one would
   structure a root-cause investigation, or handle cross-team
   disagreement) without asserting it as something already accomplished.
