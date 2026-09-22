# debugging-failure-analysis — Day 63

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only when two variables change together — the enclosure is closed and the unit is mounted. That points away from the analog signal chain itself (which is proven good on the bench) and toward something the mechanical configuration changes: grounding, shielding, thermal environment, or mechanical stress on the PCB.

I'd start by separating those variables. First, reproduce the offset with the enclosure closed but the unit sitting on the bench, then with the enclosure open but the unit in its final mounting position. If the offset follows the enclosure, it's likely an electrical or thermal effect from the closed volume — reduced airflow raising local temperature, or the enclosure changing the ground/shield topology. If it follows the mounting position, it's more likely mechanical: board flex altering a solder joint or a strain-sensitive component, or a changed ground return path through the mounting hardware.

For the electrical hypothesis, I'd measure the offset at the ADC input with the enclosure closed to confirm it's present at the analog node and not introduced downstream. Then I'd check whether the offset correlates with temperature by logging the board temperature in both states. A consistent offset that appears only in the closed enclosure often tracks a temperature rise that shifts a reference or a bridge offset.

For the mechanical hypothesis, I'd look at whether the mounting screws or clips apply force near the analog front-end, and whether the offset changes if I loosen or re-torque them. Board flex can change the value of a strain-sensitive element or open a marginal joint.

The discipline here is to change one variable at a time and confirm which one actually carries the offset, rather than assuming it's thermal or mechanical because that's the common story.

**Possible follow-ups:**
- If the offset tracks temperature, how would you determine whether it's the sensor, the reference, or the amplifier that's drifting?
- How would you design a test that distinguishes board flex from a grounding change caused by the enclosure?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a load-transient and power-integrity problem, so I'd treat the switching subsystem as a stimulus and the rail as the system under test. The ripple appearing only under load tells me the regulator's loop or the decoupling network isn't handling the transient, or the transient is coupling in through a shared impedance.

First I'd characterize the disturbance properly. I'd measure at the point of load, not at the regulator output, using a short-ground-spring probe tip rather than a long ground lead — a long lead picks up loop inductance and shows ringing that isn't really there. I'd capture the transient with enough bandwidth to see the edge, and note the frequency and amplitude of the ripple and whether it's synchronized with the switching event.

Then I'd separate two mechanisms. If the ripple is at the regulator's switching frequency or its loop bandwidth, it's likely a control-loop or compensation issue, or insufficient output capacitance for the transient. If it's at the load's switching frequency, it's more likely conducted or radiated coupling — the load current pulse developing a voltage across a shared trace or ground impedance.

To distinguish, I'd add bulk capacitance right at the load and see if the ripple drops. If it does, it's a decoupling/transient-response problem. If it doesn't, I'd look at the return path — whether the load's ground current shares a path with the sensitive rail's reference, which is a classic ground-bounce coupling. I'd also check whether the ripple appears on other rails, which would suggest a common impedance rather than a local regulator issue.

The measurement discipline matters as much as the diagnosis: probing at the right node with the right tip, and confirming the ripple is real before chasing it.

**Possible follow-ups:**
- How would you tell the difference between ripple caused by the regulator's loop response and ripple coupled in from the load's return current?
- What would you check in the layout if adding capacitance at the load didn't help?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hard part here is that nothing in the system flags the error, so the failure is invisible at runtime. That means the investigation has to start by making the invisible visible — building a way to detect and capture the bad value when it happens, rather than trying to reason about it after the fact.

First I'd characterize the error from the offline data. Is the wrong value a single-bit flip, a stale value from a previous read, a value from the wrong channel, or a plausible-but-shifted reading? Each pattern points somewhere different. A single-bit flip suggests a memory or bus integrity issue. A stale value suggests a timing or handshake problem where the firmware read before the conversion completed. A wrong-channel value suggests an indexing or multiplexer control bug. A shifted reading suggests a calibration or scaling issue.

Then I'd instrument the system to catch it live. I'd add a checksum or redundancy to the sensor read — read twice and compare, or add a range/rate-of-change sanity check — and log when the check fails, along with the raw bus traffic and the firmware state at that moment. The goal is to convert an offline mystery into a captured event with context.

Once I can reproduce it with instrumentation, I'd work the boundary: is the wrong value present on the bus (a hardware/interface problem) or only in the firmware's variable (a software problem)? Reading the raw bus with a logic analyzer while the firmware logs its parsed value answers that directly.

The broader point is that "plausible but wrong" data is the most dangerous kind in a medical device, so the corrective action usually includes adding runtime plausibility checks, not just fixing the root cause.

**Possible follow-ups:**
- How would you design a plausibility check that catches bad data without generating false alarms on legitimate fast changes?
- If the bad value is present on the bus, how would you narrow it down to the sensor, the interface, or the controller?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support and the team is split, the risk is that people start defending positions instead of testing them. My job as the lead is to convert the disagreement into an experiment that can actually discriminate between the two.

First I'd make both hypotheses explicit and falsifiable. For each one, I'd ask: what evidence would we expect to see if this were true, and what would we expect to see if it were false? Often, writing that down reveals that the two hypotheses predict different things about a specific measurement — and that measurement becomes the deciding test.

Then I'd design the cheapest, fastest test that separates them. Ideally it's a single experiment where the two hypotheses predict opposite outcomes. If no single test separates them, I'd sequence tests by cost and information value, starting with the one that eliminates the most uncertainty.

I'd also be honest about what "partial evidence" means. Sometimes both hypotheses are partly right — there's a primary cause and a contributing factor — and the investigation needs to establish the causal chain rather than pick a winner. I'd keep the team focused on the evidence rather than on whose hypothesis wins, and I'd assign the test to whoever is most skeptical of the hypothesis being tested, so the result is credible to both sides.

If the schedule forces a decision before the evidence is conclusive, I'd document the uncertainty, implement the fix that addresses the most likely cause while keeping the investigation open, and define what evidence would confirm or overturn the decision.

**Possible follow-ups:**
- How would you keep the team productive if the discriminating test takes weeks to run?
- What would you do if the test result supported neither hypothesis cleanly?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation but the system fails — usually means the bug lives in the interaction between components, not inside any one of them. Testing components in isolation can't find an interaction bug, so the engineer isn't failing; the method just can't reach the problem. I'd frame it that way first, because the frustration often comes from feeling stuck when the approach itself is the limitation.

I'd sit down with them and ask them to walk me through what they've observed, not what they've concluded. Often the useful clues are in the observations they've dismissed. Then I'd help them reframe the problem around the system boundary: what's different between the isolated test and the full system? Power source, grounding, timing, load, other active subsystems, cable lengths, temperature. The failure lives in one of those differences.

From there I'd help them build a test that exercises the system as a whole while controlling one variable at a time — for example, reproducing the failure with the full system but swapping in a bench supply, or disabling one subsystem at a time to see if the failure disappears. The goal is to shrink the search space systematically rather than test more components.

I'd also make sure they have the right instruments for an intermittent system-level bug — a logic analyzer or scope with long capture and trigger-on-anomaly, so they can catch the event rather than wait for it. And I'd check in regularly so they're not isolated with it, while letting them own the investigation so they build the skill.

**Possible follow-ups:**
- How would you help them decide when to escalate versus keep digging?
- What would you do if the failure only reproduces once every few days, making iteration slow?