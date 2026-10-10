# space-rad-hard — Day 81

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd start by treating the two feeds as genuinely independent sources that are only combined at the point of load, rather than tying them together at a single node. Each feed gets its own ORing element — ideally a controlled ORing scheme using pass elements with current sensing rather than plain Schottky diodes, so I can actively limit fault current and command a feed off. The ORing stage is where fault isolation happens: if a downstream load latches or shorts, the current-limit and overcurrent protection on that branch trips and removes the branch, but the ORing topology keeps the other feed supplying the rest of the system.

For hot-swap, the concern is inrush into bulk capacitance and the resulting bus disturbance. I'd use a hot-swap controller with a controlled slew rate on the pass FET gate, plus a dV/dt-limited startup so the inrush is bounded and the upstream bus doesn't sag. I'd also add reverse-current protection so that if one feed collapses, it doesn't get back-fed from the other through the ORing path.

On the radiation side, the pass elements and controllers need to be evaluated for SEL and SET. A latch-up in the ORing controller could either fail-open (losing a feed) or fail-short (tying the feeds together), so I'd want the controller to have a defined behavior under transient upset and ideally a watchdog that can re-assert the correct state. Current-sense elements need to be radiation-tolerant or at least characterized, because a drifted sense resistor changes the trip threshold. Finally, I'd verify the whole scheme against the bus transient requirements — the hot-swap event must not pull the 28V bus below whatever the rest of the payload needs.

**Possible follow-ups:**
- How would you decide between a diode-OR and a controlled ORing scheme, and what does each cost you in terms of voltage drop and fault behavior?
- If the two feeds come from the same upstream source, does that change your fault-isolation assumptions?

## Q2: How would you approach derating and part selection for a space-deployed board, and how does derating interact with the radiation tolerance you're trying to achieve?

**Answer:** Derating and radiation tolerance are two separate margins that both eat into the same part, so I'd treat them as a combined budget rather than two independent checks. Derating is about keeping the part within a fraction of its rated stress — voltage, current, power, junction temperature — so that it has margin against normal variation, transients, and wear-out. Radiation tolerance is about how the part's parameters shift or fail under TID, displacement damage, and single-event effects. If I derate aggressively on voltage but the part's TID response is to shift its threshold or increase leakage, the derating margin may be consumed by the radiation-induced drift.

Practically, I'd start from the mission environment: total dose, dose rate, particle environment, and lifetime. Then for each part I'd ask whether it has radiation data, whether that data covers the relevant environment, and whether the post-irradiation parameters still meet the circuit's requirements with the derating margin applied. A part that meets derating on paper but has no radiation data is an unknown, not a pass. For parts with data, I'd apply the derating to the worst-case post-irradiation parameters, not the pre-irradiation datasheet values.

I'd also be careful about derating categories that interact with radiation: for example, derating a regulator's output current may be fine, but if TID causes its reference to drift, the output voltage accuracy degrades independently of the current margin. And for anything with a latch-up concern, derating doesn't help — SEL is a structural susceptibility, not a stress-margin issue, so it needs a mitigation (current limiting, epitaxial substrate parts, or a latch-up recovery scheme) rather than more derating.

**Possible follow-ups:**
- How would you handle a part where the radiation data exists but only at a dose rate that doesn't match your mission?
- Where does derating stop being useful and mitigation have to take over?

## Q3: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a poor fit for a fault-tolerant bus because it has no inherent error detection beyond the ACK bit, and a single stuck node can hold SDA or SCL low and lock the entire bus. So the first question is whether I²C is actually required, or whether a differential bus with CRC and a defined fault-recovery mechanism would be a better choice. If I²C is fixed by the sensor selection, I'd design around its weaknesses rather than pretend they don't exist.

For data integrity, I'd add a CRC or checksum at the application layer, because the I²C ACK only confirms a byte was received, not that it was correct. I'd also add sequence numbers or a transaction ID so a corrupted or repeated read can be detected. For lock-up recovery, I'd put a bus-recovery mechanism in the master: if a transaction times out, the master toggles SCL manually for a number of clocks to free a stuck slave, then issues a STOP, then re-initializes. Some masters have this built in; if not, it can be done in firmware with GPIO control of the clock line.

For the nodes themselves, I'd consider bus isolation — a mux or switch per node, or at least a series element that can be commanded off — so one failed node can be removed without taking down the bus. That's more complex and adds its own failure modes, so it's a trade against how critical continuous operation is. On the radiation side, the I²C lines are single-ended and relatively slow, so SETs on the lines are less of a concern than upsets inside the slave state machines, which can leave a node in a bad state. A periodic re-initialization or a watchdog on each node helps there.

**Possible follow-ups:**
- How would you decide which nodes get bus isolation and which don't?
- What's the failure mode of your recovery scheme if the master itself is the node that's upset?

## Q4: You're reviewing a design for a space-deployed system that uses a COTS linear regulator to generate a 1.2V core voltage for an FPGA. The regulator's datasheet shows no radiation data, and the output voltage is specified as 1.2V ±2%. The FPGA requires 1.2V ±5% and draws up to 3A. How would you evaluate this choice and what alternatives would you recommend?

**Answer:** The first thing I'd note is that the ±2% and ±5% numbers are pre-irradiation, room-temperature, typical-condition specifications, and neither the regulator nor the FPGA numbers include radiation. So the apparent 3% margin is not real margin — it's an uncharacterized gap. TID can shift a linear regulator's reference and its error amplifier behavior, and ELDRS is a particular concern for bipolar linear regulators at low dose rates. A part with no radiation data could drift well outside ±2% over the mission, and the FPGA's ±5% requirement is itself a pre-irradiation number that may tighten or shift under dose.

Beyond accuracy, I'd be concerned about SEL. A linear regulator passing 3A is a candidate for latch-up, and a latch-up in the regulator could either drop the rail (losing the FPGA) or, worse, pass the input voltage to the core. I'd also look at SETs on the regulator's control loop, which could cause transient output excursions that the FPGA's decoupling may or may not absorb.

For alternatives, I'd look for a rad-hard or radiation-characterized regulator with data covering the mission dose and dose rate, and I'd verify the post-irradiation output accuracy against the FPGA's requirement with margin. If no suitable rad-hard part exists at that current, I'd consider a rad-hard switching regulator followed by a rad-hard LDO, or a discrete pass-element design with a radiation-tolerant reference and error amplifier. I'd also add monitoring — a voltage supervisor on the 1.2V rail that can flag or reset if the rail leaves the FPGA's window — so that a drift or transient is detected rather than silently corrupting operation. And I'd want the FPGA's own power-on and brown-out behavior understood, because the FPGA may have its own requirements that the regulator has to meet during ramp.

**Possible follow-ups:**
- How would you evaluate the regulator if it had radiation data but only for a higher dose rate than your mission?
- What would you do if the only rad-hard option at 3A had significantly worse transient response than the COTS part?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that work is an asset — I want to engage with the analysis, not dismiss the conclusion. So I'd start by asking them to walk through their assumptions: what environment they sized for, what data they used, what margin they applied, and what failure modes they considered. Often the disagreement is not about the conclusion but about an input — a dose number, a derating factor, a datasheet parameter that doesn't include radiation. Making the assumptions explicit turns a disagreement about conclusions into a shared examination of inputs, which is much more productive.

If the gap is a missing consideration — say, they sized for TID but didn't account for SETs, or they used pre-irradiation parameters — I'd frame it as "here's a case I don't think this covers" rather than "you're wrong." I'd ask them to evaluate that case and come back with their assessment. That keeps ownership with them and makes the review a technical exercise rather than a verdict.

If after that we still disagree, I'd want the decision to be made on evidence, not authority. That might mean pulling in radiation data, asking for a test, or bringing in a second reviewer. If the schedule doesn't allow a test, I'd document the residual risk and the rationale for whichever path we take, so the decision is traceable. And I'd be open to being wrong — if their analysis holds up, I should say so. The goal is the right design, not winning the review.

**Possible follow-ups:**
- What if the engineer's approach is technically defensible but you still believe the risk is too high for the mission?
- How would you handle it if the same disagreement came up again in a later review with a different engineer?