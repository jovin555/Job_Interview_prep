# hardware-design — Day 52

## Q1: How would you approach compensating a peak-current-mode buck converter that shows subharmonic oscillation at duty cycles above 50%, and what would you check before adding an external ramp?

**Answer:** Subharmonic oscillation at duty cycles above 50% is the classic signature of insufficient slope compensation in peak-current-mode control. The inner current loop is inherently unstable at D > 0.5 because a perturbation in inductor current grows rather than decays over successive cycles. The standard fix is to add an artificial ramp to the current-sense signal — either internally in the controller or externally via a resistor from the oscillator/RT pin to the current-sense node.

Before adding ramp, I'd verify a few things. First, confirm the oscillation is genuinely subharmonic (alternating wide/narrow pulses at half the switching frequency) and not a loop instability or layout artifact — a current probe on the inductor and a scope on the switch node will show the characteristic period-doubling. Second, check the current-sense signal integrity: excessive leading-edge noise from the switch node can cause the comparator to trip early, which looks similar. A small RC filter on the sense pin (typically a few tens of ohms and a few hundred pF) is often needed regardless. Third, confirm the inductor value and current-sense resistor/gain match the design intent — a larger inductor ripple ratio makes the problem worse.

For the ramp itself, the rule of thumb is that the added slope should be at least half the down-slope of the inductor current, referred to the sense node. Too little ramp leaves the instability; too much ramp pushes the converter toward voltage-mode behavior, degrading the current-loop benefits (line feedforward, cycle-by-cycle limiting) and slowing transient response. I'd start at the minimum recommended by the controller datasheet, then verify with a load-step test and a Bode plot if a loop injection point is available. The compensation network on the COMP pin (Type II usually) then sets the crossover and phase margin — I'd target 45–60° phase margin and crossover well below the switching frequency, typically 1/10 to 1/5 of fsw.

**Possible follow-ups:**
- How would you distinguish subharmonic oscillation from a poorly compensated voltage loop if both show up as instability on a load step?
- What happens to the current-limit threshold when you add external slope compensation, and how would you account for that in the design?

## Q2: How would you approach choosing between a linear charger and a switching charger for a Li-ion battery in a portable medical device, and what factors beyond efficiency would drive the decision?

**Answer:** The headline trade-off is efficiency and heat versus noise and simplicity, but for a medical device the decision usually hinges on thermal budget, EMI, and the charging profile required.

A linear charger is essentially a pass element dissipating (Vin − Vbat) × Icharge. For a single-cell Li-ion at 4.2V and a 5V input, that's only ~0.8V of headroom, so at 500mA the dissipation is ~0.4W — manageable in a small package with a decent copper pour. At 1A it's ~0.8W, which starts to dominate the thermal design. Linear chargers are quiet, simple, require few externals, and don't radiate — attractive when the device is charging while operating and the analog front-end is live. They also have no inductor, which helps board area and EMI.

A switching charger (buck or buck-boost) handles higher charge currents and wider input ranges efficiently, but introduces a switching node, an inductor, and EMI that can couple into sensitive analog circuitry. For a device that charges while in use, the switching noise during charging is a real concern — you'd need to verify the analog front-end still meets its noise floor with the charger active, or gate the measurement during charge.

Beyond efficiency, I'd weigh: input source (USB 5V vs a higher-voltage adapter — a linear charger from 12V is untenable), charge current and therefore thermal rise, whether the device must operate during charge (which affects both thermal and noise), battery capacity and desired charge time, and regulatory/thermal requirements. IEC 60601 has touch-temperature limits that a hot linear charger can violate. I'd also consider the charging profile — Li-ion needs CC/CV with tight voltage accuracy (±1% or better), and both topologies can do this, but the switching charger's control loop needs more careful compensation. Finally, safety: both need independent overvoltage, overcurrent, and thermal protection; the charger IC's integrated protections are a strong argument for using a qualified part rather than a discrete design.

**Possible follow-ups:**
- If the device must charge while operating and the analog front-end is active, how would you verify the switching charger doesn't degrade measurement accuracy?
- How would you size the thermal relief for a linear charger dissipating 0.8W in a sealed enclosure?

## Q3: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** A 1–10 Hz disturbance with the input grounded and amplitude that tracks the supply points strongly toward a supply-related or thermal/mechanical coupling mechanism rather than input-referred noise. I'd work through it systematically.

First, characterize the disturbance: is it a clean sinusoid, a sawtooth, or irregular? Is the frequency stable or does it drift? Does it correlate with anything else — a switching regulator's burst mode, a thermal cycle, a display refresh, a motor, or a wireless transmission? A spectrum analyzer or FFT on the output, with the input grounded, is the starting point. If the frequency is stable and matches a known source (e.g., a 1 Hz housekeeping timer, a 10 Hz display refresh), that's a strong lead.

Second, since amplitude varies with supply voltage, I'd look at PSRR. The front-end's PSRR degrades at low frequency for many op-amps, and if the supply has a low-frequency ripple — for example, from a switching regulator in burst mode, or from a load transient that repeats — it can couple through. I'd measure the supply rail simultaneously with the output to see if the disturbance is present on the rail and whether the phase relationship is consistent with PSRR coupling. If the rail is clean but the output still shows it, the coupling may be through the ground reference or through a bias node.

Third, I'd check the reference. If the ADC or amplifier reference is derived from the supply, any supply variation appears directly in the output. A dedicated reference with good PSRR and local decoupling is the fix.

Fourth, thermal: a 1–10 Hz oscillation can be a thermal loop — a component self-heating and changing its bias, then cooling. This is more common at very low frequencies and often shows as a slow drift rather than a clean sine. I'd use freeze spray or a hot-air pencil to see if local heating changes the amplitude or frequency.

Fifth, mechanical/ piezoelectric: some capacitors (especially high-K ceramics) are microphonic, and vibration or acoustic noise can generate low-frequency voltages. Tapping the board or using an acoustic source can confirm this.

Finally, I'd check the layout: ground returns, star points, and whether the analog ground is shared with a noisy digital or power return. A ground loop or a shared impedance can inject low-frequency currents.

The fix depends on the root cause: better supply filtering and decoupling, a dedicated low-noise reference, separating grounds, replacing microphonic capacitors with a different dielectric, or addressing the thermal loop with better heat spreading or a different bias point.

**Possible follow-ups:**
- How would you distinguish a PSRR-coupled disturbance from a ground-loop-coupled one on the bench?
- If the disturbance turns out to be microphonic, what capacitor types would you consider and what trade-offs come with them?

## Q4: How would you approach selecting a TVS diode for protecting a medical device's external connector that carries both power and a sensitive analog signal, and what parameters matter most?

**Answer:** The TVS selection has to satisfy two sometimes-conflicting goals: clamp transient energy before it reaches the downstream circuitry, and not degrade the signal it's protecting. For a connector carrying both power and a sensitive analog signal, I'd treat them as separate protection problems even if they share a connector.

For the power line, the key parameters are standoff voltage (Vwm — must be above the maximum normal operating voltage with margin), breakdown voltage (Vbr — where it starts conducting), clamping voltage (Vc at the peak pulse current), peak pulse power (Ppp) and its waveform (8/20µs is common for surge, but ESD is 8kV contact per IEC 61000-4-2 with a much faster edge), and capacitance. The standoff must exceed the highest normal rail voltage including tolerance and any transient overshoot during normal operation, or the TVS will leak or conduct and either load the rail or fail. The clamping voltage at the expected surge current must be below the absolute maximum of the downstream IC — and that's often the binding constraint, because a TVS that clamps at 20V doesn't help a 5V-only input.

For the analog signal, capacitance is the dominant concern. A TVS with several hundred pF will roll off a high-impedance or high-bandwidth signal. For a low-frequency biopotential or sensor signal, a few hundred pF may be acceptable, but for anything above a few kHz, I'd look at low-capacitance TVS arrays (often <5pF per line) or use a different protection topology — series resistance with a clamp diode to a rail, or a dedicated low-capacitance ESD array. The signal's source impedance matters: a 10kΩ source with 100pF gives a 160kHz pole, which may be fine for a 1kHz signal but not for a 1MHz one.

I'd also consider: unidirectional vs bidirectional (bidirectional for signals that swing below ground or for AC-coupled lines), leakage current (matters for high-impedance sensor inputs and for battery-powered devices in standby), and the IEC 61000-4-2 level required (typically ±8kV contact for medical devices, sometimes ±15kV air). The TVS must survive repeated strikes without degradation — some technologies wear out.

Layout is critical: the TVS must be placed so the transient current path is short and does not flow through the sensitive circuitry. The clamp should be at the connector, with a low-inductance path to the ground reference the transient is referenced to. A TVS placed after a long trace is nearly useless because the trace inductance raises the effective clamping voltage at the IC.

Finally, I'd verify the whole protection scheme — TVS plus any series impedance plus the IC's own ESD structures — as a system, because the IC's internal diodes may conduct first and fail if the TVS doesn't clamp low enough.

**Possible follow-ups:**
- How would you verify the TVS actually protects the downstream IC during an ESD event, given that a standard ESD gun test may not show the internal node voltages?
- What's the trade-off between a TVS with a low clamping voltage and one with low capacitance, and how would you resolve it for a high-impedance sensor input?

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the manufacturing engineer argues that your chosen PCB surface finish (ENIG) is too expensive and proposes replacing it with HASL to reduce cost. You believe ENIG is necessary because the board includes a high-density BGA package and a high-resolution ADC that requires a flat, uniform surface for reliable solder joints and consistent electrical performance. How would you handle this disagreement?

**Answer:** I'd treat this as a technical decision that needs to be made on evidence, not on seniority or cost pressure alone, and I'd want to bring the manufacturing engineer into the reasoning rather than just overrule them.

First, I'd acknowledge the cost concern is legitimate — ENIG is more expensive than HASL, and cost pressure on a medical device is real. I'd want to understand the magnitude: is this a few cents per board or a significant fraction of the BOM? That frames how much effort the decision deserves.

Then I'd lay out the technical case concretely. For a fine-pitch BGA, HASL's uneven surface can lead to poor solder joint formation, voids, and in the worst case, non-wetting or head-in-pillow defects that are difficult to detect and can fail in the field. For a high-resolution ADC, the concern is different: HASL's surface roughness and the potential for solder mask or flux residue to affect the surface impedance of high-impedance analog traces, plus the flatness needed for consistent solder joints on fine-pitch packages. ENIG provides a flat, coplanar surface with good shelf life and consistent solderability.

But I wouldn't just assert this — I'd propose a path to resolve it. Options: (1) check whether the BGA pitch and the ADC package actually require ENIG, or whether a middle-ground finish like immersion silver or immersion tin would satisfy both cost and technical needs; (2) if HASL is proposed, ask the manufacturer to run a small build with HASL and inspect the BGA joints with X-ray and cross-section, and measure the ADC's performance on those boards; (3) review the assembly house's capability and yield history with HASL on similar packages. If the data shows HASL works reliably for this board, I'd be willing to reconsider — the goal is a reliable product, not a particular finish.

I'd also bring in the quality/regulatory angle: for a medical device, a solder defect that escapes to the field is far more costly than the finish. The design history file needs to justify the choice, and "we saved a few cents" is a weak justification if it introduces risk.

If we can't agree, I'd escalate to the project lead or a design review board with the data, and propose a decision that's reversible — for example, qualify both finishes and choose based on the pilot build results. That keeps the project moving and makes the decision evidence-based.

**Possible follow-ups:**
- If the pilot build with HASL shows acceptable BGA joints but the ADC performance is marginal, how would you decide?
- How would you document this decision in the design history file so it's defensible during an audit?