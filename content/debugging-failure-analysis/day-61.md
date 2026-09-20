# debugging-failure-analysis — Day 61

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only after two changes happen together: the enclosure goes on, and the unit is mounted in its operating position. That points away from the analog signal chain itself — which is proven good on the harness — and toward something the enclosure and mounting introduce: mechanical stress, a changed thermal environment, a changed ground/return path, or a changed parasitic coupling path.

I'd start by separating those variables rather than treating "assembled" as one condition. First, reproduce with the board in the enclosure but sitting on the bench, unmounted. If the offset appears, the enclosure is the driver; if it doesn't, the mounting position is. Then I'd try the reverse — board on the harness but physically mounted — to confirm which variable actually correlates.

If it's the enclosure, the usual suspects are: flex or pressure on the board or on a connector/cable that changes a reference or a solder-joint resistance; a cable routing change that shifts the return current path under the analog front-end; or a thermal shift from reduced airflow raising the offset of an amplifier or reference. I'd probe the reference and the amplifier inputs directly with a high-impedance meter or scope while flexing and while at operating temperature, and compare the offset against the front-end's own input-referred error budget to see whether it's a real analog shift or a grounding/measurement artifact.

If it's the mounting position, I'd look at what the mounting changes: chassis grounding, a conductive surface creating a new return path, or mechanical stress on the sensor or its cable. A useful test is to measure the offset with the unit mounted but with the analog front-end's ground referenced to a known clean point, to see whether the "offset" is actually a ground-potential difference being amplified.

Throughout, I'd keep it to one variable at a time and log the offset value at each configuration so the correlation is unambiguous before proposing a fix. The corrective action then follows the mechanism — strain relief, a layout/return-path change, a thermal fix, or a grounding change — rather than a blanket recalibration that would mask the real cause.

**Possible follow-ups:**
- How would you tell the difference between a genuine analog offset and a ground-potential difference being measured as one?
- If the offset only appears after the unit has been mounted for a while, how would you rule thermal drift in or out?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and shared-impedance problem, so I'd treat it as a power-integrity investigation rather than a "bad regulator" investigation. The regulator is fine at idle; the question is what the switching load does to the rail and to everything sharing its return path.

First, I'd characterize the ripple properly rather than trusting a single probe point. I'd measure at the load's decoupling capacitors, not just at the regulator output, because the ripple seen at the regulator and the ripple seen at the load can differ substantially once you account for trace and via impedance. I'd use a short ground-spring probe or a proper differential/pigtail setup to avoid picking up loop-induced artifacts that look like ripple but aren't.

Then I'd separate the mechanisms. Is the ripple the regulator's transient response to a fast load step (loop bandwidth, output cap ESR/ESL, insufficient bulk capacitance)? Is it shared-impedance coupling — the switching current returning through a ground or supply path that the sensitive rail also references? Or is it radiated/conducted coupling from the switching node into the rail? I'd distinguish these by: adding local bulk capacitance right at the load and seeing if the transient dip shrinks (points to transient response); probing the ground at the load versus the ground at the regulator (points to shared return impedance); and using a near-field probe to check for magnetic coupling from the switching loop.

I'd also look at the switching edge rate and loop area of the high-current subsystem — a fast di/dt through a large loop is a common root cause, and slowing the edge or shrinking the loop often fixes it without touching the regulator. If it's a load-step response issue, the fix is usually more/appropriate output capacitance or a regulator compensation change, verified with a load-step test at the actual worst-case current slew.

The discipline is: reproduce with a defined load profile, measure at the right points with the right probe technique, identify the dominant mechanism, then fix the mechanism and re-measure against the same profile.

**Possible follow-ups:**
- How would you set up a repeatable load-step test to compare before and after a fix?
- If adding bulk capacitance reduces the ripple but doesn't eliminate it, what would that tell you?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hard part here is that nothing in the system flags the error, so the first job is to make the failure observable rather than to guess at a cause. A plausible-but-wrong value means the data path produced a number that passed every sanity check, which usually means the corruption is either a small numerical error, a stale-but-valid value, a scaling/units mismatch, or a timing issue where the wrong sample got associated with the wrong timestamp.

I'd start by adding instrumentation that captures the raw evidence at each stage of the pipeline: the raw ADC/sensor reading, the value after any calibration or filtering, and the value as transmitted or stored, each with a timestamp and a sequence counter. That lets me localize whether the error is introduced at acquisition, in processing, or in transport/storage. Without that, any hypothesis is untestable.

Then I'd think about the mechanisms that produce plausible-but-wrong values specifically. A stale read — the sensor returned its previous value because a conversion wasn't complete or a bus transaction silently failed — is a very common one, and it's invisible if the firmware doesn't check a "data ready" flag or a transaction status. A race between an ISR updating a shared buffer and the main loop reading it can produce a torn or half-updated value that still looks in-range. A units or fixed-point scaling error can be consistently wrong in a way that only shows up against a reference. And a filter with a bad initial condition or a coefficient error can drift a value into a plausible-but-wrong region.

I'd also look at the review process that caught it: how was the error detected offline? That tells me what "correct" looks like and gives me a comparison signal I can use to build a targeted test. If I can reproduce it by injecting the suspected condition — a delayed data-ready, a bus error, a specific timing pattern — that's far more valuable than waiting for it to recur naturally.

Finally, I'd make sure the fix includes a detection mechanism, not just a correction, because a silent wrong value in a medical context is a serious class of failure. Adding a plausibility cross-check, a freshness check, or a redundant read is often as important as fixing the root cause.

**Possible follow-ups:**
- How would you design a test that reliably reproduces a stale-read condition?
- What kind of runtime check would you add so this class of error can't stay silent in the future?

## Q4: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, the system fails — is a strong signal that the problem lives in an interaction, not in any single component, and the debugging method needs to change rather than the effort increase. So my first move is to help the engineer see that, without making them feel their work was wasted.

I'd sit down with them and ask them to walk me through what they've established, not what they suspect. The goal is to separate "facts I've proven" from "things I've assumed." Often the stall comes from an unexamined assumption — that the test harness is equivalent to the real system, that a passing isolated test means the component is fine in context, or that the failure is in one place when it's actually an interaction between two.

Then I'd reframe the problem around reproduction and observability. If the failure is intermittent, the priority is to make it happen on demand or at least to increase its rate, because debugging something you can't reproduce is guesswork. I'd help them find the conditions that raise the failure rate — temperature, timing, load, a specific sequence of operations — and then instrument the system to capture state at the moment of failure rather than testing components one at a time.

I'd also introduce a divide-and-conquer structure at the system level: bisect the system by disabling or stubbing subsystems to find which combination is necessary for the failure, and use that to narrow the interaction. And I'd set a checkpoint — a specific experiment with a clear expected result — so progress is measurable and the engineer gets a win, which matters for morale as much as for the schedule.

On the schedule pressure: I'd be honest that a rushed guess is likely to cost more time than a structured narrowing, and I'd take on some of the load myself — pairing on the instrumentation or running a parallel experiment — so the engineer isn't carrying it alone. The message is that the method is the problem, not their ability.

**Possible follow-ups:**
- How would you decide when to step in and take over versus coach them through it?
- What would you do if, after reframing, the failure still couldn't be reproduced?

## Q5: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the trap is to let the team argue about which is more likely, because that's a debate about belief rather than evidence. My job is to convert it into an experiment that can distinguish between them.

First, I'd make both hypotheses explicit and falsifiable. For each, I'd write down what it predicts that the other does not — a specific measurable difference. If I can't articulate a distinguishing prediction, the hypotheses aren't yet sharp enough, and the next step is to sharpen them rather than test them.

Then I'd design the cheapest, fastest test that separates them. Often that's a fault-injection or a controlled modification: if hypothesis A is true, disabling or altering X should make the failure disappear or change character; if hypothesis B is true, it shouldn't. The key is that the test must give a different result under the two hypotheses, so a single experiment can eliminate one.

I'd also be willing to run both threads in parallel if they're cheap, rather than forcing a serial choice — the goal is to reach the answer, not to win the argument. But I'd timebox each and define in advance what result would count as confirmation or elimination, so the team can't rationalize a null result into support for their preferred cause.

On the team dynamics: I'd frame it as "we have two candidates and we're going to let the evidence decide," which takes the personal stake out of it. If a senior person is attached to one hypothesis, giving them a fair, well-defined test to run respects their experience while keeping the conclusion evidence-based. And I'd keep a written record of what was tested and what it showed, so the final conclusion is traceable and defensible — which matters in a regulated context where the corrective action has to be justified.

If, after the distinguishing tests, the evidence still doesn't cleanly separate them, I'd consider whether both contribute — sometimes the answer is an interaction, and the honest conclusion is a combined mechanism rather than a single cause.

**Possible follow-ups:**
- What would you do if the distinguishing test is expensive or slow to run?
- How would you document the elimination of the rejected hypothesis for the investigation record?