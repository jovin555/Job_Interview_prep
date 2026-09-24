# debugging-failure-analysis — Day 65

## Q1: How would you approach debugging a device that only fails when it is powered from its internal battery, but passes every test when powered from a bench supply at the same nominal voltage?

**Answer:** The first instinct is to treat "same voltage" as "same condition," which is almost never true. A bench supply is a low-impedance source with effectively unlimited current headroom and no protection circuitry in the path; a battery has finite source impedance, a protection FET, a fuel gauge shunt, and a connector. So the variable I'd isolate is source impedance and transient response, not DC voltage.

Concretely, I'd start by capturing the rail at the point of load under both sources while exercising the failing operation, using a scope probe with a short ground spring rather than a long clip lead — otherwise the probe loop itself manufactures the ringing I'm trying to find. I'd look specifically at load-transient response: does the battery path sag further or recover more slowly during a current step? Then I'd measure the voltage drop across each element unique to the battery path — connector, protection FET, shunt — under the actual peak current, since a few tens of milliohms that are irrelevant at 10 mA become a real droop at 500 mA.

If the droop is real, the question becomes whether it's a source problem or a decoupling problem. I'd add bulk capacitance at the load temporarily to see whether the failure threshold moves; if it does, the design is marginal on transient energy, not on average current. I'd also check whether the battery path has different grounding — a bench supply often shares a ground with the scope and the host PC, which can mask or create ground loops and change the behavior of anything referenced to earth.

The discipline here is one change at a time and a written record of what each change did. It's very easy to "fix" this by adding capacitance and never learn whether the real issue was inrush, a marginal LDO, or a connector with high contact resistance that will get worse in the field.

**Possible follow-ups:**
- How would you distinguish a source-impedance problem from a decoupling problem if adding capacitance appears to fix it?
- What would change in your approach if the failure only appeared after the battery had partially discharged?

## Q2: You're investigating a field return where the device works correctly on arrival but fails after a few hours of operation in the customer's environment. How would you structure the investigation so that you're not just chasing a unit that currently passes?

**Answer:** A unit that passes on arrival is the hardest kind of return, because the evidence you most want — the failure state — has already been erased by the act of shipping and handling. The first thing I'd do is resist the urge to "test it until it fails" without a plan, because that generates hours of data with no hypothesis attached.

I'd structure it in three layers. First, preserve and mine whatever the device already recorded: error logs, fault counters, watchdog resets, timestamps, and any non-volatile state that survives a power cycle. Even a device that "works" often carries a history of near-misses — a counter that incremented, a retry that succeeded on the second attempt. That history is often more informative than the current pass.

Second, I'd try to reproduce the *conditions*, not just the symptom. That means asking what's different about the customer's environment: ambient temperature, duty cycle, how the device is mounted, what else is nearby, how it's powered, how long it runs. A failure that needs hours of operation points at something cumulative — thermal drift, a slow leak in a timing margin, a counter wrapping, a memory or wear mechanism, or a connector that degrades with thermal cycling.

Third, I'd instrument rather than guess. If I can't reproduce it, I'd add logging or telemetry to the next units in the field so the failure captures its own context. That's a slower path but it's the honest one when the failure is rare and environment-dependent.

Throughout, I'd keep a written hypothesis list with the evidence for and against each, and I'd be explicit about which hypotheses I've actually ruled out versus merely deprioritized. The failure mode of this kind of investigation is declaring victory when the unit happens to pass a test, which proves nothing.

**Possible follow-ups:**
- What would you log if you had to add instrumentation to field units, and how would you avoid the logging itself changing the behavior?
- How would you decide when to stop trying to reproduce and move to a design-margin fix instead?

## Q3: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only when the mechanical and electrical environments change together, so I'd treat this as a coupling problem rather than a component problem. The front-end itself hasn't changed; what changed is what's near it, how it's grounded, and how it's stressed.

I'd work through the likely coupling mechanisms in order of how cheap they are to test. First, mechanical stress: mounting torque and enclosure clamping can flex the PCB and shift a strain-sensitive component — a ceramic capacitor, a resistor, or the sensor itself — producing a small, repeatable offset. I'd test this by reproducing the mounting conditions on the bench with the same torque and standoffs, and by watching whether the offset tracks torque.

Second, grounding and reference changes: once installed, the device may be referenced to a different ground than the bench setup, or a chassis connection may now exist that didn't before. That can shift the analog reference or introduce a ground potential difference the front-end sees as offset. I'd measure the reference and the analog ground at the point of use, not at the supply.

Third, thermal: an enclosed unit runs warmer, and a small thermal EMF at a dissimilar-metal junction or a temperature coefficient mismatch in the front-end can present as a stable offset once the unit reaches equilibrium. I'd let it soak to thermal steady state before measuring, because a bench measurement taken cold will miss this entirely.

The important discipline is to reproduce the *installed* condition faithfully — same enclosure, same mounting, same grounding, same soak time — before drawing any conclusion. A test harness that doesn't replicate those conditions will keep telling you the device is fine.

**Possible follow-ups:**
- How would you separate a mechanical-stress offset from a thermal offset if both are present?
- What would you do if the offset is within the sensor's datasheet tolerance but still causes a system-level fault?

## Q4: How would you debug a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle?

**Answer:** This is a classic load-induced power integrity problem, and the first thing I'd do is stop measuring the rail in the wrong place. Ripple measured at the regulator output tells you what the regulator is doing; ripple measured at the load tells you what the load actually sees. The difference between those two points is the impedance of the path — trace inductance, via inductance, and the effectiveness of the decoupling network — and that difference is usually where the answer is.

I'd probe at the load's supply pins with a short ground spring, and simultaneously probe the switching node and the load's current waveform if I can get a current probe or a sense resistor in. The goal is to correlate the ripple event with the switching edge that causes it. If the ripple is synchronized with the load's switching, it's a transient-response problem; if it's synchronized with the regulator's own switching, it's a control-loop or compensation issue.

Then I'd separate the two main contributors. One is the regulator's transient response: when the load steps, the control loop takes time to react, and the output dips or spikes until it does. That's addressed with more bulk capacitance, better loop compensation, or a faster regulator. The other is the impedance of the decoupling network at the frequency of the transient: even a fast regulator can't help if the high-frequency current has to travel through a long inductive path to reach a capacitor. That's addressed by placing capacitance closer to the load and reducing loop area.

I'd also check for a shared-impedance coupling path — if the high-current subsystem and the sensitive rail share a ground return or a supply trace, the switching current develops a voltage across that shared impedance and injects it into the other rail. That's a layout problem, and it's worth confirming before adding components that only mask it.

**Possible follow-ups:**
- How would you tell whether the ripple is coming from the regulator's transient response or from the decoupling network's impedance?
- What would you check in the layout if the ripple persists after adding capacitance at the load?

## Q5: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the temptation is to argue about which is more likely. I'd try to convert the argument into an experiment instead. The productive question isn't "which do you believe?" but "what observation would distinguish them?" If I can find a test where the two hypotheses predict different outcomes, the disagreement resolves itself with data rather than with seniority.

So my first move is to write down, for each hypothesis, what it predicts and what it rules out. Often that exercise reveals that the two hypotheses aren't actually mutually exclusive — they may be two links in the same causal chain, or one may be a contributing factor that only matters when the other is present. Reframing them that way frequently dissolves the split.

If they are genuinely competing, I'd design the cheapest, fastest discriminating test and run it, accepting that it may take a few iterations. I'd also be honest about the cost of being wrong in each direction: if one hypothesis implies a design change and the other implies a process change, the consequences differ, and that should inform how much evidence I demand before committing.

On the team dynamics: I'd make it clear that the goal is the correct root cause, not a winning hypothesis, and that changing one's mind in light of evidence is the expected behavior, not a loss. I'd keep the investigation log visible so everyone can see what's been ruled out and why, which reduces the sense that we're going in circles. And if the schedule forces a decision before the evidence is conclusive, I'd say so explicitly and frame any interim fix as a mitigation with a known residual risk, not as a confirmed root cause — because calling an unconfirmed fix "the root cause" is how the same failure comes back six months later.

**Possible follow-ups:**
- How would you handle it if the discriminating test is expensive or slow, and the schedule won't allow it?
- What would you do if the evidence eventually points to a design decision made by someone still on the team?