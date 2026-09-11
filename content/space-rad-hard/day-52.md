# space-rad-hard — Day 52

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd treat this as two separable problems — fault isolation between feeds, and inrush/transient control at the interface — and design them so neither compromises the other.

For fault isolation, the goal is that a fault on one feed (a short, an SEL-induced overcurrent, or a failed ORing element) must not drag down the other feed or the common load rail. The classic approach is diode-OR or ideal-diode (active ORing) combining of the two feeds, so each feed can only source current, never sink it. A simple Schottky diode-OR is robust and radiation-tolerant by nature but wastes power and drops voltage; an active ORing controller with a MOSFET gives lower loss but introduces an active device that itself needs to be evaluated for SEE and single-event gate rupture. I'd weigh the efficiency budget against the added failure modes of the active part. Critically, each feed path should have its own current-limiting and latching protection — a resettable current limit or an e-fuse — so that an overcurrent on one branch trips locally rather than pulling the shared rail down. The protection must be sized so that a legitimate inrush doesn't false-trip it, which is where the two problems interact.

For hot-swap and inrush, the concern is that plugging into a live 28V bus with bulk capacitance presents a near-short until the caps charge. Without control, that produces a large di/dt and a bus droop that can disturb other loads. I'd use a hot-swap controller with a controlled slew rate on the pass FET's gate, plus a dV/dt-limiting gate capacitor, so the inrush is a defined ramp rather than a step. I'd also add a series inductor and bulk capacitance forming a filter that both limits inrush di/dt and attenuates conducted emissions, and I'd verify the SOA of the pass FET during the ramp — the FET dissipates real power during inrush and must stay inside its safe operating area at worst-case ambient.

The radiation angle: any active device in this path (ORing controller, hot-swap controller, e-fuse) is a candidate for SEL and SET. I'd prefer parts with latch-up immunity or, where not available, add current-limited supplies and a means to power-cycle the protection device. A SET on the hot-swap controller could momentarily open or close the pass FET — I'd want the controller's behavior under a transient to fail safe (stay on or gracefully retry), not to latch the load off permanently. And I'd want the protection scheme to be testable on the ground: inject a fault on one feed and confirm the other feed holds the rail within spec.

**Possible follow-ups:**
- How would you decide between a passive diode-OR and an active ORing scheme if the efficiency budget is tight but the radiation data on the active controller is thin?
- If the hot-swap controller itself experiences an SEL, how would you ensure the load isn't left unpowered or, worse, exposed to an uncontrolled transient?

## Q2: How would you approach derating and part selection for a space-deployed board, and how does derating interact with the radiation tolerance you're trying to achieve?

**Answer:** Derating and radiation tolerance are complementary but they're solving different problems, and it's a mistake to treat one as a substitute for the other.

Derating is about margin against the ordinary stresses of the mission — voltage, current, power, junction temperature, and mechanical stress — applied so that no part operates near its rated limits. The point is that a part running at 80% of its voltage rating has headroom to absorb the parametric drift that TID, aging, and temperature will introduce over the mission. Typical space derating guidelines (the kind you'd find in a program's derating standard) might call for something like 70–80% of rated voltage, 50–70% of rated current, and a junction temperature well below the absolute maximum. The exact numbers depend on the program and the part class, but the principle is consistent: leave margin.

Where this interacts with radiation is that TID causes parametric shifts — threshold voltage drift, leakage increase, gain degradation, reference drift — and those shifts eat into your derating margin. So a part that's comfortably derated at beginning of life can drift out of spec by end of life if you didn't account for the TID-induced shift. That means the derating analysis and the radiation analysis have to be done together, not sequentially. If a part's datasheet has no radiation data, you can't just derate it harder and call it qualified — you don't know the shape or magnitude of the drift, so you can't bound it.

For part selection, I'd start from the mission's total dose requirement and the SEE environment (what particles, what flux, what's the consequence of an upset). Then I'd prefer parts with published radiation test data — QML Class V or equivalent, or at least parts with single-event and TID characterization from a reputable source. Where I have to use a COTS part because no qualified alternative exists, I'd treat it as a risk item: characterize it if the budget allows, or design around its uncertainty with redundancy, current limiting, and a means to recover from upsets. And I'd keep the derating conservative specifically to buy back margin for the uncharacterized drift.

The trap to avoid is using derating as a justification for skipping radiation qualification. "It's only running at 50% voltage, so it'll be fine" is not a radiation argument — it says nothing about whether the part latches up or how its reference drifts under dose.

**Possible follow-ups:**
- How would you handle a part where the manufacturer provides TID data but no single-event data, and the part sits in a path where an SET would be consequential?
- If a derating analysis shows a part is marginal at end of life only because of TID-induced drift, what options do you have short of reselecting the part?

## Q3: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** I'd separate the claim into two parts: whether TMR on the digital side actually protects the analog measurement, and whether the analog chain has its own failure modes that TMR can't touch. The answer to both is essentially no, and I'd walk through why.

TMR on the digital side protects against upsets in the digital logic — it doesn't protect against a corrupted input. If the analog chain delivers a wrong value to the ADC, TMR will faithfully vote on the wrong value and pass it through. Redundancy downstream of a single point of failure doesn't remove the single point of failure; it just makes the failure harder to detect. So the argument that "the digital side is covered" is a category error — it's protecting the wrong thing.

Then I'd look at the analog chain's actual failure modes. A single-ended, non-redundant chain has several: the amplifier can experience an SET that produces a transient at its output; the ADC's sample-and-hold or reference can glitch; the sensor itself can drift under TID; and a single-ended topology is more susceptible to ground noise and common-mode coupling than a differential one. None of these are addressed by digital TMR.

What I'd recommend depends on the criticality and the time-sensitivity of the measurement. If the measurement is critical and a wrong value could cause a dangerous control action, I'd want at least one of: a differential signal chain to reject common-mode noise and improve SET immunity; a plausibility check or rate-of-change limit on the measured value so a transient spike is rejected before it reaches the control loop; and, where the consequence justifies it, a second independent measurement path with comparison or voting at the digital boundary. The plausibility check is often the cheapest and most effective — a single-event transient is usually a fast excursion, and a filter or a "reject if the value moved more than X in one sample period" rule catches a lot of them without full redundancy.

I'd also raise the point that "critical" needs to be defined by the consequence, not by the engineer's intuition. If the measurement feeds a control loop that adjusts an actuator, the question is what happens if the loop acts on a wrong value for one cycle — is it recoverable, or does it cause harm? That answer drives how much redundancy the analog side needs.

**Possible follow-ups:**
- How would you implement a plausibility check without introducing a lag that makes the control loop respond too slowly to a real change?
- If you add a second measurement path, how do you decide between voting the two values and using one as a cross-check on the other?

## Q4: How would you approach designing a memory scrubbing strategy for an SRAM-based FPGA in a space application, and what trade-offs would you weigh?

**Answer:** Scrubbing is about correcting accumulated configuration upsets before they cause a functional error, and the design is a set of trade-offs between detection latency, resource cost, and the risk of the scrubber itself being disturbed.

The starting point is understanding what you're protecting. In an SRAM-based FPGA, the configuration memory holds the routing and logic definition; an upset there can change the circuit's function, not just its data. That's different from an upset in user RAM or block RAM, which corrupts data but not the design. So the scrubbing strategy has to cover configuration memory, and separately you'd handle data memory with ECC and, if needed, its own scrubbing.

For configuration memory, the common approach is a scrubber that periodically reads the configuration frames, checks them against a known-good copy or an error-detecting code, and rewrites any frame that's wrong. The trade-offs:

- **Scrub rate vs. resource cost.** Scrubbing the whole device frequently catches upsets sooner but consumes more of the FPGA's logic and memory bandwidth, and it competes with the application for access to the configuration port. A slow scrub leaves an upset in place longer, increasing the window in which it can cause a functional error. The right rate depends on the upset rate and the consequence of a functional error — a design where an upset causes a brief glitch can tolerate a slower scrub than one where an upset could latch a bad state.
- **Blind scrubbing vs. readback-and-compare.** Blind scrubbing just rewrites the configuration periodically without checking; it's simple and cheap but can't tell you whether an upset occurred, so you lose the telemetry that tells you the environment is worse than expected. Readback-and-compare detects and reports, at the cost of more logic and a comparison against a golden image that itself must be protected.
- **The scrubber's own vulnerability.** The scrubber is logic in the same device, so it can be upset too. If the scrubber is a soft core, it needs to be robust — either hardened by design, or implemented in a way that a single upset in the scrubber doesn't corrupt the golden image or the scrub logic. This is where a hard-wired scrubber in a rad-hard device has an advantage over a soft implementation.
- **Interaction with partial reconfiguration and the application.** Scrubbing must not collide with legitimate configuration changes or with the application's use of the configuration port. The schedule has to account for that.

I'd also consider whether the device has built-in error detection (some rad-hard FPGAs do) and how that interacts with the scrubber — you don't want two mechanisms fighting over the same frames. And I'd want the scrubber's behavior to be observable: if the upset rate spikes, that's information the mission may need.

**Possible follow-ups:**
- How would you protect the golden configuration image that the scrubber compares against, given that it's stored somewhere that can also be upset?
- If the scrubber is a soft core in the same FPGA, how would you convince yourself that a single upset in the scrubber can't corrupt the configuration it's supposed to be protecting?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the technical question from the interpersonal one. The engineer has done real work, and treating the proposal as obviously wrong would be both unfair and counterproductive — it would make the review adversarial and cost me the engineer's engagement. So I'd start by making sure I understand the proposal on its own terms: what assumptions is it built on, what data supports it, and what does the engineer think the margin is? Often the disagreement is really about a shared assumption that hasn't been made explicit.

Then I'd try to make the disagreement concrete and testable rather than a clash of opinions. If the concern is margin, I'd ask: what's the worst-case condition, and what's the margin against it? If the engineer's answer relies on a typical value rather than a worst-case value, that's a specific, non-personal thing to examine. If it relies on a part with no radiation data, the question becomes how we bound the risk without data. Framing it as "help me understand how this holds under worst-case X" keeps it technical and gives the engineer a path to either defend the design or revise it.

I'd also be open to being wrong. The engineer may have information I don't — a test result, a vendor clarification, a precedent from a previous program. If the proposal is actually sound and my concern was based on an outdated assumption, I should say so and move on. The goal is the right decision, not winning the argument.

Where the disagreement persists after the technical discussion, I'd fall back on the process: what does the program's risk management approach say about this class of decision? If the part or approach is a risk item, it should be captured as one, with an owner and a mitigation, rather than resolved by whoever argues hardest in the room. That turns a personal disagreement into a documented, reviewable decision — and it means the engineer's proposal isn't dismissed, it's tracked. If the consequence of being wrong is high, I'd want the decision to have a second set of eyes, whether that's a peer review, a radiation subject-matter expert, or a formal risk review.

Finally, I'd be explicit about the decision and the reasoning, so the engineer understands why it went the way it did and what would change the answer. A review that ends with "we're doing it my way" and no explanation damages trust; one that ends with "here's the concern, here's the evidence, here's what we'll do and why" keeps the relationship intact even when the engineer disagrees.

**Possible follow-ups:**
- What would you do if the engineer's proposal is technically defensible but you still believe the risk is too high for the program's risk posture?
- How would you handle it if the same engineer repeatedly proposed under-margined designs — is that a technical coaching issue or a performance issue, and how would you tell the difference?