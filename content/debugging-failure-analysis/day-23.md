# debugging-failure-analysis — Day 23

## Q1: How would you approach a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent reset is caused by a firmware bug or a hardware issue — the device resets randomly, sometimes multiple times per day, sometimes not for a week, and the watchdog timer is expiring just before each reset?

**Answer:** The watchdog expiring is a symptom, not a root cause — the watchdog is doing its job by resetting a system that has stopped being serviced. The real question is why the firmware stops feeding the watchdog. I'd structure this investigation in three phases.

First, **characterize the reset event itself**. I'd instrument the device to capture the state at the moment of reset: the reset cause register (which often distinguishes between watchdog, brown-out, external reset, and power-on reset), the program counter and stack contents if they survive reset, and any debug registers that record the last bus transaction or fault address. I'd also add a "reset log" to non-volatile memory that records the time, the reset cause, and a rolling buffer of recent system state (task states, interrupt activity, recent function calls) before each reset. This turns a random event into data.

Second, **look for patterns in the data**. Once I have a dozen or more reset events logged, I'd analyze them for correlations: do resets cluster around specific operations (e.g., sensor reads, wireless transmissions, motor activity)? Do they correlate with power supply events (battery transitions, charging)? Do they happen more frequently at certain temperatures or after certain durations of operation? This pattern analysis often points to a specific subsystem or condition.

Third, **test hypotheses with targeted experiments**. If the data suggests a hardware issue — for example, resets cluster during wireless transmission — I'd monitor the power rails with a scope during those events, looking for brown-out conditions or noise-induced resets. If the data suggests firmware — for example, resets occur during a specific code path — I'd add instrumentation to that path and review the code for watchdog-feeding gaps, infinite loops, or priority inversion.

The key insight is that the watchdog expiring doesn't tell us whether the cause is hardware or firmware — it only tells us the firmware stopped running. The reset cause register and the system state at reset are what discriminate between the two. I'd also make sure both teams agree on the data collection plan before starting, so the evidence is trusted by everyone.

**Possible follow-ups:**
- How would you distinguish between a brown-out reset and a watchdog reset if the reset cause register is not reliable or not available?
- What specific instrumentation would you add to the firmware to capture the system state just before a watchdog timeout?

---

## Q2: How would you approach debugging a medical device where a specific sensor reading is consistently correct at the ADC output, but the value stored in memory and transmitted over the communication interface is occasionally wrong — and the error appears to be a single-bit flip in the data?

**Answer:** This is a classic "where does the corruption happen" problem — the data is correct at one point in the chain and wrong at another, so the corruption occurs somewhere between the ADC output and the transmitted value. I'd trace the data path step by step.

The data path is: ADC → data register → firmware reads the register → firmware stores the value in memory → firmware formats the value for transmission → the value is sent over the communication interface. The corruption could occur at any of these stages, and a single-bit flip points to different causes at different stages.

I'd start by **verifying the observation**. Is the value actually correct at the ADC output, or is the measurement method missing the corruption? I'd use a logic analyzer or scope to capture the actual SPI/I2C transaction between the ADC and the microcontroller, and compare the captured data with what the firmware reports. This confirms whether the corruption is on the bus or after the data enters the microcontroller.

If the bus data is correct, the corruption is inside the microcontroller. I'd then add **checksum or CRC verification at each stage** of the firmware data path: after reading the ADC register, after storing to memory, and after formatting for transmission. This pinpoints which stage introduces the error. A single-bit flip in memory could indicate a marginal memory cell, a power supply glitch during a write, or an EMI event. A single-bit flip during formatting could indicate a firmware bug in the data manipulation (e.g., a shift operation that loses a bit).

If the bus data is wrong, the corruption is on the communication link. I'd examine the signal integrity of the SPI/I2C bus: rise/fall times, overshoot, crosstalk from adjacent traces, and the integrity of the clock signal. A single-bit flip on the bus often points to a marginal setup/hold time violation or noise coupling.

I'd also consider **power integrity** as a contributing factor. A brief voltage dip on the microcontroller's supply rail during a memory write or a bus transaction could cause a single-bit error. I'd monitor the supply rails during the exact moment of the corruption, which requires triggering the scope on the error event.

The systematic approach is to isolate the stage where corruption occurs, then investigate the specific failure mechanisms relevant to that stage — signal integrity for the bus, memory integrity for storage, and code correctness for the data manipulation.

**Possible follow-ups:**
- How would you trigger your scope to capture the exact moment of corruption if the error is intermittent and rare?
- What firmware techniques would you use to detect and correct single-bit errors in critical data?

---

## Q3: How would you approach a failure investigation where a medical device's power supply exhibits a periodic voltage dip on a 3.3V rail — the dip is about 200mV and lasts for roughly 50 microseconds, occurring every 100ms — and the device occasionally resets during these dips, but not consistently?

**Answer:** The periodic nature of the dip is a strong clue — something is drawing current from the 3.3V rail every 100ms. I'd approach this by first identifying the load that's causing the dip, then understanding why the dip occasionally causes a reset.

**Step 1: Identify the periodic load.** A 100ms period suggests a specific operation: a sensor sampling cycle, a wireless beacon, an LED blink, or a communication poll. I'd correlate the dip timing with the device's operational state — check the firmware's task schedule and see what runs every 100ms. I'd also use a current probe on the 3.3V rail to see the current draw profile during the dip. If the current spikes at the same time as the voltage dips, it's a load transient issue.

**Step 2: Characterize the power supply response.** A 200mV dip for 50µs on a 3.3V rail could be caused by insufficient decoupling capacitance, a regulator with slow transient response, or excessive trace inductance between the regulator and the load. I'd measure the dip at different points along the rail — at the regulator output, at the load, and at the microcontroller's supply pin. If the dip is larger at the load than at the regulator, the issue is the distribution path (trace inductance/resistance). If the dip is present at the regulator output, the issue is the regulator's transient response or its input supply.

**Step 3: Understand why the reset is intermittent.** The microcontroller's reset threshold is typically around 2.9V for a 3.3V rail (the brown-out reset threshold). A 200mV dip from 3.3V to 3.1V shouldn't trigger a reset — so either the dip is occasionally deeper than 200mV, or the reset is caused by something else. I'd check the reset cause register on the devices that reset to confirm it's a brown-out reset. If it is, I'd look for conditions that make the dip deeper — perhaps the periodic load coincides with another transient, or the dip is deeper when the battery is lower or the temperature is higher.

**Step 4: Investigate the root cause.** If the dip is caused by a load transient, I'd look at the load's current profile — does it have a high inrush current? Is there a missing bulk capacitor near the load? Is the load's switching frequency interacting with the power supply's control loop? If the dip is caused by the distribution path, I'd look at trace widths, via counts, and the placement of decoupling capacitors.

The key is to measure at the right points and correlate the dip with the device's operational state. The intermittent nature of the reset suggests the dip is marginal — sometimes it crosses the threshold, sometimes it doesn't — so I'd also consider adding margin: more decoupling capacitance, a lower-impedance distribution path, or adjusting the brown-out threshold if the design allows.

**Possible follow-ups:**
- How would you determine whether the dip is caused by the load or by the power supply's transient response?
- What measurements would you take to confirm that the reset is actually caused by the voltage dip and not by something else?

---

## Q4: How would you approach a failure investigation where a medical device's wireless communication works reliably in the lab, but in the clinical environment, the device intermittently fails to transmit data — and the failures correlate with times when the hospital's paging system is active?

**Answer:** This is a classic electromagnetic interference (EMI) problem — the hospital's paging system is likely emitting RF energy that interferes with the device's wireless communication. The correlation with the paging system is a strong clue, but I'd verify it systematically rather than assuming it's the cause.

**Step 1: Characterize the interference.** I'd first understand what the paging system is transmitting — its frequency, modulation, power level, and duty cycle. Hospital paging systems often operate in the VHF/UHF bands or use Wi-Fi/Bluetooth. I'd also measure the RF environment in the clinical area using a spectrum analyzer to see what's present when the paging system is active.

**Step 2: Determine the failure mechanism.** The interference could affect the device in several ways: it could desensitize the wireless receiver (blocking), it could corrupt the data being transmitted (causing retries that eventually fail), or it could cause the wireless module to malfunction (e.g., through a reset or a firmware hang). I'd check the device's logs for the specific failure mode — does the transmission fail at the RF level, or does the module stop responding entirely?

**Step 3: Test the hypothesis.** I'd reproduce the interference in a controlled environment — using a signal generator to emulate the paging system's signal and testing the device at various frequencies and power levels. This confirms whether the interference is the cause and helps identify the specific frequency or power level that triggers the failure.

**Step 4: Identify the coupling path.** If the interference is confirmed, I'd determine how it's getting into the device: through the antenna (conducted), through the enclosure (radiated), or through cables (common-mode). I'd use near-field probes to scan the device and identify the entry point. I'd also check the device's shielding, grounding, and filtering.

**Step 5: Implement and verify a fix.** Depending on the coupling path, the fix could involve: improving the enclosure shielding, adding filtering on cables, changing the wireless module's frequency or channel, improving the antenna's rejection of out-of-band signals, or adding firmware-level retry logic with channel hopping. I'd verify the fix by repeating the interference test and confirming the device operates reliably.

The key is to move from correlation to causation — the paging system correlation is a lead, but I need to confirm the interference mechanism and the coupling path before implementing a fix. I'd also consider whether the device's wireless protocol has any inherent resilience to interference (e.g., frequency hopping, retry mechanisms) and whether those are configured optimally.

**Possible follow-ups:**
- How would you distinguish between the paging system causing RF interference versus causing a power supply disturbance in the device?
- What specific measurements would you take to identify the coupling path of the interference?

---

## Q5: You're leading a cross-functional investigation into a medical device failure where the device's motor (used for a therapeutic function) stopped mid-procedure. The device logs show a motor current spike followed by a stall condition, and the fuse is blown. The mechanical team believes the electrical design is at fault, and the electrical team believes the mechanical design caused an overcurrent condition. How would you handle this situation and structure the investigation?

**Answer:** This is a situation where the two teams are focused on their own domains, but the evidence — a current spike, a stall, and a blown fuse — suggests an interaction between the mechanical and electrical systems. My role as the investigation lead is to structure the investigation so the evidence, not the teams' opinions, determines the root cause.

**Step 1: Establish a shared understanding of the event.** I'd start by reviewing the device logs together with both teams. The current spike and stall condition tell us the motor was drawing excessive current — but we need to understand the sequence: did the stall cause the current spike, or did the current spike cause the stall? The fuse blowing is the final event, but it's a consequence, not a root cause.

**Step 2: Collect physical evidence.** I'd have the motor, the motor driver, the fuse, and the mechanical assembly (gears, shaft, bearings) all examined by the appropriate specialists. The motor should be tested for electrical integrity (winding resistance, insulation) and mechanical integrity (shaft rotation, bearing friction). The mechanical assembly should be inspected for signs of binding, wear, or misalignment. The fuse should be examined to confirm it blew due to overcurrent and not due to a manufacturing defect.

**Step 3: Analyze the failure sequence.** The key question is: what happened first? If the mechanical assembly bound up (e.g., a gear seized), the motor would stall, draw excessive current, and blow the fuse — this points to a mechanical root cause. If the motor driver failed (e.g., a shorted FET), the motor could receive uncontrolled current, causing it to overdrive and stall — this points to an electrical root cause. I'd look for evidence that discriminates between these scenarios: the motor's current profile over time, the condition of the motor driver, and the state of the mechanical assembly.

**Step 4: Consider interaction effects.** The failure could also be caused by an interaction — for example, a mechanical issue that causes intermittent binding, which stresses the electrical system over time, eventually causing a failure. Or an electrical issue that causes the motor to run erratically, which stresses the mechanical system. I'd look at the device's usage history and any prior maintenance or wear indicators.

**Step 5: Use fault tree analysis to structure the investigation.** I'd build a fault tree with the top event being "motor stopped mid-procedure" and branch down into possible causes: mechanical binding, electrical failure, firmware issue, power supply issue, etc. Each branch would have specific evidence that confirms or rules it out. This keeps the investigation systematic and prevents either team from anchoring on their initial hypothesis.

**Step 6: Manage the team dynamics.** I'd acknowledge both teams' expertise and concerns, but emphasize that the investigation is about finding the truth, not about assigning blame. I'd schedule regular check-ins where each team presents their evidence, and I'd ensure that decisions are based on data, not on seniority or conviction. If the evidence points to one team's domain, I'd present it factually and focus on corrective action rather than fault.

The goal is to reach a root cause that both teams accept, because the corrective action — whether it's a mechanical redesign, an electrical fix, or both — will only be effective if the teams believe in the diagnosis.

**Possible follow-ups:**
- How would you handle a situation where the evidence is inconclusive and both teams continue to disagree?
- What specific tests would you run on the motor and the mechanical assembly to discriminate between the two hypotheses?