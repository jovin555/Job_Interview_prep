# debugging-failure-analysis — Day 87

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key insight is that the failure correlates with a physical configuration change, not with a component or a signal path that's inherently broken — so the investigation should treat the enclosure and mounting as part of the circuit, not as a neutral container. I'd start by characterizing the offset precisely: is it a fixed DC shift, a gain change, or a change in the noise floor? That distinction narrows the mechanism considerably. A fixed offset that appears only when assembled usually points to a changed ground reference or a new parasitic path — for example, a mounting screw or chassis feature that now ties the analog ground to chassis ground at a second point, creating a ground loop that shifts the reference the ADC sees. A gain change would point more toward a changed input impedance or a leakage path across the sensor front-end.

From there I'd work by subtraction: measure the same node with the board open on the bench, then with the board in the enclosure but not mounted, then mounted in the final position. If the offset appears at the "in enclosure" step, it's a shielding/enclosure effect; if it only appears at "final mounting," it's a mechanical or grounding-path effect introduced by the installation. I'd probe the analog ground reference and the sensor's return path at each stage, because a small offset that's stable and repeatable is almost always a reference or return-path issue rather than a random noise problem. I'd also check whether the enclosure is metallic or has a conductive coating, since that changes the coupling environment around the front-end.

Once I have a hypothesis, I'd confirm it by temporarily breaking the suspected path — lifting a mounting point, adding an insulating washer, or re-routing the ground return — and seeing whether the offset disappears. That's the cheapest way to confirm a grounding hypothesis before committing to a design change. The corrective action then depends on the mechanism: a single-point ground strategy, a guard ring around the front-end, or a change to how the enclosure interfaces with the board's ground plane.

**Possible follow-ups:**
- If the offset is present with the enclosure closed but not when it's open, how would you distinguish a shielding effect from a grounding effect?
- How would you verify that a proposed grounding change actually fixes the issue across multiple units rather than just the one you tested?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and power-distribution problem, so I'd approach it as a question of where the transient energy is going and why the rail isn't absorbing it. The first step is to measure the ripple correctly — at the load, not at the regulator output, and with a proper probe technique (short ground lead, or a coax pigtail) so I'm not measuring the probe's own loop. Where I measure matters enormously here: ripple at the regulator can look fine while ripple at the load is out of spec, because the impedance of the trace and the decoupling network between them is what's actually failing.

Next I'd characterize the transient itself: what's the magnitude, the duration, and the repetition rate? A fast, high-amplitude spike suggests the bulk and high-frequency decoupling aren't supplying the initial current demand, so the rail sags until the regulator loop responds. A slower, broader dip suggests the regulator's loop bandwidth or its output capacitance is the limiting factor. I'd look at the load transient response specifically — inject a step load or trigger on the subsystem's switching edge and watch how the rail recovers.

Then I'd work through the decoupling network from the load backward: are the high-frequency caps physically close to the load, is the bulk capacitance adequate for the transient energy, and is there a resonance in the network that's being excited? I'd also check the return path — a high-current switching subsystem can inject noise into the ground plane, so what looks like rail ripple may partly be ground bounce, which means probing differentially or with a careful ground reference. If the ripple correlates with the switching edges, I'd also consider whether the subsystem's own supply is being starved and feeding back, or whether its switching node is coupling into the rail through a shared impedance.

The fix usually falls into one of a few categories: better local decoupling, a change to the regulator's compensation or output capacitance, a layout change to reduce shared impedance between the subsystem and the sensitive load, or filtering at the point of load. I'd confirm the fix by re-measuring at the load under the worst-case switching condition, not just at nominal.

**Possible follow-ups:**
- How would you tell the difference between rail ripple and ground bounce when probing a switching load?
- If adding capacitance doesn't help, what would that tell you about the mechanism?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hardest part of this class of bug is that nothing in the system considers it a failure, so there's no fault flag, no error log, and no obvious trigger to chase. I'd start by treating it as a data-integrity problem and asking where in the chain the value could have been corrupted: at the sensor, in the analog front-end, in the ADC conversion, in the firmware's read-and-store path, or in the transmission and logging. The fact that the value is plausible is important — it means whatever produced it was either a real but misattributed reading, a stale value, or a value that passed through a path that didn't validate it.

I'd first try to reproduce it under controlled conditions, because an intermittent data error that's only caught offline is very hard to reason about without a reproduction. That might mean running the device for extended periods while logging raw sensor data alongside the processed value, so I can compare what the sensor actually produced against what the firmware reported. If the raw and processed values diverge, the bug is in the firmware path; if they agree but are both wrong, the issue is upstream in the analog chain or the sensor itself.

I'd also look at the timing and concurrency around the read: is the sensor being read while another operation is in progress, is there a shared buffer that could be overwritten, is there a conversion that could be sampled mid-update? A plausible-but-wrong value is often a stale or torn read — the firmware grabbed a value that was valid a moment ago, or half of an update. I'd check whether the read path has any atomicity guarantees and whether the sensor's data-ready signal is actually being respected.

Finally, I'd add validation that would have caught this earlier — range checks, rate-of-change checks, cross-checks against a redundant source — not as a fix, but as a way to turn a silent error into a detectable one so the investigation has something to work with.

**Possible follow-ups:**
- How would you distinguish a stale read from a genuinely corrupted value?
- What kind of logging would you add to make this reproducible without changing the system's behavior?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the temptation is to argue about which is more likely, but that's usually unproductive — the better move is to find the experiment that discriminates between them. I'd start by writing down, for each hypothesis, what prediction it makes that the other one doesn't. If both hypotheses predict the same observable behavior, then the evidence so far genuinely can't distinguish them, and I need a test that probes the difference. That reframes the disagreement from "who's right" to "what test settles it," which is a much easier conversation to have.

I'd also be honest about the cost and time of each discriminating test, and pick the one that gives the most information per unit of effort. Sometimes that's a targeted measurement; sometimes it's a controlled fault injection where I deliberately create one condition and see whether the failure appears. If a test is expensive or slow, I'd look for a cheaper proxy that still separates the hypotheses.

On the team dynamics side, I'd make sure both hypotheses are treated as legitimate until the evidence says otherwise, because shutting down one camp early tends to make people defensive and withhold information. I'd assign someone to actively try to falsify each hypothesis rather than defend it — that's a healthier structure than having each side advocate for its own theory. And I'd set a checkpoint: if the discriminating test is inconclusive, we agree in advance on what we'll do next rather than re-litigating the same argument.

If it turns out both mechanisms are real and contributing, that's a valid outcome too — the investigation should be able to conclude "both, with this relative contribution" rather than forcing a single root cause.

**Possible follow-ups:**
- What would you do if the discriminating test is inconclusive and the schedule won't allow another round?
- How would you keep the team aligned if the evidence eventually points to one hypothesis and the other camp feels their work was wasted?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, the system fails — usually means the bug lives in an interaction, not in any single component, so the engineer's approach of testing parts individually can't find it no matter how long they keep at it. The first thing I'd do is validate that their work isn't wasted: the fact that everything passes in isolation is actually useful information, because it rules out a whole class of causes and tells us the problem is in how the parts behave together. Reframing it that way helps with the frustration, because it turns "I've been failing for days" into "I've eliminated a lot of possibilities."

Then I'd help them change the unit of analysis from component to condition. Instead of asking "is this part good?", ask "what's different about the system when it fails versus when it passes?" That means capturing the state at the moment of failure — supply conditions, temperature, timing, what else is running — and comparing it to a passing run. Intermittent system-level failures usually have a trigger condition that isn't present in isolated testing, and the job is to find that condition rather than to keep re-testing the parts.

I'd also look at whether they have a reliable way to reproduce the failure at all. If they can't reproduce it on demand, the priority is to build a reproduction — even a low-probability one — because debugging without a reproduction is mostly guesswork. That might mean running the system in a loop, stressing it, or instrumenting it to log more state so that when it does fail, there's evidence to work with.

On the schedule pressure, I'd be realistic: I'd help them time-box the current approach and set a checkpoint where we either have a reproduction or we escalate to a different strategy, rather than letting them grind indefinitely. And I'd pair with them for a session — not to take over, but because a fresh perspective on the same data often spots the assumption that's been invisible to the person closest to it.

**Possible follow-ups:**
- How would you help them build a reproduction when the failure only happens every few days?
- What would you do if, after pairing, you also can't find the trigger — how would you decide whether to keep investigating or work around it?