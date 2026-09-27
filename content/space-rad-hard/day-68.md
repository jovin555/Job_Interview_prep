# space-rad-hard — Day 68

## Q1: How would you approach designing a radiation-tolerant analog signal chain for a spacecraft instrument where the sensor output is a low-level differential signal, and both the amplifier front-end and the ADC reference can experience single-event transients (SETs)?

**Answer:** The core problem is that a low-level differential signal has very little amplitude headroom, so any transient that couples into the front-end or shifts the reference is a large fraction of the measurement. I'd start by separating the two failure paths — front-end SETs and reference SETs — because the mitigations differ.

For the front-end, the goal is to make the amplifier's output recover quickly and predictably rather than to prevent the transient entirely, since you generally can't. That means choosing an amplifier topology with a well-defined overload recovery characteristic, keeping the gain distributed across two stages rather than one high-gain stage (so a transient in the first stage isn't amplified by the full gain), and adding a passive RC or differential filter between stages to limit the transient's bandwidth. I'd also consider whether the amplifier can be biased so that a transient drives it toward a benign rail rather than into a latch-prone region.

For the reference, the key insight is that a reference SET is a common-mode error across the whole conversion, so it can't be rejected by differential signal conditioning. Mitigations include a large reference decoupling network with low ESR and ESL so the reference node can't move quickly, a reference buffer with good transient recovery, and — most importantly — a ratiometric or differential measurement scheme where the reference is sampled alongside the signal so a reference excursion affects both and cancels in the ratio. If the ADC supports it, using the reference as the conversion's own reference in a ratiometric bridge configuration is a strong approach.

At the system level, I'd add plausibility checking: a single SET produces a single outlier sample, so a median filter or a "two of three consecutive samples must agree" rule can reject isolated transients without adding latency that matters for a slow physical process. The trade-off is that this fails if the transient is long enough to span multiple samples, so the filter length has to be matched to the expected SET duration.

**Possible follow-ups:**
- How would you distinguish a genuine fast sensor event from an SET-induced outlier if both look like a single-sample excursion?
- If the reference and the signal share a common supply, how does that change your decoupling strategy?

## Q2: You're reviewing a design for a space-deployed system that uses a COTS linear regulator to generate a 1.2V core voltage for an FPGA. The regulator's datasheet shows no radiation data, and the output voltage is specified as 1.2V ±2%. The FPGA requires 1.2V ±5% and draws up to 3A. How would you evaluate this choice and what alternatives would you recommend?

**Answer:** The first thing I'd note is that the ±2% initial tolerance is not the real problem — it's the radiation behavior that's uncharacterized. A linear regulator's pass element and its internal reference are both susceptible to TID-induced parameter drift and to SETs, and neither is captured by the datasheet. So the question isn't "does it meet spec at time zero" but "does it still meet spec at end of life, and what happens during a transient."

I'd evaluate it in three layers. First, TID: without data, I'd have to assume the reference and error amplifier could drift by some unquantified amount over mission dose, which eats directly into the ±5% window. A ±2% initial tolerance plus uncharacterized drift is not a defensible margin. Second, SETs: a linear regulator's loop can be perturbed by a transient in the pass transistor or reference, producing an output excursion. At 3A load, the output capacitance and the regulator's transient response determine how far the rail moves and how fast it recovers — and if the FPGA's core rail moves outside its operating window, you can get logic errors or a brownout reset. Third, SEL: a linear regulator with a bipolar or CMOS pass element can latch, and at 3A the latch current could be destructive or could drag the upstream rail down.

For alternatives, I'd look at rad-hard or rad-tolerant LDOs with published TID and SEE data, or a rad-hard switching regulator followed by a rad-tolerant post-regulator if the noise budget allows. If no rad-hard part is available at that current, I'd consider a discrete pass element with a rad-hard reference and error amplifier, or a redundant regulator scheme with current sharing and a supervisor that can isolate a failed regulator. I'd also add a voltage supervisor with a tight threshold and a fast response so that any excursion outside the FPGA's window triggers a controlled reset rather than letting the FPGA run on a marginal rail.

**Possible follow-ups:**
- How would you qualify a COTS regulator for this application if you had a limited radiation test budget?
- What's the trade-off between adding a supervisor and simply derating the FPGA's operating frequency to tolerate a wider rail?

## Q3: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a poor fit for a radiation environment for two reasons: it's a shared bus with no inherent error detection beyond the ACK bit, and it has a well-known failure mode where a slave holding SDA low can lock the entire bus. Both of those get worse when SEUs can corrupt a node's state machine.

I'd approach it in layers. At the physical layer, I'd make sure each node's SDA/SCL drivers can be isolated — either with a bus switch or with series elements that let a controller forcibly release a stuck line. The classic recovery is to clock the bus manually until the stuck slave releases SDA, then issue a STOP; I'd design the controller firmware to detect a stuck bus (SDA low with SCL high for longer than a timeout) and run that recovery sequence automatically. I'd also add pull-up sizing that accounts for the total bus capacitance and the number of nodes, because a marginal pull-up makes the bus more susceptible to noise-induced false starts.

At the protocol layer, I'd add a checksum or CRC to every transaction, since the I²C ACK only confirms that a byte was received, not that it was correct. For critical data, I'd use a request/response pattern with a sequence number so a corrupted or duplicated message can be detected. I'd also consider whether the bus needs to be redundant — two independent I²C buses with each node on both, or a primary/secondary bus with a mux — so that a single stuck node doesn't take down all communication.

At the node level, the most important mitigation is a watchdog on each sensor node's I²C state machine so that a node that's been upset into a bad state resets itself rather than holding the bus. And I'd make sure the controller can address nodes individually and can tolerate a non-responding node without blocking the whole bus — timeouts on every transaction, not just on the bus as a whole.

**Possible follow-ups:**
- How would you decide between adding bus redundancy and adding better error detection on a single bus?
- What's the failure mode if the controller itself is the node that gets upset mid-transaction?

## Q4: How would you approach selecting a radiation-hardened voltage reference for a precision ADC in a space application that must maintain accuracy within 0.1% over a 5-year mission, including the effects of TID and ELDRS?

**Answer:** The 0.1% over 5 years is the binding constraint, and it forces me to think about the reference as a system component rather than a part number. The first thing I'd do is decompose the error budget: initial accuracy, temperature coefficient, long-term drift (which is really aging plus radiation), and the effects of the board-level environment (thermal gradients, mechanical stress). Radiation is one term in that budget, and it has to be small enough that the other terms still fit.

For TID, I'd want a reference with published data at the mission dose, and I'd want to know whether that data was taken at high dose rate or low dose rate. ELDRS is the key concern here — many bipolar references show significantly more degradation at low dose rates, which is what a real mission experiences, than at the high dose rates used in typical qualification testing. If the only data available is high-dose-rate, I'd treat it as a lower bound and either test at low dose rate or apply a conservative margin. For a 5-year mission, the total dose might be modest, but ELDRS can still cause parametric shifts at low total dose, so "low dose" doesn't mean "no concern."

For SEE, the reference's output can experience SETs, and the reference's internal trim or bandgap can be affected by SEUs. I'd look for a reference with SET data showing the magnitude and duration of output excursions, and I'd design the decoupling and buffering to limit how far the reference node can move. If the reference is used ratiometrically, an SET affects both the signal and the reference and partially cancels; if it's used absolutely, the SET appears directly in the measurement.

Beyond part selection, I'd design for calibration: a reference that can be periodically compared against an on-board or uplinked standard lets the system track drift over the mission, which is often more practical than trying to guarantee 0.1% open-loop for 5 years. The trade-off is added complexity and the need for a stable calibration source, but for a 5-year mission it's usually worth it.

**Possible follow-ups:**
- How would you structure a low-dose-rate test campaign for a reference if you only have access to a high-dose-rate facility?
- If the reference drifts but the drift is monotonic and slow, how would your calibration strategy differ from a case where the drift is random?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the technical question from the interpersonal one. The engineer has done real work, which means they've thought about the problem and have a model of why their solution works. If I just assert that it's under-margined, I'm asking them to abandon their model without giving them a better one, and that's both unfair and unlikely to work.

So I'd start by asking them to walk me through their margin analysis — specifically, what radiation environment they assumed, what failure modes they considered, and where the margin comes from. Often the disagreement turns out to be about assumptions rather than conclusions: they may have used a benign environment assumption, or considered only SEUs and not SETs, or treated a datasheet number as a guarantee when it's a typical. Making those assumptions explicit is usually more productive than arguing about the conclusion.

If the gap is real, I'd try to frame it as a shared problem rather than a correction. "Here's the failure mode I'm worried about — can you show me how your design handles it?" If they can, I've learned something. If they can't, the gap is now visible to both of us, and the conversation is about how to close it rather than about who's right. I'd also be explicit about the consequence: in a radiation environment, an under-margined design doesn't fail gracefully, it fails in the field, and that's a different kind of cost than a schedule slip.

If we still disagree after that, I'd escalate the decision to data — a test, a calculation, a review by someone with relevant experience — rather than to authority. And I'd make sure the engineer knows that the goal is the right design, not winning the argument. If the decision goes against their proposal, I'd want them to understand why, and I'd want their work to be acknowledged, because the next review depends on them bringing the same level of engagement.

**Possible follow-ups:**
- What would you do if the engineer's analysis is correct but the resulting design is still too risky for the mission?
- How would you handle it if the disagreement became personal or the engineer felt their work was being dismissed?