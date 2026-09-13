# high-speed-digital-fpga — Day 54

## Q1: How would you approach designing the reference clock input path for an FPGA transceiver bank, where the reference clock must meet a tight phase-noise specification and the source oscillator is located several centimeters away on the same board?
**Answer:** The reference clock path is a jitter-budget problem before it is a layout problem, so I'd start by writing down the budget: the transceiver's maximum allowable reference-clock jitter (usually specified as an RMS phase jitter over a defined integration band), the oscillator's own phase noise, and the jitter the path itself will add. That tells me how much margin I have to spend on the routing.

Practically, I'd treat the reference clock as a controlled-impedance single-ended or differential trace (depending on the oscillator output and the FPGA's reference input standard), route it as a 50 Ω (or 100 Ω differential) line, keep it short and direct, and reference it to a solid ground plane with no plane splits under it. Any split in the return path forces the return current to detour, which creates a loop that both radiates and picks up noise — that directly degrades phase noise.

I'd avoid vias if at all possible; if a layer change is unavoidable, I'd use a via with a ground return via placed close by, and I'd keep the stub length minimal. I'd also keep the clock trace away from switching supplies, high-current digital buses, and any switching node, because coupling from those sources shows up as spurs in the phase-noise plot rather than as broadband noise.

If the oscillator is a fair distance away, I'd consider whether a clock buffer or a re-driver with low additive jitter is warranted, and whether the oscillator should instead be placed closer to the FPGA. I'd also confirm the FPGA's internal clock management tile (PLL/MMCM) can accept the reference frequency and that its own jitter contribution is accounted for — the MMCM doesn't remove jitter, it filters some of it and adds its own.

For verification, I'd ask for a phase-noise measurement at the FPGA reference input pin (not at the oscillator output), because that's the number that actually matters, and I'd compare it against the transceiver's specification with margin.

**Possible follow-ups:**
- How would you decide between using the oscillator directly versus inserting a jitter-attenuating clock cleaner?
- What layout changes would you make if the phase-noise measurement showed a spur at a switching-supply frequency?

## Q2: How would you approach debugging an FPGA design where the device configures successfully and runs correctly, but the configuration appears to be lost after some time — the device stops responding and requires a reconfiguration to recover?
**Answer:** This is a "configuration integrity" problem, and I'd separate it into three candidate causes before touching anything: the configuration memory itself being disturbed, the device being reset or re-triggered by something external, and the device losing power or a critical rail momentarily.

First, I'd check whether the device is actually losing configuration or just appearing to. The `INIT_B` and `DONE` pins are the primary evidence — if `INIT_B` has gone low, the device has detected a configuration error and is re-initializing. If `DONE` is still high but the design is unresponsive, the configuration is intact and the problem is elsewhere (a hung state machine, a clock that stopped, a PLL that lost lock). Those are very different investigations, so I'd instrument both pins and capture them on a scope or logic analyzer with a long time base.

If `INIT_B` is dropping, I'd look at the configuration source: is the flash being read correctly, is the bitstream CRC failing intermittently, is there a brownout on the configuration bank's supply? A marginal supply rail that dips during a high-current event elsewhere on the board can cause a partial reconfiguration or a CRC failure. I'd also check whether the configuration clock is clean and whether the flash's access timing has margin across temperature.

If `DONE` stays high but the design hangs, I'd look at the clocking: a PLL losing lock, a reference clock dropping out, or a reset that never deasserts. I'd also consider whether the design has entered an illegal state that it can't recover from — which is a design robustness issue, not a configuration issue.

The key discipline is to not assume "configuration lost" until the pins prove it, because the two failure modes have completely different root causes and different fixes.

**Possible follow-ups:**
- How would you distinguish a brownout-induced reconfiguration from a bitstream CRC error using only board-level measurements?
- What design practices would you add to make the system recover gracefully from a transient configuration loss?

## Q3: How would you approach designing the clock domain crossing for a status/control register that is written by a slow serial interface (e.g., a few MHz SPI) and read by a fast logic domain, where the register value must never be observed in a partially updated state?
**Answer:** The core requirement is atomicity of the multi-bit value, not just metastability avoidance. A simple two-flop synchronizer per bit prevents metastability but does not guarantee that all bits arrive in the same destination clock cycle — if the source bits change on different edges relative to the destination clock, the destination can sample a mix of old and new bits. That's the classic multi-bit CDC hazard, and it's exactly what "never partially updated" rules out.

The standard robust approach is a handshake or a data-valid scheme. The writer places the new value in a holding register, then asserts a single-bit "update" or "valid" signal. That single bit is synchronized into the destination domain with a two-flop synchronizer (or a proper synchronizer cell if the device provides one). The destination domain, on seeing the synchronized valid, captures the entire multi-bit value in one clocked operation. Because the data is stable before the valid is asserted and remains stable until the destination has captured it, the destination always sees a coherent word.

An alternative is a dual-clock FIFO if the register is really a stream of updates, but for a single register the handshake is simpler and has bounded, predictable latency.

I'd also consider the reverse direction if the fast domain needs to acknowledge back to the slow domain — a full handshake (request/acknowledge) gives clean flow control and avoids the writer overwriting the value before the reader has consumed it. If the writer can update faster than the reader can consume, I'd add a small buffer or a "latest value wins" policy with an explicit overflow indication, rather than silently dropping updates.

For verification, I'd use a CDC lint tool and, if available, formal verification of the synchronizer structure, plus a directed simulation that deliberately skews the source and destination clocks to try to catch a partial update.

**Possible follow-ups:**
- How would you decide between a handshake and a dual-clock FIFO for this register?
- What would change if the register were updated continuously rather than occasionally?

## Q4: How would you approach verifying that a high-speed FPGA design's timing constraints are complete and correct before sign-off, given that missing or incorrect constraints can produce a design that passes timing analysis but fails in hardware?
**Answer:** The fundamental problem is that timing analysis only proves what you told it to prove. A design with no constraints, or with over-permissive constraints (false paths, multicycle paths that aren't actually multicycle, clocks that aren't declared), will report "timing met" while containing real violations. So the verification effort is about proving the constraint set is complete and correct, not just that the tool is happy.

I'd start by enumerating every clock in the design — every input clock, every PLL/MMCM output, every generated clock, every forwarded clock — and confirming each is declared with the correct frequency, phase relationship, and source. Undeclared clocks are the most common source of false "timing met" results, because paths between an undeclared clock and a declared one are often not analyzed at all.

Next I'd audit every exception: every `set_false_path`, `set_multicycle_path`, and `set_max_delay`/`set_min_delay`. Each one is a claim that a path doesn't need to meet normal timing, and each one needs a justification. A false path on a path that actually carries data is a latent hardware failure. I'd want to see the justification documented and, ideally, the path's actual behavior confirmed in simulation or by a CDC analysis tool.

I'd also verify the I/O constraints: input and output delays, board-level skew, and the relationship between the FPGA's clocks and the external device's clocks. These are frequently wrong because they depend on board-level information that the FPGA designer may not have.

Then I'd cross-check with a CDC analysis tool, which catches structural issues (unsynchronized crossings, multi-bit crossings without proper synchronization) that timing analysis doesn't address. I'd also run the design through a lint tool for clock and reset issues.

Finally, I'd do a "constraint review" as a formal design-review item, with the constraint file treated as a deliverable that gets the same scrutiny as the RTL. The goal is to have a reviewer who didn't write the constraints ask "why is this a false path?" for every exception.

**Possible follow-ups:**
- How would you catch a missing clock constraint that the tool didn't flag?
- What's your approach to reviewing I/O timing constraints when the board-level skew is not well characterized?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?
**Answer:** I'd treat this as a teaching moment rather than a confrontation, because the engineer's reasoning is a very common and understandable mistake — they're thinking about the signal's logical stability, not its timing relative to the destination clock.

First, I'd acknowledge the part they got right: if the signal really is stable for many destination clock cycles, the probability of a metastable event is low. But "low probability" is not "no probability," and in a medical or safety-critical context, a single missed or corrupted control signal can have serious consequences. I'd explain that the issue isn't whether the signal is stable, it's whether the destination flip-flop's setup and hold windows are respected relative to the destination clock. If the source signal changes near the destination clock edge, the destination flip-flop can go metastable, and the resulting value is indeterminate — it may resolve to 0, to 1, or oscillate before settling, and downstream logic can see different values on different paths.

Then I'd walk through the standard fix: a two-flop synchronizer for a single-bit signal, which gives the metastable event a full clock cycle to resolve before the value is used. For a multi-bit signal, a two-flop synchronizer per bit is not sufficient — that's a separate discussion about handshakes or FIFOs.

I'd also point out that the CDC analysis tool would flag this, and that the design review's job is to catch exactly this kind of issue before it reaches hardware. I'd frame the fix as a small, well-understood addition, not a redesign, so the engineer doesn't feel their work is being dismissed.

Finally, I'd follow up by asking them to add the synchronizer and to run the CDC tool to confirm no other crossings were missed. The goal is that they internalize the principle, not just fix this one instance.

**Possible follow-ups:**
- How would you handle it if the engineer pushed back and said the synchronizer adds latency the design can't afford?
- What would you do if the CDC tool flagged several similar issues elsewhere in the design?