# debugging-failure-analysis — Day 6

## Q1: A medical device passes all functional tests at the module level, but when integrated into the full system, a sensor reading drifts slowly over several hours. The drift is small — within the sensor's datasheet accuracy — but the system's algorithm treats it as a fault condition. How would you approach this?

**Answer:** This is a classic integration-level issue where the problem only emerges at the system boundary. I'd start by confirming the fault condition threshold in the algorithm — what specific delta or rate-of-change triggers the fault, and whether that threshold is appropriate for the sensor's actual drift characteristics. Sometimes the algorithm was written with an ideal sensor model in mind, and the real-world drift, while within spec, exceeds the fault detection window.

Next, I'd instrument the system to capture the sensor reading, the reference voltage (if the sensor uses an ADC with Vref), and the system temperature simultaneously over the drift period. The goal is to correlate the drift with an external variable. Common culprits in medical devices include:
- Temperature drift of the sensor or its signal conditioning components
- Reference voltage drift as the system warms up
- Self-heating of the sensor from continuous excitation current
- Power supply drift as the battery discharges or the regulator heats up

I'd also check whether the drift is present when the sensor is tested in isolation with a stable power supply and controlled temperature — if it's not, the root cause is likely in the system's power or thermal environment rather than the sensor itself. Once the correlating variable is identified, the fix could be as simple as adding a temperature compensation lookup table, adjusting the algorithm's fault threshold, or improving the reference voltage stability.

**Possible follow-ups:** How would you distinguish between sensor drift and actual physiological change in a patient monitoring context? What if the drift only appears in a specific production batch — how would you isolate the component-level cause?

---

## Q2: You're debugging a firmware crash that occurs when a medical device transitions from battery power to USB charging — but only about one in twenty times. The system uses a battery charger IC with a power-path architecture. How would you approach this?

**Answer:** This is a power-state transition bug, and the intermittent nature suggests a timing race condition rather than a static hardware fault. I'd approach it in layers:

First, I'd characterize the electrical behavior during the transition. Using an oscilloscope with deep memory, I'd capture the voltage rails (especially the system rail that powers the microcontroller), the battery voltage, the USB VBUS, and the charger's power-good or status output pin simultaneously during repeated transitions. I'm looking for glitches, droops, or sequencing issues — for example, does the system rail dip below the microcontroller's brown-out reset threshold during the switchover? Does the charger assert its status output before the rail is stable, causing the firmware to act on incomplete information?

Second, I'd review the firmware's power management state machine. The crash likely occurs because the firmware is in the middle of a critical operation (e.g., writing to non-volatile memory, communicating with a sensor) when the power source changes, and the interrupt handler or state transition doesn't properly handle the in-progress operation. I'd look for:
- Interrupts that fire during the transition but aren't properly masked or prioritized
- Shared resources (I2C bus, SPI bus) that get accessed from both the main loop and the power-management interrupt handler
- Timing assumptions — does the firmware wait for a status bit that takes longer to assert than expected?

Third, I'd add instrumentation — a GPIO toggle at key points in the power transition code, logged alongside the power rail captures — to correlate the electrical event with the firmware state at the moment of the crash.

**Possible follow-ups:** What if the crash is actually a hardware reset rather than a firmware crash — how would you distinguish between the two from the evidence available? How would you design a test fixture to reproduce this intermittently at a higher rate?

---

## Q3: A medical device's wireless communication (Bluetooth) drops connection intermittently, but only when the device is held in a specific orientation relative to the patient's body. The antenna is a chip antenna on the PCB. How would you approach this?

**Answer:** This sounds like an antenna detuning or body-loading effect. When a chip antenna is placed close to the human body, the body's dielectric properties (high permittivity and conductivity) shift the antenna's resonant frequency and reduce its radiation efficiency. The orientation-dependence suggests the antenna's near-field pattern interacts differently with body tissue depending on the device's position.

I'd start by characterizing the antenna's performance in free space versus on the body. Using a vector network analyzer (VNA), I'd measure the antenna's S11 (return loss) and resonant frequency in both conditions. A chip antenna that's well-matched at 2.45 GHz in free space might shift to 2.3 GHz or lower when placed against body tissue, causing significant mismatch loss at the operating frequency.

If detuning is confirmed, the solution options include:
- Selecting an antenna with a wider bandwidth to tolerate the frequency shift
- Adding a matching network that's optimized for the on-body condition (since that's the primary use case)
- Moving the antenna to a location on the PCB that's farther from the body or has more ground plane clearance
- Using a different antenna type (e.g., a PIFA or a custom flex antenna) that's less sensitive to body loading

I'd also check the Bluetooth receiver's RSSI during the connection drops to confirm it's a range/sensitivity issue rather than a protocol-level problem. If the RSSI is still high when the connection drops, the issue might be in the Bluetooth stack's handling of packet errors rather than the RF link itself.

**Possible follow-ups:** How would you test the antenna performance in a repeatable way that simulates body proximity? What regulatory implications does antenna detuning have for a medical device's wireless certification?

---

## Q4: You're leading a failure investigation on a medical device that was returned from the field with a cracked PCB near a mounting screw hole. The crack is visible under a microscope and appears to have propagated from the edge of the hole outward. The device was in use for approximately 18 months. How would you structure this investigation?

**Answer:** This is a mechanical reliability failure, and I'd approach it using a structured root-cause analysis framework — likely an 8D process since it's a field-returned medical device. Here's how I'd structure it:

**Step 1: Containment.** Immediately identify whether other devices in the field are at risk. Check the production date codes, batch records, and any design changes that correlate with the affected unit. If the crack could lead to a safety hazard (e.g., exposed conductors, loss of isolation), issue a field safety notice or recall as appropriate.

**Step 2: Physical analysis.** Examine the crack in detail under a scanning electron microscope (SEM) to determine the fracture mode — is it a fatigue crack (beach marks, striations), a stress-rupture crack, or a manufacturing defect (void, delamination)? Use energy-dispersive X-ray spectroscopy (EDS) to check for contamination or corrosion at the fracture surface. Measure the PCB thickness and copper weight at the hole to verify they meet the design specification.

**Step 3: Mechanical analysis.** Determine the loads that could cause this crack. Common causes include:
- Overtorquing of the mounting screw during assembly or field service
- Thermal expansion mismatch between the PCB and the housing material
- Vibration or flexing of the PCB during use (especially if the device is portable or worn)
- Stress concentration from a sharp corner or burr in the mounting hole

I'd measure the actual screw torque used in production (from torque driver calibration records) and compare it to the design specification. I'd also model the PCB stress around the mounting hole using finite element analysis (FEA) under expected thermal and mechanical loads.

**Step 4: Design review.** Review the PCB stack-up, the hole-to-edge clearance, the use of stress-relief features (teardrops, fillets), and whether the mounting hole is connected to a copper pour that could stiffen the area. Check if the hole is plated-through or non-plated — plated holes are more susceptible to cracking from thermal stress.

**Step 5: Corrective action.** Depending on the root cause, corrective actions could include: increasing the hole-to-edge distance, adding a stress-relief slot, changing the screw torque specification, adding a washer or grommet, or changing the PCB material to one with a lower coefficient of thermal expansion.

**Possible follow-ups:** How would you determine whether this is a single-event failure or a systemic issue affecting multiple units? What documentation would you expect to produce as part of the corrective and preventive action (CAPA) process?

---

## Q5: A junior engineer on your team has been debugging a medical device that intermittently fails to boot — the microcontroller starts, runs for about 100ms, then resets. They've spent a week checking the power supply, the crystal oscillator, and the reset circuit, all of which look fine on the oscilloscope. They're frustrated and the project is behind schedule. How would you handle this situation?

**Answer:** This is both a technical and a leadership challenge. The technical issue is a boot-time reset that's likely caused by something the engineer hasn't considered yet — possibly a firmware-hardware interaction that doesn't show up on static measurements. The leadership challenge is to redirect their effort without undermining their confidence.

Technically, I'd start by asking them to show me their oscilloscope captures and their test setup. A common blind spot in boot-time debugging is that the engineer is triggering the scope on the reset event itself, so they're seeing the aftermath rather than the cause. I'd suggest:
- Using a deep-memory scope with a pre-trigger capture, triggered on the reset line going low, to see what happened in the 100ms before the reset
- Adding a GPIO toggle at the very first line of the firmware's main() function, and another at the end of the initialization sequence, to see how far the firmware gets before the reset
- Checking whether the watchdog timer is configured correctly — sometimes the watchdog starts running before the firmware has a chance to kick it, especially if the bootloader or startup code takes longer than expected
- Looking at the microcontroller's brown-out reset (BOR) threshold — if the supply rail is clean at the bulk capacitor but has a transient dip at the microcontroller's supply pin due to trace inductance or a poor decoupling cap placement, the BOR could trigger even though the bulk rail looks fine

From a leadership perspective, I'd approach it supportively:
- Acknowledge their effort and the difficulty of the problem — intermittent boot failures are notoriously hard to debug
- Ask them to walk me through their hypothesis and what they've eliminated, rather than jumping in with my own ideas
- Suggest we pair-debug for an hour, with them driving the scope and me asking questions — this keeps them engaged and learning rather than feeling like I'm taking over
- After we find the root cause, debrief on what the systematic approach was and how they can apply it next time

**Possible follow-ups:** What if the engineer is defensive about their work and resists suggestions? How would you balance coaching with the need to meet the project deadline?