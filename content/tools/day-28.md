# tools — Day 28

## Q1: How would you approach setting up a Zephyr RTOS project to support runtime calibration of an analog sensor front-end, where the calibration coefficients need to be stored in flash and survive firmware updates?

**Answer:** I'd structure this around three concerns: where calibration data lives, how it's protected, and how it's accessed at runtime.

For storage, I'd use a dedicated flash partition separate from the firmware image — Zephyr's flash map API and the settings subsystem (or NVS, the non-volatile storage module) are designed for exactly this. The key is that the calibration partition is never touched by the firmware update process; the bootloader only writes to the firmware slot. This way, a firmware update can't accidentally wipe calibration data.

For the data format, I'd define a versioned structure with a header containing a magic number, version, CRC or checksum, and the coefficients themselves. The version field is critical — if a future firmware release changes the calibration algorithm or coefficient format, the code can detect the old version and either migrate the data or trigger a recalibration.

For runtime access, I'd create a dedicated driver or module that loads the coefficients once at boot into RAM, validates the CRC, and provides a clean API for the sensor reading code. If the CRC fails or the data is invalid, the system should fall back to default coefficients and flag a warning — in a medical device context, you'd want this to be a visible alert, not a silent failure.

For the update path, I'd add a calibration write function that's only accessible through a controlled interface — for example, a factory test mode or a service command — and that writes the new coefficients atomically (write to a staging area, validate, then commit). This prevents a power loss mid-write from corrupting the active calibration.

**Possible follow-ups:**
- How would you handle the case where the calibration data is corrupted but the device is already in the field?
- How would you design the calibration data structure to be forward-compatible with future sensor revisions?

---

## Q2: How would you approach using a logic analyzer to debug a USB 2.0 device that enumerates correctly on some hosts but fails on others, where the failure is intermittent and appears to be timing-related?

**Answer:** USB enumeration timing failures that are host-dependent are classic signal-integrity or timing-margin issues. I'd approach this systematically.

First, I'd capture the full enumeration sequence on both a working and a failing host, using the logic analyzer with USB protocol decoding enabled. I'd compare the timing of key events — specifically the device's response to the GET_DESCRIPTOR request, the SET_ADDRESS command, and the configuration request. The critical timing window is the device's response time to SET_ADDRESS: the USB spec requires the device to complete the status stage within a specific time, and some hosts are more lenient than others.

Second, I'd look at the electrical characteristics. Even though a logic analyzer gives you digital timing, I'd use it to check for marginal signal quality — for example, if the D+ and D- edges are slow or have excessive ringing, the logic analyzer might still decode them correctly, but a host with a stricter receiver threshold might not. I'd correlate the logic analyzer captures with oscilloscope measurements of the same signals, looking at rise/fall times, eye diagram quality, and whether the signal levels are within spec.

Third, I'd check the device's firmware for timing dependencies. A common issue is that the device takes too long to respond because the firmware is doing too much work in the interrupt handler, or because the USB clock is derived from a source that drifts. I'd look at the time between the host's request and the device's response across multiple captures to see if there's jitter that could push the response past the timeout on stricter hosts.

Finally, I'd check the cable and connector — a marginal connection or an out-of-spec cable can cause intermittent timing issues that only manifest on certain hosts with different receiver characteristics.

**Possible follow-ups:**
- What specific timing parameters in the USB 2.0 spec would you check first?
- How would you distinguish between a firmware timing issue and a hardware signal integrity issue?

---

## Q3: How would you approach setting up a component library management strategy in Altium Designer for a medical device project that needs to maintain strict revision control and regulatory traceability?

**Answer:** For a medical device project, the component library isn't just a design convenience — it's part of the design history file (DHF) and needs to be traceable. I'd structure the strategy around three layers: the library itself, the revision control system, and the traceability documentation.

For the library structure, I'd use a centralized managed library approach — either Altium 365 or a local server-based vault — rather than scattered schematic symbols and footprints. Each component would have a unique identifier that ties together the schematic symbol, PCB footprint, 3D model, and datasheet. The key is that the library item itself has a revision, so when a component changes — say, a manufacturer updates the datasheet or you discover a footprint error — you create a new revision of the library item, not a new component.

For revision control, I'd integrate the library with the same version control system used for the project — Git or SVN. The library database or files should be under version control, and I'd enforce a workflow where library changes go through review before being committed. In a medical device context, this review should include a check that the change doesn't affect any existing designs that use the component — you don't want to update a footprint and silently break a board that's already in production.

For traceability, I'd maintain a component traceability matrix that maps each component in the BOM to its library item revision, the datasheet revision it was validated against, and any relevant compliance documentation (e.g., RoHS, REACH, biocompatibility for materials that contact the patient). This matrix should be generated as part of the design release process, not maintained manually. In Altium, this can be done through the managed library's reporting features or through a custom script that extracts the data.

The critical discipline is that the library is treated as controlled documentation — changes are logged, reviewed, and approved, just like schematic changes. This is what allows you to answer the regulatory question: "What exact component was used in the device that was tested, and how do we know it's the same one in production?"

**Possible follow-ups:**
- How would you handle a component that becomes obsolete and needs a substitute mid-project?
- What information would you require in a component's library entry to consider it "release-ready" for a medical device?

---

## Q4: How would you approach using a spectrum analyzer with a near-field probe to determine whether a radiated emissions failure at 150 MHz is coming from a switching regulator's harmonic or from a digital clock, and how would you confirm your hypothesis?

**Answer:** This is a classic EMI source identification problem, and the approach is to systematically narrow down the source using both frequency-domain and spatial information.

First, I'd calculate the expected frequencies. If there's a 25 MHz clock, 150 MHz is the 6th harmonic. If there's a 500 kHz switching regulator, 150 MHz is the 300th harmonic — which is unlikely to have significant energy unless there's a resonance or ringing. More likely, if it's a switching regulator, it would be a harmonic of a higher-frequency switching converter, say a 2 MHz switcher (75th harmonic) or a 5 MHz switcher (30th harmonic). I'd list all the clocks and switching frequencies in the design and compute their harmonics to see which ones land near 150 MHz.

Second, I'd use the near-field probe to map the spatial distribution of the 150 MHz emission across the board. A clock harmonic will typically be strongest near the clock source, the clock trace, or the IC that uses the clock. A switching regulator harmonic will be strongest near the inductor, the switching node, or the output capacitors. By moving the probe across the board and watching the amplitude at 150 MHz on the spectrum analyzer, I can create a hot-spot map.

Third, I'd use a key distinguishing test: turn off or disable the suspected source. If I can disable the switching regulator (e.g., through a firmware command or by removing its enable jumper) and the 150 MHz emission disappears, that confirms it. Similarly, if I can halt the clock (e.g., by holding the microcontroller in reset) and the emission disappears, that confirms the clock. This is the most definitive test.

Fourth, I'd look at the harmonic pattern. A clock source will typically show a series of harmonics at integer multiples of the fundamental — 25, 50, 75, 100, 125, 150 MHz — with a characteristic roll-off. A switching regulator will show harmonics of its switching frequency, but the pattern may be more irregular, and there may be broadband noise from the switching transients rather than clean harmonics.

Finally, I'd confirm by measuring the signal at the source with an oscilloscope — for example, probing the clock pin or the switching node to see if the 150 MHz component is present in the time-domain waveform and correlates with the spectrum analyzer measurement.

**Possible follow-ups:**
- What if the emission is present even when both the clock and the regulator are disabled — where would you look next?
- How would you determine whether the emission is being radiated directly from the source or coupled onto a cable or connector?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** This is a high-pressure situation, but the first thing I'd do is slow down the "who's right" debate and focus on getting the facts on the table. Both teams being confident doesn't matter — what matters is what the hardware actually does and what the firmware actually expects.

My first step would be to call a short, focused meeting with both teams, but not to argue — to gather information. I'd ask the hardware team to show me the schematic and the datasheet for the sensor, specifically the address pins and the register map. I'd ask the firmware team to show me the driver code and the sensor datasheet they used. The goal is to identify where the divergence happened — was it a datasheet revision issue, a misread of the address pins, or a copy-paste error from a different sensor?

Once I have the facts, I'd determine which side is actually correct — or whether both are partially wrong. For example, the hardware might be correct for the physical sensor, but the firmware might be using a driver from a different sensor variant. Or the hardware might have the address pins strapped incorrectly for the intended register map.

Then I'd assess the impact. Can the firmware be changed to match the hardware in two days? If it's just an address change and a register map update, that's likely feasible — it's a driver-level change, not an application-level rewrite. Can the hardware be changed? If the PCB is already fabricated, changing the address straps might require a rework, which is more expensive and time-consuming.

I'd then make a decision based on the risk assessment. If the firmware change is low-risk and can be verified quickly, I'd direct the firmware team to make the change, with a clear deadline and a verification plan. If the hardware change is necessary, I'd assess whether a rework is feasible or whether the schedule needs to shift.

Throughout this, I'd keep the focus on the engineering problem, not on blame. The junior engineers on both teams are likely feeling defensive, and the goal is to solve the problem, not to assign fault. I'd also document the root cause and the resolution so that the same class of error can be prevented in the future — for example, by adding a protocol/interface check to the design review checklist.

Finally, I'd communicate the situation to the project manager or stakeholders with a clear assessment of the impact on the integration testing schedule and what we're doing to mitigate it.

**Possible follow-ups:**
- What if the firmware change is more extensive than expected and can't be completed in two days — how would you reprioritize?
- How would you prevent this class of hardware-firmware interface mismatch from happening on future projects?