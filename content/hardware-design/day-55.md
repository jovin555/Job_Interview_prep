# hardware-design — Day 55

## Q1: How would you approach selecting a shunt resistor and current-sense amplifier topology for measuring a bidirectional motor current of up to 1A, where the measurement must be accurate to ±2% over temperature and the shunt must not dissipate excessive power?
**Answer:** Start by defining the measurement window and the acceptable burden. For a 1A full-scale bidirectional measurement, the two dominant topologies are a high-side shunt with a current-sense amplifier that has a matched resistor network for common-mode rejection, or a low-side shunt with a simpler difference amplifier. High-side is generally preferred when the load's ground reference must stay clean (e.g., a motor return that also carries sensor ground), because it keeps the shunt out of the ground path; low-side is simpler and cheaper but breaks the load's ground reference and can inject a small offset into any circuit sharing that node.

For shunt value, work backwards from the accuracy budget. The sense amplifier's input offset voltage and its drift over temperature set a floor on the minimum usable shunt voltage — if you pick a shunt so small that the full-scale drop is comparable to the amplifier's offset drift, the ±2% target becomes unreachable regardless of resistor tolerance. A common approach is to size the shunt so full-scale drop is at least 10–20× the amplifier's worst-case offset over temperature, then check power dissipation: P = I²R. For 1A and, say, a 10 mΩ shunt, that's 10 mW — negligible. A 100 mΩ shunt would be 100 mW, which starts to matter for thermal drift and for a battery-powered device.

Choose the shunt itself for low temperature coefficient (a few tens of ppm/°C, not hundreds) and for a four-terminal (Kelvin) footprint so the sense traces don't pick up solder-joint resistance. Route the sense pair as a tight differential pair back to the amplifier, symmetric and away from switching nodes.

For the amplifier, the key datasheet parameters are input offset voltage and its drift, CMRR (especially at the common-mode voltage the shunt actually sits at, which for high-side sensing is near the supply rail), and gain error from the internal resistor matching. A dedicated current-sense amplifier with a trimmed internal gain network will beat a discrete difference amplifier on CMRR and gain drift. Verify the common-mode input range covers the full supply range including transients, and check that the output swing fits the ADC's input range without clipping at either current extreme.

**Possible follow-ups:**
- How would you verify the ±2% accuracy claim on the bench, and what would you do if the measured error exceeded it?
- What changes if the motor is driven by PWM, so the current has a large ripple component on top of the DC average?

## Q2: How would you approach choosing between a comparator and an op-amp for a threshold-detection function in a hardware protection circuit, and what would drive the decision?
**Answer:** The core distinction is that a comparator is designed to be operated open-loop and to saturate cleanly at its output rails, while an op-amp is designed for closed-loop linear operation and its behavior when overdriven is not guaranteed — it may saturate asymmetrically, recover slowly, or even phase-invert on one input. For a protection threshold, you want a clean, fast, well-defined digital transition, so a comparator is almost always the right primitive.

What drives the decision further: propagation delay and response time. A protection comparator needs to assert its output within the required window (microseconds for overcurrent, milliseconds for over-temperature). Comparators specify propagation delay and rise/fall times directly; op-amps specify slew rate and settling time, which are the wrong figures of merit for a threshold crossing.

Hysteresis is the next consideration. A bare comparator will chatter when the input hovers near the threshold, especially with noise on the sensed signal. You add positive feedback (a resistor from output to the non-inverting input) to create a defined hysteresis band. The band must be wide enough to reject the worst-case noise and ripple on the sensed signal, but narrow enough that the protection still trips before the fault becomes dangerous. This is a real trade-off: too much hysteresis and you miss a slow-rising fault; too little and you get false trips.

Input common-mode range and offset also matter. A comparator whose input range doesn't include the sensed node's voltage will behave unpredictably. Offset and its drift set how accurately you know the actual trip point — for a ±5% threshold over temperature, the comparator's offset drift has to be a small fraction of the threshold voltage, or you need to trim.

Finally, output stage: open-drain vs push-pull. Open-drain lets you wire-OR multiple fault sources onto one line and level-shift to the logic supply, which is often convenient in a protection tree. Push-pull is faster and doesn't need a pull-up, but ties the output to the comparator's supply.

An op-amp used as a comparator is a compromise you accept only when you need the op-amp's other characteristics (very low offset, for instance) and the speed requirement is modest — and even then you should verify the datasheet actually characterizes the open-loop saturation behavior.

**Possible follow-ups:**
- How would you set the hysteresis band if the sensed signal has 50 mV of ripple and the threshold must be accurate to ±5%?
- What would you add to the comparator output to make the protection latch rather than follow the input?

## Q3: How would you approach debugging a circuit where a switching regulator's output is stable at room temperature but shows increased ripple and occasional dropout as the ambient temperature rises, even though the load current is unchanged?
**Answer:** Temperature-dependent behavior with a constant load points at a parameter that drifts with temperature, not at a load-related issue. I'd work through the likely candidates systematically.

First, the output capacitor. Electrolytics lose capacitance and gain ESR as they cool, but some ceramic dielectrics (Class II, X5R/X7R) lose a large fraction of their nominal capacitance as they heat and as DC bias is applied — the effective capacitance at the operating point can be a small fraction of the marked value. If the output cap's effective capacitance drops with temperature, the ripple rises. I'd measure the actual ripple with a scope at the output, using a proper tip-and-barrel probe or a short ground lead, and compare against the datasheet's expected ripple at the actual effective capacitance.

Second, the feedback network. If the divider uses resistors with a poor temperature coefficient, the output voltage can drift, and if it drifts toward the dropout region the regulator may lose regulation intermittently. I'd measure the output DC level at temperature and compare to the setpoint.

Third, the inductor. A ferrite-core inductor's saturation current and inductance fall as temperature rises. If the inductor was already near saturation at room temperature, the extra temperature rise can push it into saturation, causing the current ramp to steepen, the peak current to rise, and the ripple to increase. I'd check the inductor's temperature derating curve and measure the switch-node waveform at temperature to see if the current ramp is changing shape.

Fourth, the compensation. If the regulator's loop is marginally stable, temperature-induced shifts in the output cap's ESR or the inductor's resistance can push it toward instability, which shows up as increased ripple or subharmonic oscillation. I'd look at the switch node and the output for signs of jitter or period-doubling.

Fifth, the thermal path. If the regulator IC itself is heating up (poor thermal relief, no thermal vias, insufficient copper), its internal reference and error amplifier can drift, and its current-limit threshold can fold back. I'd measure the IC's case temperature and check whether the dropout correlates with the IC's own temperature rather than ambient.

The practical approach is to instrument the board in a thermal chamber or with a heat gun and a thermocouple, and watch the switch node, output ripple, and output DC level simultaneously as temperature rises. That usually isolates which parameter is moving.

**Possible follow-ups:**
- If the output cap turns out to be the culprit, how would you decide between a different dielectric and a larger nominal value?
- How would you distinguish between a compensation issue and an inductor saturation issue from the switch-node waveform alone?

## Q4: How would you approach designing a hot-swap protection circuit for a device that receives power from an external supply through a connector, where the input voltage is 12V and the device can draw up to 3A steady-state?
**Answer:** Hot-swap protection has to handle three distinct events: inrush current when the connector mates and the input capacitance charges, transient overvoltage or reverse voltage during mating or from the source, and steady-state overcurrent or short-circuit faults. Each needs its own mechanism.

For inrush, the input capacitance (bulk plus the sum of the downstream decoupling) will draw a large current spike at the instant of connection, limited only by the source impedance and the connector's contact resistance. If that spike exceeds the upstream supply's current limit or the connector's rating, you need to limit it. The common approach is a hot-swap controller driving a series N-channel MOSFET in its linear region, with a controlled gate ramp so the MOSFET's on-resistance decreases gradually and the capacitor charges at a bounded dI/dt. The controller senses the current through a shunt and either limits it or trips if it exceeds a threshold for too long. The MOSFET must be chosen for safe operating area (SOA) during the linear-region ramp — this is the parameter that kills hot-swap designs, because a MOSFET that looks fine on R_DS(on) can fail if its SOA at the applied voltage and ramp time is exceeded.

For overvoltage, a TVS diode or a clamp across the input handles short transients; for sustained overvoltage, the hot-swap controller can be configured to latch off above a threshold. For reverse polarity, a series diode is simple but drops voltage and dissipates power; a P-channel MOSFET in the return path or an ideal-diode controller gives a much lower drop and is preferred at 3A.

For steady-state overcurrent and short circuit, the hot-swap controller's current-limit and circuit-breaker functions handle it, but you need to decide between auto-retry and latch-off. For a medical device, latch-off with a deliberate reset is usually the safer choice, because auto-retry into a persistent fault can cause repeated thermal cycling.

Layout matters: the shunt and the MOSFET's source/drain loops must be tight, the gate drive loop short, and the sense traces Kelvin-connected to the shunt. The controller's ground reference must be the same node the shunt sees, or the current measurement will be wrong.

**Possible follow-ups:**
- How would you calculate the MOSFET's SOA requirement from the input capacitance and the desired inrush limit?
- What would you add to make the circuit fail safe if the hot-swap controller itself fails?

## Q5: (Behavioral) Imagine you're leading the hardware design for a medical device, and a supplier notifies you that a component you've designed in — a regulator that's already qualified and in your design history file — is being discontinued, with a last-time-buy window that closes before your production ramp. How would you handle the situation?
**Answer:** The first thing is to establish the facts before reacting: what's the exact last-time-buy date, what quantity is available, what's the lead time, and is there a pin-compatible or functionally equivalent replacement already qualified by the supplier? I'd get that in writing and share it with the program manager and supply chain immediately, because the decision affects purchasing, regulatory, and schedule.

Then I'd assess the impact across three axes. Technically, is there a drop-in replacement, or does the substitute differ in package, pinout, electrical characteristics, or thermal behavior? If it differs, the change triggers a re-qualification: bench characterization, thermal testing, and potentially a partial re-run of the regulatory testing that touched the affected rail. Regulator changes can ripple into noise-sensitive analog sections, so I wouldn't assume a "similar" part is actually similar without measuring.

Regulatory-wise, a component change in a qualified medical device is a change control action. It needs to go through the change control board, be documented in the design history file, and be assessed for whether it requires a new submission or a letter-to-file, depending on the jurisdiction and the nature of the change. I'd loop in regulatory affairs early rather than after the fact.

Commercially, the last-time-buy quantity has to cover production through the qualification of the replacement plus a safety margin. If the window is tight, I'd recommend placing a last-time-buy order to cover the gap while the replacement is qualified, even if it ties up inventory, because the alternative is a production stoppage.

Then I'd run the replacement through the same qualification path as the original: bench verification, thermal, EMC if relevant, and any regulatory testing the change triggers. I'd also look at whether this is a single-point failure in the supply chain and whether a second source should be qualified as a longer-term mitigation.

Throughout, I'd keep the cross-functional team informed with a clear decision timeline and the trade-offs at each step, so the program manager can make schedule and cost calls with full information.

**Possible follow-ups:**
- How would you decide whether a replacement regulator requires a full re-run of EMC testing or just a bench check?
- If the last-time-buy quantity would tie up significant capital, how would you frame the trade-off to the program manager?