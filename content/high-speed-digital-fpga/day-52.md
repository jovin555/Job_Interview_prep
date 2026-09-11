# high-speed-digital-fpga — Day 52

## Q1: How would you approach bringing up a multi-rail FPGA design where the configuration bitstream loads successfully but the device never asserts its "ready" or "init done" handshake to the rest of the system, and the failure is intermittent across boards?

**Answer:** I'd treat this as a bring-up sequencing and handshake-integrity problem rather than a configuration problem, since the bitstream itself clearly loads. The first thing I'd do is separate the two possible failure classes: the FPGA genuinely isn't reaching its internal ready state, or it is reaching it but the handshake signal isn't being observed correctly by the downstream logic.

For the first class, I'd check the power sequencing and reset architecture. Many FPGAs require rails to come up in a specific order and require the configuration reset to be released only after all rails are stable and the PLL/MMCM has locked. If the ready signal is gated on a PLL lock that is marginal, some boards will lock and some won't, which matches the intermittent behavior. I'd scope the rails and the lock signal simultaneously on a passing and a failing board and compare ramp rates and lock timing.

For the second class, I'd look at how the ready signal crosses from the FPGA's internal clock domain to whatever domain the downstream logic uses. If it's a single-bit level signal crossing into an asynchronous domain without proper synchronization, it can be missed or metastable depending on phase alignment — which is exactly the kind of thing that varies board to board. I'd verify there's a proper two-flop synchronizer or a handshake protocol, and that the signal isn't being sampled before the destination domain's clock is running.

I'd also check whether the ready signal is being driven from configuration logic that depends on an external component — for example, a DDR calibration or a transceiver reset that must complete first. If that dependency exists, the "ready" is really "ready after calibration," and calibration marginality would explain the intermittency.

The systematic approach: reproduce on a known-failing board, instrument both the internal state (via a debug core or spare I/O) and the external handshake, and bisect whether the failure is upstream (FPGA not ready) or downstream (handshake not observed). Then fix the root cause — sequencing, synchronization, or calibration margin — rather than masking it with a longer timeout.

**Possible follow-ups:**
- How would you distinguish a genuine PLL lock failure from a lock signal that's being sampled too early?
- If the ready signal is a single bit crossing domains, what specific synchronization structure would you require, and why isn't a simple two-flop synchronizer always sufficient for a level signal?

## Q2: How would you approach designing the reset architecture for a high-speed FPGA design that contains multiple clock domains, a DDR memory controller, and high-speed transceiver links, where an improperly sequenced reset can leave the device in a non-functional state?

**Answer:** Reset architecture in a multi-domain design is really a sequencing and synchronization problem, and I'd design it deliberately rather than letting each block reset itself independently.

The core principle is that every reset must be synchronized to the clock domain it resets, and resets must be released in an order that respects dependencies. Asynchronous assertion with synchronous de-assertion is the standard pattern: assert the reset immediately when the source asserts (so the block is held in reset regardless of clock state), but release it synchronously to the destination clock so that all flops in that domain come out of reset on the same clock edge. This avoids the classic problem where different flops exit reset on different cycles and the block briefly sees an inconsistent state.

For sequencing, I'd define the dependency order explicitly. Typically: power rails stable → reference clocks stable → PLLs/MMCMs locked → global resets released → per-domain resets released → high-speed links and memory controller brought up → application logic enabled. The DDR controller and transceivers usually have their own internal calibration or training sequences that must complete before the logic that uses them is allowed to run, so their "ready" outputs should gate the release of the downstream resets.

I'd implement this as a small reset controller — either in fabric or using the device's dedicated reset resources — that takes the external reset, the lock signals, and the calibration-done signals as inputs, and produces per-domain synchronized resets as outputs. The controller itself should be robust: if a PLL loses lock, it should re-assert the dependent resets rather than leaving the design running on a bad clock.

I'd also make sure there's a way to observe the reset state during bring-up — spare I/O or a debug core that shows which domains are held in reset — because "the design doesn't work" is much easier to debug when you can see which reset is still asserted.

**Possible follow-ups:**
- Why is asynchronous assertion with synchronous de-assertion preferred over fully synchronous reset for a domain whose clock may not be running yet?
- How would you handle a PLL that loses lock transiently — should the design re-reset, and how would you avoid a reset loop?

## Q3: How would you approach debugging an FPGA design where the transceiver link passes its built-in PRBS checker at the physical layer, but application-level data is occasionally corrupted, and the corruption only appears at full line rate?

**Answer:** This is a classic case where the physical layer is healthy but something above it is not, and the fact that it only appears at full line rate is the key clue — it points to a timing, buffering, or flow-control issue rather than a signal integrity problem.

The PRBS checker validates the serial deserializer and the analog front end, but it typically runs on a fixed pattern and doesn't exercise the fabric-side datapath, the clock domain crossing between the recovered clock and the fabric clock, or the flow control. So I'd focus there.

First, I'd check the clock domain crossing between the transceiver's recovered/user clock and the fabric clock. If the design uses a FIFO to cross between them, I'd verify the FIFO depth is adequate for the worst-case phase and frequency difference, and that the FIFO's flags are being used correctly — an overflow or underflow that happens rarely would produce exactly this symptom. I'd also check whether the FIFO is being reset or flushed correctly at link startup.

Second, I'd look at flow control. At full line rate, if the receiver can't sustain the throughput — because the fabric logic is backpressured, because the FIFO is too shallow for the burst behavior, or because the credit/ready handshake has a bug — data will be dropped or overwritten. I'd instrument the FIFO's almost-full and almost-empty flags and the flow-control signals, and see whether they correlate with the corruption.

Third, I'd check the datapath itself for width mismatches or endianness issues that only manifest when the data is moving fast enough to expose a race. A common one is a signal that's used combinationally in one place and registered in another, so it's correct at low rate but wrong when the pipeline is full.

The systematic approach: reproduce at full rate, capture the corrupted data and the surrounding control signals with a debug core, and determine whether the corruption is a dropped word, a duplicated word, a bit error, or a reordering. Each points to a different root cause — dropped/duplicated suggests FIFO or flow control, bit errors suggest a datapath timing issue, reordering suggests a multi-lane skew or a FIFO read/write pointer bug.

**Possible follow-ups:**
- How would you size the CDC FIFO between the transceiver clock and the fabric clock, and what determines the minimum depth?
- If the corruption turns out to be a single bit flip that only occurs at full rate, how would you determine whether it's a fabric timing issue or a transceiver issue?

## Q4: How would you approach verifying that a high-speed FPGA design's timing constraints are complete and correct before sign-off, given that missing or incorrect constraints can produce a design that passes timing analysis but fails in hardware?

**Answer:** Timing sign-off is only as good as the constraints, so I'd treat constraint completeness as a first-class verification activity, not an afterthought.

The starting point is a constraint review against the design's actual clock and I/O structure. I'd enumerate every clock in the design — every PLL/MMCM output, every external clock input, every recovered clock from a transceiver — and confirm each has a create_clock or create_generated_clock constraint with the correct period, and that the relationships between them (synchronous, asynchronous, or exclusive) are declared correctly. A missing generated clock is one of the most common causes of a design that "meets timing" but doesn't work, because the tool has no idea the clock exists.

Next, I'd review the I/O constraints. Every input and output needs a set_input_delay or set_output_delay relative to its clock, with values derived from the external device's timing requirements and the board's flight time. If these are missing or wrong, the internal timing can be clean while the interface fails at the board level. I'd cross-check the values against the datasheets of the external components and the board's trace delays.

Then I'd review the exceptions — false paths, multicycle paths, and clock groups. These are where incorrect constraints hide, because they tell the tool to ignore paths that may actually need to meet timing. I'd require that every exception be justified in writing, with a reference to the design intent, and I'd be especially suspicious of false paths on anything that crosses a clock domain or feeds a control signal. A false path on a real path is exactly the failure mode described in the question.

I'd also use the tool's own reporting to find gaps: unconstrained paths, unconstrained endpoints, and clocks with no timing relationship defined. Many tools will report these, and they should be driven to zero or explicitly waived with justification.

Finally, I'd validate the constraints against the hardware where possible — running the design at the target frequency and temperature, and using the on-chip debug or a test pattern to confirm the interfaces actually work. Constraints that pass static timing but fail on hardware are a signal that the constraints, not the design, are wrong.

**Possible follow-ups:**
- How would you decide whether a path between two clocks should be a false path, a multicycle path, or a properly timed synchronous path?
- What would you do if the tool reports a large number of unconstrained paths but the design works on hardware — is that acceptable?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** I'd handle this as a teaching moment first and a design correction second, because the engineer's reasoning is a common and understandable misconception, and the goal is to make sure they understand why it's wrong — not just to fix this one instance.

I'd start by acknowledging the part that's true: if the signal really is stable for many cycles of the destination clock, the probability of capturing it incorrectly is low. But "low probability" is not "never," and in a high-speed design running for hours or days, low-probability events happen. I'd explain the two distinct problems: metastability, where the destination flop can enter an unstable state if the setup/hold window is violated, and the more insidious problem of multi-bit signals, where different bits can be captured on different cycles, producing a value that was never valid. For a single-bit level signal, a two-flop synchronizer addresses metastability but not the fundamental issue that the signal may be sampled at an arbitrary point relative to its transitions.

I'd then ask the engineer to walk me through the timing: what is the source clock, what is the destination clock, what is the relationship between them, and what is the worst-case timing of the signal relative to the destination clock edge? Often, working through this themselves is more convincing than being told. If the clocks are asynchronous, there is no "stable long enough" guarantee that holds across all phase relationships and all process/voltage/temperature corners.

For the fix, I'd work with them to choose the right structure: a two-flop synchronizer for a single-bit level signal, a pulse synchronizer or handshake for a pulse, or a proper CDC FIFO or handshake for multi-bit data. I'd also point them at the design's CDC verification — whether the tooling flags unsynchronized crossings — and make sure this instance gets caught by that check in the future.

Throughout, I'd keep the tone collaborative. The engineer isn't being careless; they're applying intuition that works at low speed to a high-speed problem. The review's job is to surface that and turn it into a learning point for the whole team, not to single anyone out.

**Possible follow-ups:**
- How would you decide between a two-flop synchronizer, a handshake, and a CDC FIFO for a given signal?
- What would you do if the engineer pushed back and said the design has been running for weeks without a problem?