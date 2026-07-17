# medical-devices — Day 2

## Q1: What are the key differences between designing for IEC 60601 compliance versus commercial/industrial electronics, and how did these requirements affect your PCB layout decisions on the Lotus (Printer and Toco) project?

**Answer:** IEC 60601 introduces requirements that fundamentally change hardware design priorities compared to commercial electronics. The most critical differences include: **patient leakage current limits** (typically <10 µA for applied parts), **creepage and clearance distances** that are significantly larger than general PCB design rules, **two means of patient protection (2MOPP)** requirements, and **dielectric strength testing** (e.g., 1500V AC hipot testing between patient-connected circuits and mains).

On the Lotus project—specifically the Toco device for noninvasive uterine contraction monitoring—these requirements drove several layout decisions. The Toco device is an applied part that contacts the patient during labor, so we had to ensure galvanic isolation between the sensor front-end and any digital processing or power circuitry. I increased creepage distances between primary and secondary sides beyond standard IPC-2221 recommendations, used slot cuts in the PCB under optocouplers and isolated DC-DC converters to prevent surface tracking, and selected components with reinforced isolation ratings. We also had to route sensitive analog traces from the pressure sensor away from any high-speed digital lines to prevent coupling that could create unintended leakage paths during hipot testing. During IEC 60601 testing, we actually discovered a clearance issue near a mounting hole that was too close to a mains-referenced trace—this required a board respin to add a routed slot, which I then documented in the 8D root-cause process.

**Possible follow-ups:**
- How did you verify creepage and clearance distances in Altium Designer before sending the board to fabrication?
- What specific test failed during IEC 60601 testing on the Lotus project, and how did you resolve it?

---

## Q2: Describe a time when you had to troubleshoot a critical failure in a medical device during regulatory testing. What was your approach, and what was the outcome?

**Answer:** *(Behavioral/Experience question — STAR format)*

**Situation:** During IEC 60601 compliance testing for the **Lotus (Printer and Toco)** project, we encountered a failure during the dielectric strength (hipot) test. The test applied 1500V AC between the patient-connected circuit and the secondary ground, and we observed breakdown at approximately 1100V—well below the required threshold. This was a critical issue because it meant the device did not meet basic safety isolation requirements, and it threatened the entire project timeline.

**Task:** As the Electronics Design Engineering Specialist, I needed to identify the root cause of the isolation breakdown, implement a corrective design change, and ensure the fix passed re-testing without introducing new issues or delaying the regulatory submission.

**Action:** I led an 8D root-cause investigation. First, I visually inspected the PCB under a microscope and identified that a via near the transformer on the isolated power supply had insufficient annular ring clearance to a ground plane on an adjacent layer—the clearance was only 0.3 mm instead of the required 1.5 mm for 2MOPP at 1500V. I cross-referenced the layout against the IEC 60601-1 Table 6 creepage/clearance requirements and confirmed the violation. I then redesigned that section of the PCB: I moved the via, increased the slot gap around the transformer, added a routed slot between primary and secondary sides, and updated the Altium Designer design rules to flag any clearance below 1.5 mm for patient-connected circuits. I also reviewed all other isolation boundaries on the board to catch similar issues proactively.

**Result:** The redesigned PCB passed the dielectric strength test at 1500V AC with margin. The fix required only a single board respin and added two weeks to the schedule, which was acceptable. The 8D report was submitted to the regulatory body as part of the design history file, and the Lotus device ultimately received Health Canada clearance. This experience also led me to create a checklist for future medical device layouts that pre-validates creepage/clearance against IEC 60601 before fabrication.

**Possible follow-ups:**
- How did you ensure the fix didn't introduce new EMC or signal integrity problems?
- What was the most challenging part of explaining this failure to the regulatory test house?

---

## Q3: How would you design a power management system for a portable medical device that must operate continuously for 7 days, and what battery chemistry and protection features would you prioritize?

**Answer:** This directly maps to the **Smart OPEP Device** project, which required 7 days of continuous use from a Li-ion battery. The design approach involves three layers: **cell selection, power path management, and safety/protection circuitry**.

For **cell selection**, Li-ion is the standard for medical portables due to energy density. I would use a single-cell or two-series configuration depending on voltage requirements—for the OPEP device, we used a single 3.7V nominal cell with a boost converter to generate 5V for the pressure sensor and RGB LED, and a 3.3V LDO for the microcontroller. Capacity must be calculated based on worst-case current draw: sensor sampling rate, LED duty cycle, and MCU sleep current. For 7 days, we targeted a 5000 mAh cell with 20% derating for aging and temperature.

For **power path management**, I'd implement a dedicated power management IC (PMIC) with dynamic power path control so the device can run from USB power while charging the battery simultaneously, without interrupting operation. The OPEP device used a TI BQ2407x charger with power-path architecture. This also enables "instant-on" even with a deeply discharged battery.

For **protection features**, medical devices require redundant safety: over-voltage protection (OVP) at 4.2V per cell, under-voltage lockout (UVLO) at 3.0V to prevent deep discharge damage, over-current protection (OCP) with a PTC resettable fuse, and temperature monitoring via an NTC thermistor bonded to the cell. Additionally, IEC 60601 requires that a single-fault condition (e.g., a shorted FET in the charger) cannot cause patient harm—so we added a second independent OVP IC on the output rail. The OPEP device also included a fuel gauge IC (TI BQ27441) for accurate remaining capacity reporting, which was critical for the 7-day usage guarantee.

**Possible follow-ups:**
- How do you handle battery charging when the device is in use by a patient (e.g., charging while monitoring)?
- What thermal management considerations are unique to medical devices versus consumer electronics?

---

## Q4: Explain how you would implement noninvasive pressure sensing for uterine contraction monitoring, including sensor selection, signal conditioning, and noise mitigation strategies.

**Answer:** For the **Lotus Toco device**, noninvasive uterine contraction monitoring requires measuring the mechanical pressure changes on the maternal abdomen during labor. This is fundamentally different from invasive intrauterine pressure catheters—we're measuring through tissue, so the signal is low-amplitude (typically 0–100 mmHg range, with 1–2 mmHg resolution needed) and subject to motion artifacts.

**Sensor selection:** I would use a MEMS-based piezoresistive pressure sensor with a silicone gel interface to the abdomen. For the Toco device, we selected a sensor with a 0–300 mmHg range, ratiometric analog output, and built-in temperature compensation. The sensor must be medical-grade with biocompatible materials contacting the patient's skin.

**Signal conditioning:** The raw sensor output is in the millivolt range, so a precision instrumentation amplifier (e.g., AD8226 or INA333) with gain of approximately 100–200 is needed to bring the signal into the 0–3.3V ADC range. I'd use a 2nd-order Sallen-Key low-pass filter with a cutoff around 5 Hz to reject high-frequency noise while preserving the contraction waveform (typical contraction duration is 30–90 seconds). A DC-blocking capacitor after the amplifier removes the baseline offset, and a software baseline tracking algorithm re-centers the signal.

**Noise mitigation strategies:** Three key approaches were used on the Toco device. First, **PCB layout**: the analog front-end was isolated on a separate ground plane with a single-point connection to the digital ground, and all traces from the sensor connector were kept as short as possible with guard rings around the high-impedance inputs. Second, **shielding**: the sensor cable was a shielded twisted pair, with the shield driven by a guard buffer to reduce capacitive coupling from patient movement. Third, **digital filtering**: after the 12-bit ADC sampling at 100 Hz, we applied a moving average filter with a 1-second window and a median filter to reject motion artifacts caused by the patient shifting position. During testing, these techniques reduced baseline drift by approximately 15% compared to the initial prototype.

**Possible follow-ups:**
- How do you calibrate the pressure sensor for each patient, given differences in abdominal tissue?
- What happens if the patient moves suddenly—how does the device distinguish artifact from a real contraction?

---

## Q5: What are the most critical firmware considerations when developing a life-support device like the SOBA Heart-Lung Support Machine, and how would you ensure real-time reliability?

**Answer:** The **SOBA — Heart Lung Support Machine** is an ECMO/PCPS life-support device, so firmware failures are literally life-threatening. The critical considerations are **deterministic timing, fault detection and safe-state transitions, watchdog architecture, and communication reliability**.

**Deterministic timing:** The motor speed control loop for the centrifugal pump must run at a fixed rate (e.g., 1 kHz) with jitter under 100 µs. On the SOBA project using Zephyr RTOS, I configured the motor control as a high-priority thread with a hardware timer triggering a semaphore, rather than relying on RTOS ticks which can have variable latency. All interrupt service routines (ISRs) were kept under 10 µs, and any non-critical logging or Wi-Fi communication ran in lower-priority threads.

**Fault detection and safe states:** The firmware must continuously monitor biological parameters (temperature, pressure) and motor status. I implemented a three-tier fault response: (1) **warnings** — parameters slightly out of range, logged and displayed but no action; (2) **alarms** — parameters approaching critical limits, triggers audible/visual alert and reduces motor speed gradually; (3) **emergency stop** — parameters exceeding absolute limits (e.g., pressure > 400 mmHg), immediately stops the motor and engages a mechanical brake, then transitions to a safe state where the control box maintains basic monitoring but disables the pump. The safe state must be fail-safe: if the MCU crashes, the watchdog timer resets the system into the safe state by default.

**Watchdog architecture:** I used a dual-watchdog approach: an internal windowed watchdog in the STM32 that checks the main loop executes within 100 ms, and an external watchdog IC (e.g., TPS3823) that monitors a heartbeat from the motor control thread. If either watchdog expires, the system enters safe state. The external watchdog is critical because it can reset the MCU even if the internal watchdog fails.

**Communication reliability:** The Wi-Fi link to the tablet for real-time monitoring/logging must not interfere with the control loop. I implemented a publish-subscribe pattern where sensor data is written to a ring buffer by the control thread, and the Wi-Fi thread reads from the buffer at its own pace. If the Wi-Fi connection drops, the device continues operating autonomously and buffers up to 1 hour of data in flash memory for later retrieval. The tablet connection is advisory, not critical—the device must function perfectly without it.

**Possible follow-ups:**
- How did you test the fault detection logic to ensure no false positives during normal operation?
- What happens if the external watchdog IC itself fails—how do you protect against that single point of failure?