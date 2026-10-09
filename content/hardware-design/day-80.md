# hardware-design — Day 80

## Q1: How would you approach selecting a shunt resistor value and current-sense amplifier topology for measuring a bidirectional motor current of up to 1A, where the measurement must be accurate to ±2% over temperature and the shunt must not dissipate excessive power?
**Answer:** Start by budgeting the error and the power dissipation together, because they pull in opposite directions. A larger shunt gives more signal for the amplifier to work with, which improves the achievable accuracy, but dissipates more power (P = I²R) and drops more voltage in the motor path. A smaller shunt reduces loss but pushes the amplifier's offset and noise to dominate the error budget.

For a 1A full-scale, bidirectional measurement, I'd first pick a target full-scale shunt voltage that keeps the amplifier's input-referred offset and gain error small relative to the ±2% budget. Something in the tens of millivolts at full scale is a reasonable starting point — it keeps dissipation low while still giving the amplifier a usable signal. Then I'd check the dissipation: at 1A, a shunt producing, say, 50mV drops 50mW, which is usually acceptable, but I'd confirm the resistor's power rating and temperature coefficient, since self-heating shifts the resistance and therefore the gain.

For topology, a bidirectional measurement needs the amplifier to handle both polarities, so I'd look at a current-sense amplifier designed for bidirectional operation — either a dedicated bidirectional current-sense amp with a reference pin to set the zero-current output level, or a difference amplifier built around a precision op-amp with matched resistor networks. The dedicated part is usually preferable because the internal resistor matching is specified and the common-mode range is designed for the application.

The key error terms to budget: the shunt's initial tolerance and tempco, the amplifier's input offset voltage and its drift, gain error and gain drift, and CMRR (because the shunt sits at a common-mode voltage that may move with load). I'd sum these in an RSS sense for the typical case and also check the worst-case linear sum, since a medical device usually needs a defensible worst-case number. If the budget is tight, I'd move to a larger shunt voltage, a lower-offset amplifier, or a calibrated gain stage.

**Possible follow-ups:** How would you lay out the shunt and the sense amplifier to avoid picking up switching noise from the motor drive? What would change if the motor current were PWM'd rather than DC?

## Q2: How would you approach designing a hardware-based power-on self-test for a medical device's analog signal chain, and what would you want it to verify independently of firmware?
**Answer:** The point of a hardware POST is to verify that the analog signal chain is actually alive and within range *before* trusting any measurement the firmware takes — and to do it in a way that doesn't depend on the ADC or the firmware being correct, since those are exactly the things you're trying to gain confidence in.

I'd think about what can be checked with dedicated hardware. A common approach is to inject a known reference or a divided-down version of a precision rail into the front-end input through an analog switch, and compare the resulting signal against a window using a comparator. If the front-end output falls outside the expected window, the comparator flags a fault. This verifies the amplifier, the filter, and the signal path gain/offset in one shot, without involving the ADC.

I'd also want independent rail monitors — comparators watching each critical supply against a reference — so a rail that's out of tolerance is caught regardless of what the firmware thinks. And a reference check: compare the ADC's reference against a second, independent reference, or against a known divider, to catch a reference that has drifted or failed.

The design principle is independence: the POST should use its own reference, its own comparator, and its own signal path where possible, so a single fault in the ADC or firmware can't mask a real problem. The result should be a hardware status line the firmware reads, not a value the firmware computes.

I'd also make sure the POST is fail-safe: if the check can't run, or the result is ambiguous, the default should be to flag a fault rather than to pass silently.

**Possible follow-ups:** How would you avoid the POST itself introducing noise or loading the signal chain during normal operation? How would you verify the POST circuit is working, given that it's supposed to be the thing that catches failures?

## Q3: How would you approach debugging a circuit where an op-amp's output is correct at DC but shows a slow, large-amplitude drift over minutes when the board is warmed by nearby power components?
**Answer:** A slow drift over minutes, correlated with board warm-up, points strongly at a thermal effect rather than an electrical noise or stability problem. The timescale — minutes, not milliseconds — is the signature of thermal mass heating up, so I'd start by confirming the correlation: does the drift track the temperature of a specific component, and does it stop once the board reaches thermal equilibrium?

First I'd localize the heat source. Using a thermal camera or a thermocouple, I'd find which component is warming and how the op-amp's local temperature compares. If the op-amp itself is heating, its own offset voltage drift and bias current drift will show up as output drift — and the sign and magnitude will tell me whether it's offset drift (roughly proportional to the op-amp's tempco) or bias-current drift interacting with the source impedance.

If the drift is larger than the op-amp's own tempco would predict, I'd look at the passive components around it. Resistor tempco in a gain-setting network produces gain drift; a thermocouple junction formed at a connector or a solder joint between dissimilar metals produces a small voltage that drifts with temperature; a capacitor with a strong temperature coefficient in a filter or integrator changes the time constant.

I'd also check whether the drift is really thermal or whether it's a slow electrical effect that happens to correlate with warm-up — for example, a leakage path that changes as the board warms, or a supply rail that drifts as a regulator heats up. Measuring the supply rails and the op-amp's inputs directly, while logging temperature, separates these.

Once I've localized it, the fix depends on the cause: move the heat source or add thermal relief, choose a lower-tempco op-amp or resistors, balance the input impedances to cancel bias-current effects, or add a thermal compensation if the drift is inherent and predictable.

**Possible follow-ups:** How would you distinguish offset drift from bias-current drift experimentally? What layout changes reduce thermal gradients across a precision analog front-end?

## Q4: How would you approach selecting between a crowbar protection scheme and a clamping scheme for a low-voltage rail that feeds sensitive analog circuitry, and what would drive the decision?
**Answer:** The two schemes protect against overvoltage in fundamentally different ways, and the choice comes down to what the downstream circuitry can tolerate and what the failure mode needs to be.

A clamping scheme — typically a TVS diode, a Zener, or an active clamp — limits the rail voltage to a defined maximum but lets the rail continue to operate, possibly at an elevated voltage, for the duration of the event. The downstream circuitry sees a voltage above nominal but below its absolute maximum. This is fast, doesn't interrupt operation, and is usually the right choice for a transient event where you want the system to ride through.

A crowbar scheme deliberately short-circuits the rail when the voltage exceeds a threshold, pulling it down hard and typically blowing a fuse or tripping a protection device to remove the source. It's a latching, destructive-to-the-fault response: the rail goes to zero, and the system stops. This is appropriate when the downstream circuitry cannot tolerate *any* sustained overvoltage — for example, a sensitive analog front-end whose absolute maximum is only slightly above nominal, where even a brief clamp at the clamp voltage would exceed the part's rating.

So the decision drivers are: how much headroom is there between nominal and the downstream absolute maximum (if it's small, clamping may not be enough); whether the system must continue operating through the event or can safely shut down; and what the failure mode needs to be. For a medical device, the fail-safe direction matters — if the rail going down is safe and the rail staying up at an elevated voltage is not, crowbar is the safer choice. If the system must keep operating and the downstream parts have margin, clamping is simpler and less disruptive.

I'd also consider the response time and the energy the protection device has to absorb, since a crowbar has to survive the fault current until the fuse clears.

**Possible follow-ups:** How would you size the fuse in a crowbar scheme so it clears reliably without nuisance trips? What are the trade-offs between a passive TVS clamp and an active clamp using a comparator and a pass FET?

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review the reliability engineer argues that your chosen connector for the patient cable is not rated for the number of mating cycles the device will see over its lifetime, and proposes a more expensive, higher-cycle connector. You believe the current connector is adequate because the cable is intended to be connected once and left in place, but the reliability engineer is concerned about field replacement. How would you handle this disagreement?
**Answer:** This is really a disagreement about the *use case*, not about the connector — so the first thing I'd do is get the two of us aligned on the actual expected number of mating cycles, because that's the number the decision hinges on. If we're working from different assumptions about how the device is used in the field, no amount of connector datasheet comparison will resolve it.

I'd ask the reliability engineer to walk me through the scenario they're worried about: is it field replacement of the cable by a technician, by the patient, or by a service depot? How often? Over what service life? And I'd bring my own assumption — that the cable is connected once at setup — and we'd compare. If the reliability engineer's scenario is realistic and mine isn't, that changes my position, and I'd say so.

If we still disagree after aligning on the use case, I'd look for data rather than opinion. The connector datasheet gives a mating-cycle rating, but that rating is typically at a defined test condition; the real question is how the connector behaves at the expected cycle count with the expected insertion force and contamination. If the number is close to the rating, that's a real risk and I'd lean toward the higher-cycle part. If it's far below, the concern may be over-conservative.

I'd also weigh the cost of being wrong in each direction. If I'm wrong and the connector wears out, that's a field failure on a medical device — expensive and potentially a safety issue. If the reliability engineer is wrong and we over-specify, we've spent money and board space we didn't need to. Given the asymmetry, I'd be inclined to take the conservative choice unless the data clearly supports the lower-cycle part, and I'd document the decision and the reasoning so it's traceable.

The key is not to treat it as a win/lose argument but as a shared effort to get the use case right, and to let the data drive the decision.

**Possible follow-ups:** How would you verify the connector's actual cycle life if the datasheet rating were ambiguous? How would you document this decision so it's defensible in a design history file?