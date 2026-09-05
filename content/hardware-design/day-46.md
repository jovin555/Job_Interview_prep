# hardware-design — Day 46

## Q1: How would you approach designing a power supply architecture for a medical device that contains both a high-resolution analog front-end (requiring a noise floor below 50 µV RMS) and a motor driver that can draw 1A peaks?

**Answer:** The fundamental principle here is separation — both physical and electrical — between the noisy, high-current domain and the sensitive analog domain. I would start by defining the power tree with independent rails rather than trying to share a single regulator between the motor driver and the analog front-end.

For the motor driver, a switching regulator (buck or boost depending on the input source) makes sense because of the 1A peak demand and the efficiency requirement. The analog front-end, by contrast, should be powered from a low-noise linear regulator, even though it's less efficient, because the noise floor requirement of 50 µV RMS essentially rules out a switching regulator directly feeding the analog rail.

The key architectural decision is where to place the isolation or filtering between the two domains. I would use a multi-stage approach: first, a bulk switching regulator to generate an intermediate rail from the battery or input supply; then, a dedicated low-noise LDO for the analog section, fed from that intermediate rail. The motor driver would be fed either directly from the intermediate rail or from its own regulator, depending on voltage requirements.

The critical details are in the implementation. The analog LDO needs adequate PSRR across the frequency range of interest — not just at DC, but at the switching frequency of the upstream regulator and its harmonics. I would check the LDO's PSRR curve against the switching noise spectrum. I'd also add a pi-filter (ferrite bead plus capacitors) between the intermediate rail and the LDO input if the LDO's PSRR isn't sufficient at the switching frequency.

Grounding strategy is equally important. The motor driver's high-current return path must not share copper with the analog ground. I would use a star-ground or split-ground approach, with a single point connecting the analog and power grounds, typically at the input supply return or the ADC's ground reference. The PCB layout would keep the motor driver's switching loop small and physically distant from the analog front-end.

Finally, I would verify the architecture with measurements — checking the analog rail's noise spectrum with the motor running at full load, not just in standby. The 50 µV RMS requirement needs to hold under worst-case conditions, including motor start-up transients and stall conditions.

**Possible follow-ups:**
- How would you decide between a single LDO versus multiple LDOs for different analog sub-circuits (e.g., ADC reference, analog supply, digital supply)?
- What specific measurements would you take to verify the noise floor requirement is met under worst-case motor load?

---

## Q2: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** This is a classic symptom pattern that points to something in the power or reference path rather than the signal path itself. The fact that the input is shorted to ground rules out external signal pickup, and the amplitude varying with supply voltage suggests the disturbance is coupled through the power supply or a reference.

My first step would be to characterize the disturbance precisely. I'd capture the waveform on an oscilloscope with sufficient resolution and timebase to see the full period — at 1–10 Hz, that means a timebase of 100–500 ms per division. I'd look at whether the disturbance is sinusoidal, sawtooth, or irregular, and whether it's truly periodic or drifting. I'd also check if it correlates with any other activity in the system — for example, a display refresh, a wireless beacon, or a periodic ADC conversion.

The amplitude varying with supply voltage is a strong clue. I would probe the actual supply rail at the analog front-end's power pin with an oscilloscope set to AC coupling and high sensitivity. A 1–10 Hz disturbance on the supply could come from several sources: a thermal oscillation in a regulator (unlikely at this frequency but possible with certain compensation networks), a low-frequency ripple from a switching regulator operating in burst or PFM mode at light load, or a reference source that's oscillating due to inadequate decoupling.

Another possibility is that the disturbance is thermal in nature — a component self-heating and cooling at a low rate, causing its parameters to drift. For example, a voltage reference with poor thermal response, or an op-amp with a large DC offset current heating up. I'd check component temperatures with a thermal camera or by touch (carefully, at low power).

I would also suspect the reference voltage path. If the ADC or amplifier uses a shared reference that's being loaded periodically — for instance, by a sample-and-hold circuit or a multiplexer switching — that could create a low-frequency disturbance. I'd probe the reference voltage directly.

The systematic approach is: isolate the stages. Short the input at each stage — at the first amplifier's input, at the ADC input, at the reference input — and see where the disturbance originates. Then, power the analog front-end from a clean bench supply (battery or linear supply) to see if the disturbance disappears, which would confirm it's coming from the power path.

**Possible follow-ups:**
- What if the disturbance only appears when the device is running from battery but not from a bench supply — what would that tell you?
- How would you distinguish between a power supply issue and a ground loop issue in this scenario?

---

## Q3: How would you approach selecting between a SAR ADC and a sigma-delta ADC for a medical device that measures a slowly varying physiological signal (e.g., temperature or pressure) with high resolution, and what are the key trade-offs you'd consider?

**Answer:** For a slowly varying physiological signal, the first question is what "high resolution" actually means in context — is it 12 bits, 16 bits, or 24 bits? And what's the required accuracy, which is different from resolution? The signal bandwidth is low (temperature changes slowly, pressure in a respiratory device might have components up to a few tens of Hz), so the ADC architecture choice is driven more by noise performance, power, and system integration than by raw sampling speed.

A sigma-delta ADC is often the natural choice for this application. Its oversampling and noise-shaping architecture gives excellent resolution for low-bandwidth signals — you can achieve 16–24 effective bits relatively easily. Sigma-delta converters also have built-in digital filtering, which can simplify the anti-aliasing requirements dramatically. For a temperature sensor with a bandwidth of a few Hz, you don't need a sharp analog anti-aliasing filter because the sigma-delta modulator's internal filtering handles it. Power consumption is generally reasonable at low output data rates, and many sigma-delta ADCs offer a sleep or low-power mode between conversions.

The SAR ADC has different strengths. It offers true sample-and-hold behavior with no latency — the output code corresponds to the instant of sampling, which matters if you need to correlate samples with an external event. SAR ADCs are also less sensitive to the input multiplexer settling issues when switching between channels, because each conversion is independent. However, achieving 16+ effective bits with a SAR ADC requires a very clean analog front-end, careful layout, and a low-noise reference — the noise performance is generally not as good as a sigma-delta for the same power budget.

Key trade-offs I'd weigh: noise performance (sigma-delta wins for low-bandwidth, high-resolution), anti-aliasing complexity (sigma-delta simplifies this), latency and sample correlation (SAR wins), multiplexing multiple channels (SAR is often easier, though sigma-delta with a fast enough modulator can handle it), and power consumption (both can be low, but sigma-delta at very low data rates can be extremely power-efficient).

For a medical device measuring temperature or pressure, I'd lean toward sigma-delta unless there's a specific reason for SAR — such as needing to synchronize samples with an external trigger, or multiplexing many channels with very different source impedances. I'd also check the sigma-delta's input-referred noise specification against the actual signal range — a 24-bit sigma-delta with 100 nV/√Hz noise is only useful if the front-end can deliver a signal at that level.

**Possible follow-ups:**
- How would the presence of a multiplexer with multiple sensor channels change your decision?
- What role does the ADC's input-referred noise specification play in your selection, and how would you verify it in practice?

---

## Q4: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The core requirement is that the latch must be fail-safe — it must maintain the fault state indefinitely, even if power is cycled or the triggering condition disappears, and it must only clear through a deliberate reset action. This is a safety-critical function in a medical device, so the design philosophy starts with understanding what "safe" means for the specific fault and what the reset procedure should be.

The classic implementation uses a comparator feeding a latch — either a discrete flip-flop or a thyristor/SCR-based crowbar approach. The comparator monitors the fault condition (temperature, current, voltage) against a reference threshold. When the threshold is exceeded, the comparator's output sets the latch, which drives a shutdown signal — for example, disabling a motor driver or opening a load switch.

The key design decisions are: how the latch is powered, how it's reset, and how it behaves during power-up.

For powering the latch, I would use a dedicated rail that's independent of the main processor and the circuit being protected. If the main power rail fails or is removed, the latch should still hold its state — which means it needs its own supply or a supply that's always present when the device has any power. In a battery-powered device, this might be a small always-on rail from the battery through a low-dropout regulator.

The reset mechanism needs careful thought. A simple push-button reset is common, but in a medical device, the reset action might need to be more deliberate — for example, requiring the operator to acknowledge the fault condition, or requiring the device to be powered down and powered up in a specific sequence. I would design the reset to be edge-triggered rather than level-triggered, so that holding the reset button doesn't mask a persistent fault. The reset signal should also be debounced and verified — for instance, requiring the reset to be held for a minimum duration, or requiring the fault condition to be cleared before the reset is accepted.

Power-up behavior is critical. The latch must default to the safe state on power-up — that is, if the device is powered on and a fault condition exists, the latch must engage. This means the latch's default state on power-up should be "faulted" until proven otherwise, or the power-up sequence should check the fault condition before enabling the output. I would use a pull-up or pull-down that ensures the latch starts in the safe state, and I'd verify this behavior with power cycling tests.

I would also consider redundancy. For a truly safety-critical latch, a single comparator and latch might not be sufficient — I might use two independent comparators with different reference sources, or a window comparator that detects both over- and under-threshold conditions. The output would then require both to agree before enabling.

Finally, I'd add testability. The latch circuit should have test points and possibly a test mode that allows verifying the comparator threshold, the latch operation, and the reset mechanism during manufacturing test and periodic maintenance.

**Possible follow-ups:**
- How would you design the reset mechanism to prevent an operator from accidentally clearing a fault that hasn't been resolved?
- What happens if the latch's own power supply fails — how does the circuit behave?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing your hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the hardware approach is necessary because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical disagreement, and my approach would be to move the discussion from opinion to evidence and risk analysis. The first thing I would do is acknowledge the firmware lead's valid points — a firmware solution does offer flexibility and cost savings, and those are legitimate engineering considerations. Dismissing them outright would be counterproductive.

However, the fundamental issue here is about the safety architecture and what happens under fault conditions. I would frame the discussion around the device's risk analysis and the requirements that flow from it. In a medical device, the over-temperature protection is typically a safety mechanism — it's there to prevent harm to the patient or damage to the device. The question isn't whether firmware *can* do the job in the normal case; it's whether firmware *can be relied upon* to do the job in the failure case.

I would walk through specific failure scenarios. What happens if the firmware hangs — not just in the application code, but in an interrupt storm or a memory corruption event? What happens if the ADC's reference drifts, or the ADC itself fails in a way that produces a valid-looking but incorrect reading? What happens during a firmware update, when the code is being reprogrammed and the protection routine isn't running? These aren't hypothetical edge cases — they're credible failure modes that need to be addressed in the risk analysis.

I would also reference the relevant standards thinking. IEC 60601 and the associated risk management process (ISO 14971) require that safety functions be designed with appropriate integrity. A single firmware path that depends on the ADC, the firmware loop, and the GPIO all working correctly is a single point of failure. A hardware comparator and latch provides an independent path that doesn't depend on the processor at all.

Rather than simply insisting on the hardware approach, I would propose a path forward that addresses both concerns. Perhaps we keep the hardware comparator as the primary protection but add a firmware-based monitoring layer as a secondary check that can provide early warning or more nuanced response. Or perhaps we can reduce the cost and board space of the hardware solution by integrating the comparator into an existing component, or by using a simpler, less expensive comparator. The goal is to find a solution that meets the safety requirements while addressing the firmware lead's legitimate concerns about cost and flexibility.

I would also suggest a concrete evaluation: let's do a failure mode analysis together, or let's review the risk assessment document and see what integrity level the protection function requires. If the risk analysis shows that a firmware failure doesn't lead to an unacceptable hazard — for example, if there's a secondary mechanical thermal fuse — then the firmware approach might be acceptable. But if the over-temperature protection is the primary safety mechanism, then independence is likely required.

The key is to keep the discussion focused on patient safety and regulatory requirements, not on whose design wins. I would aim for a collaborative decision that's documented in the risk analysis, with clear rationale for whatever approach we choose.

**Possible follow-ups:**
- What if the firmware lead argues that the hardware comparator could also fail — how would you respond?
- How would you handle this disagreement if the project schedule is tight and the firmware lead's approach would save significant development time?