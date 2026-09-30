# debugging-failure-analysis — Day 71

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only when two variables change together: the enclosure is closed and the unit is mounted in its final position. That points away from a component-level fault and toward something mechanical, thermal, or grounding-related that the bench setup doesn't reproduce. I'd start by deliberately separating those two variables rather than treating "assembled and mounted" as one condition.

First, I'd reproduce the offset with the board in the enclosure but sitting on the bench, then with the board out of the enclosure but physically mounted in the final orientation. If the offset follows the enclosure, I'd look at mechanical stress on the board — flexure from mounting screws, standoffs, or connector mating forces that slightly strain a solder joint, a via, or a high-impedance node. If it follows the mounting position, I'd look at grounding and reference-plane behavior: how the chassis or mounting surface couples to the analog ground, whether a mounting point is now acting as an unintended ground path, or whether the reference for the front-end has shifted.

For the analog side specifically, a small consistent offset usually means a DC-level shift rather than noise. I'd measure the front-end's reference voltage, the input common-mode, and the amplifier's offset at the actual pins with the unit assembled — not at the test harness — using a high-impedance probe so I'm not loading the node. I'd also check whether the enclosure changes the thermal environment enough to shift a bias point, and whether any cable routing inside the enclosure is now running near a sensitive node and injecting a small DC or low-frequency component.

Throughout, I'd keep it to one change at a time: swap enclosure on/off, change mounting torque, add or remove a grounding strap, and log the offset after each. The goal is to convert "assembled vs bench" into a single identifiable mechanism — mechanical stress, grounding, thermal, or coupling — and then verify it by making the offset appear and disappear with that one variable.

**Possible follow-ups:**
- If the offset tracks mounting screw torque, how would you confirm it's board flexure and not a grounding change at the mounting point?
- How would you design a test that distinguishes a thermal offset from a mechanical one when both correlate with the enclosure being closed?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a load-transient and power-distribution problem, so I'd approach it as a question of where the transient current is actually flowing and which part of the power network is failing to supply it cleanly. The fact that it only appears under switching tells me the steady-state regulation is probably fine and the issue is dynamic.

I'd start by characterizing the ripple properly rather than just observing it. That means measuring at the load, not at the regulator output — the two can look very different because of trace and via impedance between them. I'd use a short-ground-tip probe or a coaxial pigtail at the decoupling capacitors right at the switching load, because a long ground lead will pick up loop inductance and show ringing that isn't really there. I'd capture the ripple synchronized to the switching event so I can see whether it's a transient droop, a resonant ring, or high-frequency noise.

Next I'd separate the possible mechanisms. If it's a transient droop, the bulk and local decoupling may be insufficient for the di/dt, or the regulator's loop bandwidth is too slow to respond — I'd look at the load transient response and the phase margin of the regulator. If it's ringing, I'd suspect parasitic inductance in the current path: the loop from the load back to the regulator, the capacitor ESL, or a long via. If it's high-frequency content, I'd check whether the switching return current is sharing a path with the analog or sensitive supply and coupling through a common impedance.

I'd then test hypotheses one at a time: add local bulk capacitance at the load and see if the droop shrinks; shorten or widen the current return path; add a small series element or ferrite to see if the ripple is conducted or radiated; and probe the ground at multiple points to check for ground bounce between the regulator and the load. The measurement discipline matters as much as the fix — a lot of "excessive ripple" turns out to be a probing artifact, so I'd confirm the ripple is real at the load pins before changing the design.

**Possible follow-ups:**
- How would you tell whether the ripple is coming from the regulator's control loop versus the decoupling network?
- If adding capacitance reduces the ripple but doesn't eliminate it, what would that tell you about the remaining mechanism?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** This is one of the harder classes of bug because every automated check passes — the value is in range, the self-test is satisfied, and the system has no reason to flag it. The failure is only visible against ground truth, so the first job is to create a way to detect it in real time rather than relying on offline review.

I'd start by defining what "wrong" means precisely. Is the value offset by a fixed amount, scaled, stale (a previous sample repeated), or a plausible value from a different channel or a different time? That distinction narrows the mechanism enormously. A stale value points to a timing or buffer-management issue; a scaled or offset value points to a conversion or calibration path; a value from another channel points to an indexing or multiplexer bug.

Then I'd build a reference. If I can feed a known signal and log both the raw ADC output and the processed value, I can see whether the corruption happens at acquisition, in the conversion math, or in the storage/transmission path. I'd add instrumentation that captures the raw sample alongside the reported value and a timestamp, so when a bad value appears I have the surrounding context — what else was happening, whether an interrupt fired, whether a DMA transfer overlapped.

Because the error is intermittent and plausible, I'd suspect a race or a shared-resource conflict: a buffer being read while it's being written, a conversion using a calibration constant that's momentarily stale, or a sample being tagged with the wrong timestamp. I'd look at the firmware-hardware boundary — DMA completion versus CPU read, interrupt priority, and whether the sensor interface and the processing share any state without proper synchronization. I'd also check whether the error correlates with a specific operating mode, temperature, or timing pattern.

Finally, I'd make the failure reproducible in a controlled way — fault injection, a stress pattern, or a loop that runs the acquisition path at high rate — so I can confirm a fix rather than just observe that the symptom stopped. The corrective action needs to be tied to a mechanism, not to "it hasn't happened since."

**Possible follow-ups:**
- How would you distinguish a stale-value bug from a data-corruption bug when both produce a plausible but wrong reading?
- What logging would you add so that a future occurrence is caught in the field rather than in offline review?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the risk is that the team splits into camps and each side accumulates evidence for its own view while discounting the other. My job as lead is to convert the disagreement into a testable question and let the evidence decide, rather than letting seniority or persistence decide.

First I'd make both hypotheses explicit and falsifiable. For each one, I'd ask: what observation would we expect if this were true, and what would we expect if it were false? Often the two hypotheses predict different behavior under a specific condition, and that condition becomes the decisive experiment. If they predict the same thing under every condition we can test, then the distinction may not matter for the fix — and I'd say so.

Then I'd design the cheapest, fastest test that discriminates between them, and I'd assign it clearly with a defined pass/fail criterion agreed in advance. Agreeing on the criterion before running the test is important — it prevents the result from being reinterpreted after the fact to fit a preferred hypothesis.

In parallel, I'd keep the investigation honest about what's actually established versus assumed. I'd maintain a shared record of confirmed facts, open questions, and the evidence for each hypothesis, so the team is working from the same picture. If the decisive test is expensive or slow, I'd look for a proxy or a simulation that gives a strong signal first.

If after the discriminating test the evidence still doesn't cleanly separate the two, I'd consider whether both contribute — sometimes there are two mechanisms and the failure needs both. In that case the corrective action has to address both, and I'd be explicit that we're mitigating two contributing causes rather than claiming a single root cause. Throughout, I'd keep the tone collaborative: the goal is to find the mechanism, not to win the argument, and I'd credit whoever's hypothesis survives the test.

**Possible follow-ups:**
- How would you handle it if the decisive test is inconclusive because the failure is too rare to reproduce on demand?
- What would you do if the two hypotheses imply very different corrective actions and you can't afford to implement both?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, the system fails — usually means the bug lives in an interaction that the isolation testing deliberately removes. The junior engineer isn't wrong to test components, but they've been testing in a way that can't reproduce the failure, so the effort isn't converging. My first move is to reframe the problem rather than add more effort to the same approach.

I'd sit down with them and ask what they've established, not just what they've tried. Specifically: can they reproduce the failure on demand, and if not, what's the closest they've gotten? An intermittent failure that can't be reproduced is nearly impossible to debug, so the highest-value next step is usually to make it reproducible — run the system in a loop, stress it, change temperature, add logging, or run it for longer — even if that means the reproduction is slow. A reliable reproduction changes everything.

Then I'd help them move from component-level testing to system-level hypothesis testing. Instead of "does this part work," the question becomes "what condition is present at the system level that isn't present in isolation?" That could be a shared power rail, a shared ground, a timing interaction, a bus contention, or a state that only exists when the full system runs. I'd encourage them to instrument the system — add logging, use a scope on the actual signals during the failure, capture the state at the moment it happens — rather than continuing to test parts on the bench.

I'd also watch for the frustration trap: when someone is stuck, they often repeat variations of the same test because it feels productive. I'd help them step back and list the assumptions they're making, then pick the one that's cheapest to challenge. And I'd be careful not to take over — the goal is to get them unstuck and keep them owning the investigation, with me as a sounding board.

On the schedule pressure, I'd be honest: a fix without a confirmed mechanism is a guess, and a guess on an intermittent failure often comes back. I'd rather spend a bounded amount of time making it reproducible than ship a speculative fix. If the schedule truly can't absorb that, I'd escalate the trade-off explicitly rather than quietly cutting the investigation short.

**Possible follow-ups:**
- How would you decide when to step in and debug it yourself versus continuing to coach the junior engineer?
- If the failure can't be reproduced on demand, what would you do to make progress without a reliable reproduction?