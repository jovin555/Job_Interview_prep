# space-rad-hard — Day 57

## Q1: How would you approach designing a radiation-tolerant analog multiplexer front-end for a space-deployed system, where a single-event transient (SET) on the mux select lines could route the wrong sensor channel to a precision ADC and trigger an incorrect control action?

**Answer:** The core problem is that the mux select lines are digital control signals that directly determine which analog channel reaches the ADC, so a transient on those lines is not just a data error — it is a routing error that can feed a completely wrong physical quantity into a control loop. I would approach it in layers.

First, treat the select lines as safety-critical digital signals and protect them at the source: latch the select word in a register that is itself protected (TMR or at minimum a redundant register with a comparator), and only update it on an explicit, validated command. A transient that flips a bit in a single unprotected register is the most likely failure mode, so redundancy there removes most of the exposure.

Second, add temporal validation at the ADC. After every channel switch, discard the first sample or two — this is standard settling practice anyway, but it also gives any SET-induced glitch on the select lines time to clear before a measurement is trusted. Then compare the new reading against a plausibility window derived from the previous reading and the known rate of change of that sensor. A sudden jump to a value consistent with a different channel's range is a strong signature of a mis-route, and the firmware can reject it and re-issue the channel select.

Third, consider the analog side. A mux with break-before-make switching and a defined off-state is preferable, because a transient that momentarily selects two channels can otherwise short two sensor sources together. If the mux has an enable pin, gate it so that the channel is only enabled after the select lines have settled and been validated.

Finally, for the most critical measurement, I would consider not multiplexing it at all — give it a dedicated ADC channel or a dedicated ADC. Redundancy in the signal path is often cheaper than trying to make a shared mux perfectly immune.

**Possible follow-ups:**
- How would you distinguish a genuine fast sensor transient from an SET-induced mis-route, given that both look like a sudden change in reading?
- If the mux select lines are driven directly from an FPGA I/O bank, what additional protection would you add at that interface?

## Q2: How would you approach derating and part selection for a space-deployed board, and how does derating interact with the radiation tolerance you are trying to achieve?

**Answer:** Derating and radiation tolerance are two separate reliability levers, and the mistake is to treat them as substitutes. Derating addresses the intrinsic, statistical failure modes of a part — voltage, current, power, junction temperature, and so on — by keeping the part well inside its rated limits so that wear-out and random failure rates stay low. Radiation tolerance addresses the environment-induced failure modes: TID-induced parameter drift, SEE, displacement damage. A part can be perfectly derated and still fail in a day from latch-up, and a rad-hard part can still fail from overstress if you run it at its absolute maximum ratings.

My approach to derating starts with a derating standard — typically a project- or agency-specific table derived from MIL-STD-1547 or similar — and applies it per part class: resistors, capacitors, semiconductors, connectors. For semiconductors, the big ones are junction temperature (often derated to something like 110°C or lower for a 125°C-rated part), voltage (typically 70–80% of rated), and power. For capacitors, voltage derating is critical, and for electrolytics you also worry about ripple current and lifetime. I would build the derating into the schematic capture and layout review checklists so it is verified, not assumed.

The interaction with radiation is where it gets interesting. TID causes parametric drift — leakage currents rise, gain drops, reference voltages shift, timing margins shrink. If a part is already derated to, say, 70% of its voltage rating, it has more headroom to absorb that drift before it leaves its functional window. So derating buys you margin against TID-induced drift. Conversely, a part that is derated aggressively but has no radiation data is still a risk, because derating does nothing for a latch-up or a destructive single-event burnout. And some radiation effects — ELDRS in bipolar parts, for example — are not mitigated by derating at all.

So the practical rule is: derate for the intrinsic reliability, then separately qualify or select for the radiation environment, and check that the derated operating point still leaves margin after the expected TID drift. The two analyses have to be done together, not sequentially.

**Possible follow-ups:**
- How would you handle a part that meets your derating requirements but has only a total-dose rating and no SEE data?
- Where does derating interact with thermal design in a vacuum, where there is no convection?

## Q3: You are reviewing a design for a space-deployed system that uses a COTS FPGA for data processing. The design uses external configuration memory (flash) that is not radiation-hardened. How would you evaluate the risk of configuration upsets and what mitigation strategies would you recommend?

**Answer:** The first thing I would do is separate the two distinct failure modes: upsets in the FPGA's own configuration SRAM, and upsets in the external flash that holds the bitstream. They have different probabilities, different consequences, and different mitigations.

For the FPGA configuration SRAM, the risk is that a single-event upset flips a configuration bit and changes the function of the logic — potentially creating a short, a stuck state, or a functional interrupt. The standard mitigations are configuration scrubbing (periodically rewriting the configuration from a known-good source, or using the FPGA's built-in frame ECC if it has it) and, for the most critical logic, TMR in the fabric. I would want to know the device's configuration memory size, its measured or estimated upset rate, and whether the vendor provides a scrub controller or whether we have to build one.

For the external flash, the risk is different: the stored bitstream itself can be corrupted, so even a full reconfiguration from flash loads a bad image. This is the more insidious failure because it survives a power cycle. Mitigations here include storing the bitstream with error-detecting or error-correcting coding, keeping a second copy in a separate device or a separate region, and validating the bitstream (CRC or hash) before loading it. If the primary image fails validation, fall back to the secondary. I would also consider whether the flash is read-only in flight — if the application never writes to it, the upset rate is lower than for a device that is being erased and rewritten.

Beyond that, I would look at the system-level recovery path. If the FPGA does enter a bad configuration, can the system detect it — for example, through a heartbeat or a functional self-test — and recover by reconfiguring from a validated source? A watchdog that only resets the FPGA is not enough if the flash is corrupt; you need a fallback image.

The key point I would make in the review is that "TMR on the fabric" is not a complete answer. TMR protects the logic against upsets during operation, but it does nothing for the configuration memory or the stored bitstream. You need scrubbing, bitstream integrity checking, and a recovery path.

**Possible follow-ups:**
- How would you decide between scrubbing frequency and the overhead it imposes on the FPGA's operation?
- If the flash is a single point of failure, how would you architect the fallback without doubling the board area?

## Q4: How would you approach designing a fault-tolerant communication bus for a space-deployed system where multiple sensor nodes must reliably report data to a central controller, and single-event upsets (SEUs) can corrupt individual messages?

**Answer:** The starting point is to assume that any individual message can be corrupted, and design the protocol so that corruption is detected and recovered from rather than silently accepted. That means every message carries a checksum or CRC strong enough to catch the expected error patterns — a simple parity bit is not enough for a bus that may see multi-bit upsets. I would size the CRC to the message length and the acceptable undetected-error rate.

Detection alone is not enough; you need a recovery strategy. For periodic telemetry, the simplest approach is retransmission on CRC failure, with a bounded retry count so a persistently failing node does not monopolize the bus. For time-critical data, retransmission may not be acceptable, so you need either a redundant transmission (send the same measurement twice on separate frames and compare) or a forward-error-correction scheme that can reconstruct the message without a retry.

At the protocol level, I would add sequence numbers or a rolling counter so the controller can detect dropped, duplicated, or out-of-order messages. This also helps distinguish a corrupted message from a lost one. For a shared bus, I would also think about arbitration and lock-up: a single node that is upset and starts transmitting continuously can block the bus. A timeout-based arbitration scheme, or a bus master that can force a node off the bus, prevents one failed node from taking down the whole system.

At the physical layer, the choice of bus matters. A differential bus like RS485 or CAN-FD has good common-mode noise rejection, which helps against SET-induced transients on the bus lines themselves. If the nodes are in different radiation environments, I would also consider whether the transceivers need to be rad-tolerant or whether the protocol can tolerate a transceiver that occasionally produces a bad bit.

Finally, I would design the controller to be tolerant of missing data. If a node fails to report, the controller should have a defined degraded mode rather than treating the absence as a fault that shuts down the system. The overall principle is: detect corruption, recover where possible, and degrade gracefully where recovery is not possible.

**Possible follow-ups:**
- How would you handle a node that is upset in a way that makes it report plausible but incorrect data, which passes the CRC?
- What trade-offs would you consider between a shared bus and a point-to-point star topology for this kind of system?

## Q5: You are leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I would do is separate the technical question from the interpersonal one. The engineer has done real work, and that deserves respect — the goal is not to win the argument but to make sure the design is right. So I would start by making sure I understand their reasoning. It is entirely possible they have considered something I have not, or that they are working from a different assumption about the environment or the mission profile. I would ask them to walk me through their margin analysis: what environment are they designing to, what part data are they using, and how did they arrive at the margin they have?

If, after that, I still believe the margin is insufficient, I would try to make the disagreement concrete and evidence-based rather than a matter of opinion. That means framing it in terms of the specific failure mode and the specific consequence: for example, "if this part sees a latch-up at the expected rate, the rail collapses and we lose the payload — here is the data I am basing that on." I would also be explicit about what would change my mind: if they can show me radiation data or a derating analysis that closes the gap, I am open to it.

If we still disagree, I would not resolve it by pulling rank in the room. I would propose a path forward: either a targeted test or analysis to settle the question, or a design change that adds margin without a major cost, or — if the schedule does not allow either — escalating to a broader review with the data laid out. The key is that the decision gets made on evidence, not on seniority.

Throughout, I would keep the tone collaborative. I would acknowledge the work they have done, be specific about my concern rather than vague, and make it clear that the goal is a design that survives the mission, not a design that satisfies me. If the review becomes adversarial, people stop raising concerns, and that is how real problems get missed.

**Possible follow-ups:**
- What would you do if the engineer's approach was actually correct and your concern was based on an outdated assumption?
- How would you handle a situation where the schedule pressure makes a redesign impractical, but the margin concern is real?