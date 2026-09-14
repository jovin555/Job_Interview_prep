# debugging-failure-analysis — Day 55

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only when two variables change together — the enclosure is closed and the unit is mounted. That points away from the analog signal chain itself and toward something mechanical, thermal, or grounding-related that changes with assembly and installation. I'd start by separating those two variables: test the board open on the bench (baseline), then in the closed enclosure but not mounted, then closed and mounted in the final position. If the offset appears at the "closed enclosure" step, it's likely thermal (self-heating trapped inside) or a mechanical stress effect on a component. If it only appears at the "mounted" step, it's more likely a grounding or reference-plane issue — the mounting position may be introducing a ground loop or changing the reference potential the front-end sees.

For a consistent offset, I'd suspect a few specific mechanisms: mechanical stress on a strain-sensitive component (some precision resistors and ceramic capacitors are piezoelectric or piezoresistive), a change in the reference voltage due to a ground-path shift, or a thermal gradient across the instrumentation amplifier input pair. I'd measure the offset with a known-good reference signal injected at the sensor connector, then repeat with the enclosure closed and with the unit mounted, logging the offset magnitude at each stage. If the offset correlates with temperature, I'd use a thermal camera or thermocouples to map the gradient across the front-end. If it correlates with mounting torque or position, I'd vary the mounting and see if the offset tracks.

The corrective direction depends on the mechanism: if it's thermal, it may be a layout or thermal-management fix; if it's mechanical stress, it may be a component selection or mounting-isolation change; if it's grounding, it may be a reference or shielding change. The important thing is to reproduce the offset reliably under controlled conditions before proposing a fix, so the corrective action can be verified against the same setup.

**Possible follow-ups:**
- How would you distinguish a thermal offset from a mechanical-stress offset if both are plausible?
- If the offset is within the sensor's datasheet accuracy but still triggers a system fault, how would you decide whether to fix the hardware or adjust the algorithm?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and power-distribution problem, and the first thing I'd do is characterize the ripple properly rather than just observe it. I'd measure at the point of load, not at the regulator output, because the ripple a downstream device sees is often dominated by the impedance between the regulator and the load — trace inductance, via inductance, and the ESR/ESL of the decoupling network. I'd use a short-ground-tip probe or a proper coaxial measurement to avoid picking up radiated noise that isn't actually on the rail.

Next I'd look at the switching event itself. Is the ripple synchronous with the subsystem's switching edges? If so, it's likely a load-step response issue: the regulator's control loop can't respond fast enough, so the rail dips or rings until the loop catches up. I'd check the regulator's transient response spec against the actual load step, and look at whether the bulk and decoupling capacitance is adequate and correctly placed. A common finding is that the bulk cap is far from the load, so its charge can't reach the load fast enough through the trace inductance.

I'd also check for ground bounce. If the high-current subsystem shares a ground return path with the sensitive rail, the switching current can modulate the ground reference and appear as ripple. Probing ground at multiple points — at the regulator, at the load, and at the subsystem's ground return — would show whether the ground is moving. If it is, the fix is usually to separate the return paths or add a local ground plane/stitching.

Finally, I'd consider whether the ripple is actually conducted or radiated. A near-field probe scan around the switching subsystem would show if the ripple is being coupled magnetically or capacitively into the rail. If it's radiated, the fix is layout and shielding; if it's conducted, it's decoupling and loop response. The measurement approach determines which fix is appropriate, so I'd resist the temptation to just add capacitors until the mechanism is understood.

**Possible follow-ups:**
- How would you measure the regulator's loop response without a dedicated network analyzer?
- If the ripple is within the regulator's spec but still causes the downstream device to misbehave, how would you approach the problem?

## Q3: How would you approach a failure investigation where a device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and the error is only caught later when the data is reviewed offline?

**Answer:** This is one of the harder classes of failure because there's no obvious fault signature — the value passes every range check and plausibility test, so the system has no way to know it's wrong at the time. The first thing I'd do is establish whether the error is in the acquisition, the processing, or the reporting path. I'd add instrumentation to log the raw sensor data, the intermediate processed value, and the final reported value, all timestamped, so I can see exactly where the value diverges from what it should be.

If the raw data is correct but the processed value is wrong, the issue is in the firmware's signal chain — a race condition, a buffer overwrite, a stale value being read, or an arithmetic issue. If the raw data is already wrong, the issue is in the acquisition path — the sensor interface, the ADC, or the timing of the read. If both are correct but the reported value is wrong, the issue is in the communication or storage path.

A common cause of "plausible but wrong" values is a stale read: the firmware reads a register before the sensor has updated it, or reads a buffer that hasn't been refreshed. Another is a race condition where two tasks access the same variable without proper synchronization, so the value is a mix of old and new data. Another is a single-bit error in a memory location that happens to produce a plausible value. I'd look for these by adding checksums or sequence counters to the data path, and by stress-testing the system under conditions that maximize the chance of the race — high load, fast sampling, concurrent operations.

The corrective action depends on the mechanism, but the investigation discipline is the same: capture the data at each stage, reproduce the error under controlled conditions, and trace it to the specific point where the value goes wrong. Without that trace, any fix is a guess.

**Possible follow-ups:**
- How would you design a self-test that could catch a plausible-but-wrong value without adding excessive overhead?
- If the error only occurs in the field and never on the bench, how would you approach reproducing it?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** The first thing I'd do is make sure both hypotheses are stated clearly and falsifiably — not as vague suspicions but as specific claims about what mechanism is causing the failure and what evidence would confirm or refute each one. Often, when a team is split, the disagreement is partly about framing rather than about evidence, and clarifying the hypotheses can reveal that they're not actually mutually exclusive or that one is much easier to test than the other.

Then I'd design a discriminating test — an experiment whose outcome would be different depending on which hypothesis is correct. That's the most efficient way to break a tie: instead of trying to prove one hypothesis right, find a test that would prove one of them wrong. If no single test can discriminate, I'd look for a test that can at least raise or lower the probability of each hypothesis, and run them in parallel if resources allow.

I'd also be explicit about the cost of being wrong. If one hypothesis, if true, would require a major design change and the other would require a firmware patch, the investigation priority should reflect that — but not to the point of confirming the cheaper fix just because it's cheaper. The evidence has to drive the conclusion.

Throughout, I'd keep the team aligned on the decision criteria: what evidence would be sufficient to conclude, and what would be sufficient to rule out. If the team can agree on those criteria up front, the split usually resolves itself when the data comes in. If it doesn't, I'd make the call based on the weight of evidence and document the reasoning, so the decision is traceable even if it later turns out to be wrong.

**Possible follow-ups:**
- What would you do if the discriminating test is inconclusive?
- How would you handle a situation where the team's split is driven by organizational pressure rather than by evidence?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The first thing I'd do is acknowledge the frustration — intermittent system-level failures are genuinely hard, and spending days on isolation testing that keeps passing is a common and demoralizing experience. Then I'd help them step back from the component-level approach and reframe the problem. If every component passes in isolation but the system fails, the failure is almost certainly in the interaction between components — timing, power, grounding, or a condition that only exists when the full system is running.

I'd ask them to describe exactly what they've tried and what they've observed, not just what they've concluded. Often, the observations contain a clue that was dismissed because it didn't fit the current hypothesis. I'd also ask whether they've been able to reproduce the failure reliably — if not, that's the first problem to solve, because without a reliable reproduction, every test is a coin flip.

Then I'd work with them to design a test that captures more of the system state at the moment of failure: logging, instrumentation, or a trigger that freezes the system when the failure occurs. The goal is to move from "it fails sometimes" to "it fails under these specific conditions," which is the point where the investigation becomes tractable.

I'd also make sure they're not working in isolation — pairing them with someone who can look at the problem fresh, or bringing in someone from a different discipline (firmware, mechanical, test) who might see something they've missed. And I'd check in regularly, not to pressure them but to make sure they're not stuck in a loop. The schedule pressure is real, but the fastest path to a fix is usually a better understanding of the failure, not more hours of the same approach.

**Possible follow-ups:**
- How would you decide when to reassign the investigation versus continuing to coach the engineer?
- What would you do if the engineer resists the change in approach because they're convinced their method is right?