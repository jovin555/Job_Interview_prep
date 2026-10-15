# high-speed-digital-fpga — Day 86

## Q1: How would you approach designing the decoupling network for an FPGA's core voltage rail, where the rail supplies a large, fast-changing current to the fabric and must stay within a tight tolerance across a broad frequency range?

**Answer:** The core rail's decoupling problem is fundamentally about impedance versus frequency, not about simply placing "enough" capacitors. The goal is to keep the impedance of the power distribution network below a target value — roughly the allowable ripple voltage divided by the worst-case transient current — across the frequency band where the FPGA draws its dynamic current.

I would approach it in layers. At the highest frequencies (tens to hundreds of MHz), the on-die and package capacitance dominates, and the board's job is to not get in the way: small-value, low-ESL capacitors placed as close as physically possible to the FPGA's power pins, with short, wide traces and vias that connect directly to the plane. At mid frequencies (hundreds of kHz to tens of MHz), bulk ceramic capacitors distributed around the device handle the bulk of the transient energy. At lower frequencies (below the regulator's bandwidth), the VRM itself and larger bulk capacitors take over.

The key insight is that the network must be designed as a whole, not as a pile of parts. Capacitors of the same value in parallel create a sharp anti-resonance with the plane inductance, so I would use a spread of values and, more importantly, low-ESL geometries (reverse-geometry or wide-body parts) to flatten the impedance curve. I would model the network — plane capacitance, via inductance, capacitor ESL/ESR, and the VRM's output impedance — and simulate the impedance versus frequency to confirm there are no peaks above the target. Then I would verify with a VNA measurement on the assembled board, injecting a small signal and measuring the rail impedance, before committing to production.

**Possible follow-ups:**
- How would you decide how many capacitors of each value to place, and where?
- What would you do if the measured impedance showed a peak at a frequency where the FPGA's current draw is significant?

## Q2: How would you approach debugging an FPGA design where the device configures successfully and runs correctly for a period of time, but then the configuration appears to be lost — the device stops responding and requires a reconfiguration to recover?

**Answer:** This is a class of failure where the design is functionally correct at power-up but something degrades over time. I would treat it as a systematic investigation across three domains: power, thermal, and configuration integrity.

First, I would instrument the board to capture the state at the moment of failure. Is the DONE pin still asserted? Is the INIT_B pin toggling? Is the device's internal temperature within spec? If DONE drops, the configuration memory has been disturbed or the device has entered an error state. If DONE stays high but the design stops responding, the issue may be in the application logic or a clock that has stopped.

Second, I would look at the power rails. A marginal rail — one that is within tolerance at room temperature but drifts or becomes noisy as the device heats up — can cause the configuration memory to lose integrity or the internal PLLs to lose lock. I would monitor the rails with a scope during the failure, looking for droop, ripple, or transient events that correlate with the failure.

Third, I would consider whether the configuration memory itself is being corrupted. In some devices, radiation or electrical noise can flip configuration bits. If the failure is random and not correlated with a specific operation, this becomes more likely. I would check whether the device has a CRC error detection mechanism and whether it is reporting errors. If so, I would enable it and log the error.

Finally, I would look at the board-level environment: is there a thermal issue causing a solder joint or via to become intermittent? Is there a mechanical or vibration-related cause? The fact that the device recovers only after reconfiguration suggests the configuration memory is the affected element, so I would focus there first.

**Possible follow-ups:**
- How would you distinguish between a configuration memory corruption and a logic failure?
- What design practices would you put in place to make the system recover automatically from this kind of failure?

## Q3: How would you approach designing the clock domain crossing for a multi-bit Gray-coded counter value that increments continuously in a fast domain (e.g., 250 MHz) and must be sampled by a slower domain (e.g., 50 MHz) for logging, where the sampled value must always be a coherent snapshot and never a corrupted mix of bits?

**Answer:** The Gray code is the key enabler here, because only one bit changes between consecutive values. That property means that even if the sampling clock edge arrives while the counter is transitioning, at most one bit is in flight, and the sampled value will be either the old value or the new value — never a corrupted mix. This is fundamentally different from a binary counter, where multiple bits can change simultaneously and a metastable sample could produce an arbitrary value.

The design approach is to register the Gray-coded value in the source domain, then pass it through a two-flop synchronizer in the destination domain. Because the value is Gray-coded, the synchronizer only needs to resolve a single bit, and the worst case is that the destination sees the value one count late — which is acceptable for a logging application where the exact sample instant is not critical.

However, there is a subtlety: the synchronizer must be applied to the entire bus, and the destination must sample all bits simultaneously. If the bus is wide, the routing skew between bits can cause the destination to capture a mix of old and new values even with Gray coding, because the bits arrive at slightly different times. To mitigate this, I would either keep the Gray-coded bus narrow enough that skew is manageable, or use a handshake-based transfer where the source asserts a valid signal and the destination acknowledges, ensuring the data is stable when captured. For a continuously incrementing counter, a handshake adds latency and complexity, so the Gray-code-plus-synchronizer approach is usually preferred, with careful attention to matching trace lengths and using a single synchronizer register for the whole bus.

I would also verify the design with a formal CDC checker or a CDC-aware lint tool, and simulate with injected skew and metastability models to confirm the destination never captures an invalid value.

**Possible follow-ups:**
- What would you do if the counter were binary instead of Gray-coded?
- How would you verify that the synchronizer is actually resolving metastability correctly in simulation?

## Q4: How would you approach mitigating via stub effects on a high-speed serial channel that must transition between the top and bottom layers of a thick backplane?

**Answer:** A via stub is the unused portion of a via barrel that extends beyond the layer where the signal enters or exits. At high frequencies, that stub acts as a resonant transmission line, causing a notch in the channel's frequency response and degrading signal integrity — particularly at the data rates where the stub's electrical length approaches a quarter wavelength.

The first approach is to avoid the stub entirely by using blind or buried vias, where the via only connects the layers it needs to and does not extend through the entire board. This is the cleanest solution but adds cost and fabrication complexity, so it is usually reserved for the most critical channels.

If through-vias are required, the next approach is back-drilling: after plating, the unused portion of the via barrel is mechanically drilled away from the bottom of the board, leaving only the portion needed for the signal layers. This shortens the stub and pushes its resonance above the frequency band of interest. The depth of back-drilling must be controlled carefully — too little leaves a stub, too much can damage the via or the connection.

A third approach is to use a via design that minimizes the stub's impact: smaller via diameter, shorter stub length by routing the signal on layers closer to the bottom, or using a "via-in-pad" or "via with a smaller capture pad" to reduce the stub's capacitance. In some cases, a compensating structure — such as a small inductor or a tuned stub — can be added to cancel the stub's effect, but this is a narrowband fix and is difficult to implement reliably.

I would model the via in a 3D electromagnetic solver, extract the S-parameters, and simulate the channel with the stub included to see the impact on eye height and jitter. Then I would compare the options — back-drilling, blind vias, or layer reassignment — against the cost and manufacturing constraints, and choose the approach that meets the channel's requirements with the least risk.

**Possible follow-ups:**
- How would you decide how deep to back-drill a via?
- What are the trade-offs between blind vias and back-drilling for a high-volume production board?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** I would treat this as a teaching moment rather than a confrontation, because the engineer's reasoning is a common and understandable mistake — it comes from thinking about the signal in terms of its logical value rather than its timing relative to the destination clock.

First, I would acknowledge that the signal may indeed be stable for a long time in the current design, and that the engineer's observation is not unreasonable. Then I would explain the underlying issue: the destination clock is asynchronous to the source, so the signal can change at any time relative to the destination clock edge. If the signal changes near the setup or hold window of the destination register, the register can enter a metastable state — its output may be neither a clean high nor a clean low, and it may resolve to either value, or oscillate, before settling. The fact that the signal is stable "long enough" in nominal conditions does not guarantee it will be stable at the moment the destination clock samples it, especially across process, voltage, and temperature variations.

I would then walk through the standard solution: a two-flop synchronizer for a single-bit signal, or a handshake or FIFO-based scheme for a multi-bit bus. I would explain that the synchronizer does not eliminate metastability — it reduces the probability of it propagating to an unacceptable level by giving the first flop time to resolve before the second flop samples it.

To make the point concrete without being condescending, I would suggest we simulate the design with a metastability model or run it through a CDC lint tool, and look at the results together. If the tool flags the path, that is objective evidence that the design needs to change. I would also make sure the engineer understands that this is a standard part of high-speed design, not a personal failing, and that catching it in review is exactly what the review process is for.

Finally, I would follow up by making sure the team has a checklist or guideline for CDC handling, so that this class of issue is caught earlier in the design process rather than in review.

**Possible follow-ups:**
- How would you handle it if the engineer pushed back and insisted the signal was fine?
- What would you do if you found this issue after the board was already manufactured?