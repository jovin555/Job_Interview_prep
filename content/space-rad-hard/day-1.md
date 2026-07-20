# space-rad-hard — Day 1

## Q1: What are the primary radiation effects that concern an embedded systems designer, and how would you mitigate them in a circuit design?

**Answer:** The main radiation effects fall into two categories: total ionizing dose (TID) and single-event effects (SEE). TID is cumulative — over time, ionizing radiation builds up trapped charge in oxide layers, shifting threshold voltages in MOSFETs and eventually causing parametric failure or functional breakdown. SEE includes single-event upsets (SEUs) where a single energetic particle flips a memory bit, single-event latch-up (SEL) where it triggers a parasitic SCR structure that creates a low-impedance path (potentially destructive), and single-event gate ruptures (SEGR) in power MOSFETs.

Mitigation starts at component selection: use radiation-hardened (rad-hard) or radiation-tolerant parts rated for the expected TID (e.g., 50 krad or 100 krad). For COTS components, you'd characterize them or derate aggressively. On the circuit level, add guard rings around sensitive CMOS structures to collect stray charge and prevent latch-up. For power supplies, current-limiting circuits can detect latch-up and cycle power before damage occurs. For SEUs in memory or logic, use triple-modular redundancy (TMR) — triplicate the logic and vote — plus EDAC (error detection and correction) on memories, and periodic scrubbing of configuration memory in FPGAs. Shielding (e.g., aluminum or tantalum) helps reduce TID but adds mass, so it's a trade-off in space applications.

**Possible follow-ups:** How would you decide between using a rad-hard part versus a radiation-tolerant COTS part with mitigation? What about single-event transients (SETs) in analog or mixed-signal paths?

---

## Q2: How would you approach designing a power supply for a space-deployed embedded system that must survive a 50 krad total ionizing dose?

**Answer:** I'd start by selecting power components with known radiation tolerance — either qualified rad-hard DC-DC converters or COTS parts with published test data for the expected dose. Linear regulators are generally more radiation-tolerant than switching regulators because they lack complex control loops and magnetic components that can degrade, but they're less efficient. For a switching supply, the key concerns are the power MOSFET (SEGR risk) and the control IC (SEU and TID). I'd use a rad-hard MOSFET or derate a COTS part significantly, and choose a control IC with a simple, proven topology (e.g., current-mode control) that's been characterized.

On the board level, I'd add redundancy: a primary and secondary converter with OR-ing diodes, so if one fails (e.g., from latch-up or parametric drift), the other takes over. Input filtering with transient-voltage suppressors (TVS) rated for single-event transients is important. I'd also include current-monitoring and a watchdog that can cycle power to a latch-up section. For the output, I'd use derated capacitors — ceramic with COG/NP0 dielectric (less prone to TID-induced leakage than X7R) and tantalum with voltage derating of 50% or more to avoid catastrophic failure. Finally, I'd simulate the thermal profile because radiation-induced leakage current increases power dissipation, and that can create a positive-feedback thermal runaway.

**Possible follow-ups:** How would you test or verify that the power supply meets its radiation requirements? What failure modes would you prioritize in a worst-case analysis?

---

## Q3: You're debugging a microcontroller in a space-deployed system that intermittently resets or produces corrupted data. How would you determine whether radiation is the cause?

**Answer:** I'd approach this systematically, ruling out non-radiation causes first. Start with the power supply: use an oscilloscope to check for glitches, droops, or noise on the supply rails — a momentary dip could cause a brown-out reset. Check the watchdog timer configuration and whether it's being triggered by a software hang rather than a hardware event. Look at the clock source: a crystal oscillator can be sensitive to vibration or temperature, though in space the main concern is radiation-induced frequency shifts or phase noise.

If those are clean, I'd look for radiation signatures. SEUs in memory or registers can cause corrupted data — I'd check if the corruption follows a pattern (e.g., single-bit flips in a predictable location) or occurs during periods of higher solar activity (if telemetry timestamps are available). For resets, a single-event latch-up would draw excess current, so I'd examine current telemetry for spikes preceding the reset. If the system has a watchdog that logs the reset source register, that can tell you whether it was an external reset, brown-out, or software-initiated.

To confirm radiation, I'd add diagnostic features: a memory scrubber that logs corrected errors, a current monitor with high-resolution logging, and a radiation monitor (e.g., a PIN diode detector) if the system can accommodate it. In a lab environment, you'd replicate the issue with a radiation source (e.g., a cobalt-60 gamma source for TID or a proton beam for SEE) to reproduce the failure mode. Without that, you'd rely on statistical analysis of error rates versus the expected space environment.

**Possible follow-ups:** What if the resets are too infrequent to reproduce in testing? How would you design a software-based mitigation for SEU-induced resets?

---

## Q4: How would you design a firmware architecture for a radiation-hardened system to ensure reliable operation over a multi-year mission?

**Answer:** The firmware architecture should assume that any memory cell or register can flip at any time, so the design must be defensive by default. I'd start with a supervisor architecture: a hardware watchdog timer that's independent of the main processor, with a timeout that forces a full reset if the main loop doesn't service it. The main firmware would run in a cyclic executive or a simple RTOS with memory protection (if the MCU supports it), but I'd avoid dynamic memory allocation entirely — no malloc, no heap — because heap corruption from an SEU is catastrophic and hard to detect.

For critical data, I'd use triple-modular redundancy (TMR) in software: store three copies of each critical variable (e.g., state machine state, sensor calibration constants, communication sequence numbers) and vote on read. For non-critical data, single-bit error correction codes (ECC) on memory are sufficient. I'd implement a periodic memory scrubber that reads through all critical data structures, corrects single-bit errors, and logs multi-bit errors. The bootloader should support remote firmware update with rollback capability, because a corrupted flash image could brick the system.

For the control flow, I'd use a state machine with a "safe" state that the system enters on any anomaly — for example, if a sensor reading is out of range or a communication timeout occurs, transition to a safe mode that powers down non-essential subsystems and waits for ground command. I'd also include a "heartbeat" telemetry packet that reports system health (current draw, temperature, error counters, last reset cause) so ground operators can detect degradation trends. Finally, I'd design the firmware so that a watchdog reset restores the system to a known good state without requiring ground intervention — the system should be self-healing for single-event upsets.

**Possible follow-ups:** How would you test the firmware's radiation tolerance in a lab? What trade-offs exist between using an RTOS versus a bare-metal cyclic executive in a rad-hard system?

---

## Q5: Imagine you're leading a team designing a radiation-hardened control board for a space mission, and a junior engineer proposes using a popular, low-cost COTS microcontroller instead of a qualified rad-hard part. How would you handle this disagreement?

**Answer:** I'd start by acknowledging the engineer's reasoning — COTS parts are cheaper, easier to source, have better development tools, and often perform better in terms of speed and power. Then I'd frame the discussion around risk and mission requirements. The key question is: what is the radiation environment and mission duration? For a low-earth-orbit (LEO) mission of a few months, a COTS part with mitigation (e.g., shielding, TMR in software, watchdog) might be acceptable. For a geostationary or deep-space mission of years, the cumulative TID and SEE rate would likely exceed the COTS part's tolerance.

I'd walk through a structured trade-off: list the radiation requirements (TID, SEE rate, latch-up immunity), compare the COTS part's known or assumed performance against those requirements, and identify the gaps. If the COTS part has no published radiation data, we'd need to budget for characterization testing (e.g., proton beam testing for SEE, cobalt-60 for TID) — that adds cost and schedule risk. I'd also consider the system-level impact: if the COTS part fails, can the system recover? For example, if it's a non-critical telemetry processor, a reset might be acceptable; if it's the main flight computer, it's not.

Ultimately, I'd propose a compromise: use the COTS part for a non-critical subsystem (e.g., a housekeeping monitor) where failure is tolerable, and use a rad-hard part for the critical control path. Or, if the COTS part is the only option, we'd implement extensive mitigation (redundant processors, voting, latch-up detection with power cycling) and test thoroughly. The decision should be documented in a trade study with clear rationale, so the team understands the risk acceptance. My role as lead is to guide the team to a decision that balances cost, schedule, and mission success — not to dictate, but to ensure the trade-offs are understood.

**Possible follow-ups:** What if the rad-hard part is unavailable due to supply chain issues? How would you quantify the risk of using a COTS part without radiation test data?