# space-rad-hard — Day 51

## Q1: How would you approach designing a radiation-tolerant analog signal chain for a spacecraft instrument where the sensor output is a low-level differential signal, and both the amplifier front-end and the ADC reference can experience single-event transients (SETs)?

**Answer:** I'd treat the analog chain as a series of stages and ask, for each one, "what happens to the system if this stage produces a transient, and how long does it last?" The front-end amplifier is usually the most exposed because it has the most gain and the smallest signal — a SET there gets amplified along with everything else. So the first line of defense is to keep the front-end gain modest and push more of the gain downstream, where the signal is larger relative to the transient. I'd also look at whether the amplifier topology is inherently SET-tolerant: some topologies recover faster than others, and a part with a known SET cross-section and a short transient duration is preferable to one with no data at all.

For the ADC reference, the concern is different — a transient on the reference shifts the entire conversion result, not just one sample. I'd consider a reference with a large output capacitor and a low-pass filter at the reference pin, sized so that a short transient is attenuated before it reaches the ADC's internal reference buffer. If the reference itself is a COTS part with no radiation data, I'd either qualify it with a targeted heavy-ion test or add a redundant reference with a comparator that flags when the two disagree beyond a threshold.

The other piece is the digital side: I'd add plausibility checks on the converted data — rate-of-change limits, range checks, and a requirement that a sample be confirmed by a second conversion before it's used for control. That doesn't fix the analog problem, but it prevents a single SET from propagating into an actuator command. The trade-off is latency: if the measurement is time-critical, you can't always afford a confirm-and-retry, so you have to decide per-channel whether the cost of a false reading is worse than the cost of a delayed one.

**Possible follow-ups:**
- How would you decide between filtering the reference and adding a redundant reference with a comparator?
- If the sensor signal is genuinely fast and you can't afford a second conversion, what other options do you have?

## Q2: You're reviewing a design for a space-deployed system that uses a COTS operational amplifier in a critical analog signal-conditioning path. The op-amp has no radiation data, but the designer argues that "it's a simple, mature part with a well-understood topology, and the system has a calibration routine." How would you evaluate this approach?

**Answer:** The "simple and mature" argument is true as far as it goes, but it doesn't address the two failure modes that matter most here: total ionizing dose (TID) drift and single-event transients. A mature part can still have a TID-induced input offset shift or bias-current drift that the calibration routine can't distinguish from a real sensor change — and if the calibration routine runs periodically, it may actually "calibrate out" a radiation-induced shift and mask the problem. That's worse than not calibrating, because it hides the degradation.

I'd want to know three things before accepting the part. First, what's the TID tolerance of the process — even without a radiation report, the process node and the manufacturer's own data can give a rough bound. Second, what's the SET cross-section and transient duration — this is harder to bound without testing, but a part with a large geometry and a well-understood topology is generally less SET-prone than a modern high-speed part. Third, what's the consequence of a transient reaching the control loop — if the loop has a rate limiter or a plausibility check, a short transient may be tolerable; if it directly drives an actuator, it isn't.

If the part is genuinely critical and there's no data, I'd push for either a targeted heavy-ion test at a facility or a redesign to a part with known radiation performance. The calibration routine is not a substitute for radiation data — it's a mitigation for slow drift, not for transients or for a shift that looks like a legitimate signal.

**Possible follow-ups:**
- How would you design the calibration routine so it doesn't mask radiation-induced drift?
- What would you do if the schedule doesn't allow for a heavy-ion test before the design freeze?

## Q3: How would you approach designing a fault-tolerant communication bus for a space-deployed system where multiple sensor nodes must reliably report data to a central controller, and single-event upsets (SEUs) can corrupt individual messages?

**Answer:** The first question is what "reliably" means for each message — is a corrupted reading a nuisance, or does it trigger a control action? That determines how much overhead you're willing to spend. For a bus like I²C or RS485, the physical layer itself has no error detection beyond what the protocol provides, so I'd start by adding a CRC to every message and a sequence number so the controller can detect both corruption and loss. A CRC catches most SEU-induced bit flips in the payload; the sequence number catches dropped or duplicated messages.

The next layer is the bus arbitration and lock-up problem. A SEU in a node's bus interface can cause it to hold the bus low indefinitely, which takes down every other node. I'd address this with a bus timeout in the controller — if a transaction doesn't complete within a bounded time, the controller resets the bus and re-initializes the nodes. Some buses (CAN-FD, for example) have built-in error detection and fault confinement, which makes this easier; for simpler buses, the timeout has to be implemented in firmware.

For the data itself, I'd add a plausibility check at the controller: a sensor reading that's outside its physical range, or that changes faster than the sensor could physically change, is flagged rather than acted on. And for the most critical channels, I'd consider sending the same measurement over two independent paths — either two buses or two nodes measuring the same quantity — and comparing them. That's expensive in power and mass, so it's reserved for the channels where a wrong reading has real consequences.

**Possible follow-ups:**
- How would you handle a node that's alive but sending corrupted data continuously, versus one that's stopped responding entirely?
- Would you use a time-triggered protocol instead of an event-triggered one, and why?

## Q4: How would you approach selecting and qualifying a voltage supervisor or reset IC for a space-deployed system, given that most commercial parts are not radiation-characterized?

**Answer:** The voltage supervisor is a deceptively critical part because it's the thing that decides whether the processor is allowed to run. If it falsely asserts reset, the system is down; if it fails to assert when the rail is out of spec, the processor runs on a bad rail and may execute garbage. So the selection criteria are different from a normal commercial design.

I'd start by looking for parts that are either on a qualified manufacturers list (QML) or that have published radiation data — even a single-event latch-up (SEL) threshold and a TID tolerance are enough to make a first cut. If nothing qualified is available, I'd look at the process technology: a part built on an older, larger-geometry process is generally more TID-tolerant and less SEL-prone than a modern sub-micron part, even without a formal report. Bipolar supervisors tend to be more robust than CMOS ones for this reason.

For qualification, I'd want at least a TID test to the mission dose with margin, and a heavy-ion or proton test to establish the SEL threshold and the SET behavior on the reset output. The SET behavior matters specifically: a transient on the reset line that's long enough to reset the processor is a functional interrupt, and you need to know whether the supervisor itself can produce one. If testing isn't feasible, I'd add a second, independent supervisor with a different threshold and AND the two reset outputs — a single SET on one supervisor then can't reset the system, and a genuine out-of-spec rail trips both.

**Possible follow-ups:**
- How would you set the supervisor threshold relative to the processor's minimum operating voltage, and what margin would you use?
- If you use two supervisors, how do you handle the case where one fails permanently?

## Q5: Imagine you're leading a design review for a space-deployed system, and a junior engineer proposes using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." How would you handle this disagreement, and how would you keep the review constructive rather than adversarial?

**Answer:** I'd start by acknowledging the part of the argument that's correct — a low-current rail does have a smaller SEL cross-section than a high-current one, and the consequences of a transient on a 50 mA rail are usually less severe than on a 3 A rail. That's a real consideration, and it's worth saying so, because the engineer has thought about the problem.

Then I'd separate the two failure modes and ask about each one specifically. For TID: what's the mission dose, and what happens to the regulator's output voltage and dropout as it accumulates dose? A 5V rail that drifts to 4.8V over five years may still be in spec, or it may not — that's a number, not an opinion. For SEE: what happens if the regulator's pass transistor latches up? On a 50 mA rail the latch-up current may be limited by the load itself, but the regulator can still drag the rail down and take the analog front-end with it. The question is whether the system detects that and recovers, or whether it just produces bad data until someone notices.

I'd frame the outcome as a decision the team makes together, not a verdict I hand down: either we find radiation data for this part, or we qualify it with a targeted test, or we add a mitigation (a redundant regulator, a current limit, a rail monitor), or we accept the risk explicitly and document why. The key is that "the risk is minimal" becomes a documented assumption with a rationale, not an assertion. That keeps the review constructive because the engineer isn't being told they're wrong — they're being asked to make their reasoning explicit, which is what a design review is for.

**Possible follow-ups:**
- If the team decides to accept the risk, what would you want documented, and who signs off?
- How would you handle it if the engineer continues to push back after the risk is documented?