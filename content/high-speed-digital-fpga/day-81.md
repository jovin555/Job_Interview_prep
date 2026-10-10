# high-speed-digital-fpga — Day 81

## Q1: How would you approach designing the clock domain crossing for a multi-bit Gray-coded counter value that increments continuously in a fast domain (e.g., 250 MHz) and must be sampled by a slower domain (e.g., 50 MHz) for logging, where the sampled value must always be a coherent snapshot and never a corrupted mix of bits?

**Answer:** The key insight is that a Gray code changes only one bit per increment, so a single-bit metastability event at the sampling boundary can only ever produce a value that is either the old count or the new count — never a wild, unrelated value. That property is what makes Gray coding the right encoding choice here, and it's why you don't need a full handshake or a multi-cycle synchronizer for this case.

The approach is: encode the counter in the fast domain as Gray code (binary-to-Gray conversion is a simple XOR of adjacent bits), then pass each bit through a two-flop synchronizer in the slow domain. Because only one bit can be in transition at any given sampling edge, the worst case is that the slow domain captures either the pre-transition or post-transition value — both are valid, coherent snapshots. After synchronization, convert back from Gray to binary in the slow domain for display or logging.

The trade-offs to be aware of: Gray coding only works cleanly for counters that increment or decrement by one. If the counter can jump by arbitrary amounts, or if it's a free-running counter that wraps, you need to make sure the wrap also only changes one bit — a standard binary wrap from all-ones to all-zeros changes many bits, so you either use a Gray-coded wrap (which is possible but requires care) or you accept that the wrap is a special case. Also, the slow domain will see the count lag by a few slow clock cycles due to the synchronizer latency, which is usually fine for logging but matters if the value is used for control.

For verification, I'd simulate with the synchronizer modeled with metastability injection (or at least with random delay on the first flop) and check that the slow-domain value is always either the old or new count, never an intermediate. I'd also run a formal CDC check if the tool supports it, to confirm that no multi-bit path exists without proper synchronization.

**Possible follow-ups:**
- What if the counter must also be able to reset or load an arbitrary value — how does that change the scheme?
- How would you handle the case where the slow domain needs to detect that the counter has wrapped, not just read its current value?

## Q2: How would you approach debugging an FPGA design where the DDR3 memory interface passes its built-in calibration and memory test at power-up, but fails intermittently only after the device has been running for several minutes and the board has warmed up?

**Answer:** This is a classic temperature-dependent timing margin problem, and the fact that it passes at power-up but fails after warm-up strongly suggests that one or more timing parameters are marginal and drift with temperature. The first step is to characterize the failure precisely: does it fail at a specific temperature, or gradually? Does it correlate with a particular access pattern (e.g., long bursts, specific bank interleaving)? Does it happen on all boards or only some?

From there, I'd approach it in layers. At the physical layer, I'd check whether the failure correlates with the memory's temperature-dependent timing parameters — tREFI (refresh interval) shortens at high temperature, and if the controller isn't issuing refreshes fast enough, you can get data retention failures. I'd also look at the FPGA's I/O timing: the output delay and input setup/hold windows shift with temperature, and if the calibration was done at power-up (cold) and not re-run, the delay taps may no longer be optimal. Many DDR3 controllers support periodic re-calibration or temperature-compensated delay tracking — if that's available, enabling it is a strong candidate fix.

At the board level, I'd check whether the termination scheme is adequate across temperature. ODT resistors and the FPGA's on-die termination have temperature coefficients, and if the effective termination drifts, reflections can grow. I'd also check the power supply: DDR3 VDD and VTT rails can drift with temperature, and if the VTT regulator is marginal, the input threshold shifts.

For diagnosis, I'd use the FPGA's built-in eye scan or margin analysis (many vendors provide a way to sweep the input delay and measure the passing window). If the eye is closing at temperature, that tells you it's a timing margin issue rather than a logic bug. I'd also run the memory test at elevated temperature in a chamber, with the ability to log which addresses fail — if failures cluster in a particular bank or row, that points to a specific signal or a refresh issue.

The fix depends on the root cause: re-calibration, adjusting the refresh rate, improving termination, or adding margin to the board layout. The key is to not just "make it pass" but to understand which parameter is marginal and why.

**Possible follow-ups:**
- How would you distinguish between a memory-side issue (DRAM retention) and an FPGA-side issue (I/O timing) without swapping parts?
- What would you change in the bring-up procedure to catch this kind of marginality before it reaches production?

## Q3: How would you approach designing the return-current path for a high-speed digital board where a signal transitions between two reference planes (e.g., from a ground plane to a power plane) on its way through a via?

**Answer:** The fundamental principle is that every high-speed signal has a return current that follows the path of least impedance — at high frequency, that's the path of least inductance, which means the return current flows on the reference plane directly beneath (or above) the signal trace. When the signal transitions from one reference plane to another through a via, the return current must also transition, and if there's no low-inductance path for it to do so, the return current will find a long, inductive path — which creates a discontinuity, radiates, and degrades signal integrity.

The standard solution is to place a stitching capacitor (or a set of them) between the two reference planes, close to the signal via. The capacitor provides a low-inductance path for the return current to jump from one plane to the other. The capacitor value isn't critical for high-frequency return — what matters is the loop inductance, so you want a small, low-ESL capacitor (e.g., 0201 or 0402) placed as close as possible to the via, with short, wide traces to the planes. In practice, you often use multiple capacitors in parallel to reduce the effective inductance.

The alternative — and often better — approach is to avoid the plane transition altogether by keeping the signal on the same reference plane for its entire route. If the signal must change layers, you can sometimes route it so that the reference plane is the same (e.g., both layers reference the same ground plane) even if the signal layer changes. If the stack-up forces a reference change, then the stitching capacitor is the mitigation.

There's also the question of whether the two planes are at the same DC potential. If you're transitioning from ground to a power plane, the stitching capacitor also provides AC coupling between them, which is fine for return current but means you need to be careful about the capacitor's voltage rating and placement. In some cases, you can use a via farm (multiple ground vias) if the two planes are both ground — but if they're different nets, you need the capacitor.

For verification, I'd simulate the via transition in a 3D field solver (or use the vendor's via model) to see the impedance discontinuity, and I'd check the return path in the layout review — specifically, that every high-speed via that changes reference planes has a nearby stitching capacitor or a via to the same net. I'd also look at the plane splits: if the return current has to cross a split in the plane, that's a similar problem, and the fix is to stitch across the split or reroute.

**Possible follow-ups:**
- How would you decide how many stitching capacitors to use, and where exactly to place them?
- What's the difference in return-path behavior between a signal via that transitions from ground to ground versus ground to power?

## Q4: How would you approach choosing between a global clock network and a regional/banked clock resource for a logic block that only needs to run at a modest rate, when the device's global clock resources are nearly exhausted?

**Answer:** The decision comes down to a few factors: the clock's fan-out and span, the required skew and jitter performance, and the resource cost. Global clock networks are designed to reach every flip-flop in the device with minimal skew and controlled jitter, but they're a scarce resource — typically a handful per device. Regional or banked clock networks only reach a portion of the device (a clock region or a set of I/O banks), but they're more plentiful and often have lower insertion delay within their region.

If the logic block is confined to a single clock region — for example, a small state machine or a data path that only talks to I/O in one bank — then a regional clock is usually the right choice. It frees up a global clock for something that genuinely needs to span the whole device, like a system clock or a DDR controller clock. The regional clock will have slightly different skew characteristics, but for a modest-rate block that's usually irrelevant.

The trade-offs to watch: if the logic block needs to communicate with logic in another region, and that communication is synchronous to the same clock, then using a regional clock means the clock has to be routed to both regions — which may not be possible with a regional resource, or may require a global clock after all. Also, some regional clock networks have restrictions on how they can be driven (e.g., only from specific clock-capable pins or MMCM outputs), so you need to check the device's clocking resources.

Another consideration is clock domain crossing: if the regional clock is a different frequency or phase from the main system clock, you've created a CDC boundary, and you need to handle it properly. If the block is truly independent and only needs to run at a modest rate, that's fine — but it's a design decision that should be made deliberately, not as an afterthought.

In practice, I'd start by mapping out the clocking requirements: which clocks need to reach which parts of the device, what the frequency and jitter requirements are, and how many global clock resources are available. Then I'd allocate global clocks to the most demanding or widest-spanning clocks, and use regional clocks for localized, lower-demand blocks. If the global resources are nearly exhausted, I'd look for clocks that can be consolidated (e.g., two clocks that are always the same frequency and phase could potentially be merged) or moved to regional resources.

**Possible follow-ups:**
- What are the implications for timing analysis if a clock is on a regional network versus a global network?
- How would you handle a situation where a block initially assigned to a regional clock later needs to communicate with logic in another region?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** This is a situation where the engineer's reasoning is superficially plausible but fundamentally flawed, and the stakes are high because an unsynchronized CDC can cause intermittent, hard-to-reproduce failures that may not show up until the board is in the field. My approach would be to treat it as a teaching moment, not a confrontation.

First, I'd acknowledge the engineer's point: yes, if the signal is stable for many cycles of the destination clock, the probability of a metastability event is low. But "low probability" is not "zero," and in a system that runs for years, low-probability events become certainties. I'd explain that the issue isn't whether the signal is stable long enough in the typical case — it's what happens when the timing is marginal, which can occur due to temperature, voltage, or process variation. A single metastable capture can propagate through the design and cause a failure that's nearly impossible to debug.

Then I'd walk through the correct solution: a two-flop synchronizer for a single-bit control signal, or a handshake or FIFO for multi-bit data. I'd explain why the two-flop synchronizer works — the first flop may go metastable, but the second flop gives the metastable output time to resolve before it's used. I'd also point out that the synchronizer needs to be placed correctly (both flops in the destination domain, with the first flop's input coming directly from the source domain) and that the signal should be treated as asynchronous in the timing constraints (e.g., a false path or a dedicated CDC constraint).

I'd also use this as an opportunity to review the rest of the design for similar issues. If one CDC was missed, there may be others. I'd suggest running a CDC lint check or a formal CDC verification tool to catch any other unsynchronized crossings. And I'd make sure the team has a clear guideline: any signal that crosses a clock domain boundary must be synchronized, and the synchronization scheme must be documented and reviewed.

Finally, I'd follow up with the engineer after the review to make sure they understand the reasoning and can apply it independently. The goal is not just to fix this one instance, but to build the team's ability to catch these issues themselves.

**Possible follow-ups:**
- How would you handle it if the engineer pushed back, arguing that the synchronizer adds latency that the design can't afford?
- What would you do if you discovered this issue after the board had already been manufactured and deployed?