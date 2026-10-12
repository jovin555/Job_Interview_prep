# debugging-failure-analysis — Day 83

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key insight is that the failure correlates with mechanical state, not electrical state, so the investigation should treat the enclosure and mounting as part of the circuit. I'd start by characterizing the offset precisely: magnitude, sign, whether it's stable or drifts, and whether it changes with orientation or mounting torque. Then I'd try to reproduce it on the bench by progressively adding the variables the enclosure introduces — first the enclosure alone (unmounted), then mounted in a representative fixture, then with the final mounting hardware torqued to spec. If the offset appears only at the final step, that points to mechanical stress: PCB flexure changing the stress state of a strain-sensitive component, a connector or cable shield making contact with the chassis, or a ground reference shifting because the board's ground is now tied to the enclosure at a different point.

I'd measure the analog front-end's reference and ground at the ADC pins relative to the system ground while in the failing state, not just at the input, because a "sensor offset" is often actually a reference or ground shift. A differential probe across the signal and its return, plus a check of the reference voltage at the ADC, will separate a true input offset from a reference error. If the offset tracks mounting torque, that's strong evidence of mechanical stress on a component — a ceramic capacitor with piezoelectric behavior, a solder joint under strain, or a flex-induced change in a resistor's value. I'd also check whether the enclosure is creating a new ground loop or a shield connection that wasn't present on the bench.

The corrective direction depends on the mechanism: if it's flexure, stiffen the mounting or relocate the sensitive component; if it's a ground reference shift, revisit the grounding scheme and the enclosure tie points; if it's a shield/contact issue, fix the mechanical interface. The important discipline is to change one variable at a time — enclosure, then mounting, then torque — so the offset can be attributed to a specific cause rather than a bundle of them.

**Possible follow-ups:**
- How would you distinguish a piezoelectric capacitor effect from a genuine ground shift, given both can produce a stable offset?
- If the offset only appears in the customer's installation and not in your fixture, how would you structure the investigation to avoid chasing a unit that passes on your bench?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and power-distribution problem, so I'd approach it as a question of where the ripple originates and how it propagates. First, I'd measure the ripple at the load — right at the switching subsystem's supply pins — and then at the regulator output, and compare. If the ripple is large at the load but small at the regulator, the problem is in the distribution path: trace inductance, insufficient decoupling, or a ground return that's shared with the switching current. If the ripple is large at the regulator too, the regulator's loop response or its input supply is the issue.

I'd probe with a proper high-bandwidth setup — short ground lead or a ground spring, AC-coupled, limited bandwidth to avoid picking up ambient noise — and look at the ripple's frequency content. Ripple at the switching frequency points to the regulator or its input; ripple at the subsystem's own switching edges points to the load's current draw and the decoupling network's ability to supply it. I'd also check the ground: probing across a decoupling capacitor's own terminals, rather than from a distant ground point, tells you what the capacitor actually sees versus what the rest of the board sees.

The likely fixes are adding or relocating bulk and high-frequency decoupling close to the load, improving the ground return so the switching current doesn't share impedance with sensitive nodes, or slowing the load's edge rate if that's acceptable. If the regulator's transient response is the limit, increasing output capacitance or adjusting compensation may help, but that has stability implications. The discipline is to measure at multiple points along the path — regulator output, mid-rail, load pins — so the ripple's source and its coupling mechanism are both identified before changing anything.

**Possible follow-ups:**
- How would you tell whether the ripple is being conducted along the rail versus radiated and picked up by your probe?
- What would you check if adding decoupling reduced the ripple but didn't eliminate it?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hardest part of this class of failure is that nothing in the system flags it, so the investigation has to start by making the failure observable. I'd first try to characterize the error statistically: how often it occurs, whether it correlates with operating mode, temperature, time since boot, or a particular sensor, and whether the wrong value has any structure — a fixed offset, a stuck bit, a value from a previous reading, or a plausible but shifted number. That structure often points directly at the mechanism: a stale buffer, a race between the read and the conversion, a scaling or calibration error applied intermittently, or a communication error that passes the sensor's own checksum.

I'd add instrumentation that captures the raw data path — the ADC or sensor output, the value as received, and the value as stored or transmitted — so the point of corruption can be localized. If the raw value is correct but the stored value is wrong, the problem is in the firmware's handling; if the raw value is already wrong, it's in the acquisition or the sensor interface. I'd also look at timing: if the error correlates with a concurrent operation, that suggests a shared resource, a missing lock, or a read that overlaps a conversion. A logic analyzer or trace on the interface, plus a timestamped log of the value at each stage, usually narrows it down.

Because the error is only caught offline, I'd also consider whether the system's own validation is too weak — a plausibility check or a cross-check against a second measurement might have caught it earlier. That's a separate corrective action from the root cause, but it's worth raising, because a failure that's invisible in the field is a reliability risk regardless of how it's eventually fixed.

**Possible follow-ups:**
- How would you decide whether the wrong value is a data-integrity problem or a calibration/scaling problem?
- What would you add to the firmware to make this class of error detectable in the field without generating false positives?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the productive move is to stop arguing about which is more likely and instead design a test that discriminates between them. I'd ask the team to state, for each hypothesis, what evidence would confirm it and what evidence would rule it out — and then look for the cheapest, fastest experiment whose outcome differs depending on which hypothesis is true. That reframes the disagreement from opinion to prediction, which is usually enough to get people aligned even when they started on opposite sides.

I'd also make sure both hypotheses are being evaluated against the same evidence, because teams often weight the data that supports their own view. Writing down the observations and the inferences separately helps: the observations are shared facts, the inferences are where the disagreement lives. If the discriminating test isn't feasible, I'd look at whether the two causes could both be contributing — sometimes the split is artificial and the real answer is a combination, or one cause that presents differently under different conditions.

On the process side, I'd set a time-box for the discriminating experiment and be explicit about what happens if it's inconclusive: either escalate to a broader test, or, if the risk justifies it, implement a conservative fix that addresses both while continuing the investigation. The goal is to keep the team moving on evidence rather than letting the split harden into a stalemate. I'd also make sure the person whose hypothesis loses isn't left feeling dismissed — the point is to follow the data, and a well-designed test protects everyone from having to defend a position.

**Possible follow-ups:**
- How would you handle it if the discriminating test is expensive or would take weeks, and the schedule won't allow it?
- What would you do if the team's disagreement is really about risk tolerance rather than about the evidence?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The first thing I'd do is acknowledge that the approach they've taken — testing components in isolation — is reasonable, and that the fact it hasn't worked is information, not failure. Intermittent system-level failures often can't be found by testing parts in isolation, because the failure depends on the interaction between parts, and that's a genuinely different problem. Framing it that way takes some of the frustration out of it and makes it easier to redirect.

Then I'd work with them to make the failure observable and reproducible, because that's usually the real blocker. If the failure is intermittent, the priority is to increase its rate — run the system in the failing condition longer, stress it with temperature or load, or add instrumentation that captures state at the moment of failure. A failure that happens once a day is nearly impossible to debug; one that happens every few minutes is tractable. I'd help them set up logging or a trigger that captures the relevant signals when the failure occurs, so they're not relying on catching it by eye.

I'd also help them question their assumptions. "Everything passes in isolation" often means the test conditions don't match the system conditions — different supply, different grounding, different timing, different load. I'd ask what's different between the isolated test and the real system, and whether the failure could be a timing or interaction effect rather than a component defect. And I'd make sure they're changing one variable at a time, because a frustrated debugger under schedule pressure tends to change several things at once, which destroys the ability to attribute the result.

Finally, I'd stay involved rather than just giving advice — pair on the next experiment, or check in daily — because the schedule pressure is real and the fastest way to unblock them is often to work the problem alongside them for an hour rather than to send them off with a suggestion.

**Possible follow-ups:**
- How would you decide when to take over the debugging yourself versus continuing to coach them?
- What would you do if the failure can't be made to reproduce at a useful rate, and the schedule won't allow a long soak test?