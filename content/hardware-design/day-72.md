# hardware-design — Day 72

## Q1: How would you approach selecting a shunt resistor value and current-sense amplifier topology for measuring a bidirectional motor current of up to 1A, where the measurement must be accurate to ±2% over temperature and the shunt must not dissipate excessive power?

**Answer:** The first decision is the sense topology. For bidirectional current, I'd choose between a high-side or low-side shunt. Low-side sensing is simpler and cheaper because the common-mode voltage is near ground, but it breaks the motor's ground return path, which can create ground-shift issues and complicate fault detection — often unacceptable in a medical motor drive where the load return must stay clean. High-side sensing keeps the ground intact but requires an amplifier with a common-mode input range that includes the supply rail, and the common-mode voltage swings with PWM, so I'd need an amplifier with high CMRR and good AC common-mode rejection, not just DC.

For the shunt value: I'd start from the power budget. If I want to keep dissipation low — say under 100 mW at 1A — that caps the shunt at around 100 mΩ. But a smaller shunt means a smaller signal, which pushes the amplifier's offset and noise to dominate the error budget. So I'd work the trade both ways: pick a shunt that gives a full-scale signal comfortably above the amplifier's input-referred offset and noise, then check that the resulting dissipation and voltage drop are acceptable. A 50–100 mΩ shunt typically lands in a reasonable spot for 1A.

For the amplifier, I'd use a dedicated current-sense amplifier rather than a generic op-amp, because it's designed with matched internal gain resistors (so gain drift tracks and CMRR stays high) and a common-mode range that extends to the supply. I'd check the datasheet for offset voltage and its drift over temperature, gain error and gain drift, and CMRR — those three dominate the ±2% budget. I'd also verify the amplifier's bandwidth is adequate for the PWM frequency so the current waveform isn't distorted, and that its input bias current doesn't create additional error across the shunt.

Finally, I'd do a worst-case error stack: shunt tolerance (use a low-TCR part, e.g., 50 ppm/°C or better), amplifier offset drift, gain error drift, and CMRR error over the common-mode swing, all summed over the 0–50°C range. If the stack exceeds ±2%, I'd either tighten the shunt tolerance, choose a lower-drift amplifier, or add a calibration step.

**Possible follow-ups:**
- How would you lay out the shunt and the sense amplifier to preserve CMRR and reject PWM switching noise?
- If the motor is driven with a PWM that has fast edges, how would you keep the current-sense signal clean without adding so much filtering that you lose the current waveform's shape?

## Q2: How would you approach debugging a circuit where a switching regulator's inductor is audible (whining) at light load, even though the output voltage and ripple are within specification?

**Answer:** Audible whining means the inductor is being mechanically excited at a frequency in the audible range — roughly 20 Hz to 20 kHz. The most common cause is that the regulator has entered a pulse-skipping or burst mode at light load, and the burst repetition rate has dropped into the audible band. The output is still in spec because the regulator is doing exactly what it's designed to do; the problem is acoustic, not electrical.

My first step is to confirm the mechanism rather than guess. I'd put a current probe on the inductor (or a small sense resistor in series) and look at the switching node and inductor current on a scope, triggered in a way that lets me see the burst envelope. If I see groups of switching pulses separated by idle periods at a few kHz, that confirms burst-mode operation. I'd also check whether the whine correlates with load: does it appear only below a certain load current, and does the pitch change with load? That's a strong signature of burst mode.

Once confirmed, the fix depends on the design constraints. Options, roughly in order of preference:

1. **Change the operating mode.** Many regulators let you select forced-PWM (continuous conduction) versus burst/PFM at light load. Forced PWM eliminates the audible burst but costs quiescent current — a real trade-off in a battery-powered device. If the light-load efficiency penalty is acceptable, this is the cleanest fix.
2. **Move the burst frequency out of the audible band.** Some regulators let you set the burst repetition rate, or the rate is a function of output capacitance and hysteresis. Increasing output capacitance can lower the burst frequency below 20 Hz, but that adds cost and board area and may slow transient response.
3. **Damp or stiffen the inductor.** The whine comes from magnetostriction and winding movement. A different inductor construction — potted, molded, or with a tighter winding — can be much quieter even under the same electrical excitation. This is often the most practical fix if the electrical behavior is otherwise fine.
4. **Add a small preload.** A bleeder resistor or a small always-on load can keep the regulator out of burst mode, at the cost of standby current.

I'd also rule out other acoustic sources before committing: ceramic capacitor singing (the piezoelectric effect in high-K dielectrics) can sound identical and is fixed differently — by changing dielectric or package size. I'd touch a probe to the inductor and to the capacitors to localize the source.

**Possible follow-ups:**
- If forced-PWM fixes the whine but raises standby current above your budget, how would you decide between accepting the whine and re-architecting the light-load behavior?
- How would you distinguish inductor whine from ceramic capacitor singing on the bench?

## Q3: How would you approach designing a hardware-based power-on self-test for a medical device's analog signal chain, and what would you want it to verify independently of firmware?

**Answer:** The purpose of a hardware POST is to verify that the analog signal chain is alive and within its expected operating envelope *before* the firmware trusts any measurement it takes — and ideally to do so in a way that doesn't depend on the firmware or the ADC being correct. If the firmware is the only thing checking the signal chain, a firmware fault or a stuck ADC can produce plausible-looking but wrong readings, which is exactly the failure mode a POST should catch.

I'd structure it around a few independent checks:

1. **Rail monitoring.** Comparators (or a supervisor IC) on each critical supply rail verify the rail is within window before the processor is allowed to release reset or before the measurement subsystem is enabled. This is independent of the ADC and firmware.
2. **Reference verification.** The precision voltage reference that sets the ADC's full-scale is checked against a second, independent reference (or against a ratiometric divider from a known-good source). If the reference has drifted or failed, every downstream measurement is wrong, so this is a high-value check.
3. **Signal-chain continuity and gain check.** A known stimulus — a precision resistor switched into the front-end, or an on-board reference injected at the input — is applied, and the resulting signal is compared against an expected window. This exercises the amplifier, filter, and ADC path end-to-end. The comparison can be done by a hardware comparator with a fixed window, so it doesn't rely on the firmware's interpretation of the ADC.
4. **Open/short detection on sensor inputs.** For a sensor front-end, a bias current or pull-up can detect a disconnected or shorted sensor before a measurement is attempted.

The key design principle is *independence*: the checks that matter most for safety should not depend on the same element they're checking. A rail monitor that uses the ADC to read the rail is not independent — if the ADC is broken, the check passes anyway. So I'd use comparators and discrete logic for the critical checks, and reserve ADC-based checks for non-safety-critical diagnostics.

I'd also think about what the POST does on failure: it should fail safe — inhibit the therapeutic output, flag the fault, and require a deliberate reset — rather than silently continuing.

**Possible follow-ups:**
- How would you keep the POST from adding so much test circuitry that it becomes a reliability liability itself?
- How would you verify that the POST actually catches the faults it's designed to catch — what would your fault-injection testing look like?

## Q4: How would you approach choosing between a comparator and an op-amp for a threshold-detection function in a hardware protection circuit, and what would drive the decision?

**Answer:** The core difference is that a comparator is designed to operate open-loop and saturate cleanly, while an op-amp is designed to operate closed-loop and stay linear. For a threshold-detection function, that distinction drives almost everything.

A comparator is the right choice when I need a clean, fast digital transition at a defined threshold. Its output stage is designed to swing rail-to-rail (or to a logic level) quickly, it has hysteresis built in or easily added, and its propagation delay is specified and short. For a protection circuit — say, overcurrent detection that must assert a shutdown within microseconds — the comparator's defined propagation delay and clean saturation are exactly what I want. I'd add external hysteresis (positive feedback) to prevent chatter when the input sits near the threshold, and I'd check the input offset voltage and its drift over temperature, because those set the threshold accuracy.

An op-amp used as a comparator will eventually saturate, but it's not designed for it. It may have a slow recovery from saturation (overload recovery time), it may draw excessive supply current when saturated, and its output may not reach a clean logic level. It can also oscillate or behave unpredictably near the threshold. So using an op-amp as a comparator is generally a compromise — acceptable for a slow, non-critical threshold where the op-amp is already on the board and the transition speed doesn't matter, but not for a protection function where timing and clean logic levels matter.

The decision drivers, then:
- **Speed:** If the response must be fast and well-defined, comparator.
- **Threshold accuracy:** Comparator offset and drift are specified for open-loop use; op-amp offset specs assume closed-loop. Comparator wins for a precision threshold.
- **Output interface:** Comparator outputs are designed to drive logic; op-amp outputs are not.
- **Cost and board space:** If an op-amp is already there and the threshold is slow and non-critical, reusing it can save a part — but I'd only do that after confirming the overload recovery and saturation behavior are acceptable.
- **Hysteresis:** Comparators make it easy; op-amps require more thought and can interact with the feedback network.

For a protection circuit specifically, I'd default to a comparator with hysteresis, and only consider an op-amp if the function is genuinely non-critical and slow.

**Possible follow-ups:**
- How would you size the hysteresis on a comparator used for overcurrent detection so it rejects noise but doesn't delay the response past your timing budget?
- What would you check in the comparator's datasheet to make sure its propagation delay is guaranteed over the full temperature range, not just at 25°C?

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review the reliability engineer argues that your chosen connector for the patient cable is not rated for the number of mating cycles the device will see over its lifetime, and proposes a more expensive, higher-cycle connector. You believe the current connector is adequate because the cable is intended to be connected once and left in place, but the reliability engineer is concerned about field replacement. How would you handle this disagreement?

**Answer:** The disagreement is really about an assumption, not about the connector: is the cable connected once and left in place, or is it expected to be mated and unmated repeatedly in the field? If we don't agree on that, we'll never agree on the connector. So my first move is to surface the assumption and get it resolved with data, not opinion.

I'd ask the reliability engineer what field-replacement scenario they're envisioning — is this based on a service procedure, a customer complaint pattern from a similar product, or a regulatory expectation? And I'd check the product requirements and the intended use: does the device's labeling or instructions for use imply the cable is user-replaceable, or is it a single connection made at installation? If the requirements are ambiguous, that's the real problem to fix, and it's worth escalating to the product owner or systems engineer to clarify.

If the requirements genuinely call for repeated mating — say, the cable is a consumable or a serviceable item — then the reliability engineer is right and I'd accept the higher-cycle connector, because the cost of field failures and the regulatory risk of a connector that wears out prematurely outweigh the connector cost. If the requirements confirm a single connection, I'd document that assumption explicitly, share it with the reliability engineer, and propose a compromise: keep the lower-cost connector but add a verification step (a mating-cycle test at the expected worst-case count, plus a field-replacement procedure that specifies replacing the cable and connector together if service is ever needed). That way the reliability concern is addressed with evidence rather than dismissed.

Throughout, I'd keep the tone collaborative — the reliability engineer is raising a legitimate concern, and the goal is a design that's defensible in a design review and in a regulatory submission, not winning the argument. If we still disagree after the requirements are clarified, I'd document both positions and let the design review or the systems owner make the call, because that's a requirements decision, not a hardware decision.

**Possible follow-ups:**
- If the requirements are genuinely ambiguous and the product owner won't commit, how would you decide which way to design?
- How would you verify the connector's mating-cycle rating in a way that satisfies the reliability engineer without adding a full qualification test to the schedule?