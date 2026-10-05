# hardware-design — Day 76

## Q1: How would you approach selecting a shunt resistor value and current-sense amplifier topology for measuring a bidirectional motor current of up to 1A, where the measurement must be accurate to ±2% over temperature and the shunt must not dissipate excessive power?

**Answer:** Start by budgeting the error and the power together, because they trade against each other. Shunt power is I²R, so at 1A a 100 mΩ shunt dissipates 100 mW, a 10 mΩ shunt dissipates 10 mW, and a 1 mΩ shunt dissipates 1 mW. The sense voltage at full scale is I·R, so a 10 mΩ shunt gives 10 mV at 1A — workable, but now every downstream error term (amplifier offset, gain error, reference tolerance, PCB trace resistance) is a larger fraction of the signal. A 100 mΩ shunt gives 100 mV, which is comfortable for accuracy but burns power and adds a small series drop in the motor path.

For ±2% over temperature, I'd pick a shunt with low temperature coefficient — a metal-element or four-terminal Kelvin-sensed part rather than a thick-film chip resistor, whose TCR and self-heating drift can eat the budget. I'd also derate the shunt's power rating substantially, since self-heating changes both resistance and the local temperature the amplifier sees.

For topology, bidirectional sensing rules out a simple high-side unidirectional amp. Options are: a high-side bidirectional current-sense amplifier that accepts a common-mode range spanning the supply and handles the sign internally; a difference amplifier built from an op-amp with a matched resistor network; or a low-side shunt with a differential amp. High-side keeps the motor's ground reference clean and catches faults that a low-side shunt would miss (e.g., a short to ground downstream of the shunt), but the amplifier must tolerate the full common-mode swing and reject it well — CMRR and common-mode range become the dominant specs. Low-side is simpler and cheaper but breaks the motor's ground reference and can't detect certain fault paths.

I'd verify the amplifier's input offset voltage and offset drift against the smallest current I need to resolve, not just full scale — a 10 mV full-scale signal with a 1 mV offset is already 10% error at low currents. I'd also check gain error, CMRR over temperature, and the reference used for the ADC, since the reference error appears directly in the result. Finally, I'd lay out the shunt with Kelvin connections and route the sense pair as a tight differential pair away from the switching node.

**Possible follow-ups:**
- How would you decide between a dedicated current-sense amplifier IC and a discrete difference amplifier built from a precision op-amp?
- What layout mistakes most commonly corrupt a low-value shunt measurement?

## Q2: How would you approach designing a hardware-based power-on self-test for a medical device's analog signal chain, and what would you want it to verify independently of firmware?

**Answer:** The point of a hardware POST is to verify the analog signal chain using known, on-board references and switches — not by trusting the ADC or the firmware to tell you everything is fine. If the only check is "read the ADC and see if the number looks reasonable," a stuck ADC, a shorted input, or a dead reference can all produce plausible-looking values.

I'd design in a small set of test injection points: a precision reference or divided-down rail that can be switched into the front-end input in place of the sensor, and a way to short the input to a known node (e.g., mid-supply or the reference) to check offset. A multiplexer or analog switch selects between the real sensor and the test source under hardware control. Then the POST sequence is: inject a known voltage, read the result, inject a second known voltage, read again, and check that the difference matches the expected gain and that the offset is within tolerance. That verifies gain, offset, and that the signal path is actually connected — not just that the ADC produces numbers.

What I want verified independently of firmware: that the reference is present and at the right voltage (a comparator against a divided version of the supply, or a window comparator), that the supply rails are within range (rail monitors), and that the analog switches and multiplexer actually toggle (a continuity or loopback check). The firmware can orchestrate the sequence and read results, but the pass/fail thresholds and the reference comparison should be hardware-defined so a firmware bug can't mask a hardware fault.

I'd also think about what the POST can and cannot prove. It can prove the electronics are functional at the moment of test. It cannot prove the sensor itself is good, nor that the patient connection is correct — those need separate checks. And I'd make sure the POST doesn't leave the device in a state where the test source is still connected to the patient path; the default state of the switches must be "sensor connected," with test injection only active during the test window.

**Possible follow-ups:**
- How would you handle the case where the POST passes but the device later fails in the field — what would you add to the design to narrow that down?
- What are the risks of running the POST too frequently during operation?

## Q3: How would you approach debugging a circuit where an op-amp's output is correct at DC but shows a slow, large-amplitude drift over minutes when the board is warmed by nearby power components?

**Answer:** A slow drift over minutes that correlates with board warming points at thermal effects rather than noise or oscillation. I'd separate the problem into three questions: is the drift in the op-amp itself, in the components around it, or in the signal source?

First, I'd confirm the correlation. Use a thermal camera or a thermocouple to map which components heat up and how the drift tracks. If the drift starts when a specific regulator or power stage warms, that's a strong clue. I'd also check whether the drift is reversible when the board cools — a reversible thermal drift suggests a temperature coefficient issue; an irreversible shift suggests something like a solder joint or a component being stressed.

Second, I'd isolate the op-amp from its surroundings. If I can thermally decouple the op-amp (air gap, remove the heat source temporarily, or use a hot-air gun to heat only the op-amp), I can tell whether the op-amp's own offset drift is the cause. Op-amp offset voltage drift is typically specified in µV/°C; a few degrees of local heating on a high-offset-drift part can produce visible output shift, especially with high gain.

Third, I'd look at the passive components. Resistor dividers and feedback networks with mismatched temperature coefficients produce a gain drift that looks like offset drift if the input is near zero. A resistor with a poor TCR in the feedback path, or a capacitor whose leakage changes with temperature, can both cause slow drift. I'd also check for thermocouple effects at solder joints — dissimilar metals at a junction produce small voltages that change with temperature, and this is a classic cause of slow drift in high-impedance or high-gain circuits.

Fourth, I'd check the input source. If the sensor or input network has a temperature-dependent impedance or offset, the op-amp may be faithfully amplifying a drifting input. Shorting the input to a known reference and seeing whether the drift persists separates the two.

The fix depends on the cause: choose a lower-drift op-amp, match resistor TCRs, add thermal isolation or a heat spreader, or move the heat source away from the sensitive node. In a medical device, I'd also want to verify the drift stays within the measurement's error budget across the full operating temperature range, not just at the bench.

**Possible follow-ups:**
- How would you distinguish op-amp offset drift from resistor TCR mismatch in a gain stage?
- What layout techniques reduce thermal gradients across a precision analog front-end?

## Q4: How would you approach selecting between a crowbar protection scheme and a clamping scheme for a low-voltage rail that feeds sensitive analog circuitry, and what would drive the decision?

**Answer:** The two schemes protect differently, and the choice comes down to what the downstream circuitry can tolerate and what failure mode you're defending against.

A clamping scheme uses a device — a TVS diode, a Zener, or an active clamp — that limits the rail voltage to a safe level but keeps conducting and holding the rail at the clamp voltage as long as the overvoltage persists. The rail stays powered, the downstream circuitry sees a voltage above nominal but below its absolute maximum, and operation may continue (possibly degraded). The clamp must be able to absorb the fault energy without failing, and its clamp voltage must be below the downstream absolute maximum with margin over temperature.

A crowbar scheme deliberately short-circuits the rail when an overvoltage is detected, pulling the rail down to near zero and forcing the upstream protection (a fuse, a current-limited supply, or a latching shutdown) to trip. The downstream circuitry is protected by being de-powered, but the rail is lost until the fault is cleared and the crowbar is reset. A crowbar typically uses an SCR or a latching comparator driving a thyristor or a MOSFET, and it must be able to handle the surge current until the upstream protection opens.

What drives the decision: if the downstream analog circuitry cannot tolerate any voltage above nominal — for example, a precision reference or an ADC input that would be damaged or would produce invalid readings above its supply — a crowbar that removes power may be safer than a clamp that lets the rail ride high. If the system must continue operating through a transient overvoltage, a clamp is preferable. If the overvoltage is a sustained fault (e.g., a wrong supply connected), a crowbar that forces a fuse to open gives a clear, safe shutdown, whereas a clamp may overheat and fail.

I'd also consider the fault energy and the upstream protection. A crowbar only works if the upstream source can be interrupted — if the supply can deliver unlimited current into the short, the crowbar device itself may fail. A clamp only works if the clamp device can dissipate the fault power for the duration of the fault. In a medical device, I'd want the protection to fail safe: if the protection device itself fails, the downstream circuitry should not be exposed to the overvoltage. That often argues for a crowbar with a fuse, or a clamp with a secondary disconnect.

**Possible follow-ups:**
- How would you size the crowbar device's surge rating against the upstream fuse's I²t curve?
- What are the risks of a clamp that holds the rail at a voltage the downstream circuitry tolerates but that degrades its accuracy?

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review the reliability engineer argues that your chosen connector for the patient cable is not rated for the number of mating cycles the device will see over its lifetime, and proposes a more expensive, higher-cycle connector. You believe the current connector is adequate because the cable is intended to be connected once and left in place, but the reliability engineer is concerned about field replacement. How would you handle this disagreement?

**Answer:** I'd treat this as a requirements question first, not a component argument. The disagreement is really about the expected use case: is the cable connected once and left in place, or is it disconnected and reconnected in the field? If the two of us disagree on that, the right move is to get the answer from the source — the clinical use case, the instructions for use, and any field service assumptions. I'd ask the reliability engineer what mating-cycle count they're assuming and where that number comes from, and I'd share my assumption and its basis. Often the disagreement dissolves once both sides are looking at the same use-case definition.

If the use case genuinely includes field replacement — for example, a cable that gets damaged and is swapped by a technician, or a device that's cleaned and stored with the cable detached — then the reliability engineer's concern is legitimate and I'd want to design to the higher cycle count. The cost of a higher-cycle connector is small compared to a field failure or a recall, and in a medical device the reliability argument usually wins when there's real uncertainty.

If the use case is truly connect-once, I'd still want to verify that assumption rather than just assert it. I'd check whether the instructions for use or the service manual imply any disconnection, and I'd consider whether a lower-cycle connector could fail in a way that's detectable or whether it would fail silently. I'd also look at whether the connector's other specs — contact resistance stability, retention force, sealing — matter more than cycle count for this application.

If we still disagreed after aligning on the use case, I'd escalate to the systems or clinical lead to make the call, and I'd document the decision and its rationale in the design history file. In a regulated environment, the important thing is that the decision is traceable and defensible, not that I win the argument. I'd also be open to a middle path: a connector rated for more cycles than the minimum, if the cost delta is small, buys margin against an uncertain use case.

**Possible follow-ups:**
- How would you verify the connector's cycle life if the datasheet rating is ambiguous or the vendor won't commit?
- What other connector parameters would you weigh alongside mating cycles for a patient cable?