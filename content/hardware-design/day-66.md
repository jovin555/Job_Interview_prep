# hardware-design — Day 66

## Q1: How would you approach selecting a load switch versus a discrete MOSFET-plus-gate-driver for power-gating a peripheral rail in a battery-powered medical device, and what factors would drive the decision?

**Answer:** The first thing I'd do is define the rail's actual requirements before touching part selection: input voltage range (for a single Li-ion cell, roughly 3.0–4.2V), peak and average load current, whether the rail needs to be switched on the high side or low side, and whether the load has significant input capacitance that will produce an inrush event at turn-on. Those numbers drive everything else.

An integrated load switch is usually the better default when the current is modest, the voltage is low, and I want a controlled turn-on. The advantages are real: an integrated device typically includes a gate-drive charge pump or level shifter, a defined slew-rate-controlled soft-start, thermal shutdown, and often reverse-current blocking — all in a small package with a known, characterized behavior. For a battery-powered medical device, that integration matters because it reduces the number of things I have to verify and document, and it gives me a predictable inrush profile without me having to design an RC ramp on a discrete gate.

A discrete MOSFET plus gate driver starts to win when the current is high enough that the integrated switch's on-resistance would dissipate too much, when the rail voltage is outside what integrated parts support, when I need a specific switching behavior the integrated part can't give me, or when cost at volume dominates and I have the board area to spare. The trade-off is that I now own the gate-drive design, the soft-start, the thermal path, and the failure modes — including the possibility of the MOSFET operating in its linear region during a slow turn-on and overheating.

For a medical device specifically, I'd also weigh the safety and regulatory angle. An integrated load switch with a defined behavior is easier to characterize and document in a design history file than a discrete circuit whose turn-on depends on gate charge, threshold voltage spread, and temperature. I'd lean integrated unless there's a concrete reason not to.

**Possible follow-ups:**
- How would you verify the inrush behavior of the chosen solution on the bench, and what would you measure?
- If the load has a large input capacitance, how would that change your selection or your soft-start design?

## Q2: How would you approach debugging a circuit where an op-amp's output is correct at DC but shows a slow, large-amplitude drift over minutes when the board is warmed by nearby power components?

**Answer:** A slow drift over minutes, correlated with board warm-up, points strongly toward a thermal effect rather than a noise or grounding problem. The first thing I'd do is separate "the op-amp itself is drifting" from "something feeding the op-amp is drifting." I'd start by monitoring the op-amp's input pins, its supply rails, and its output simultaneously while the board warms, using a scope or a logging DMM, so I can see which node moves first.

Common culprits, roughly in order of likelihood: the input offset voltage of the op-amp itself drifting with temperature (especially if it's a non-chopper part with a poor offset tempco); a resistor in the feedback or input network whose tempco is being exercised by the thermal gradient; a reference or bias node that's drifting; or a thermocouple effect at a solder joint or connector where dissimilar metals meet. I'd also check whether the drift is monotonic with temperature or whether it tracks something else — for example, a nearby regulator entering a different mode as it heats.

To localize it, I'd use a can of freeze spray or a hot-air tool carefully on individual components while watching the output, and I'd compare the board's thermal map against the schematic to see which parts are actually being heated. If the drift disappears when I thermally isolate a specific resistor or the op-amp, that's the answer. If it persists, I'd look at the supply — a regulator whose output shifts with temperature will move the op-amp's output through finite PSRR.

The fix depends on the cause: a chopper-stabilized or lower-drift op-amp, a lower-tempco resistor, better thermal layout to keep the sensitive analog section away from the heat sources, or a compensation scheme if the drift is systematic and predictable.

**Possible follow-ups:**
- How would you distinguish an op-amp's own offset drift from a resistor tempco effect if both are present?
- What layout changes would you make to reduce thermal gradients across the analog front-end?

## Q3: How would you approach selecting a crystal for a microcontroller that must maintain timing accuracy over a wide temperature range, and what would you verify on the bench?

**Answer:** The starting point is the accuracy budget. I'd work backward from the system requirement — for example, if the application needs ±20 ppm over 0–50°C, I need to know how much of that budget is allocated to the crystal's initial tolerance, its temperature stability, its aging, and the load capacitance pulling. A standard AT-cut crystal might give ±10–30 ppm over that range depending on the cut angle, while a TCXO or an oven-controlled part would be needed for tighter requirements. The cut angle is the key parameter: a crystal cut for a turnover point near the operating temperature will have much better stability across a narrow range than one cut for room temperature.

Beyond accuracy, I'd look at the crystal's load capacitance specification and match it to the MCU's oscillator circuit — the total load capacitance seen by the crystal is the series combination of the two load caps plus stray capacitance, and getting this wrong pulls the frequency. I'd also check the drive level: too much drive can age or damage the crystal, too little can cause startup problems, especially at temperature extremes. And I'd check the ESR and the negative resistance margin of the oscillator circuit — the oscillator needs enough loop gain to start reliably across the full temperature range and with component tolerance.

On the bench, I'd verify startup margin by measuring the negative resistance (injecting a series resistor and finding the value at which oscillation stops), and I'd verify frequency accuracy across temperature in a chamber, not just at room temperature. I'd also check startup time and whether the oscillator starts reliably at cold and hot extremes, since startup margin often degrades at temperature.

**Possible follow-ups:**
- How would you measure the oscillator's negative resistance margin, and what margin would you consider acceptable?
- What would you do if the crystal meets accuracy but fails to start reliably at cold temperature?

## Q4: How would you approach designing a hardware-based power-on self-test for a medical device's analog signal chain, and what would you want it to verify independently of firmware?

**Answer:** The purpose of a hardware POST is to verify that the analog signal chain is actually functional before the firmware trusts any reading from it — and to do so in a way that doesn't depend on the firmware or the ADC being correct. If the firmware is the thing checking the ADC, a stuck ADC or a firmware bug can produce a false pass. So the hardware POST should inject a known stimulus and check the response through a path that's independent of the normal signal path.

Concretely, I'd want to verify a few things. First, that the supply rails are within tolerance — a simple comparator or supervisor per rail, with the result latched or gated into a status register the firmware can read but not fake. Second, that the voltage reference is present and at the right value, again via an independent comparator. Third, that the analog front-end responds correctly to a known injected signal: a switch that disconnects the real sensor and injects a reference voltage or a known current into the front-end, with the output compared against an expected window by a hardware comparator. That verifies the amplifier, the filter, and the ADC input path are all alive.

The key design principle is independence: the POST should not rely on the ADC or the main processor to make its pass/fail decision. It can report its result to the firmware, but the decision itself should be made in hardware. I'd also want the POST to be non-destructive — it shouldn't disturb the patient-connected signal path in a way that could affect a real measurement, so the injection point and switching need to be thought through carefully.

**Possible follow-ups:**
- How would you handle the case where the POST's own injection switch fails, so the test always passes?
- What would you want the device to do if the POST fails — and how would that interact with the risk management file?

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review the reliability engineer argues that your chosen connector for the patient cable is not rated for the number of mating cycles the device will see over its lifetime, and proposes a more expensive, higher-cycle connector. You believe the current connector is adequate because the cable is intended to be connected once and left in place, but the reliability engineer is concerned about field replacement. How would you handle this disagreement?

**Answer:** The first thing I'd do is recognize that this isn't really a disagreement about connectors — it's a disagreement about the use case, and the use case is something we can actually resolve with data rather than opinion. The reliability engineer's concern is legitimate if the cable is expected to be replaced in the field; my assumption that it's connected once and left in place is only valid if that's actually how the device is used and maintained. So I'd want to get the actual field-replacement expectation from the people who own the product requirements — clinical, service, or product management — rather than each of us defending our own assumption.

If the requirement genuinely is "connected once," I'd want to document that clearly and make sure the connector's rating is adequate for that plus a reasonable margin for service events. If the requirement is "replaced periodically," then the reliability engineer is right and I should be looking at the higher-cycle part — or at a different connector family entirely that meets the cycle count without the cost premium. I'd also want to look at whether there's a middle option: a connector with a higher cycle rating that isn't the most expensive one, or a design change that reduces the number of mating cycles the connector actually sees.

The important thing is to keep the discussion on the requirement, not on whose part is better. If we can't agree on the requirement, that's the thing to escalate — not the connector choice. And I'd want the decision documented either way, because in a medical device the connector's cycle rating is part of the reliability and risk analysis, and it needs to be traceable.

**Possible follow-ups:**
- How would you verify the connector's cycle rating in practice, and what would you do if the vendor's data is incomplete?
- If the requirement turns out to be ambiguous, how would you decide whether to design for the higher cycle count anyway?