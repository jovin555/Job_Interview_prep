# high-speed-digital-fpga — Day 85

## Q1: How would you approach designing the clock domain crossing for a multi-bit Gray-coded counter value that increments continuously in a fast domain (e.g., 250 MHz) and must be sampled by a slower domain (e.g., 50 MHz) for logging, where the sampled value must always be a coherent snapshot and never a corrupted mix of bits?

**Answer:** The key insight is that a Gray code guarantees only one bit changes per increment, so a single-bit synchronizer per bit is sufficient to avoid incoherent multi-bit captures — but only if the code is genuinely Gray-coded and the counter increments by exactly one per source clock. I would structure it as follows:

1. **Source side:** Maintain the counter in binary for arithmetic, but convert to Gray code combinationally (or maintain a parallel Gray register) so the value presented to the synchronizer is always Gray. The conversion is `gray = bin ^ (bin >> 1)`.
2. **Synchronizer:** Pass each Gray bit through a two-flop synchronizer clocked by the destination domain. Because only one bit changes per source clock edge, at most one synchronizer output can be metastable at any sampling instant, and after the second flop it resolves to either the old or new value — never a mix.
3. **Destination side:** Convert the synchronized Gray value back to binary (`bin[i] = gray[i] ^ bin[i+1]`, MSB down) for use in the destination logic.
4. **Constraint:** Add `set_max_delay -datapath_only` (or the tool's equivalent) on the synchronizer input path so the timing engine doesn't try to meet a single-cycle setup across the two domains, and mark the synchronizer flops with the appropriate `ASYNC_REG` attribute so they're placed close together and not retimed.

The critical caveats: this only works if the counter increments by one per source clock. If the counter can jump (e.g., a preset load, or a multi-bit increment), the Gray guarantee is broken and you need a handshake or a FIFO instead. Also, the destination must tolerate the value being one increment stale — which is fine for logging, but not for control.

**Possible follow-ups:**
- What happens if the source counter is reset or preset-loaded while the destination is sampling it, and how would you handle that?
- How would you verify in simulation that the CDC is correct, given that metastability itself isn't modeled in RTL?

## Q2: How would you approach mitigating via stub effects on a high-speed serial channel that must transition between the top and bottom layers of a thick backplane?

**Answer:** A via stub is the unused portion of a plated through-hole below the layer where the signal enters or exits. At multi-gigabit rates, that stub behaves as a resonant transmission-line branch, producing a notch in the channel's insertion loss at a frequency set by the stub's electrical length (roughly `f_notch ≈ c / (4 · L_stub · √εr)`). On a thick backplane, a stub of even a few millimeters can push the notch into the band of interest and close the eye.

Approaches, roughly in order of preference:

1. **Back-drilling (controlled-depth drilling):** After plating, re-drill the unused portion of the via barrel from the opposite side to remove the stub. This is the standard production solution for thick backplanes. The remaining stub is typically specified as a maximum (e.g., a few hundred microns), and the drill depth tolerance must be accounted for in the stack-up so the back-drill doesn't nick the layer the signal actually uses.
2. **Blind/buried vias:** If the stack-up allows, use vias that only span the layers needed, eliminating the stub entirely. This costs more in fabrication but is common on high-layer-count backplanes where the signal only needs to go a short distance.
3. **Via-in-pad / microvia transitions:** For the FPGA escape region, microvias from the surface to the first internal layer can avoid long barrels altogether.
4. **Layer assignment:** Route the high-speed channel on layers close to the top or bottom of the stack-up so the stub is inherently short, and reserve the middle layers for slower signals.

I would verify the choice by extracting the via with a 3D field solver (or the fabricator's via model) and running the full channel — package, via, connector, trace — through an eye-diagram simulation with the actual transmitter's pre-emphasis and the receiver's equalization settings. If the notch is unavoidable, the receiver's CTLE/DFE may compensate, but I'd rather remove the stub than rely on equalization to fix a resonance.

**Possible follow-ups:**
- How does back-drill depth tolerance affect the impedance of the remaining via, and how would you specify it to the fabricator?
- At what data rate does via stub mitigation stop being optional and become mandatory, and what drives that threshold?

## Q3: How would you approach designing the reset architecture for a high-speed FPGA design that contains multiple clock domains, a DDR memory controller, and high-speed transceiver links, where an improperly sequenced reset can leave the device in a non-functional state?

**Answer:** Reset architecture is one of the most under-designed parts of a high-speed FPGA, and most "works on my bench, fails in the field" bugs trace back to it. I would approach it in layers:

1. **Define reset domains explicitly.** Every clock domain gets its own reset, and the reset for a domain must be synchronous to that domain's clock (asynchronous assert, synchronous deassert — the standard reset synchronizer). This prevents recovery/removal violations when the reset releases.
2. **Establish a reset tree, not a reset net.** A single global reset that fans out to every domain will release at slightly different times in each domain due to routing and synchronizer latency. For blocks that talk to each other (e.g., the DDR controller and the fabric logic that feeds it), the reset release order matters. I would define a dependency graph: transceiver and PLL lock first, then the memory controller, then the application logic that uses them.
3. **Use PLL/MMCM lock as a gating condition.** The reset for a domain should not release until its clock source is locked and stable. A common failure is logic coming out of reset before the PLL has locked, so it runs on a glitchy or absent clock and ends up in an undefined state.
4. **Transceiver reset sequencing.** Transceivers have their own reset and initialization sequence (per the vendor's requirements), often involving a `reset_done` handshake. The fabric logic that consumes the transceiver's recovered clock and data must not release until the transceiver signals it's ready.
5. **DDR controller reset.** The memory controller typically has its own initialization and calibration sequence that must complete before the fabric issues transactions. The reset architecture should expose a "controller ready" signal that gates the application logic's access.
6. **Watchdog / recovery.** For a system that must recover from a hung state, include a watchdog that can assert a global reset and re-run the sequence. The watchdog itself must be in a domain that's guaranteed to be running.

I would document the reset tree as a diagram with explicit dependencies and release conditions, and verify it in simulation by forcing each reset to release in the wrong order and confirming the design either recovers or fails safe — not silently.

**Possible follow-ups:**
- How would you verify the reset architecture in simulation, given that reset release timing is often not modeled accurately in RTL?
- What's the difference between a reset synchronizer and a reset bridge, and when would you use each?

## Q4: How would you approach debugging an FPGA design where the timing analysis reports that all constraints are met, but the design fails in hardware only when the device is operated at the maximum specified junction temperature?

**Answer:** A design that passes static timing analysis but fails only at high junction temperature is almost always a case of the analysis not reflecting reality. I would work through the possibilities systematically:

1. **Confirm the failure is real and repeatable.** Is it a specific data pattern, a specific interface, or a specific block? Does it correlate with a temperature threshold, or is it probabilistic above a certain temperature? This narrows the search enormously.
2. **Check the timing corners.** Static timing analysis is only as good as the corners it was run at. If the design was signed off at a typical corner but not at the worst-case (slow-slow, high-temperature, low-voltage) corner, the reported "all constraints met" is meaningless. Re-run timing at the full set of corners the device is specified for, including the temperature derating on the I/O and the on-chip variation.
3. **Suspect the I/O timing.** At high temperature, the I/O buffers slow down and the setup/hold windows on source-synchronous interfaces (DDR memory, ADC/DAC interfaces) shift. If the design relies on the FPGA's internal timing being met but the board-level skew between the forwarded clock and data is marginal, it can pass at room temperature and fail hot. Check the input/output delay constraints against the actual board skew and the device's temperature-derated I/O timing.
4. **Suspect the clock network.** PLL/MMCM jitter and phase noise increase with temperature. If a CDC or a high-speed interface has marginal timing margin, the added jitter can push it over. Check the clock's phase noise at temperature and whether the design's margin accounts for it.
5. **Suspect the power delivery.** At high temperature, the device draws more leakage current, and the PDN's impedance may be higher than modeled. A marginal rail can cause timing failures that look like logic errors. Measure the rails at temperature with a scope and a wideband probe.
6. **Suspect the silicon itself.** Some failures at temperature are not timing at all — they're marginal cells, or a configuration memory bit that's temperature-sensitive. If the failure is a single bit or a single block, this becomes more likely.

The practical debugging sequence: reproduce at temperature, then use the device's internal debug resources (ILA, transceiver eye scan, temperature sensor) to see where the failure occurs, and compare against a room-temperature capture. If the failure is in a specific interface, re-run the timing analysis at the hot corner and look for the path with the least margin.

**Possible follow-ups:**
- How would you set up a temperature-corner timing analysis, and what derating factors would you apply?
- If the failure turns out to be a marginal I/O timing issue, what are your options for fixing it without a board respin?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** This is a teaching moment, not a confrontation. The engineer's reasoning is a common and understandable mistake — "it works in simulation" is not the same as "it's correct," and the failure mode (metastability) is probabilistic and may not show up until the design is in the field.

My approach:

1. **Acknowledge the reasoning, then separate the two questions.** The engineer is answering "does it work?" I want to redirect to "is it guaranteed to work?" Those are different questions, and the second is the one that matters for a design that ships.
2. **Explain the failure mode concretely.** Metastability isn't a logic error you can see in RTL simulation — it's a physical phenomenon where the receiving flop's output can be indeterminate for a setup/hold violation, and the resolution time is unbounded. The probability of failure per event is small, but over millions of events and across temperature and voltage variation, it becomes a real field failure rate. The fact that the signal is "stable long enough" in the source domain doesn't help — the receiving flop samples it at an arbitrary phase relative to its own clock, and the violation window is what matters.
3. **Show the fix, not just the problem.** Walk through the standard solution: a two-flop synchronizer for a single-bit level signal, a pulse synchronizer or handshake for a pulse, and a proper CDC structure (Gray code, handshake, or async FIFO) for multi-bit data. If the signal is a control signal that's only asserted for a known duration, a pulse synchronizer with a toggle handshake is often the right answer.
4. **Make it a review action, not a blame item.** Add it to the review checklist: every signal crossing a clock domain boundary must be identified and either synchronized or explicitly justified. This turns a one-off correction into a process improvement.
5. **Follow up.** After the review, check that the fix is in and that the engineer understands the general principle, not just this instance. If they're receptive, this is a good opportunity to have them present the CDC methodology to the rest of the team — teaching it reinforces the learning.

The tone matters: the goal is a correct design and a better engineer, not a "gotcha." A junior engineer who feels attacked will hide the next mistake; one who feels coached will bring it up early.

**Possible follow-ups:**
- How would you structure a design review checklist to catch CDC issues before they reach hardware?
- What would you do if the engineer pushed back and insisted the signal was fine because it had been running on the bench for weeks without a failure?