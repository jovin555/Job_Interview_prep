# debugging-failure-analysis — Day 8

## Q1: A medical device has been returned from the field with intermittent resets that occur roughly once every 48 hours of continuous operation. The device logs show a watchdog timeout event just before each reset, but no other pattern. How would you approach this investigation?

**Answer:** I'd start by treating this as a systematic investigation rather than jumping to conclusions about the firmware or hardware. First, I'd want to establish whether the watchdog is timing out because the firmware genuinely hangs, or because the watchdog's clock source or reset circuit is unreliable at the edge of its specification.

My approach would be:
1. **Reproduce and characterize** — Set up multiple units in a test rack running continuously, with extended logging that captures power rail monitoring, reset pin activity, and a timestamped firmware trace. If possible, add a separate data logger that's independent of the device under test, so we can correlate events even if the main processor stops logging.
2. **Examine the watchdog circuit** — Measure the watchdog timeout period across temperature and voltage variations. Watchdog ICs have tolerances, and if the device is operating near the edge of the timeout window, a slight drift in the RC timing or the watchdog's internal oscillator could cause premature resets. I'd check the watchdog's supply voltage ripple and the integrity of its input pin connections.
3. **Analyze the firmware's watchdog servicing pattern** — Work with the firmware team to map out exactly where in the code the watchdog is kicked. Look for code paths that might take longer than expected — perhaps a sensor read that retries on failure, a flash write that blocks, or a communication routine that waits for an acknowledgment that never comes.
4. **Consider power-related causes** — A brief voltage droop during a high-current event (like a motor start or wireless transmission) could cause the microcontroller to brown out, which might manifest as a watchdog reset in the logs. I'd use a deep-memory oscilloscope to capture the supply rails over extended periods, triggered on a voltage dip below the reset threshold.

The key is to avoid the trap of assuming the watchdog is working correctly just because it's a simple IC. I've seen cases where a marginal watchdog circuit was the root cause, not the firmware it was supposed to monitor.

**Possible follow-ups:** How would you design an experiment to distinguish between a firmware hang and a hardware-induced reset? What would you look for in the reset pin waveform to differentiate the two?

---

## Q2: How would you approach debugging a situation where a medical device's analog front-end shows increased noise floor only when the device is connected to a specific patient monitor model, but not when connected to other monitors or test equipment?

**Answer:** This sounds like a ground loop or common-mode coupling issue that's specific to the grounding architecture of that particular patient monitor. I'd approach it systematically:

1. **Characterize the noise** — First, capture the noise waveform on the analog output with a scope, using a differential probe to avoid introducing additional ground loops. Note the frequency content — is it 50/60 Hz line frequency, higher harmonics, or something else? This gives clues about the coupling mechanism.

2. **Map the ground paths** — Trace the signal ground and chassis ground connections between the medical device and the patient monitor. Many medical devices use isolated front-ends, but the isolation barrier might be bypassed through shield connections, cable drain wires, or the monitor's own grounding scheme. I'd check if the problem changes when using a different cable, or when the devices are plugged into different power outlets (same circuit vs. different circuits).

3. **Isolate the coupling mechanism** — Try inserting a common-mode choke on the signal cable, or add a ferrite bead. If the noise decreases, it suggests common-mode current is the culprit. If the noise changes frequency or amplitude when I add a ground strap between the two chassis, that points to a ground loop.

4. **Check the isolation architecture** — In medical devices, patient protection usually requires isolation. I'd verify that the isolation barrier in the analog signal path is functioning correctly — measure the isolation capacitance and check for any unintended conductive paths through cable shields or connector shells that might bypass the isolation.

5. **Test with a representative load** — If possible, create a simple circuit that simulates the patient monitor's input impedance and grounding configuration, so I can reproduce the issue on the bench without needing the actual monitor for every test.

The root cause is often a subtle grounding incompatibility — for example, the patient monitor might have a different approach to connecting signal ground to protective earth, creating a loop that wasn't present during the device's own EMC testing.

**Possible follow-ups:** How would you determine whether the noise is being injected through the signal path or through the power connection? What modifications would you consider to fix this without changing the device's isolation rating?

---

## Q3: You're investigating a failure where a medical device's battery charging circuit overheats, but only when the device is placed on a specific type of conductive surface (like a metal cart). The charger IC is not damaged, and the device charges normally on a non-conductive surface. How would you approach this?

**Answer:** This strongly suggests a thermal management issue where the conductive surface is either creating an unintended heat path or, more likely, causing an electrical problem that increases power dissipation in the charging circuit. Here's my approach:

1. **Understand the thermal design** — First, I'd review the charging circuit's layout and thermal management. Does the charger IC have a thermal pad that's supposed to dissipate heat through the PCB? Is there any exposed copper or heatsinking that could contact the conductive surface? I'd check if the device's bottom case has any exposed metal or if the PCB is close enough to the case that a conductive surface could create a capacitive coupling path.

2. **Check for unintended electrical paths** — The conductive surface could be creating a parasitic path to ground or to another potential. I'd use a multimeter to measure resistance between the device's exposed metal parts (connector shells, screw heads, any exposed PCB areas) and the charging circuit's nodes. If the surface is creating a low-impedance path to ground through the device's case, it could alter the charger's operation.

3. **Measure temperature rise systematically** — Use a thermal camera to capture the temperature distribution during charging on both surfaces. Note the ambient temperature, charge current, and battery voltage. If the temperature rise is significantly higher on the metal surface, I'd look for increased power dissipation — perhaps the charger is entering a different operating mode or the battery management system is responding to a false temperature reading.

4. **Examine the battery temperature sensing** — Many charging circuits use a thermistor to monitor battery temperature and adjust charge current. If the thermistor is located near a point that couples thermally to the conductive surface, the charger might be getting a false temperature reading and entering a fault mode that actually increases dissipation rather than reducing it.

5. **Test with isolation** — Place a thin insulating layer (like a sheet of plastic) between the device and the metal surface. If the overheating stops, it confirms the issue is electrical rather than purely thermal. Then I'd work to identify exactly which node is being affected.

The fix might be as simple as adding insulation inside the device's enclosure, adding a thermal pad to better manage heat, or modifying the charging algorithm to be more robust against external thermal coupling.

**Possible follow-ups:** How would you determine whether the overheating is caused by increased charge current, reduced efficiency, or a fault condition in the charger IC? What safety considerations would you prioritize before modifying the design?

---

## Q4: A firmware engineer reports that a medical device's real-time clock (RTC) drifts significantly — losing about 5 minutes per day — but only when the device is in a low-power sleep mode. The RTC uses an external 32.768 kHz crystal. How would you approach this as a hardware engineer?

**Answer:** This is a classic symptom of a crystal oscillator issue that's specific to the operating conditions during sleep mode. The fact that it only drifts in low-power mode is a critical clue. Here's my systematic approach:

1. **Measure the crystal frequency in both modes** — Use a high-impedance active probe (or a low-capacitance probe) to measure the crystal's oscillation frequency in active mode and in sleep mode. A 5-minute-per-day drift corresponds to roughly 114 ppm, which is far beyond a typical crystal's tolerance. I'd expect to see the frequency shift significantly between modes.

2. **Examine the sleep-mode power architecture** — In low-power sleep mode, many systems shut down regulators or switch to lower-power LDOs. I'd check whether the RTC's supply voltage changes between active and sleep modes. A voltage change can shift the crystal's oscillation frequency through the crystal's drive level dependency and the oscillator circuit's bias point. I'd measure the RTC supply voltage and the oscillator's input/output waveforms in both modes.

3. **Check for load capacitance mismatch** — The crystal's oscillation frequency depends on the total load capacitance presented by the circuit. If the RTC's I/O pins change their capacitance in sleep mode (some microcontrollers reconfigure pin characteristics during low-power states), the effective load capacitance could shift, pulling the frequency off. I'd review the datasheet for the RTC or microcontroller to see if pin capacitance changes in sleep mode.

4. **Investigate the oscillator's drive level** — Some crystal oscillators are sensitive to drive level. If the oscillator circuit reduces drive current in sleep mode to save power, the crystal might not oscillate at its specified frequency. I'd measure the amplitude of the oscillation waveform in both modes — a significantly lower amplitude in sleep mode could indicate insufficient drive.

5. **Consider temperature effects** — If the device's internal temperature changes between active and sleep modes (because the main processor and other circuits are powered down), the crystal's temperature coefficient could cause frequency drift. I'd monitor the temperature near the crystal during mode transitions.

6. **Test with an external oscillator** — As a diagnostic step, I'd temporarily bypass the crystal and feed a precision 32.768 kHz signal from a function generator into the RTC's input. If the drift disappears, it confirms the crystal oscillator circuit is the problem, not the RTC itself.

The most common root cause I've seen in similar cases is a mismatch between the crystal's specified load capacitance and the actual circuit capacitance during low-power operation, often because the microcontroller's pin capacitance changes or because a series resistor in the oscillator circuit was chosen for active-mode operation without considering sleep-mode behavior.

**Possible follow-ups:** How would you determine the optimal load capacitance for the crystal in this application? What changes would you consider to make the oscillator more stable across operating modes?

---

## Q5: You're leading a cross-functional investigation into a medical device failure where a patient experienced discomfort during use, and the device's log shows an unexpected spike in output power that lasted approximately 200ms before the system's safety shutdown activated. The firmware team believes the hardware allowed an unsafe condition, and the hardware team believes the firmware should have prevented it. How would you handle this situation and structure the investigation?

**Answer:** This is a critical safety investigation where the natural tendency will be for teams to defend their own work. My priority is to establish a fact-based, collaborative investigation that focuses on the system's behavior rather than assigning blame. Here's how I'd structure it:

1. **Establish the investigation framework** — I'd call a kickoff meeting with both teams and clearly state that we're investigating a system-level failure, not individual mistakes. I'd propose using a formal root-cause analysis method — likely an 8D process or a structured fault tree analysis — so we have a shared methodology and documentation trail. This depersonalizes the investigation and focuses on evidence.

2. **Secure and preserve all evidence** — The failed device, logs, any related test equipment, and the specific accessory cable or consumable used should be quarantined. I'd ensure we have the full log data, including timestamps for all sensor readings, control outputs, and safety checks. If the device has non-volatile memory, I'd extract the full contents before anyone modifies the firmware or configuration.

3. **Reconstruct the timeline** — Together with both teams, I'd map out the exact sequence of events leading up to the power spike. What was the device doing in the seconds and minutes before? Were there any sensor readings that were near threshold limits? Were any fault flags set but not acted upon? This timeline helps identify where the system should have intervened.

4. **Examine the safety architecture** — I'd lead a review of the safety requirements and how they're implemented. Specifically:
   - What is the hardware-based safety limit (e.g., a comparator, a crowbar circuit, a current limit)?
   - What is the firmware-based safety check (e.g., monitoring output power and shutting down if exceeded)?
   - Which layer should have caught this 200ms event? Was the firmware's sampling rate fast enough? Was the hardware's response time within specification?
   - Are there single points of failure that could defeat both layers simultaneously?

5. **Conduct controlled experiments** — I'd work with both teams to design experiments that test each layer independently. For example, can we trigger the hardware safety shutdown intentionally and measure its response time? Can we simulate the conditions that led to the power spike in a lab setting and observe whether the firmware responds correctly? These experiments should be done with safety precautions in place, using a test fixture that limits maximum output.

6. **Facilitate, don't adjudicate** — When disagreements arise, I'd ask each team to articulate their position with evidence: "Show me the data that supports your conclusion." If the hardware team says the firmware should have caught it, I'd ask: "What is the firmware's sampling rate for the output power signal, and what is the latency from sample to action?" If the firmware team says the hardware allowed an unsafe condition, I'd ask: "What is the hardware's specified response time, and does the data show it exceeded that?"

7. **Document findings and corrective actions** — Once the root cause is identified, I'd lead the team in developing corrective actions that address the system-level vulnerability, not just the specific component that failed. This might include adding redundant monitoring, increasing sampling rates, adding hardware-based latches that require a power cycle to reset, or improving the fault injection testing in the design verification phase.

The goal is to leave the investigation with a stronger system, not a defeated team. A well-facilitated investigation builds trust between hardware and firmware engineers and improves the product's safety architecture.

**Possible follow-ups:** How would you handle a situation where the investigation reveals that both teams made reasonable design choices individually, but the combination created a vulnerability? What changes to the design review process would you recommend to catch similar issues earlier in development?