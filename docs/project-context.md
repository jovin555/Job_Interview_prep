# Project & Experience Context

This file is the ground truth fed to the LLM when generating new Q&A entries.
It exists so generated answers stay grounded in real experience instead of
inventing plausible-sounding but false details. Update it whenever new
projects, roles, or details should be reflected in future entries.

## Profile
Jovin Basil — Senior Embedded Systems Engineer, 10+ years, specializing in
Medical IoT devices: mixed-signal & high-speed PCB design, firmware
(Zephyr RTOS, Embedded C, MicroPython), IEC60601 regulatory compliance,
Class II medical device hardware, radiation-hardened space electronics.

## Core Competencies
- Hardware: mixed-signal & high-speed circuit design, power supply design,
  PCB layout & review
- Firmware/software: Embedded C, Zephyr RTOS, MicroPython
- Compliance: IEC60601 medical standards, regulatory testing, Health Canada
  standards
- Protocols: I2C, SPI, UART, RS485, CAN-FD, USB 2.0
- Tools: Altium Designer, Cadence Allegro, KiCad, Keil uVision, MPLAB IDE

## Employment History
- **Trudell Medical International** (London, ON) — Electronics Design
  Engineering Specialist, Oct 2020–Jul 2026. Led hardware design for Class II
  medical devices with high-accuracy sensor integration; optimized PCB
  layouts/decoupling to cut signal noise 15%; ran 8D root-cause
  investigations for critical medical device failures.
- **GE Healthcare** (contractor via Quest Global, Bangalore) — Lead Engineer,
  Apr 2019–Apr 2020. Managed medical product development, executed
  regulatory testing phases.
- **Larsen and Toubro** (Mysore) — Senior Engineer, Aug 2017–Feb 2019.
  Medical product prototypes, translated client requirements into circuit
  designs.
- **Vinvish Technologies** (Trivandrum) — Embedded Hardware Engineer,
  May 2013–Aug 2017. Circuits for high-power laser products and fiber
  amplifiers; board-level debugging/testing and client technical support.
- **Beginow Pvt Ltd** (Trivandrum) — Junior Engineer, May 2011–Aug 2013.
  Industrial product development, Embedded C, PCB design in Eagle CAD.

## Key Projects
- **Smart OPEP Device** — intelligent respiratory device to clear mucus and
  monitor patient technique. Pressure sensors for flow capture, RGB LED
  feedback, Li-ion power management for 7 days continuous use.
- **Lotus (Printer and Toco)** — maternal/infant care systems. Toco device
  for noninvasive continuous uterine contraction monitoring during labor;
  printer unit records Toco values, maternal heart rate, Toco UA values,
  fetal heart rate. IEC 60601 testing performed; resolved circuit design
  issues found during testing.
- **SOBA — Heart Lung Support Machine** — portable control/sensor box for
  ECMO and PCPS life-support procedures. Motor speed control, biological
  parameter monitoring (temperature/pressure), Wi-Fi comms for real-time
  monitoring/logging via tablet.
- **5W High-Reliability EDFA (Erbium-doped Fiber Amplifier)** —
  radiation-hardened (50K rad-hard) hardware for space-qualified booster
  modules. STM32 microcontrollers with external DAC/ADC, hot-swap
  protection, used in industrial laser cutting applications too.

## Education
- Post Graduate Diploma, Keltron Education, Trivandrum — Advanced Embedded
  System Design
- Bachelor's degree, Kerala University, Trivandrum — Electronics and
  Communication

## Generation rules for the LLM
1. Every "based on experience" answer must trace to a project/role above.
   Do not invent metrics, part numbers, or outcomes not listed here.
2. General knowledge questions (e.g. "what is I2C clock stretching") don't
   need to reference a project, but a strong answer should still connect it
   to how/where it would matter in one of these projects if natural.
3. Prefer STAR-style structure (Situation, Task, Action, Result) for
   behavioral entries, using only the roles/projects above.
