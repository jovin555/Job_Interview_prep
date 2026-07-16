# medical-devices — Day 1

## Q1: What are the key differences between designing for IEC 60601 compliance versus general commercial electronics?

**Answer:** IEC 60601 introduces requirements that simply don't exist in commercial design. The most critical difference is **patient leakage current** — you must ensure that even under single-fault conditions, current through a patient cannot exceed specified limits (typically 10 µA for BF-type applied parts, 50 µA for CF-type). This drives isolation architecture from the start: you need reinforced or double insulation between mains and patient-accessible circuits, creepage distances of 8mm or more depending on voltage and pollution degree, and often two independent protection mechanisms (2MOPP/1MOPP). 

Another major difference is **risk management per ISO 14971** integrated into the design process. Every component failure mode must be analyzed for its effect on patient safety. For example, on the **Project Y** project at Company A, we discovered during IEC 60601 testing that a particular protection diode's failure mode could create a leakage path to the patient. We had to redesign the isolation barrier layout and add a redundant series component to achieve 2MOPP. This kind of failure analysis isn't typical in commercial electronics where you might just add a fuse and move on.

**Possible follow-ups:**
- How do you test for patient leakage current during development?
- What's the difference between BF and CF applied parts, and when would you use each?

---

## Q2: Describe a time you had to resolve a critical issue discovered during regulatory testing of a medical device.

**Answer:** (STAR format)

**Situation:** During IEC 60601 compliance testing of the **Project Y** system at Company A, we ran into a circuit design issue that caused intermittent failures in the uterine contraction monitoring channel. The device uses a pressure sensor to noninvasively monitor contractions during labor — reliability is absolutely critical because clinicians make delivery decisions based on this data.

**Task:** I needed to identify the root cause of the signal integrity issue, implement a fix, and get the device through retesting without delaying the regulatory submission timeline.

**Action:** I led an 8D root-cause investigation. We traced the problem to insufficient decoupling on the analog front-end power rail, which created noise injection into the pressure sensor signal chain when the printer motor drew current. I redesigned the PCB layout to add dedicated local decoupling capacitors closer to the sensor amplifier, separated the analog and digital ground planes with a star-point connection, and added ferrite beads on the power trace feeding the analog section. We also updated the test protocol to include worst-case simultaneous printing and monitoring scenarios.

**Result:** The redesign cut signal noise by 15% (confirmed by before/after measurements), and the device passed all IEC 60601 EMC and performance tests on the next attempt. The fix was incorporated into the production design, and no field failures related to this issue have been reported.

**Possible follow-ups:**
- What specific decoupling values did you choose and why?
- How did you isolate the problem between the printer motor and the sensor channel?

---

## Q3: How would you design a power management system for a portable medical device that must operate continuously for 7 days?

**Answer:** Drawing from the **Project X** project, which required 7-day continuous operation from a Li-ion battery, the approach involves several layers:

First, **battery capacity sizing**: You calculate total system power draw across all operating modes (active therapy, standby, LED feedback, sensor polling) and add margin for battery aging and temperature derating. For Project X, we targeted a 20-30% capacity margin above the calculated minimum.

Second, **power architecture**: Use a high-efficiency buck-boost regulator to maintain stable output as the Li-ion cell voltage drops from 4.2V to ~3.0V. Select a converter with >90% efficiency across the load range. Include a fuel gauge IC with coulomb counting for accurate remaining capacity estimation — critical for clinical confidence.

Third, **low-power mode management**: The microcontroller (running Zephyr RTOS) should spend most of its time in deep sleep, waking periodically to check the pressure sensor for breathing events. Each subsystem must have independent power gating — the RGB LED driver, for instance, draws significant current and should only be powered during active feedback windows.

Fourth, **safety and protection**: Include over-discharge protection (cut off at ~3.0V/cell to prevent damage), over-current protection, and cell balancing if using multi-cell packs. For a medical device, you also need redundant protection — a primary fuel gauge with cutoff FET and a secondary hardware voltage comparator as backup.

**Possible follow-ups:**
- How do you handle battery charging while the device is in use?
- What happens if the battery estimation drifts over time — how do you recalibrate?

---

## Q4: Explain how you would approach isolation design for a medical device that communicates with a tablet over Wi-Fi while monitoring patient vitals.

**Answer:** This is directly relevant to the **Project Z** project, which had Wi-Fi communication to a tablet for real-time monitoring of ECMO/PCPS life-support parameters.

The key principle is that **any data leaving the patient-connected circuitry must cross an isolation barrier** before reaching the Wi-Fi module, which is connected to the outside world. The architecture would be:

1. **Patient-side domain**: All sensors (temperature, pressure), analog front-ends, and the primary microcontroller that processes biological parameters stay on the isolated patient side. This domain is powered by a medically approved isolated DC-DC converter (e.g., 5V input, 5V output with 5000VAC isolation rating).

2. **Isolation barrier**: Use digital isolators (like ISO7240 or ADuM series) for all data signals crossing the barrier — SPI or UART between the patient-side MCU and the communication-side MCU. These provide reinforced isolation with >8mm creepage.

3. **Communication side**: A secondary microcontroller handles Wi-Fi protocol stack, data formatting, and tablet communication. This side is non-patient-connected, so it doesn't need the same stringent leakage current requirements.

4. **Data integrity**: Add CRC checks on all data crossing the barrier, and implement a watchdog that alerts the tablet if the isolation link fails. For life-support data, you might also buffer critical parameters on the patient side so no data is lost during brief communication interruptions.

The critical design rule: **never let a ground or signal path bypass the isolation barrier**. This means separate ground planes, optocouplers or digital isolators for every crossing signal, and careful PCB layout to maintain creepage distances.

**Possible follow-ups:**
- What happens if the Wi-Fi connection drops during a procedure?
- How do you ensure the isolation barrier doesn't introduce latency that affects real-time monitoring?

---

## Q5: What are the most common pitfalls you've seen in medical device firmware development, and how do you avoid them?

**Answer:** Based on experience across multiple medical device projects including the **Project X** and **Project Z**, the most critical pitfalls are:

**1. Watchdog timer misuse or absence.** In medical devices, a firmware hang can be life-threatening. You need a properly configured independent watchdog timer (IWDG in STM32 terms) that resets the system if the main loop stops responding. But the trap is feeding the watchdog from interrupt contexts or without actually verifying system health — the watchdog should only be kicked after confirming all critical tasks have completed. On the Project Z, we implemented a "supervisory loop" that checked motor speed control, sensor readings, and communication health before clearing the watchdog.

**2. Insufficient error handling for sensor failures.** Medical sensors will fail — they drift, saturate, or lose connection. Firmware must detect these conditions and transition to a safe state. For Project X's pressure sensor, we implemented sanity checks (reading must be within expected physiological range), stuck-bit detection (value hasn't changed for N consecutive samples), and communication integrity checks (CRC on each sensor read). If any check fails, the device alerts the user and enters a fail-safe mode rather than continuing with potentially incorrect data.

**3. Race conditions in RTOS task scheduling.** Zephyr RTOS enables multiple tasks, but shared resource access without proper mutexes or semaphores can cause data corruption. A common pattern: a sensor reading task writes to a shared buffer, while a display task reads from it. Without a mutex, the display might read partially updated data. We caught this during code review on the Project Z — the motor control task and the data logging task shared a speed variable without synchronization. Adding a mutex with a short timeout prevented data corruption without blocking critical control loops.

**4. Ignoring real-time constraints.** Medical devices often have hard real-time requirements. For Project X, the pressure sensor needed to be sampled at exactly 100Hz to accurately capture breathing waveforms. Using a hardware timer to trigger ADC conversions (rather than relying on RTOS task timing) ensured consistent sampling regardless of other system activity.

**Possible follow-ups:**
- How do you test for race conditions in an RTOS-based medical device?
- What's your approach to firmware update safety — how do you handle a failed update in the field?