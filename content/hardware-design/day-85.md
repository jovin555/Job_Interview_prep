# hardware-design — Day 85

## Q1: How would you approach choosing between a voltage-mode and a current-mode control architecture for a buck converter that must supply a fast-transient digital load while also feeding a sensitive analog rail through a downstream LDO?

**Answer:** The two architectures differ mainly in what the control loop regulates and how it responds to line and load changes. Voltage-mode control senses only the output voltage, compares it against a reference through an error amplifier, and compares that error signal against a fixed-amplitude ramp to set duty cycle. It's straightforward, gives good noise immunity on the feedback node, and handles wide duty-cycle ranges well — but it's a second-order system with a double pole from the LC output filter, so compensation is more involved and the loop tends to be slower to react to load steps unless the crossover is pushed high.

Current-mode control adds an inner loop that senses inductor current (via a sense resistor, DCR sensing, or the low-side FET's Rds(on)) and uses that ramp instead of a fixed oscillator ramp. This effectively removes the inductor from the outer loop's transfer function, turning it into a single-pole system that's easier to compensate and inherently provides cycle-by-cycle current limiting. It also gives better line-transient rejection because input voltage changes are reflected immediately in the current ramp slope. The trade-offs are noise sensitivity on the current-sense signal, the need for slope compensation above 50% duty cycle to prevent subharmonic oscillation, and slightly more complex layout.

For a load that combines fast digital transients with a sensitive analog rail, I'd lean toward current-mode control for the main converter: the faster transient response and built-in current limit are valuable, and the downstream LDO will clean up whatever ripple and switching noise remains for the analog rail. The LDO's PSRR does the heavy lifting on the analog side, so the switcher's job is to be efficient and stable, not necessarily ultra-low-noise. I'd verify the current-sense signal integrity carefully, add slope compensation if duty cycle can exceed 50%, and confirm the LDO's PSRR is adequate at the switcher's switching frequency and its harmonics — PSRR often rolls off badly above a few hundred kHz, so the switcher's ripple frequency matters.

**Possible follow-ups:**
- How would you decide whether the current-sense signal needs a sense resistor versus DCR or Rds(on) sensing, and what would each choice cost you in accuracy?
- If the LDO's PSRR at the switching frequency turns out to be marginal, what would you change — the switcher, the LDO, or the filtering between them?

## Q2: How would you approach selecting a decoupling capacitor network for a high-resolution ADC that shares a board with a switching regulator and a digital section?

**Answer:** I'd think about decoupling in layers, because a single capacitor value can't cover the frequency range that matters. The ADC's supply pins need a small, low-ESL ceramic right at the pin — typically 100 nF or so in an 0402 or 0201 package to minimize parasitic inductance — to handle the high-frequency current pulses the ADC draws during conversion. That cap's job is to supply charge locally before the current has to travel through any trace inductance.

Below that, I'd add a bulk capacitor in the 1–10 µF range per supply domain to handle lower-frequency transients and to act as a local reservoir. If the ADC has separate analog and digital supply pins, I'd decouple them independently and be careful not to let digital return currents share the analog ground path — the decoupling caps should return to the appropriate ground plane, not to a shared stub.

The reference pin deserves special attention. Many high-resolution ADCs draw their reference current in short bursts at the sampling instant, so the reference needs its own low-ESL decoupling close to the pin, often with a small series resistor or ferrite to isolate it from the rest of the reference network. I'd also consider whether the reference buffer can source those transients or whether the cap has to.

For the interaction with the switching regulator, I'd place the ADC's supply filtering as a pi or LC network fed from a point that's already been filtered, and I'd keep the switcher's hot loop — input cap, high-side FET, inductor, output cap — physically compact and away from the ADC. The decoupling network can't fix a layout problem where the ADC sits in the switcher's near field.

Finally, I'd verify with a scope probe at the ADC's supply pin, not at the regulator output, using a short ground lead. The measurement point matters more than the schematic.

**Possible follow-ups:**
- How would you decide whether a ferrite bead between the regulator and the ADC supply is helping or creating a resonance problem?
- What would you look for on the scope to tell you the decoupling is inadequate versus the layout being the real issue?

## Q3: How would you approach debugging a circuit where a device works correctly on the bench but fails intermittently once it's installed in its enclosure, and the failure correlates with the device being handled or moved?

**Answer:** Intermittent, motion-correlated failures usually point to something mechanical or something that changes when the board is constrained. I'd start by trying to reproduce the failure in a controlled way — flexing the board, tapping components, wiggling connectors and cables, and varying temperature — while monitoring the relevant signals. If I can make it fail on demand, I've turned an intermittent problem into a reproducible one, which is most of the battle.

The usual suspects are: a solder joint that's cracked or marginal (often on a connector, a large component, or a BGA), a connector that's not fully seated or has insufficient contact force, a cable that's strained in the enclosure and pulling on a pad, a component that's mechanically stressed by the enclosure or a mounting screw, or a board flex that changes a critical trace's impedance or opens a via. Cold solder joints and head-in-pillow BGA defects are classic for this pattern because they can pass continuity checks at rest but open under flex or thermal expansion.

I'd also consider whether the enclosure changes the electrical environment — for example, a metal enclosure shifting grounding or shielding, or a cable routing that now runs near a noise source. And I'd check whether the failure is actually electrical or whether it's a mechanical switch or sensor being actuated by the handling.

The tools I'd reach for: a thermal chamber or heat gun plus freeze spray to see if temperature interacts with the motion, a vibration table if available, X-ray or dye-and-pry for BGA and connector joints, and a careful visual inspection under magnification. If I can instrument the board, I'd bring out test points and monitor rails and key signals while flexing, looking for glitches that correlate with the mechanical event.

The key discipline is to change one variable at a time and to confirm the root cause before applying a fix — reflowing everything might make the symptom go away without telling me what was actually wrong, which means it can come back in the field.

**Possible follow-ups:**
- If you suspect a BGA head-in-pillow defect, what inspection methods would you use, and how would you confirm it before committing to a rework?
- How would you decide whether the fix belongs in the design (strain relief, different connector) versus the process (reflow profile, handling)?

## Q4: How would you approach designing a hardware-based power-on self-test for a medical device's analog signal chain, and what would you want it to verify independently of firmware?

**Answer:** The purpose of a hardware POST is to verify that the analog signal chain is functional and within tolerance before the device is trusted to make measurements — and to do so in a way that doesn't depend on the same firmware and ADC path that the measurement itself uses. If the POST relies entirely on the ADC and firmware to check the ADC and firmware, a fault in either can mask itself.

I'd structure it around a few independent checks. First, rail monitoring: comparators or supervisory ICs that verify each supply rail is within its window, with the results latched or fed to a status register the firmware can read but can't easily fake. Second, reference verification: a check that the precision reference is present and within tolerance, ideally by comparing it against a second, independent reference or a ratiometric check, so a drifted or failed reference is caught. Third, signal-chain integrity: injecting a known stimulus — a precision voltage or current derived from the reference — at the front end and verifying the chain responds as expected. This can be done with an analog switch that routes a known signal into the input, and a comparator or window detector at the output that flags out-of-range results.

The key design principle is independence: the stimulus source, the comparison threshold, and the pass/fail decision should not all live in the same silicon or the same firmware path. A comparator with a fixed threshold derived from the reference is a good building block because it's simple, fast, and hard to spoof.

I'd also want the POST to be verifiable — meaning I can inject a fault on the bench and confirm the POST catches it. That's part of the design validation, not an afterthought. And I'd want the results to be logged or latched so a failure isn't lost if the device resets.

The trade-off is board area and cost: every independent check adds components. I'd prioritize the checks that cover the highest-risk failure modes — the ones that could lead to an incorrect measurement being displayed or acted upon — and accept that not every node can be independently verified.

**Possible follow-ups:**
- How would you verify that the POST itself hasn't been defeated by a fault, without adding so much redundancy that the design becomes impractical?
- What would you do if the POST flags a marginal failure that's within the device's specified accuracy but outside the POST's tighter window?

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review the software lead argues that the device's power-on self-test can be simplified by removing the hardware checks — rail monitors, reference checks — and relying on firmware to verify the system by reading the ADC and checking that values are in range. The software lead argues this reduces component count and board area. You believe the hardware checks are necessary because they verify the analog signal chain independently of the ADC and the firmware. How would you handle this disagreement?

**Answer:** I'd start by making sure I understand the software lead's proposal fully and treating it as a legitimate engineering position rather than something to dismiss. The goal of reducing component count and board area is real, and if the firmware approach genuinely covers the risk, it's worth considering. So the first step is to get specific about what each approach actually verifies.

The core issue is independence. A firmware-only self-test reads the ADC and checks that the values are in range — but if the ADC is stuck, if the reference has drifted, or if the firmware itself is hung or corrupted, the test can pass when it shouldn't, or fail to run at all. The hardware checks exist precisely to catch those cases: a rail monitor that's independent of the MCU can flag a supply fault even if the firmware never runs, and a reference check that compares against an independent source can catch a drifted reference that the ADC would otherwise report as a valid reading.

I'd want to frame this in terms of the failure modes we're trying to cover and the risk associated with each. If the device's measurement is used for a clinical decision, a self-test that can be defeated by the same fault it's supposed to catch is a real hazard. That's a risk-management argument, not a preference argument, and it's the kind of thing that belongs in the risk file.

I'd propose a concrete comparison: list the failure modes each approach covers, identify the gaps, and estimate the residual risk. If the firmware approach leaves a gap that matters, that's the basis for keeping the hardware checks. If the gap is small and the risk is acceptable, I'd be open to simplifying — but I'd want that decision documented and agreed, not made implicitly.

I'd also look for a middle ground: maybe some checks can move to firmware while the highest-risk ones stay in hardware. That way we get some of the cost and area savings without giving up the independence that matters most. And I'd want to bring in the quality/regulatory perspective early, because in a medical device this is exactly the kind of decision that gets scrutinized.

Throughout, I'd keep the conversation focused on the failure modes and the risk, not on whose approach is better. The software lead and I both want a device that's safe and works; we just have different views on how to get there, and the way to resolve that is with evidence and a shared risk framework.

**Possible follow-ups:**
- If the team decides to keep the hardware checks, how would you justify the added cost and board area to a program manager who's under schedule and budget pressure?
- How would you document this decision so that it's defensible during a regulatory review, regardless of which approach is chosen?