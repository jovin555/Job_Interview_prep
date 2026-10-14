# debugging-failure-analysis — Day 85

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key insight is that the failure correlates with a physical configuration change, not with a component or a signal path that's already been validated. That points toward something mechanical, thermal, or electromagnetic that only exists in the assembled state. I'd start by treating the enclosure and mounting as variables in their own right, not as a fixed backdrop.

First, I'd try to reproduce the offset reliably and quantify it — is it truly constant, or does it drift with time, temperature, or orientation? A "consistent offset" that appears only in the final mounting position often turns out to be one of a few things: a ground reference shift caused by the board now being tied to chassis or mounting hardware at a different point than the bench ground; a mechanical stress on a component (a flexed PCB changing a resistor or capacitor value, or a connector partially seated); a thermal gradient created by the enclosure trapping heat near the analog front-end; or a nearby conductor (metal chassis, mounting plate) altering the parasitic environment around a high-impedance node.

I'd divide the problem by progressively adding the enclosure back in stages: board alone on the bench, board in the enclosure but open, board fully closed, board closed and mounted. At each stage I'd measure the analog input at the ADC pin with a high-impedance probe and compare it to what the firmware reports, so I can tell whether the offset is in the analog domain or introduced later. If the offset appears only when the board is fastened down, I'd suspect mechanical stress or a changed ground return path — I'd check whether loosening the mounting screws changes it, and whether the offset tracks the mounting torque. If it appears only when the lid is closed, I'd suspect thermal or parasitic coupling — I'd log the board temperature and look for correlation.

Throughout, I'd keep the measurement reference consistent. A common trap here is that the bench ground and the installed ground are not the same node, so what looks like a sensor offset can actually be a ground potential difference being measured. I'd verify the ground reference at the analog front-end in both configurations before concluding anything about the sensor itself.

**Possible follow-ups:**
- If loosening the mounting screws makes the offset disappear, how would you confirm whether it's mechanical stress on a component versus a changed ground path?
- How would you distinguish a thermal offset from a mechanical one if both correlate with the enclosure being closed?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and power-distribution problem, and the fact that it's load-dependent tells me the issue is in the delivery path, not the regulator's steady-state regulation. I'd approach it by separating the question of "is the regulator itself struggling" from "is the distribution network between the regulator and the load inadequate."

First, I'd characterize the ripple properly. Where am I measuring it? A ripple measurement taken at the wrong point — say, at the regulator output with a long ground lead — can be dominated by probe loop inductance and tell me nothing useful. I'd use a short-ground-spring probe tip and measure right across the decoupling capacitor at the load, not at the regulator. I'd also measure at the regulator output simultaneously, so I can see whether the disturbance originates at the regulator or appears between the regulator and the load.

If the ripple is present at the regulator output too, the regulator's loop response or its input supply may be the issue — a high-current switching event can pull down the input rail, and if the input decoupling is marginal, that propagates to the output. I'd check the input rail during the switching event and look at the regulator's transient response against its datasheet load-step curves.

If the ripple is only at the load and not at the regulator output, the problem is the impedance between them — trace inductance, insufficient bulk capacitance, or a high-impedance via/plane transition. I'd estimate the transient current step and the acceptable voltage deviation, then work out how much bulk and high-frequency capacitance is actually needed at the load, and compare that to what's populated. I'd also check the ground return path: a high-current return that shares impedance with the analog or logic ground can inject the switching noise as a ground bounce rather than as a supply dip, which looks similar on a single-ended probe but has a different fix.

The systematic principle is: measure at multiple points along the delivery path, determine whether the disturbance is generated at the source or developed across the path, and only then decide whether the fix is more capacitance, better layout, or a change to the switching behavior itself.

**Possible follow-ups:**
- How would you tell the difference between a supply dip and a ground bounce if you only have a single-ended probe?
- If adding bulk capacitance at the load reduces the ripple but doesn't eliminate it, what would you investigate next?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** This is one of the harder classes of bug because there's no fault flag, no out-of-range value, and no obvious trigger — the system believes it's operating normally. The first thing I'd do is resist the temptation to guess at a cause and instead focus on making the failure observable and reproducible, because right now the only evidence is offline data review, which is far removed from the event.

I'd start by improving instrumentation. If the firmware doesn't already log the raw sensor data alongside the processed value, the timestamp, and the relevant state (which mode, what else was happening), I'd add that. The goal is to capture the context around a bad reading so I can see whether it correlates with anything — a particular operating mode, a temperature, a time since boot, a concurrent operation like a radio transmission or a motor actuation. Without that context, any hypothesis is just a guess.

Next, I'd think about where a plausible-but-wrong value can come from. It's usually one of a few categories: a data integrity problem (a bit flip in transit, a buffer overrun, a race where the value is read while it's being updated), a stale value (the sensor read failed silently and the firmware reused the last good value, or a conversion wasn't complete when it was read), a scaling or calibration error that only manifests under certain conditions, or a genuine sensor transient that the filtering didn't catch. Each of these leaves a different signature, so the logging needs to capture enough to distinguish them.

I'd also consider whether the value is wrong at the source or wrong after processing. If I can log the raw ADC or raw bus value and the processed value together, I can tell whether the corruption happens in acquisition or in the firmware's math. If the raw value is correct and the processed value is wrong, it's a firmware issue; if the raw value is already wrong, it's acquisition or the sensor itself.

Finally, I'd try to reproduce it under controlled conditions — fault injection, accelerated cycling, or running the suspect operation in a tight loop — so I can move from "it happened once in the field" to "I can make it happen on demand." A bug you can reproduce is a bug you can fix with confidence.

**Possible follow-ups:**
- If the raw value is correct but the processed value is wrong, what kinds of firmware bugs would you suspect first?
- How would you design the logging so it doesn't itself change the timing and mask the bug?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support and the team is split, the danger is that the investigation stalls into a debate rather than progressing. My job as the lead is to convert the disagreement into a set of discriminating tests — experiments whose outcomes would be different depending on which hypothesis is true.

I'd start by making both hypotheses explicit and falsifiable. For each one, I'd ask: what evidence would we expect to see if this were the cause, and what would we expect *not* to see? Often, writing this down reveals that one hypothesis makes a prediction the other doesn't, and that prediction is testable. If both hypotheses predict the same observations, then they may not actually be competing explanations — they might be two parts of the same failure, or one might be a symptom of the other.

Then I'd design the cheapest, fastest test that separates them. The goal isn't to prove one right; it's to find an observation that's inconsistent with one of them. I'd prioritize tests that can be run quickly and that don't require committing to a fix. If a test can only be run by building hardware or waiting for a field return, I'd look for a bench-level proxy first.

I'd also be deliberate about the team dynamics. When people are split, it's often because each side has invested in their hypothesis, and the disagreement becomes personal. I'd frame the discriminating tests as a shared way to settle it objectively, so nobody has to "lose" — the evidence decides. I'd make sure both hypotheses get a fair test, not just the one I favor, because if I only test the hypothesis I believe, I'll lose the team's trust and possibly miss the real cause.

If after discriminating tests the evidence still doesn't clearly favor one, I'd consider whether the failure could be caused by an interaction of both — some failures genuinely require two conditions to coincide. In that case, the investigation shifts from "which one" to "how do they combine," and I'd design tests that vary both factors together.

Throughout, I'd keep a written record of what was tested, what was observed, and what was ruled out, so the conclusion is traceable and defensible — which matters a great deal in a regulated medical device context.

**Possible follow-ups:**
- How would you handle it if the discriminating test is expensive or slow, and the schedule pressure is high?
- What would you do if a team member continues to advocate for their hypothesis even after a test contradicts it?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, system fails — is a strong signal that the bug lives in an interaction, not in any single component, and the engineer's approach of testing parts in isolation is structurally unable to find it. So the most useful thing I can do is not to take over, but to help them reframe the problem and give them a method that can actually reach the failure.

I'd start by asking them to walk me through what they've observed, not what they've concluded. I want to understand the failure itself: how often does it happen, under what conditions, and how do they know when it's happened? A common trap with intermittent failures is that the engineer hasn't actually characterized the failure rate or the conditions — they've been chasing it reactively. If we don't know what makes it more or less likely, we can't design a test that reproduces it.

Then I'd help them shift from "test the parts" to "test the system while varying one thing at a time." The failure is intermittent, so the goal is to find a condition that changes its probability — temperature, timing, load, a particular sequence of operations, a specific unit. Once you can make it happen more often, you can start to isolate it. I'd suggest they instrument the system to capture the state at the moment of failure, rather than trying to catch it by watching.

I'd also gently point out the sunk-cost trap: several days of the same approach without progress means the approach, not the effort, is the problem. That's not a criticism of them — it's a normal thing that happens to everyone — but naming it helps them let go of the method that isn't working.

On the morale and schedule side, I'd be honest that the schedule is tight but that flailing faster won't help; a focused method will. I'd offer to pair with them for a session, not to solve it for them but to model the systematic approach, and I'd check in regularly so they don't feel alone with it. If the pressure is genuinely severe, I'd consider whether the investigation needs more resources or a scope decision, but I wouldn't let schedule pressure push us into a fix without a root cause — in a medical device context, that's how you end up with a recurrence.

**Possible follow-ups:**
- How would you help them characterize an intermittent failure's rate and conditions if it only happens in the field and not on the bench?
- At what point would you decide to reassign the investigation rather than continue coaching, and how would you do that without demoralizing them?