# high-speed-digital-fpga — Day 61

## Q1: How would you approach designing the termination scheme for a high-speed differential pair carrying a multi-gigabit serial signal between two boards, and how would you decide between AC and DC coupling?

**Answer:** I'd start by identifying the signaling standard and the DC bias requirements of both the transmitter and receiver, because that decision drives almost everything else. For a multi-gigabit serial link, the pair is a controlled-impedance transmission line, so the termination must match the differential characteristic impedance (typically 100 Ω differential, 50 Ω single-ended to the reference plane) to absorb the wave and prevent reflections. In most modern transceiver-based links, the receiver already provides on-die differential termination, so the board-level design is mainly about not adding stubs or discontinuities that would degrade the match — I'd avoid placing discrete termination resistors unless the standard or the receiver requires them, since extra pads and vias create impedance bumps.

For AC vs DC coupling: I'd use AC coupling when the two ends have different common-mode voltages or different supply domains, which is common between boards or between a transmitter and a receiver that don't share a ground-referenced bias. AC coupling also blocks any DC offset and protects against ground-potential differences between boards. The series capacitors must be placed with attention to their own parasitics — they need to be small enough in package and pad to not create a discontinuity, and their value must be large enough that the low-frequency content of the signal (especially for protocols with long run-lengths or DC-balanced encoding) isn't attenuated. I'd check the protocol's coding scheme: 8b/10b or 64b/66b encoding keeps the DC content low, so a modest coupling cap works, but a protocol with long runs of identical bits needs more care.

I'd use DC coupling when both ends share a compatible common-mode and the standard requires it — for example, some memory or chip-to-chip interfaces where the DC level carries information or where the receiver expects a specific bias. DC coupling avoids the capacitor discontinuity but requires the two ends to agree on common-mode, which is harder across a connector and cable.

The other things I'd verify: the termination is placed as close to the receiver as the layout allows, the return path is continuous under the pair (no splits in the reference plane), and the connector and any AC-coupling caps are chosen for the frequency band of interest, not just DC continuity. I'd also confirm the link budget — insertion loss, connector loss, and any via transitions — against the transceiver's equalization capability.

**Possible follow-ups:**
- How would you decide the AC-coupling capacitor value, and what would you check to make sure it doesn't degrade the eye at the data rate?
- If the two boards have a significant ground-potential difference, how does that affect your choice, and what else would you do to protect the link?

## Q2: How would you approach stack-up design for a board that carries both high-speed serial links and a DDR memory interface, and what are the key trade-offs?

**Answer:** The stack-up is where a lot of signal integrity problems are either prevented or baked in, so I'd treat it as a first-class design decision rather than a default from the fab. The main goals are: controlled impedance for every high-speed net, a continuous reference plane under each high-speed layer, enough copper for power delivery, and a symmetric construction so the board doesn't warp during reflow.

A typical approach is a multi-layer stack with signal layers referenced to adjacent ground planes. For high-speed serial links, I want the differential pairs on a layer adjacent to a solid ground plane, with the pair geometry (trace width, spacing, dielectric thickness) chosen to hit the target differential impedance. For DDR, the single-ended nets (address/command, data) need their own controlled impedance — often 40–50 Ω single-ended — and the data/address groups should be referenced to a plane that gives a clean return path. If DDR and serial links share a layer, I'd keep them in separate regions and make sure the reference plane under each is continuous; a split in the reference plane under a high-speed net is one of the most common causes of EMI and signal degradation.

Key trade-offs:
- **Layer count vs. cost and manufacturability.** More layers give more routing freedom and better reference-plane continuity, but add cost and stack-up complexity. I'd start from the routing density and the number of high-speed interfaces, then add layers until every high-speed net has a clean reference.
- **Dielectric material.** Standard FR-4 is fine for lower-speed DDR and moderate serial rates, but at higher frequencies the loss tangent and dielectric constant variation matter more. I'd consider a low-loss material for the highest-speed layers if the link budget is tight, but that increases cost and can complicate the stack-up symmetry.
- **Plane assignment.** Ground planes are the reference for high-speed signals; power planes are for delivery. I'd avoid using a power plane as the reference for a high-speed net unless the return path is well-controlled, because the return current has to flow somewhere and a power plane can create unwanted coupling.
- **Via transitions.** Every layer change is a via, and a via stub on a thick board can create a resonance that hurts high-speed signals. I'd keep high-speed signals on as few layers as possible and use back-drilling or blind/buried vias where the stub would be a problem.

I'd also define the stack-up early enough that the PCB designer and I agree on the impedance targets and the reference planes before routing starts, because changing the stack-up after routing is expensive.

**Possible follow-ups:**
- How would you verify the stack-up's impedance targets before the board is fabricated?
- If the board is space-constrained and you can't give every high-speed net its own reference plane, how would you prioritize?

## Q3: How would you approach debugging an FPGA design where the timing analysis reports all constraints met, but the design fails in hardware only at the maximum specified operating temperature?

**Answer:** This is a classic case where the static timing analysis is telling you one story and the silicon is telling you another, so I'd treat it as a discrepancy between the model and the physical device. The first thing I'd do is confirm the failure is real and repeatable — is it a hard failure at a specific temperature, or intermittent? Is it one board or several? That tells me whether I'm chasing a design margin issue or a manufacturing/process variation issue.

Assuming it's a design margin issue, the most likely culprits are:
- **Timing margin that's too thin.** Timing analysis reports the worst-case corner, but if the design is only marginally passing, temperature-dependent effects (carrier mobility, interconnect resistance) can push it over. I'd look at the slack report and identify the paths with the least margin — not just the ones that fail, but the ones that are close. A path with a few picoseconds of slack at the nominal corner can fail at temperature.
- **Clock uncertainty and jitter.** The timing analysis uses a jitter model, but if the actual clock source or the clock network has more jitter than modeled, the effective margin shrinks. I'd check the clock generation (PLL/MMCM settings, reference clock quality) and whether the jitter budget is realistic.
- **I/O timing.** If the failure involves an external interface, the FPGA's I/O timing (setup/hold, output valid) may be marginal at temperature, especially if the external device's timing also shifts. I'd check the interface timing budget against the device datasheets at the temperature extremes.
- **On-chip variation and voltage.** Temperature and voltage interact; if the core voltage is at the low end of its tolerance and the temperature is high, the device is at its slowest corner. I'd verify the power supply is within spec at temperature and that the design was analyzed at the correct corner.

My debugging approach would be: reproduce the failure in a controlled way (thermal chamber or controlled heating), then use the FPGA's internal debug resources — integrated logic analyzer, timing analyzer, or a soft error monitor — to see which signal or path is failing. If I can't observe it directly, I'd add instrumentation to the design (counters, status registers) to narrow down where the failure occurs. I'd also compare the failing board against a known-good board at the same temperature to see if it's a design issue or a board-specific issue.

If the root cause is insufficient margin, the fix is usually to add pipeline stages to the critical path, relax the clock frequency, or improve the clock quality — not to just re-run timing analysis and hope. I'd also revisit the constraints to make sure the analysis is actually modeling the worst case, because a constraint error can make a marginal design look like it passes.

**Possible follow-ups:**
- How would you distinguish between a timing margin issue and a temperature-dependent analog issue (e.g., a power supply or reference drifting)?
- What would you change in the design flow to catch this kind of margin issue before hardware?

## Q4: How would you approach designing the clock domain crossing for a control/status register that is written by a slow serial interface and read by a fast logic domain, where the register value must never be observed in a partially updated state?

**Answer:** The core requirement is atomicity: the fast domain must see either the old value or the new value, never a mix of bits from both. The right approach depends on whether the register is a single bit, a multi-bit value that changes as a unit, or a set of independent bits.

For a single-bit control signal, a two-flop synchronizer in the destination domain is the standard solution — it handles metastability by giving the first flop a full clock cycle to resolve before the second flop samples it. The trade-off is latency: the signal takes two destination clock cycles to propagate, which is usually fine for a control register.

For a multi-bit value that must be updated atomically, a two-flop synchronizer per bit is not sufficient, because the bits can be captured on different cycles and the destination can see a transient mixed value. The common solutions are:
- **Handshake-based transfer.** The source domain asserts a "valid" signal, the destination domain synchronizes it, captures the data, and asserts an "acknowledge" back to the source. The data bus itself is held stable until the handshake completes, so the destination always samples a coherent value. This is robust and works for any bus width, at the cost of latency and some control logic.
- **Gray coding.** If the value changes monotonically (e.g., a counter), gray coding ensures only one bit changes per increment, so a synchronizer per bit can't produce a mixed value. This is elegant but only applies to specific data patterns.
- **Asynchronous FIFO.** If the register is part of a stream of values, an async FIFO with gray-coded pointers handles the crossing and the buffering together. This is more logic but scales well.

For a status register that's read by the fast domain, I'd also consider whether the read needs to be coherent across multiple registers. If the fast domain reads several registers that are updated together, I'd either use a single handshake to latch a snapshot, or use a double-buffered scheme where the source writes to a shadow register and then transfers the whole set atomically.

The other considerations: I'd make sure the source domain holds the data stable long enough for the destination to capture it (the handshake guarantees this), and I'd add a synchronizer on the handshake signals themselves. I'd also verify the design with a CDC checker or formal tool, because these bugs are hard to catch in simulation — they depend on timing relationships that RTL simulation doesn't model.

**Possible follow-ups:**
- How would you verify that the CDC is correct, given that RTL simulation doesn't model metastability?
- If the register is updated frequently and the fast domain reads it often, how would you handle the case where the fast domain misses an update?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA board. A junior engineer has proposed a clocking scheme that you believe will cause jitter problems, but they've run simulations that show it working and are confident in their approach. How do you handle the situation?

**Answer:** I'd start by making sure I understand their reasoning before I push back, because there's a real chance they've considered something I haven't, and a design review is more productive when it's a technical discussion rather than a verdict. I'd ask them to walk me through the clocking scheme, what simulations they ran, and what assumptions those simulations make. Simulations are only as good as their models — if the simulation doesn't include the jitter of the actual clock source, the phase noise of the PLL, or the board-level effects, then "it works in simulation" doesn't tell us much about the real board.

Once I understand their approach, I'd explain my concern in concrete terms: what specifically I think will cause jitter, why, and what the consequence would be. If I can point to a datasheet spec, an application note, or a known failure mode, that's more useful than a general "I've seen this go wrong." I'd also try to find a way to test the concern rather than just argue about it — for example, asking them to run a simulation that includes the jitter model, or to build a small test case that isolates the clock path.

If we still disagree after that, I'd treat it as a risk-management decision rather than a "who's right" decision. I'd ask: what's the cost of being wrong? If the clocking scheme is hard to change later (e.g., it's baked into the PCB layout), the risk is high, and I'd want more evidence before committing. If it's easy to change, we can try their approach and measure it. I'd also consider whether there's a middle ground — for example, adding a test point or a provision for an alternative clock source that we can populate if needed.

Throughout, I'd keep the tone collaborative. The goal isn't to win the argument; it's to get the design right. If the junior engineer turns out to be correct, I'd say so clearly and explain what convinced me. If I turn out to be correct, I'd explain the reasoning so they learn from it. Either way, the review should leave the team with a better understanding of the trade-off, not just a decision.

**Possible follow-ups:**
- How would you handle it if the engineer felt you were overruling them based on experience rather than evidence?
- If the clocking scheme is already committed to the PCB and you discover the jitter problem late, how would you approach the recovery?