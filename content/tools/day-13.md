# tools — Day 13

## Q1: How would you approach setting up a Zephyr RTOS project to support over-the-air (OTA) firmware updates for a medical device that must maintain safety-critical functionality during the update process?

**Answer:** For a medical device, OTA updates introduce risk that needs to be managed carefully. I'd start by partitioning the flash memory into two application slots (A/B scheme) plus a small bootloader, so the device can roll back to the previous known-good firmware if the new image fails validation. The bootloader would be minimal and independently verified — it should only handle image integrity checks (hash/signature verification), slot selection, and jumping to the application; it should not contain any device logic.

On the Zephyr side, I'd use the MCUboot bootloader with the Zephyr image manager, configuring the flash layout via the device tree and partition manager. The application would use the DFU (Device Firmware Update) subsystem to receive the image over the existing wireless link, write it to the inactive slot, and trigger a swap only after the full image is received and its cryptographic signature is verified. For a medical device, I'd also want the update to be atomic — if power is lost mid-swap, the bootloader must be able to recover to a known-good state.

Safety-critical functionality during the update is the harder part. If the device is actively monitoring a patient, I would not interrupt that function. The approach would be to either (a) defer the update until the device is idle or in a non-critical state, or (b) run the update in a way that doesn't disturb real-time operations — for example, writing to the inactive slot while the active application continues running, then scheduling the swap at a safe point. I'd also add a "update available" flag that the application can check, so the device can decide when it's safe to proceed based on its current operational state.

**Possible follow-ups:**
- How would you handle the case where the new firmware fails to boot after the swap?
- What additional considerations would you have for regulatory approval of an OTA update mechanism in a Class II medical device?

---

## Q2: How would you approach using a spectrum analyzer with a near-field probe to differentiate between common-mode and differential-mode radiated emissions on a PCB?

**Answer:** The key distinction is that common-mode emissions are driven by the voltage difference between the PCB and its reference (e.g., the ground plane or the cable shield), while differential-mode emissions come from current loops on the board itself. They behave differently with distance and with probe orientation, so I can use that to tell them apart.

First, I'd set up the spectrum analyzer with the near-field probe and do a broad sweep to identify emission peaks. For each peak of interest, I'd then vary the probe position and orientation. A differential-mode source is localized — the field is strongest directly over the current loop, and it falls off very quickly (roughly 1/r² or faster) as I move the probe away. A common-mode source tends to be more distributed — the field is often stronger near cable connectors, board edges, or heatsinks, and it falls off more slowly.

I'd also use the probe's polarization. A loop probe is sensitive to the magnetic field perpendicular to the loop plane. By rotating the probe, I can determine the direction of the current flow. If the emission is coming from a specific trace loop (differential mode), the field will be strongest when the probe loop is aligned with that loop's axis. If it's common mode, the field pattern will be more uniform and tied to the overall board geometry rather than a specific trace.

Another useful technique is to compare measurements with and without the attached cables. If the emission level changes dramatically when I disconnect or re-route a cable, that's a strong indicator of common-mode radiation — the cable is acting as an antenna. If the emission is unchanged, it's more likely differential-mode from an on-board loop. Finally, I'd cross-check with a current probe on the cable: common-mode current on the cable will show up as a clear reading, while differential-mode on-board emissions won't couple strongly to the cable.

**Possible follow-ups:**
- Once you've identified an emission as common-mode, how would you go about suppressing it?
- How would you use a near-field probe to estimate the radiation efficiency of a specific trace loop?

---

## Q3: How would you approach setting up a multi-board bring-up test plan for a system with a main processor board, a sensor board, and a power distribution board, where the boards are connected via board-to-board connectors?

**Answer:** I'd structure the bring-up in stages, starting with the power board in isolation, then adding the processor board, and finally the sensor board. The principle is to verify each board's basic functionality before introducing the complexity of inter-board communication.

**Stage 1 — Power board alone:** Verify all output rails are present, within tolerance, and have acceptable ripple/noise. Check power sequencing if multiple rails are involved. I'd use an oscilloscope with proper probing (ground spring, not the long ground lead) to measure ripple. I'd also verify the current limits and protection circuits work — for example, shorting a test point through a current-limited supply to confirm the protection trips.

**Stage 2 — Power board + processor board:** Before connecting, I'd check for shorts between power and ground on the processor board, and verify the board's power input isn't reversed. Then connect and check that the processor's core voltage, I/O voltage, and any peripheral rails are correct. I'd then attempt to connect a debugger (e.g., Segger J-Link) and verify the processor can be halted, that the clock is running, and that basic memory access works. I'd also check the boot mode pins and any strap options.

**Stage 3 — Add sensor board:** Before connecting, verify the sensor board's power pins aren't shorted and that its interface pins (I2C, SPI, etc.) are at the correct idle levels. Then connect and check that the sensor board's power consumption is reasonable. I'd then bring up each interface one at a time — first I2C, then SPI, then any analog channels — using a logic analyzer to verify the protocol traffic and an oscilloscope to check analog signal levels.

Throughout, I'd keep a bring-up log documenting each test, the expected result, and the actual result. If something fails, I'd stop and debug that specific issue before proceeding — the whole point of staged bring-up is to isolate failures to a single board or interface rather than having to debug a system where multiple things could be wrong simultaneously.

**Possible follow-ups:**
- How would you decide what to test first if the processor board doesn't boot at all?
- What role would the board-to-board connector play in your bring-up strategy — how would you verify the connections themselves?

---

## Q4: How would you approach setting up a hardware-in-the-loop (HIL) test environment for a medical device that needs to verify firmware behavior against simulated sensor inputs?

**Answer:** For a medical device, HIL testing is valuable because it lets me exercise the firmware against realistic sensor signals without needing a physical patient or a full clinical setup. The core idea is to replace the real sensors with a simulator that generates electrical signals the device's analog front-end would see in real operation.

I'd start by defining the test scenarios — what physiological signals need to be simulated, what ranges, what failure modes (e.g., sensor disconnect, signal dropout, out-of-range values). Then I'd select the hardware: a function generator or arbitrary waveform generator for analog signals, possibly a DAQ (data acquisition) card for multiple synchronized channels, and a way to inject digital signals (e.g., for a digital sensor interface like I2C or SPI, I'd use a microcontroller or FPGA that can emulate the sensor's protocol behavior).

The key challenge is synchronization. If the device has multiple sensors that need to be sampled together (e.g., pressure and flow in a respiratory device), the simulated signals need to be phase-aligned. I'd use a single clock source and trigger the waveform generators from a common trigger signal. For digital sensors, the emulator needs to respond to the device's I2C/SPI transactions in real time — this is where a small microcontroller with a carefully written protocol emulator is useful.

On the firmware side, I'd want the device to run its normal application code — no special test hooks — so the HIL test validates the actual production firmware. The test harness would monitor the device's outputs (e.g., display, communication, actuator commands) and compare them against expected behavior for each simulated input scenario. I'd also inject fault conditions — like a sensor that suddenly reads zero or a signal that goes out of range — to verify the firmware's error handling.

Finally, I'd document the test setup thoroughly: the signal generation parameters, the expected outputs, and the pass/fail criteria for each scenario. This documentation is important for regulatory purposes — it shows the device was tested against a defined set of input conditions and behaved correctly.

**Possible follow-ups:**
- How would you verify that the HIL simulator is accurately representing the real sensor's electrical characteristics?
- How would you handle the case where the firmware's response to a simulated input is different from what you expected?

---

## Q5: (Behavioral) Imagine you are leading a project where the hardware team has delivered a PCB with a critical flaw — the power supply for the main microcontroller has a decoupling capacitor with the wrong voltage rating, and it's failing intermittently under load. The PCB is already in fabrication, the project is on a tight schedule, and the junior engineer who selected the capacitor is confident the rating is sufficient based on a datasheet they read. How would you handle this situation?

**Answer:** The first priority is to confirm the technical facts — I wouldn't want to override the junior engineer's judgment without solid evidence. I'd start by reviewing the specific capacitor's datasheet myself, focusing on the DC bias characteristics. Many ceramic capacitors lose a significant portion of their capacitance when DC voltage is applied — a 10 µF capacitor rated for 6.3 V might only provide 4 µF at 5 V. If the capacitor is operating near its rated voltage, the effective capacitance could be far below what the design requires, which would explain the intermittent failures under load.

I'd also look at the actual circuit: what's the nominal voltage on that rail, what's the ripple, and what are the transient conditions? If the rail is nominally 3.3 V but has transients up to 4 V, a 6.3 V-rated capacitor should be fine from a voltage standpoint — but if the derating curve shows the capacitance drops too much at 3.3 V DC bias, that's the problem.

Once I've confirmed the issue, I'd bring the junior engineer into the discussion. I'd walk through the DC bias curve together and explain why the effective capacitance matters more than the nominal value. The goal is to help them understand the engineering reasoning, not to assign blame. I'd acknowledge that the datasheet does list the capacitor as 6.3 V-rated, so their selection wasn't unreasonable — but the application requires looking beyond the headline rating.

For the immediate fix, I'd assess options: (a) if the PCB is still in fabrication, can we change the BOM to a higher-rated capacitor that's footprint-compatible? (b) if the board is already made, can we add a parallel capacitor in a spare footprint, or is there a rework option? (c) if neither is possible, can we reduce the transient voltage on that rail with a different power supply configuration? I'd also check if the same capacitor is used elsewhere on the board — if so, the issue might be more widespread.

Finally, I'd use this as a learning opportunity. I'd suggest adding a design rule to the component selection checklist: always check DC bias derating for ceramic capacitors on power rails, and document the effective capacitance in the design review materials.

**Possible follow-ups:**
- How would you handle the situation if the junior engineer still disagrees after you've shown them the DC bias curve?
- What would you do to prevent this type of issue from happening again in future designs?