# tools — Day 1

## Q1: What is your primary PCB design tool and what features do you rely on most for mixed-signal medical device layouts?
**Answer:** I primarily use Altium Designer for PCB layout, which I've used extensively at Trudell Medical International. For mixed-signal medical devices like the Smart OPEP Device, I rely heavily on Altium's layer stack manager to define controlled impedance stacks for high-speed signals, and the differential pair routing tools for sensitive analog traces. The component placement and interactive routing features are critical when I need to optimize decoupling capacitor placement—this directly contributed to the 15% signal noise reduction we achieved on that project. I also use the design rule checker extensively to enforce clearance rules that meet IEC60601 creepage and clearance requirements for medical safety isolation.

**Possible follow-ups:**
- How do you handle mixed-signal partitioning in Altium to prevent digital noise from coupling into analog sensor paths?
- Have you used Altium's multi-board assembly features for systems like the SOBA heart-lung support machine?

---

## Q2: Walk me through your firmware development toolchain for a Zephyr RTOS project.
**Answer:** For Zephyr RTOS development at Trudell Medical, my toolchain starts with VS Code as the editor, with the nRF Connect SDK plugin for project management and Zephyr configuration. I use West (Zephyr's meta-tool) for building, flashing, and managing multiple application repositories. For debugging, I rely on SEGGER J-Link debug probes with Ozone for real-time trace and variable monitoring—critical when debugging sensor timing issues on the Smart OPEP Device's pressure sensor capture. I also use Git for version control with a branching strategy that separates firmware releases for regulatory compliance tracking. For unit testing, I integrate Ceedling into the build pipeline to validate sensor fusion algorithms before hardware integration.

**Possible follow-ups:**
- How do you handle Zephyr device tree overlays when adding custom sensor peripherals?
- What debugging approach do you use when a Zephyr thread crashes in production?

---

## Q3: Describe a time you used simulation tools to validate a design before building hardware.
**Answer:** On the Lotus (Printer and Toco) project at Trudell Medical, we needed to verify the uterine contraction sensor analog front-end before committing to PCB fabrication. I used LTspice to simulate the instrumentation amplifier stage, including the filter response for the 0.1–3 Hz physiological signal band. The simulation revealed a gain peaking issue at the filter cutoff that would have caused measurement inaccuracies during labor monitoring. I adjusted the RC component values in simulation until the response was flat within 0.5 dB across the passband. This caught the problem before layout, saving a prototype spin. The design passed IEC 60601 testing on the first submission for that signal chain.

**Possible follow-ups:**
- Did you also simulate the power supply rejection ratio (PSRR) requirements for that medical sensor?
- How did you correlate simulation results with real-world measurements during compliance testing?

---

## Q4: What is your approach to version control for hardware design files, and how does it differ from software version control?
**Answer:** For hardware at Trudell Medical, I use Altium 365 for PCB project management, which provides version history, design reviews, and release management. Unlike Git for software, Altium 365 tracks schematic sheets, PCB layouts, and BOMs as a single design entity with revision numbering tied to our medical device design history file (DHF). Each revision gets a formal release with ECO (Engineering Change Order) approval, required for IEC 60601 design control. For the SOBA heart-lung support machine, we maintained separate branches for prototype, verification, and production releases, with each branch containing the complete design package—schematics, layout, BOM, and assembly drawings. This is critical because a medical device audit requires traceability from requirements through to the manufactured PCB.

**Possible follow-ups:**
- How do you handle component obsolescence tracking within your version control system?
- Do you use any automated BOM comparison tools between revisions?

---

## Q5: (Behavioral) Tell me about a time you had to learn a new tool quickly to solve a production issue.
**Answer:** At Vinvish Technologies, we had a critical production issue with a 5W high-power EDFA laser driver board where the hot-swap protection circuit was intermittently latching up during field installation. The original designer had used Cadence Allegro, but I was primarily an Altium user at that point. I had to learn Allegro's constraint manager and simulation tools within two days to analyze the hot-swap controller's layout parasitics. I used Allegro's SigXplorer to simulate the power-up sequence with extracted PCB parasitics, identified a trace inductance issue in the current sense path, and proposed a layout change. The fix was implemented in the next board spin, and the latch-up issue was eliminated. This experience later helped me when I moved to Trudell Medical, where I could work across both Altium and Allegro environments depending on the project.

**Possible follow-ups:**
- What specific resources did you use to ramp up on Allegro quickly?
- How did you validate your simulation results matched the actual hardware behavior?