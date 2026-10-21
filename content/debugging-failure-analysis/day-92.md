# debugging-failure-analysis — Day 92

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only after two changes happen together — enclosure assembly and final mounting — so I'd treat those as the variables to isolate rather than assuming the analog chain itself is at fault. First, I'd reproduce the offset in a controlled way: measure with the board open on the bench (baseline), then with the enclosure fitted but the unit still on the bench, then with the unit in its final mounting position. That three-point sequence tells me whether the enclosure alone causes it, the mounting position alone causes it, or only the combination does.

If the offset appears with the enclosure fitted, I'd suspect mechanical effects on the analog front-end: flexing of the PCB changing a solder joint or a connector contact resistance, a cable or harness routed differently and coupling noise, or a shield/grounding path that changes when the enclosure is closed. A consistent DC offset often points to a changed ground reference or a changed input bias path rather than random noise. I'd measure the offset at the ADC input with a meter and compare it to the firmware-reported value to confirm the offset is genuinely in the analog domain and not introduced downstream.

If it only appears in the final mounting position, I'd look at what the installation changes: grounding through a mounting bracket, proximity to a metal surface, cable dress, or a chassis connection that creates a ground loop or shifts the reference. I'd also check whether the offset is stable or drifts, and whether it correlates with temperature after the unit has been running in its installed position.

Throughout, I'd keep one change at a time and log the offset value at each configuration so the evidence points to a single cause rather than a guess. Once isolated, the corrective action depends on the mechanism — a grounding/return path fix, a mechanical strain relief change, or a shielding change — and I'd verify it by repeating the same three-point sequence.

**Possible follow-ups:** How would you distinguish a ground-reference shift from a genuine sensor offset in this scenario? What would you do if the offset only appeared in the customer's installation and you couldn't reproduce the mounting position in the lab?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** Ripple that appears only under a switching load points at the interaction between the load's transient current demand and the power delivery network, not necessarily at the regulator's steady-state performance. I'd start by characterizing the ripple properly: probe at the load's decoupling capacitors with a short ground lead (a long ground clip will pick up its own loop and inflate the reading), and capture both the ripple waveform and the load current simultaneously so I can correlate ripple events with switching edges.

Then I'd separate the possible mechanisms. One is insufficient decoupling or high ESR/ESL in the bulk and local capacitors, so the transient current isn't supplied locally and the rail sags until the regulator loop responds. Another is regulator loop response — the control loop may be marginally stable or too slow for the load step, producing ringing or overshoot. A third is layout: a high-diode-loop area, a shared return path, or a via/plane discontinuity adding inductance between the regulator and the load. A fourth is ground bounce — the "ripple" may actually be a ground shift measured because the probe reference moves with the switching current.

I'd test these in order of ease: add temporary bulk capacitance close to the load and see if the ripple drops (points to decoupling); check the regulator's loop compensation and load-transient response with a controlled step (points to loop); inspect the return path and switching loop layout (points to layout/ground). I'd also check whether the ripple frequency matches the subsystem's switching frequency or a harmonic, which helps confirm the coupling path.

The fix follows the mechanism — better local decoupling, revised loop compensation, improved return path, or added filtering — and I'd verify by re-measuring ripple at the same probe point under the same load condition.

**Possible follow-ups:** How would you tell whether the ripple is differential-mode noise on the rail versus common-mode ground bounce? What measurement mistakes most often make ripple look worse than it is?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hard part here is that nothing in the system flags the error, so the investigation has to start from the data itself. I'd first characterize the wrong values: are they single-bit errors, small offsets, stuck values, or values from a neighboring channel or a previous sample? That pattern often reveals the mechanism — a single-bit flip suggests a memory or bus integrity issue, a stuck value suggests a stale read or a communication timeout returning the last good value, and a plausible-but-wrong value from another channel suggests an indexing or multiplexing bug.

Next I'd establish where in the chain the corruption enters: at the sensor, at the ADC, in the firmware's processing, in the storage, or in the transmission. I'd add instrumentation — raw ADC captures, timestamps, and a checksum or sequence counter on the data path — so I can compare the value at each stage. If the raw ADC value is correct but the reported value is wrong, the problem is downstream in firmware or storage; if the raw value is already wrong, it's analog or timing.

I'd also look at correlation: does the error cluster around specific events such as a communication retry, a mode change, a low-power transition, or a temperature extreme? Since it's only caught offline, I'd build a lightweight on-device validation — range checks, rate-of-change checks, cross-channel consistency — to catch and log the event in real time so I get the surrounding context rather than just the bad value.

Finally, I'd try to reproduce it under accelerated conditions: fault injection on the bus, forced retries, and stress on the timing. The corrective action depends on the mechanism, but the discipline is the same — find where the value first goes wrong, then fix that stage and verify with the same instrumentation.

**Possible follow-ups:** How would you design the on-device validation so it catches the error without generating false positives? If the corruption is in stored data, how would you distinguish a write-path problem from a read-path problem?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the risk is that the team argues about which is "right" instead of designing a test that separates them. My first move is to reframe the discussion: for each hypothesis, what evidence would we expect to see if it were true, and what would we expect if it were false? That turns the disagreement into a set of discriminating predictions.

Then I'd look for the cheapest, fastest test that gives a different result under the two hypotheses — ideally a single experiment that can confirm one and rule out the other. If no single test separates them, I'd run the two most informative tests in parallel rather than sequentially, so we're not spending weeks on one path while the other goes unexamined. I'd assign clear owners and a deadline for each, and agree in advance what result would change our view.

I'd also make sure the split isn't personal. Often the team is attached to a hypothesis because someone proposed it, so I'd keep the framing on the evidence and explicitly credit good reasoning on both sides. I'd document the decision criteria so that when the data comes in, the conclusion follows from the evidence rather than from who argued hardest.

If the tests are inconclusive, I'd consider whether both mechanisms could be contributing — sometimes the answer is "both, under different conditions" — and design a test matrix that varies the conditions each hypothesis depends on. The goal is to converge on a defensible root cause with traceable evidence, not to win the argument.

**Possible follow-ups:** What would you do if the discriminating test is expensive or slow and the schedule is tight? How do you keep the team engaged on the hypothesis that ultimately gets ruled out?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, the system fails — usually means the failure depends on an interaction the isolated tests don't reproduce, so the first thing I'd do is help the engineer step back from component-level testing and reframe around the system conditions. I'd ask what's different between the isolated test and the real system: power source, grounding, cabling, load, timing, temperature, and what else is running at the same time. The failure is telling us something about the interaction, and the isolated tests are, by design, removing exactly that.

I'd also check the debugging method itself. Are they reproducing the failure reliably, or chasing it intermittently? If it's intermittent, the priority is to increase the reproduction rate — stress the conditions, run longer, log more — so each experiment gives a clear signal. I'd help them set up instrumentation that captures the system state at the moment of failure rather than testing components one at a time and hoping.

On the human side, I'd be direct that several days without progress usually means the approach needs to change, not that the engineer is failing — and I'd say that explicitly so frustration doesn't turn into self-doubt. I'd pair with them for a session, model the "what's different at the system level" questioning, and give them a concrete next experiment with a clear success criterion. I'd also protect the schedule by making sure the investigation has a defined checkpoint where we reassess, so the pressure doesn't push us into a premature fix.

The balance is to be supportive without lowering the bar: acknowledge the effort, redirect the method, and keep ownership with the engineer so they build the skill rather than just receiving the answer.

**Possible follow-ups:** How would you decide when to step in versus let the engineer keep working? What would you do if the engineer resisted changing their approach?
