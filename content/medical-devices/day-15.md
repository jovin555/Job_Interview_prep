# medical-devices — Day 15

## Q1: How would you approach verifying that a medical device's firmware correctly handles a brownout or undervoltage condition on its power supply, given that the device logs physiological data that must not be corrupted?

**Answer:** A brownout condition is particularly insidious because the system may not fully reset — it can operate in an undefined state where the CPU is running but peripherals are behaving erratically, or where flash writes are only partially completed. My approach would start at the hardware level: ensure the design has a proper voltage supervisor or brownout detector with a threshold above the minimum operating voltage of all components, and that the reset signal is clean and glitch-free. The firmware must treat this as a first-class state, not an afterthought.

For the firmware architecture, I'd implement a multi-layered strategy. First, a power-loss detection interrupt that triggers as soon as the supply drops below a warning threshold — this gives the system time to enter a controlled shutdown sequence. Second, the shutdown sequence itself must be prioritized: stop non-critical tasks, flush any pending data to non-volatile storage using a write pattern that's atomic or at least power-loss tolerant (e.g., write to a double-buffered region with a valid flag written last, or use a journaling approach). Third, on power-up, the firmware must perform a recovery check — verify the integrity of the last logged data, and if corruption is detected, mark that record as invalid rather than presenting it as good data.

For verification, I'd build a test harness that can simulate brownout conditions at various points in the logging cycle — mid-write, between writes, during a sensor read, during a UI update. The key is to vary the timing and depth of the brownout (e.g., drop to 80% of nominal, 50%, or full power loss) and verify that the device either completes the write correctly or leaves the storage in a state that's detectable as incomplete on the next boot. I'd also verify that the device recovers to a known good state and resumes logging without user intervention, since in a monitoring context the device may be unattended.

**Possible follow-ups:** How would you test the brownout handling if the device uses an external flash chip rather than internal MCU flash? What if the brownout occurs during a firmware update — how would your approach change?

---

## Q2: You're leading a project where a supplier has delivered a batch of medical device PCBs, and incoming inspection reveals that the conformal coating thickness on the high-voltage isolation area is below specification. The supplier claims it's within their manufacturing tolerance and the boards will pass hi-pot testing. How would you handle this situation?

**Answer:** This is a classic situation where a single test passing isn't sufficient justification to accept a deviation from a specified requirement. The conformal coating thickness isn't just about passing hi-pot once — it's about maintaining safety margins over the product's lifetime, accounting for coating wear, moisture ingress, contamination, and manufacturing variability. The supplier's claim that "it will pass hi-pot" is addressing a necessary but not sufficient condition.

My first step would be to understand the actual risk. I'd review the design specification to confirm what thickness was specified and why — was it derived from creepage distance calculations, from IEC 60601-1 requirements for insulation, or from a safety margin analysis? If the specification was arbitrary, there may be room to revisit it with engineering justification. If it was derived from a risk analysis, then the deviation is a safety issue, not just a quality issue.

Next, I'd want data. I'd ask the supplier for their process capability data — what's the distribution of coating thickness across the batch, not just the minimum reading? If the batch is mostly within spec with a few outliers, that's different from a systematic shift in their process. I'd also request their own hi-pot test results, but I'd be cautious about relying solely on those, because hi-pot testing at incoming inspection may not replicate the conditions the device will face in the field (humidity, temperature cycling, mechanical stress).

From a quality system perspective, I'd formally document the non-conformance and initiate a disposition process. The options would be: (a) accept with a documented engineering rationale and risk assessment, (b) reject and require the supplier to rework or scrap, or (c) accept conditionally with additional testing or derating. Given that this is a medical device, I'd lean toward rejection unless there's a very strong engineering case for acceptance, because the cost of a field failure in a high-voltage isolation area is potentially catastrophic. I'd also work with the supplier to understand why their process drifted and what corrective action they'd take to prevent recurrence.

**Possible follow-ups:** What if the supplier's process data shows this is within their normal variation and they've always shipped boards this way? How would you determine whether the coating thickness specification itself needs to be revised?

---

## Q3: How would you approach designing a test strategy for verifying that a medical device's alarm system correctly prioritizes and presents multiple simultaneous alarms, given that the device monitors several physiological parameters with different alarm priority levels?

**Answer:** Alarm management is a patient safety issue, and the test strategy needs to reflect that. The core challenge is that you're not just testing whether individual alarms trigger correctly — you're testing how the system behaves when multiple alarms compete for the user's attention, and whether the presentation logic (which alarm is shown first, how it's annunciated, how it's acknowledged) matches the clinical priority.

I'd start by defining the alarm specification clearly: what are the priority levels (e.g., high, medium, low per IEC 60601-1-8), what are the clinical conditions that trigger each alarm, and what is the expected presentation behavior for each combination? This becomes the basis for a traceability matrix from requirements to test cases.

The test strategy would have several layers. First, individual alarm testing: verify each alarm triggers at the correct threshold, with the correct visual and audible characteristics, and that the alarm annunciation meets the IEC 60601-1-8 requirements for signal patterns and priority distinctions. Second, simultaneous alarm testing: this is where the complexity lies. I'd create a matrix of alarm combinations — two high-priority alarms, a high and a medium, multiple low-priority, and so on — and verify that the presentation logic follows the specified prioritization. For example, if two high-priority alarms occur simultaneously, does the system display both, or does it cycle between them? Is the most recent alarm given precedence, or the highest priority?

Third, I'd test the acknowledgment and reset behavior. What happens when the clinician acknowledges one alarm while another is still active? Does the system allow silencing of a high-priority alarm, and if so, for how long? What's the behavior if a new alarm occurs while the system is in an alarm-silenced state? These are the scenarios where real-world usability issues emerge.

For the actual test execution, I'd use a combination of simulated physiological signals (e.g., waveform generators feeding the sensor inputs) and scripted scenarios that create specific alarm sequences. I'd also include timing verification — the alarm must be annunciated within the specified latency after the triggering condition occurs. Finally, I'd involve clinical users in usability testing to verify that the alarm presentation is actually interpretable in a realistic clinical workflow, because a technically correct alarm that confuses the user is still a safety hazard.

**Possible follow-ups:** How would you handle the situation where the alarm prioritization logic is implemented in software but the clinical team disagrees with the priority assigned to a particular alarm condition? How would you test the alarm system's behavior during a partial system failure, such as a failed speaker?

---

## Q4: How would you approach developing a design verification test plan for a medical device that uses a motor to drive a mechanical actuator, where the motor's performance directly affects patient safety, and the device must operate reliably over a 5-year service life?

**Answer:** This requires a test plan that addresses both functional performance and long-term reliability, with a clear link back to the risk management file. The motor's performance is safety-critical, so the test plan must verify not just that it works, but that it works within defined tolerances over its expected lifetime, and that failure modes are either prevented or detected.

I'd start by identifying the critical motor parameters from the design inputs: speed, torque, position accuracy, response time, current draw, temperature rise, and acoustic noise. Each of these would have a specification with acceptable limits, and the test plan would verify each one under defined load conditions. The load conditions are important — a motor that works correctly under no load may fail under the maximum expected mechanical load, so the test plan must include worst-case loading scenarios.

For the 5-year service life, I'd use a combination of accelerated life testing and design analysis. Accelerated testing might involve running the motor continuously at elevated temperature or with increased duty cycle to accelerate wear mechanisms, then extrapolating the results using established models (e.g., Arrhenius for temperature-related degradation, or bearing life calculations for mechanical wear). I'd also review the motor manufacturer's own reliability data and qualification testing to supplement our testing.

The test plan would also include fault injection and failure mode testing. For example, what happens if the motor stalls? Does the current limiting circuit protect the motor and the electronics? What happens if the motor's encoder fails — does the system detect the fault and enter a safe state? These tests verify that the risk control measures identified in the risk analysis actually work.

Finally, I'd include periodic verification points throughout the accelerated life test — not just a single "did it survive" check at the end. This allows us to detect degradation trends (e.g., increasing current draw or decreasing torque) before a catastrophic failure occurs, which gives us insight into the failure mechanism and helps us set appropriate preventive maintenance or end-of-life indicators in the field.

**Possible follow-ups:** How would you determine the acceleration factor for the accelerated life test, and how would you validate that the acceleration model is appropriate for this specific motor? What if the accelerated test reveals a failure mode that wasn't identified in the original risk analysis?

---

## Q5: You're leading a project where a senior hardware engineer and a junior firmware engineer disagree on the root cause of an intermittent device failure that occurs only when the device is connected to a specific brand of patient monitor. The hardware engineer believes it's a grounding issue between the two devices, while the firmware engineer believes it's a communication protocol timing issue. How would you handle this disagreement and drive the investigation forward?

**Answer:** This is a situation where the disagreement itself is valuable — it means we have two plausible hypotheses, and the job is to design experiments that discriminate between them rather than trying to resolve the argument through debate. My approach would be to structure the investigation so that data, not opinion, drives the conclusion.

First, I'd call a meeting with both engineers and establish the ground rules: we're not here to determine who's right, we're here to design experiments that will narrow down the possibilities. I'd ask each engineer to articulate their hypothesis in terms of testable predictions. For the grounding hypothesis, what specific measurements would confirm or refute it? For the timing hypothesis, what specific protocol analysis would show the issue? This forces both hypotheses to be concrete and falsifiable.

Then I'd prioritize the experiments based on cost, time, and diagnostic power. A good first step might be a simple isolation test — connect the device to the patient monitor through a medical-grade isolation transformer or a ground isolator. If the failure disappears, that strongly supports the grounding hypothesis. If it persists, grounding is less likely. In parallel, I could capture the communication traffic between the two devices using a protocol analyzer, looking for timing violations or corrupted frames that correlate with the failure events.

I'd also consider whether there's a third hypothesis that neither engineer has considered. For example, the specific brand of patient monitor might have a different input impedance or a different common-mode voltage characteristic that's interacting with the device's output stage in an unexpected way. Or the issue might be related to the cable — a specific cable length or shielding configuration that's marginal. I'd encourage both engineers to think beyond their initial positions.

Throughout this process, I'd document everything — the hypotheses, the experiments, the results, and the evolving understanding. This isn't just for the current investigation; it's also valuable for the design history file and for future troubleshooting. Once the root cause is identified, I'd ensure we capture the lesson learned and update any relevant design guidelines or test procedures.

The key leadership point is that I'm not trying to mediate a personality conflict — I'm facilitating a scientific investigation. By focusing on experiments and data, I'm giving both engineers a constructive way to contribute, and I'm preventing the investigation from stalling while the team argues.

**Possible follow-ups:** What if the experiments are inconclusive — the failure occurs intermittently and neither hypothesis is clearly confirmed or refuted? How would you decide when to escalate the issue to a formal root cause analysis process (e.g., 8D) versus continuing with the current investigation?