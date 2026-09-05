# space-rad-hard — Day 46

## Q1: How would you approach designing a fault-tolerant analog output stage for a space-deployed system where a single-event transient (SET) on a DAC's reference voltage could cause a momentary but dangerous output spike to an actuator?

**Answer:** I'd approach this from three layers: prevention at the reference source, filtering in the signal path, and safety at the actuator interface.

First, on the reference itself, I'd consider whether the DAC reference can be made more robust. A common technique is to use a reference buffer with a low-pass filter between the reference IC and the DAC's reference input. The filter time constant needs to be short enough to not affect normal operation—particularly settling time when the DAC output changes—but long enough to attenuate the majority of SET pulse widths, which are typically in the nanosecond to low-microsecond range. I'd also consider using two references with a diode-OR or averaging configuration, though that adds complexity and drift concerns.

Second, in the signal path, I'd add a slew-rate-limited output stage or a clamp circuit. A precision clamp using an op-amp with a fast comparator that detects when the output exceeds a safe threshold and forces it back within bounds can work, but the comparator itself must be radiation-tolerant and fast enough to catch the transient before it reaches the actuator. An alternative is a passive approach: a series resistor followed by a capacitor to ground creates a low-pass filter that limits how fast the output can change, effectively bounding the energy delivered during a transient.

Third, at the actuator interface, I'd consider whether the system can tolerate a brief output disturbance at all. If it cannot, then the design needs a hardware interlock—for example, a series switch (FET) that is normally on but can be opened by a watchdog or monitor circuit if an out-of-range condition is detected. This requires defining what "out-of-range" means and ensuring the detection circuit itself is not susceptible to the same SET.

Finally, I'd verify the design through fault injection testing: deliberately injecting transients at the reference node during bench testing to characterize the actual output response and confirm the mitigation works as intended.

**Possible follow-ups:** How would you choose the filter time constant without degrading the DAC's normal settling time? What if the actuator requires a fast response—how would that change your approach?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." How would you handle this disagreement?

**Answer:** I'd acknowledge that the engineer's point about low power is partially valid—the SEL risk is indeed lower at lower currents because the latch-up holding current may not be reached—but I'd explain that the risk assessment is incomplete. The issue isn't just about whether the part will latch up; it's about the full range of radiation effects.

For a linear regulator, the primary concerns are TID-induced drift in the reference voltage and output voltage, which could shift the rail outside the ADC's or op-amp's acceptable range over the mission. Even a small drift in a precision analog rail can degrade measurement accuracy. There's also the question of whether the part is susceptible to SEL at all—some linear regulators are, even at modest currents, because the internal parasitic SCR can trigger with a single heavy ion. And SETs on the regulator's feedback pin or reference could cause transient output disturbances that propagate into the analog signal chain.

I'd also point out that "no radiation data" means we have no basis to claim the risk is minimal. The absence of evidence is not evidence of absence. The right approach is to either select a part with existing radiation characterization, run a targeted test on this specific part (which may be cost-effective given it's a simple linear regulator), or add mitigation such as a current-limiting circuit on the input and output filtering to contain the effects of a potential SEL.

Rather than simply rejecting the proposal, I'd work with the engineer to quantify the risk: what's the mission impact if this rail drifts by 5%? What's the impact if the regulator latches up and draws excessive current? If the answers are "degraded performance but not mission failure," then a COTS part with a current-limit and a test program might be acceptable. If the answers are "loss of the payload," then we need a different part.

**Possible follow-ups:** How would you structure a cost-benefit analysis for testing this specific regulator versus selecting a rad-hard alternative? What test would you run first if budget only allowed one test?

---

## Q3: How would you approach designing a fault-tolerant communication bus for a space-deployed system where multiple sensor nodes must reliably report data to a central controller, given that single-event upsets (SEUs) can corrupt individual messages?

**Answer:** I'd design for three properties: error detection, error recovery, and graceful degradation.

For error detection, every message should have a strong checksum or CRC. The CRC polynomial should be chosen based on the expected error patterns—for SEUs, which typically corrupt one or a few bits, a CRC-16 or CRC-32 is usually sufficient. I'd also include a message sequence counter to detect lost or duplicated messages, and a source identifier so the controller knows which node sent the data.

For error recovery, the protocol needs a retransmission mechanism. This could be as simple as an acknowledgment from the controller with a timeout and retry at the sensor node, or a more efficient scheme like continuous transmission with the controller detecting gaps in the sequence numbers and requesting specific retransmissions. The retry count and timeout values need to be tuned so that a transient bus disturbance doesn't cause a cascade of retries that saturate the bus.

For graceful degradation, the system should tolerate a node that is persistently failing. If a node doesn't respond after multiple retries, the controller should mark it as degraded and continue operating with the remaining nodes, rather than letting one faulty node block the entire bus. This is particularly important on a shared bus like I²C or RS-485, where a stuck node can hold the bus in a busy state.

I'd also consider physical-layer mitigation. On a shared bus, a single node experiencing a latch-up could drag down the bus voltage. Adding per-node bus isolation—such as a series FET that can be switched off by the controller—prevents one faulty node from taking down the entire bus. This is especially relevant for I²C, where a stuck-low SDA or SCL line can halt all communication.

Finally, I'd think about whether a shared bus is even the right architecture. If the sensor data is critical, a point-to-point topology or a redundant bus (two independent buses with the controller reading from both) might be worth the extra wiring and connectors.

**Possible follow-ups:** How would you handle clock stretching on an I²C bus if a node is stuck? What are the trade-offs between a shared bus with isolation switches versus a star topology?

---

## Q4: How would you approach designing a memory scrubbing strategy for an SRAM-based FPGA in a space application, and what trade-offs would you consider?

**Answer:** Memory scrubbing for an SRAM-based FPGA is about periodically reading the configuration memory and correcting any bit flips before they accumulate to a point where they cause a functional failure. The key parameters are scrub rate, scrub method, and the interaction with the rest of the system.

The scrub rate should be tied to the expected SEU rate in the target orbit. If the expected upset rate is, say, one bit per day in the configuration memory, scrubbing every hour gives a very low probability of multiple upsets accumulating in the same frame. But if the upset rate is higher—such as during a solar particle event—the scrub rate needs to be correspondingly faster. I'd design the scrub rate to be adjustable from the ground so it can be increased during periods of high solar activity.

For the scrub method, there are two main approaches: readback and repair, or blind scrubbing. Readback and repair involves reading the configuration frames, comparing them against a golden copy stored in radiation-hardened memory, and rewriting any frames that have errors. This is more efficient because it only rewrites corrupted frames, but it requires a reliable golden copy and the ability to detect errors. Blind scrubbing simply rewrites all configuration frames on a periodic basis without reading them first. It's simpler and doesn't require a golden copy, but it uses more bandwidth and can momentarily disrupt operation if the FPGA doesn't support "glitchless" partial reconfiguration.

The trade-offs I'd consider include: the size of the golden copy memory and its own vulnerability to SEUs (the golden copy needs its own protection, such as ECC or triple redundancy); the bandwidth available for scrubbing versus the bandwidth needed for normal data flow; and whether the FPGA supports partial reconfiguration without interrupting operation. Some FPGAs allow scrubbing of individual frames while the rest of the device continues to function; others require a full reconfiguration, which means the system must tolerate a brief outage.

I'd also consider the interaction between scrubbing and TMR. Scrubbing corrects configuration upsets, while TMR corrects the effects of upsets in the logic fabric. They're complementary: TMR prevents a single upset from causing a wrong output, and scrubbing prevents multiple upsets from overwhelming the TMR voting logic. The scrub rate should be fast enough that the probability of two upsets in the same TMR domain before a scrub cycle is acceptably low.

**Possible follow-ups:** How would you protect the golden configuration copy stored in external flash? What happens if a scrub cycle itself is interrupted by a higher-priority event?

---

## Q5: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement, and how would you ensure the design review process remains constructive rather than adversarial?

**Answer:** When an engineer continues to push back after the technical risks have been explained, it usually means one of two things: either they don't fully accept the risk assessment, or they feel their solution is being dismissed without adequate consideration. My approach would be to shift from advocacy to joint problem-solving.

First, I'd reframe the discussion around what we can agree on. The engineer is right that a calibration routine can handle slow drift, and the ADC may indeed tolerate brief transients. So let's accept those points and focus on the risks that remain: SEL, which could cause a hard failure rather than a transient, and the possibility that the regulator's output could drift outside the ADC's input range over the mission, which calibration can't fully correct if the drift is nonlinear or if the calibration reference itself is affected.

Second, I'd propose a concrete way to resolve the uncertainty: a targeted test. A simple heavy-ion test on this specific regulator would tell us whether it's SEL-sensitive and give us a cross-section. If budget is truly constrained, we could start with a TID test using a cobalt-60 source, which is relatively inexpensive, to characterize the output voltage drift. The results would either validate the engineer's position or provide data to support a different part selection.

Third, I'd ask the engineer to help define the acceptance criteria. What level of drift is acceptable? What transient magnitude and duration can the ADC tolerate? What's the mission impact if the regulator latches up and the rail is lost? By involving the engineer in defining these criteria, we move from "my opinion versus yours" to "what does the system actually need?" This is more constructive and also helps the engineer develop their own engineering judgment.

Finally, I'd make sure the design review process itself has a clear path for resolving disagreements. If we can't reach consensus, the decision should be escalated to the systems engineer or the project lead with a written summary of the risk, the options, and the trade-offs. The goal is not to win the argument but to make the best decision for the mission with the information available.

**Possible follow-ups:** What if the test results come back showing the regulator is SEL-sensitive—how would you present that to the engineer? How would you handle a situation where the schedule doesn't allow time for testing?