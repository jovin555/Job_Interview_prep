# hardware-design — Day 56

## Q1: How would you approach selecting a shunt resistor and current-sense amplifier topology for measuring a bidirectional motor current of up to 1A, where the measurement must be accurate to ±2% over temperature and the shunt must not dissipate excessive power?

**Answer:** I'd start by working backward from the accuracy budget and the power-dissipation constraint, because those two pull in opposite directions on shunt value.

For a bidirectional measurement, the first architectural decision is high-side versus low-side sensing. Low-side sensing is simpler and cheaper — the amplifier sits near ground, so a standard difference amplifier works and common-mode requirements are easy — but it breaks the ground path of the load, which can be unacceptable if the motor shares a ground reference with other circuitry or if a fault to ground would be undetected. High-side sensing keeps the load ground intact and can catch faults, but it forces the amplifier to reject a common-mode voltage near the supply rail, which constrains the part choice and often requires a dedicated current-sense amplifier rather than a generic op-amp difference stage.

For the shunt value: power dissipation is I²R, so at 1A a 100 mΩ shunt burns 100 mW, which is usually too much for a small package in a thermally constrained device; 10 mΩ burns 10 mW, which is manageable. But a smaller shunt means a smaller signal, so the amplifier's offset and gain error become a larger fraction of the reading. I'd compute the worst-case error stack: shunt tolerance (including its temperature coefficient), amplifier input offset voltage and its drift, gain error, and CMRR error over the common-mode range. If the total can't hit ±2% over temperature with a 10 mΩ shunt, I'd either move to a larger shunt with a better package/thermal path, or choose a lower-offset, lower-drift amplifier.

Topology-wise, for bidirectional current I need an amplifier that can handle both polarities — either a difference amplifier with a reference pin to bias the output at mid-supply, or a dedicated bidirectional current-sense amp that does this internally. I'd also consider whether the motor current is PWM'd: if so, the amplifier needs enough bandwidth and slew rate to follow the waveform without excessive settling error, or I'd synchronize sampling to the PWM period and measure at a known point. Finally, I'd verify the shunt's parasitic inductance doesn't matter at the switching frequency, and lay out the Kelvin sense connections so trace resistance doesn't add to the shunt value.

**Possible follow-ups:**
- How would you verify the accuracy of the current-sense circuit over temperature on the bench, and what would you use as a reference?
- If the motor is driven by PWM and the current is discontinuous, how does that change your measurement approach?

## Q2: How would you approach choosing between a comparator and an op-amp for a threshold-detection function in a hardware protection circuit, and what would drive the decision?

**Answer:** The core distinction is that a comparator is designed to be operated open-loop or with positive feedback (hysteresis), while an op-amp is designed for closed-loop negative feedback and is only compensated to be stable in that configuration. If I use an op-amp as a comparator, it will typically work at low speed, but it can exhibit slow, unpredictable recovery from saturation, and it may oscillate or produce glitches during transitions because its internal compensation assumes negative feedback. For a protection circuit where the output drives a latch or a shutdown, that unpredictability is a liability.

So the decision drivers are: speed, output interface, and hysteresis requirements. A dedicated comparator gives me a defined propagation delay (often nanoseconds to microseconds), a logic-compatible output (open-drain, push-pull, or a specific logic family), and often a built-in or easily added hysteresis pin. For a protection function that must respond within microseconds, a comparator is almost always the right choice.

An op-amp might be preferable if I need the threshold detection to also do some analog conditioning — for example, if the same stage must amplify a small sense signal before comparing it — or if I need a very low input offset and the comparator options at that offset are limited. In that case I might use an op-amp as a preamp followed by a comparator, rather than trying to make one op-amp do both jobs.

Other considerations: input common-mode range (does the threshold sit near a rail?), input bias current (matters if the source impedance is high), output type (open-drain lets me wire-OR multiple fault signals into one latch), and whether I need hysteresis to prevent chatter when the input crosses the threshold slowly or with noise. For a protection circuit I'd almost always add hysteresis, either via positive feedback around the comparator or a dedicated hysteresis pin, and I'd define the hysteresis band explicitly so it's wide enough to reject noise but not so wide that it delays a genuine fault response.

**Possible follow-ups:**
- How would you calculate the hysteresis band for a given amount of input noise, and what would you watch for if the input signal is slow-moving?
- What failure modes would you consider if the comparator's output drives a latch that must hold a fault state?

## Q3: How would you approach designing a snubber network for a switching node in a converter, and how would you decide whether it's actually needed?

**Answer:** I'd start by asking whether there's a problem to solve, because a snubber is a lossy element — it trades efficiency for reduced ringing and EMI — and adding one "just in case" is a common mistake. The symptom that justifies a snubber is excessive voltage ringing on the switching node, usually caused by the resonant tank formed by the parasitic inductance of the loop (layout, package, and any intentional inductance) and the output capacitance of the switching FET plus the diode or synchronous FET capacitance. That ringing shows up as radiated EMI, as voltage stress on the FET (possibly exceeding its rating), or as noise coupling into nearby sensitive circuitry.

To decide whether it's needed, I'd measure the switching node with a properly compensated, short-ground-lead probe — a long ground lead will show ringing that isn't really there. If the peak voltage is comfortably within the FET's rating and the EMI scan is clean, no snubber is needed. If there's ringing, the first fix is usually layout: minimize the high-di/dt loop area, place the input capacitor as close as possible to the switch and diode, and use a tight return path. Layout improvements often eliminate the need for a snubber entirely, and they don't cost efficiency.

If layout can't solve it, I'd add an RC snubber across the switching node (or across the diode, depending on the topology). The design procedure is empirical: measure the ringing frequency with a scope, add a small capacitor across the node and watch the frequency drop — the capacitance that halves the frequency is roughly three times the parasitic capacitance. Then choose the snubber resistor to critically damp the ringing, typically around the characteristic impedance of the resonant tank, and size the capacitor so the resistor's power dissipation is acceptable. I'd verify the result on the scope and check the efficiency impact, because a snubber that's too aggressive can cost several percent efficiency. For higher-power or higher-frequency designs I'd also consider an RCD clamp or an active clamp instead of a simple RC, since those recover some of the energy rather than dissipating it all.

**Possible follow-ups:**
- How would you measure the switching node without the probe itself adding ringing, and what would you look for in the waveform?
- What's the trade-off between an RC snubber and an RCD clamp, and when would you choose one over the other?

## Q4: How would you approach debugging a circuit where a switching regulator's output is stable at room temperature but shows increased ripple and occasional dropout as the ambient temperature rises, even though the load current is unchanged?

**Answer:** A temperature-dependent behavior with a constant load points to a parameter that drifts with temperature, so I'd approach it as a parameter-drift problem rather than a load problem. I'd start by confirming the symptom is repeatable and characterizing it: at what temperature does it begin, does it get worse monotonically, and is the dropout correlated with a specific operating condition (e.g., a particular input voltage or a transient)?

The usual suspects, in rough order of likelihood:

First, the output capacitor. Electrolytics dry out and their ESR rises with age and temperature; even ceramics lose capacitance with temperature and DC bias, and some dielectrics (like Y5V) lose most of their capacitance at temperature extremes. If the output cap's effective capacitance drops, the ripple rises and the loop may become marginally stable. I'd measure the cap's actual capacitance and ESR at temperature, or swap in a known-good cap of a stable dielectric to see if the symptom changes.

Second, the feedback network. If the divider uses resistors with a poor temperature coefficient, or if the reference inside the regulator drifts, the output voltage can shift enough to change the operating point. I'd measure the output voltage at temperature, not just the ripple, to see if there's a DC shift.

Third, the inductor. Core materials have temperature-dependent saturation behavior; if the inductor is near saturation at room temperature, it may saturate harder when hot, causing ripple current to spike. I'd check the inductor current waveform at temperature.

Fourth, the compensation. If the loop is marginally stable, temperature-induced changes in the FET's transconductance, the diode's forward drop, or the cap's ESR can push it into instability. I'd look at the loop response or the switching waveform for signs of subharmonic oscillation or jitter.

Fifth, thermal effects on the controller IC itself — some have internal thermal shutdown or foldback that can cause dropout as temperature rises, and the datasheet's thermal derating curves would tell me if I'm near a limit.

My debugging sequence would be: measure output voltage and ripple vs. temperature, measure the switching node waveform, measure the inductor current, then substitute components one at a time (output cap, inductor, feedback resistors) to isolate which one is responsible. I'd also check whether the dropout is actually a thermal shutdown event by monitoring the controller's behavior and any fault pins.

**Possible follow-ups:**
- If the output capacitor turns out to be the culprit, how would you choose a replacement that's stable over the full temperature range?
- How would you distinguish between a loop-stability problem and a component-drift problem from the scope waveform alone?

## Q5: (Behavioral) Imagine you're leading the hardware design for a medical device, and a supplier notifies you that a component you've designed in — a regulator that's already qualified and in your design history file — is being discontinued, with a last-time-buy window that closes before your production ramp. How would you handle the situation?

**Answer:** I'd treat this as a risk-management and change-control problem, not just a purchasing problem, because in a regulated medical device the component is part of the design history file and any change has to be justified and documented.

First, I'd quantify the exposure: how many units do we need through the last-time-buy window, what's the production forecast, and how long would the stock last? That tells me whether a last-time-buy is a viable bridge or just a stopgap. I'd also check whether the supplier has a pin-compatible or functionally equivalent replacement already qualified, because that's the cheapest path.

In parallel, I'd start the technical evaluation of alternatives. The key question is whether a candidate replacement is a drop-in or requires a design change. If it's a different part, I'd compare the critical parameters against the original — output voltage accuracy, transient response, dropout, quiescent current, thermal behavior, package and pinout, and any regulatory-relevant characteristics. Even a "compatible" regulator can have different loop compensation, different startup behavior, or different EMI signature, so I'd want bench data, not just datasheet comparison.

Then I'd bring in the cross-functional team: regulatory/quality to understand what re-verification the change triggers (does it require a new risk assessment, partial re-testing, or a design change notification?), manufacturing to understand the last-time-buy logistics and any inventory carrying cost, and the firmware team if the replacement changes any monitored behavior (e.g., a power-good signal timing). I'd present the options with their trade-offs — last-time-buy plus a longer-term redesign, immediate redesign with a qualified alternative, or a supplier negotiation for extended supply — and let the team make an informed call rather than deciding unilaterally.

Throughout, I'd keep the documentation tight: a change request, an updated risk analysis if the change affects safety or performance, and a clear traceability record from the old part to the new one. The goal is to keep the device compliant and the production line running without cutting corners on verification.

**Possible follow-ups:**
- If the replacement regulator has a different transient response, how would you decide whether re-testing of the whole system is required or just bench verification of the affected rail?
- How would you handle the situation if the last-time-buy quantity the supplier offers is smaller than your forecast, and the redesign can't be completed in time?