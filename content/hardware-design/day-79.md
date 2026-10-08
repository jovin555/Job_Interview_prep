# hardware-design — Day 79

## Q1: How would you approach selecting a shunt resistor value and current-sense amplifier topology for measuring a bidirectional motor current of up to 1A, where the measurement must be accurate to ±2% over temperature and the shunt must not dissipate excessive power?
**Answer:** Start by budgeting the error sources, because the shunt value is really a trade between signal-to-noise and self-heating. A larger shunt gives more signal for the amplifier to work with, which helps offset and noise performance, but dissipation scales with I²R, so at 1A a 100 mΩ shunt burns 100 mW and a 10 mΩ shunt burns only 10 mW. The right value is the largest one that keeps dissipation and self-heating within budget, since self-heating causes a resistance drift that directly eats into the ±2% accuracy target — a shunt with a low temperature coefficient (on the order of tens of ppm/°C) matters as much as its nominal tolerance.

For topology, a bidirectional measurement rules out a simple low-side shunt if the load's ground reference must stay clean, so I'd weigh high-side versus low-side sensing. Low-side sensing is simpler and cheaper because the common-mode voltage is near ground, but it lifts the motor's return above system ground, which can cause ground-shift issues and makes fault detection harder. High-side sensing keeps the ground intact but requires an amplifier with a common-mode input range that includes the supply rail, and often a matched resistor network for good CMRR.

For the amplifier itself, I'd choose between a dedicated current-sense amplifier and a discrete difference amplifier. A dedicated current-sense amp is usually the better choice here: it's trimmed for gain accuracy and CMRR, has a defined common-mode range, and often includes a reference pin so I can bias the output mid-supply to represent zero current and swing both directions. I'd check the gain error, offset voltage, and CMRR over temperature, since those dominate the ±2% budget at low currents. I'd also verify the amplifier's bandwidth is adequate for the motor's current dynamics and that its input bias current doesn't create an error across the shunt.

Finally, I'd lay out the shunt with a Kelvin (four-terminal) connection so the sense traces tap the resistor body directly and don't pick up solder-joint or trace resistance, and I'd keep the sense pair tightly coupled and away from the switching node to avoid magnetic pickup.

**Possible follow-ups:**
- How would you verify the ±2% accuracy claim on the bench, and what would you use as your current reference?
- If the motor's PWM switching creates large common-mode transients, how would that change your amplifier choice?

## Q2: How would you approach choosing between a comparator and an op-amp for a threshold-detection function in a hardware protection circuit, and what would drive the decision?
**Answer:** The core distinction is that a comparator is designed to be operated open-loop and to saturate cleanly at its output rails, while an op-amp is designed for closed-loop linear operation and is only incidentally usable as a comparator. For a protection function, the decision usually comes down to speed, output interface, and hysteresis behavior.

A dedicated comparator is generally the right choice when the threshold must be crossed quickly and the output must drive a logic input or a latch. Comparators specify propagation delay and are internally compensated for fast saturation, whereas an op-amp used open-loop will slew at its slew rate and may take much longer to reach a valid logic level, and its output may not swing cleanly to the logic rails. Comparators also typically offer built-in or easily added hysteresis, which is essential for a protection threshold: without hysteresis, a slow-moving or noisy input near the threshold will cause the output to chatter, which can repeatedly trigger and clear a fault.

An op-amp can be acceptable when the threshold is not timing-critical, when the required hysteresis is easy to add externally, and when the same part is already on the bill of materials — reducing part count has real value. But I'd be cautious about using an op-amp for anything where the response time is specified, because its behavior near saturation is not characterized the way a comparator's is.

For a protection circuit specifically, I'd also think about the failure mode. A comparator with a defined output state under all input conditions is easier to reason about than an op-amp whose output may sit in an indeterminate region. I'd want the threshold to be set by a stable reference, not by the supply rail, and I'd add hysteresis deliberately rather than relying on the part's internal behavior. If the comparator drives a latch, I'd also consider whether the comparator's output can be latched or whether a separate latch stage is needed.

**Possible follow-ups:**
- How would you size the hysteresis for a protection threshold, and what would you trade off?
- What comparator parameters would you check first for a microsecond-scale overcurrent trip?

## Q3: How would you approach designing a hardware-based power-on self-test for a medical device's analog signal chain, and what would you want it to verify independently of firmware?
**Answer:** The purpose of a hardware-based POST is to verify that the analog signal chain is actually functional before the firmware trusts its readings, and to do so in a way that doesn't depend on the firmware or the ADC being correct. If the firmware is the only thing checking the signal chain, a fault in the ADC or in the firmware itself can masquerade as a valid reading.

I'd structure the POST around a few independent checks. First, verify the supply rails: a set of rail monitors or a window comparator on each critical rail confirms the analog section is powered within tolerance before anything else runs. Second, verify the reference: a reference monitor or a comparison against a known divider confirms the ADC's reference is present and at the expected value, since a drifted or absent reference silently corrupts every reading. Third, inject a known stimulus into the signal chain — for example, a precision divider or a switched reference — and confirm the chain responds as expected. This is the part that actually exercises the amplifier, filter, and ADC path rather than just checking that power is present.

The key design principle is independence: the checks should not rely on the ADC or the firmware to be correct. A rail monitor is a comparator, not an ADC reading. A reference check can be a comparator against a divided-down rail. The stimulus injection can be a switch that the firmware toggles, but the verification of the response should be done by hardware — for example, a comparator that confirms the output moved into an expected window — so that a stuck ADC or a hung firmware is caught.

I'd also want the POST to be fail-safe: if a check fails, the device should go to a safe state rather than continue operating on suspect data. And I'd want the POST to be verifiable — the results should be observable, either through a status register or a dedicated indicator, so that manufacturing and service can confirm it ran.

**Possible follow-ups:**
- How would you avoid the POST itself becoming a source of false failures due to normal component tolerance?
- What would you do if the POST passes but the device later shows degraded readings in the field?

## Q4: How would you approach debugging a circuit where an op-amp's output is correct at DC but shows a slow, large-amplitude drift over minutes when the board is warmed by nearby power components?
**Answer:** A slow drift over minutes that correlates with board warming points to a thermal effect, and the first step is to confirm that correlation rather than assume it. I'd measure the op-amp's output while monitoring the local board temperature — either with a thermocouple or an IR camera — and see whether the drift tracks temperature. If it does, the question becomes which parameter is drifting: the op-amp's own offset voltage, the gain-setting resistors, the input source, or something in the feedback network.

I'd start by checking the op-amp's offset voltage temperature coefficient. A part with a poor offset drift spec will move its output as it warms, and if the gain is high, that movement is amplified. I'd also check the input bias current drift, because if the source impedance is significant, bias current drift across that impedance creates an input voltage error that looks like offset drift. This is a common cause that's easy to overlook.

Next I'd look at the passive components. Resistor temperature coefficients matter, especially if the gain network uses resistors with different tempcos — a mismatch creates a gain drift that shows up as output drift. If the feedback network includes a capacitor, its leakage or dielectric behavior can also drift with temperature. I'd also check whether the drift is actually coming from the input source rather than the op-amp: a sensor or reference that's warming up will produce the same symptom.

If the drift is thermal, the fix depends on the cause. A better-tempco op-amp or a chopper-stabilized part addresses offset drift. Matched-tempco resistors address gain drift. Physical separation or thermal relief from the heat-generating components addresses the root cause. I'd also consider whether the drift is acceptable for the application — if the device is calibrated at operating temperature, some drift may be tolerable, but for a precision medical measurement I'd want to understand and bound it rather than accept it.

**Possible follow-ups:**
- How would you distinguish between offset drift and bias-current-induced drift experimentally?
- If the drift is caused by a nearby regulator, what layout or thermal changes would you consider?

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review the reliability engineer argues that your chosen connector for the patient cable is not rated for the number of mating cycles the device will see over its lifetime, and proposes a more expensive, higher-cycle connector. You believe the current connector is adequate because the cable is intended to be connected once and left in place, but the reliability engineer is concerned about field replacement. How would you handle this disagreement?
**Answer:** I'd treat this as a question of use-case definition rather than a straight disagreement about the part, because the two positions are really about different assumptions regarding how the device is used. The reliability engineer is assuming the cable may be disconnected and reconnected in the field; I'm assuming it's connected once and left in place. The right first step is to get that assumption out in the open and check it against the actual requirements and the intended clinical workflow, rather than defending my part choice.

I'd ask what the requirements and risk analysis actually say about cable replacement. If the device is intended to be used with a single cable for its service life, then the mating-cycle requirement is low and the reliability engineer's concern may be based on a scenario that isn't in the intended use. If the cable is expected to be replaced — for example, if it's a consumable or if field service replaces it — then the reliability engineer is right and the higher-cycle connector is justified. This is exactly the kind of thing that should be traceable to a requirement, so I'd want to resolve it against the requirements rather than by opinion.

If the requirements are ambiguous, I'd propose a path that resolves the ambiguity: document the intended use and the expected number of mating cycles, and if there's genuine uncertainty, either specify the higher-cycle connector or add a design control that limits field replacement. I'd also consider whether there's a middle option — a connector with a higher cycle rating that isn't the most expensive one — and whether the cost difference is material relative to the risk.

Throughout, I'd keep the tone collaborative. The reliability engineer is raising a legitimate concern, and the goal is a defensible design decision, not winning the argument. If we can't agree, I'd escalate to the design owner or the risk management process with the data, because a connector reliability question is exactly the kind of thing that should be resolved through the risk file, not through seniority.

**Possible follow-ups:**
- How would you document the resolution so it's defensible in a design history file?
- If the higher-cycle connector is chosen, how would you verify it meets the requirement?