# space-rad-hard — Day 5

## Q1: How would you approach designing a fault-tolerant communication bus for a space-deployed system where multiple sensor nodes must reliably report data to a central controller, given that single-event upsets (SEUs) can corrupt individual messages?

**Answer:** I'd start by selecting a bus architecture that inherently supports redundancy and error detection. CAN-FD or RS-485 with a differential physical layer are good candidates because they reject common-mode noise and have established fault-containment properties. At the protocol level, I would implement:

- **Cyclic redundancy checks (CRCs)** on every message frame, with a polynomial length chosen to match the expected bit error rate from SEUs (e.g., CRC-16 or CRC-32 for critical telemetry).
- **Message acknowledgment and retry** — each node expects an ACK from the controller; if missing, the sender retransmits up to a configurable number of attempts before flagging a persistent fault.
- **Bus guardian or redundant bus lines** — for higher reliability, I'd use two independent physical buses (cross-strapped). Each node transmits on both buses; the controller compares received messages and discards any that fail CRC or don't match between buses.
- **Watchdog timers on each node** — if a node stops communicating due to a SEFI (single-event functional interrupt), the controller detects the timeout and can reset that node via a dedicated hardware line or a bus command.

For the firmware, I'd structure the communication stack so that SEU-induced corruption in a node's local memory doesn't propagate. Each message is constructed in a protected buffer, and the CRC is computed just before transmission. On the receiving side, messages are validated before any state change occurs. This approach trades some bus bandwidth for deterministic fault tolerance, which is appropriate for a space mission where data integrity is paramount.

**Possible follow-ups:** How would you handle a scenario where the bus itself becomes stuck dominant (e.g., a failed transistor holds the line low)? What metrics would you use to decide between a single redundant bus versus triple redundancy?

---

## Q2: You are reviewing a schematic for a space-rated system that uses a COTS DC-DC converter to generate a 3.3V rail for digital logic. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, but your digital load (an FPGA) has an absolute maximum rating of 3.6V. The junior engineer argues this is acceptable because there is 130 mV of margin. How would you evaluate this, and what would you recommend?

**Answer:** I would not accept this as sufficient margin for a space application. The issue is that the datasheet's "maximum output voltage" is typically specified under nominal conditions — nominal input voltage, nominal load, and room temperature. In space, the converter sees wide input voltage variations (e.g., a 28V bus that can swing from 22V to 36V), extreme temperature cycling, and radiation-induced degradation of the converter's internal reference and feedback components. Total ionizing dose (TID) can cause voltage reference drift, and single-event transients (SETs) on the feedback node can produce momentary output spikes well above the datasheet's DC maximum.

My recommendation would be to follow standard derating guidelines for space electronics (e.g., NASA EEE-INST-002 or ECSS-Q-ST-30-11C). For a digital rail, the rule of thumb is to derate the absolute maximum rating by at least 20%, meaning the steady-state output should never exceed 2.88V (3.6V × 0.8) under any combination of input voltage, load, temperature, and radiation effects. Since the converter's nominal output is 3.3V, this already exceeds the derated limit. The correct approach would be to either:

- Select a converter with a lower nominal output (e.g., 2.5V or 3.0V) and use a post-regulator or LDO to produce the 3.3V rail, or
- Choose a rad-hard DC-DC converter with tighter regulation and a known radiation tolerance, then verify through analysis that the worst-case output stays below the derated limit.

Additionally, I would add output voltage monitoring (e.g., a comparator with a precision reference) that triggers a system reset or load disconnect if the rail exceeds a safe threshold, as a last line of defense against latent failures.

**Possible follow-ups:** How would you determine the appropriate derating factor for a specific component type (e.g., ceramic capacitor vs. tantalum capacitor)? What if the mission is short-duration (e.g., 6 months) — would you relax the derating guidelines?

---

## Q3: How would you approach implementing triple modular redundancy (TMR) for a critical control loop in firmware, such as a PID controller that adjusts a motor speed in a life-support system? What are the practical challenges you would need to address?

**Answer:** TMR in firmware involves triplicating the computation and voting on the output. For a PID controller, I would structure it as three independent instances of the control algorithm, each running on separate timing domains (e.g., separate timer interrupts or separate cores if available) and using separate memory locations for their state variables (integral term, previous error, etc.). After each computation cycle, a voter compares the three outputs and selects the majority value to apply to the actuator.

The practical challenges are significant:

- **Synchronization** — the three instances must sample the input (e.g., motor speed sensor) at nearly the same instant. If they sample at different times due to clock skew or interrupt jitter, the inputs will differ slightly, causing the outputs to diverge even without faults. I would use a hardware trigger (e.g., a timer output compare that simultaneously latches the ADC readings into three separate registers) to ensure coherent sampling.

- **Voter implementation** — the voter itself must be hardened against SEUs. A software voter running on a single CPU is a single point of failure. I would implement the voter in hardware (e.g., in an FPGA or using discrete logic) or use a software voter with triple-redundant memory and periodic self-test. For a microcontroller-based system, I might use a "voter per output" approach where each of three microcontrollers computes its own output and they vote via a dedicated cross-strapped bus.

- **State divergence over time** — even with perfect inputs, floating-point rounding or minor timing differences can cause the three instances to drift apart. I would periodically "re-converge" the states by forcing all three to the voted state (e.g., after each control cycle, overwrite the integral term of any instance that disagreed with the majority). This prevents a single SEU from permanently corrupting one instance's state.

- **Failure handling** — if one instance consistently disagrees with the other two, it should be flagged as failed and taken out of the vote. The system should then operate in dual-redundant mode (with comparison, not voting) until the failed instance can be reset or replaced. This requires a health-monitoring layer that tracks voting patterns over time.

For a life-support system, I would also add a hardware watchdog that monitors the actuator output directly — if the motor speed exceeds a safe limit (regardless of what the TMR voted), the watchdog cuts power. This provides a last-resort safety net against common-mode failures that could affect all three instances simultaneously (e.g., a power supply glitch).

**Possible follow-ups:** How would you test that the TMR implementation actually works — specifically, how would you inject faults to verify the voter logic? What if the three instances are running on three separate microcontrollers — how do you handle the communication delay between them?

---

## Q4: You are leading a team that is designing a radiation-hardened control board for a satellite payload. During a design review, a junior engineer presents a plan to use a single, large FPGA for all digital processing, with TMR applied only to the critical state machines. The engineer argues that applying TMR to the entire design would exceed the FPGA's logic capacity and that the non-critical logic (e.g., configuration registers, housekeeping interfaces) is "safe enough" without redundancy. How would you handle this disagreement?

**Answer:** I would first acknowledge the engineer's practical constraint — logic capacity is a real limitation, and we can't blindly triplicate everything. However, I would challenge the assumption that "non-critical" logic doesn't need protection. In a space environment, a single SEU in a configuration register could change the behavior of a supposedly non-critical interface, which might then propagate into the critical path. For example, a housekeeping I2C controller that glitches could corrupt a sensor reading that the critical state machine relies on.

My approach would be to guide the team through a structured risk assessment:

1. **Define "critical" rigorously** — we need a clear, documented criterion. For example: any logic whose failure could cause loss of mission, loss of payload data, or unsafe operation of the spacecraft. This should be agreed upon with the systems engineering team.

2. **Perform a failure modes and effects analysis (FMEA)** on the FPGA design — for each logic block, ask: "If this block experiences an SEU, what is the worst-case consequence?" This often reveals that seemingly non-critical blocks (e.g., a UART that receives commands from the ground) are actually critical because a corrupted command could trigger a dangerous action.

3. **Consider alternative mitigation techniques** that use less logic than full TMR. For non-critical blocks, we might use:
   - **Error-correcting codes (ECC)** on memories and registers
   - **Harden-by-design** techniques like guard gates or redundant flip-flops with delayed sampling
   - **Periodic scrubbing** of configuration memory (for SRAM-based FPGAs)
   - **Watchdog timers** that reset the FPGA if it enters an unexpected state

4. **Quantify the trade-off** — if we cannot fit all the desired TMR, we need to decide what to leave out. I would ask the engineer to estimate the probability of an SEU affecting each unprotected block over the mission lifetime, and then compare that to the mission's reliability requirements. This data-driven discussion often clarifies where the real risks lie.

Ultimately, I would not accept a blanket "safe enough" argument without analysis. I would ask the engineer to produce a documented risk assessment showing that the unprotected blocks have been evaluated and that the residual risk is acceptable to the mission. If the logic capacity is truly insufficient, we may need to consider splitting the design across two smaller FPGAs, or moving to a rad-hard FPGA with more resources, even if that means a schedule impact.

**Possible follow-ups:** How would you handle it if the engineer becomes defensive and insists that their experience from previous projects justifies the approach? What if the schedule pressure is so high that doing a full FMEA would delay the project past the launch window?

---

## Q5: How would you approach designing a test plan to qualify a COTS microcontroller for use in a space-deployed system, given that the microcontroller is not on any qualified manufacturers list (QML) and you have limited budget for radiation testing?

**Answer:** I would structure the test plan as a risk-reduction activity, not a full qualification, since we cannot afford the comprehensive testing that QML parts receive. The goal is to identify show-stopper failure modes before committing to the design, and to establish derating guidelines for the parts we actually fly.

The plan would have three phases:

**Phase 1: Literature review and analysis.** Before any testing, I would research the microcontroller's fabrication process (e.g., CMOS node, SOI vs. bulk silicon, foundry) and look for published radiation data on similar parts from the same family or foundry. Many COTS microcontrollers share core IP with parts that have been tested by universities or space agencies. I would also analyze the design to identify the most radiation-sensitive functions — typically the on-chip SRAM (for SEU), the voltage regulator (for TID), and the oscillator (for SET-induced jitter).

**Phase 2: Targeted radiation testing.** With a limited budget, I would prioritize tests that answer the highest-risk questions:
- **TID testing** — expose a few samples to a Co-60 gamma source at incremental doses (e.g., 10, 20, 50 krad) while monitoring key parameters: supply current, clock frequency, I/O pin leakage, and ADC accuracy. Stop testing when parameters drift beyond acceptable limits or when the part fails. This tells us the maximum dose the part can survive.
- **Heavy-ion SEE testing** — at a particle accelerator, expose the microcontroller to ions with a range of linear energy transfer (LET) values while running a test firmware that exercises all major functional blocks (CPU, SRAM, flash, peripherals). Log any upsets, latch-ups, or functional interrupts. This tells us the SEU cross-section and the threshold LET for destructive events like SEL.
- **Neutron testing** (if available) — for low-earth orbit missions, atmospheric neutrons can cause SEUs. A neutron source can provide a quick estimate of the soft error rate.

I would test at least 5 samples per test to get statistically meaningful data, and I would test at worst-case temperature (e.g., hot for TID, cold for SEL) to capture temperature-dependent effects.

**Phase 3: Mitigation and derating.** Based on the test results, I would define operating limits:
- If TID failure occurs at 30 krad, derate to 15 krad maximum mission dose (50% margin).
- If SEL is observed at LET > 20 MeV·cm²/mg, implement latch-up current limiting and a power-cycle recovery circuit.
- If SEU rate in SRAM is high, implement ECC or memory scrubbing in firmware.

Finally, I would document all test results, assumptions, and residual risks in a radiation test report that becomes part of the project's risk management file. This report is essential for the mission-level review board to decide whether the COTS part is acceptable for the specific orbit and mission duration.

**Possible follow-ups:** How would you decide how many samples to test, given that each test costs money and you have a fixed budget? What would you do if the heavy-ion testing reveals a destructive SEL at an LET that is expected to occur multiple times during the mission?