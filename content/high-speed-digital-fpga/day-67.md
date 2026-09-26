# high-speed-digital-fpga — Day 67

## Q1: How would you approach designing the interface between an FPGA and an external ADC that uses a source-synchronous, double-data-rate (DDR) output bus, where the data and a forwarded clock arrive at the FPGA with an unknown but bounded skew between them?

**Answer:** The core problem is that the forwarded clock and the data travel nominally together, but the skew between them is not zero and is only bounded, not known precisely. So the design has to tolerate that uncertainty rather than assume a fixed alignment.

The first step is to characterize the skew budget. That means accounting for the ADC's own output skew spec, PCB trace-length mismatch between the clock and data lanes, connector and package delays, and the FPGA input buffer's setup/hold requirements. Once I know the total window, I can decide whether the interface can be captured with a simple approach or needs per-lane calibration.

For a DDR source-synchronous bus, the standard approach is to use the FPGA's input delay elements or IDELAY primitives on each data lane, plus a per-bit or per-group training routine. The forwarded clock is typically routed into a clock-capable input pin and used to drive the capture registers, often through a MMCM/PLL to generate a phase-shifted version that centers the sampling point in the data eye. Because the skew is bounded but unknown, I would not hard-code a delay value — I would implement a training sequence where the ADC (or a test pattern) drives a known pattern, and the FPGA sweeps the input delay until it finds the window where the data is captured reliably. The center of that window becomes the operating point.

I would also make sure the design uses the correct I/O standard — likely a differential standard like LVDS or a dedicated source-synchronous standard — and that the input buffers are configured for the right termination. On the PCB side, I would match trace lengths within the skew budget and keep the clock and data referenced to a continuous ground plane.

Finally, I would verify the margin, not just that it works. That means measuring the eye at the FPGA input, checking the setup/hold margin against the datasheet, and confirming the training window is wide enough to survive temperature and voltage variation over the product's life.

**Possible follow-ups:**
- How would you decide between using a per-bit IDELAY versus a per-group delay, and what are the trade-offs?
- What would you do if the training window turned out to be very narrow — say, only a few taps wide?

## Q2: How would you approach debugging an FPGA design where the transceiver link passes its built-in PRBS checker at the physical layer, but application-level data is occasionally corrupted, and the corruption only appears at full line rate?

**Answer:** The fact that the PRBS checker passes tells me the physical layer — the SerDes, the CDR, the equalization — is fundamentally working. The corruption is happening above the physical layer, and it only shows up at full line rate, which points to a timing or flow-control issue rather than a signal integrity issue.

My first instinct would be to look at the boundary between the transceiver's physical coding sublayer and the user logic. Common culprits include: the gearbox or width-conversion logic between the transceiver's internal width and the fabric width, the clock domain crossing between the transceiver's recovered clock domain and the fabric clock domain, and the FIFO or buffer that absorbs the rate mismatch. At full line rate, any marginal timing in those blocks gets exposed; at lower rates, there's enough slack to hide it.

I would start by instrumenting the design to capture the corrupted data and compare it against the expected pattern. If the corruption is a single bit flip, that suggests a timing issue in the parallel data path. If it's a whole word or a burst, that suggests a FIFO overflow/underflow or a CDC issue. I would also check whether the corruption correlates with specific data patterns — a pattern-dependent error often points to crosstalk or a marginal setup/hold in the parallel bus.

Next, I would verify the CDC between the transceiver's clock domain and the fabric domain. If the design uses a simple two-flop synchronizer on a multi-bit bus, that's a red flag — multi-bit buses need a proper handshake or a FIFO. I would also check the FIFO's depth and whether the read/write pointers are being synchronized correctly.

If the design uses the transceiver's built-in gearbox, I would check the configuration — the wrong gearbox ratio or a misconfigured comma alignment can cause occasional word misalignment that only shows up under sustained traffic.

Finally, I would use the transceiver's built-in eye scan or PRBS error injection to confirm the physical layer margin, and then use a logic analyzer or embedded debug core to capture the corrupted data at the application interface. The goal is to narrow down whether the corruption is happening in the transceiver, in the CDC, or in the user logic.

**Possible follow-ups:**
- How would you distinguish between a CDC issue and a FIFO overflow issue if both produce similar symptoms?
- What would you check in the transceiver's configuration if the corruption only happens with certain data patterns?

## Q3: How would you approach designing the return-current path for a high-speed digital board where a signal transitions between two reference planes (e.g., from a ground plane to a power plane) on its way through a via?

**Answer:** The return current for a high-speed signal follows the path of least impedance, which at high frequencies means it flows directly underneath the signal trace on the adjacent reference plane. When the signal transitions from one reference plane to another — say, from a ground plane to a power plane — the return current has to find a way to get from one plane to the other. If there's no provision for that, the return current is forced to take a long, indirect path, which creates a loop inductance that causes signal integrity problems: reflections, crosstalk, and radiated emissions.

The standard solution is to place a stitching capacitor — or a set of them — close to the via where the signal transitions. The capacitor provides a low-impedance path for the return current to jump from one plane to the other. The key is that the capacitor must be placed as close as possible to the signal via, because the return current's path is determined by the geometry — the closer the capacitor, the smaller the loop area, and the lower the inductance.

The value of the stitching capacitor matters less than its placement and its self-resonant frequency. At high frequencies, the capacitor's ESL dominates, so a small, low-ESL capacitor — like an 0201 or 0402 — is usually better than a large one. I would also use multiple capacitors in parallel to lower the effective ESL and to cover a broader frequency range.

An alternative approach is to avoid the plane transition altogether by keeping the signal referenced to the same plane throughout its route. If that's not possible, I would try to ensure that the two planes are already connected by a low-impedance path — for example, if the power plane is decoupled to ground with a capacitor nearby, the return current can use that path. But relying on that is risky; explicit stitching capacitors at the transition point are the safer design.

I would also check the via design itself. A via that transitions between planes creates a stub, and that stub can resonate at high frequencies. I would use back-drilling or blind/buried vias to minimize the stub length, and I would simulate the transition to confirm the impedance is controlled.

**Possible follow-ups:**
- How would you decide how many stitching capacitors to place, and where exactly to place them?
- What would you do if the board stack-up doesn't allow a direct transition between the two planes?

## Q4: How would you approach designing the clock domain crossing for a multi-bit counter value that is continuously incrementing in a fast domain (e.g., 250 MHz) and must be sampled by a slower domain (e.g., 50 MHz) for display or logging, where the sampled value must always be a coherent snapshot and never a corrupted mix of bits?

**Answer:** The fundamental problem is that a multi-bit value is changing continuously in the source domain, and if I just synchronize each bit independently with a two-flop synchronizer, the bits can arrive at different times in the destination domain — so I could sample a value that never actually existed. For a counter, that's especially dangerous because the bits change at different rates, and a mid-transition sample could produce a value that's wildly off.

The standard solution for a continuously changing multi-bit value is to use a handshake or a gray-code-based approach. For a counter specifically, the cleanest approach is to convert the binary count to gray code in the source domain, synchronize the gray-coded value into the destination domain with a two-flop synchronizer per bit, and then convert back to binary. Gray code has the property that only one bit changes between consecutive values, so even if the synchronization is imperfect, the worst case is that the destination sees either the old value or the new value — never a corrupted mix. This is the same principle used in asynchronous FIFOs for the read/write pointers.

The trade-off is that gray code only works cleanly for counters that increment by one. If the counter can jump or decrement, gray code doesn't guarantee single-bit changes, and I'd need a different approach — typically a handshake where the source domain asserts a "data valid" signal, the destination domain acknowledges, and the data is held stable until the handshake completes. That adds latency but guarantees coherency.

For a display or logging application, the latency of a handshake is usually acceptable. But if the value needs to be sampled frequently and the latency is a concern, the gray-code approach is faster because it doesn't require a round-trip handshake.

I would also consider whether the destination domain needs every value or just a snapshot. If it just needs a snapshot, I could use a dual-clock FIFO with the counter value written periodically, or a register that's updated only when the destination is ready to read it.

Finally, I would verify the design with a formal CDC checker or a simulation that injects random skew between the domains, to confirm that the destination never sees a corrupted value.

**Possible follow-ups:**
- What would you do if the counter could increment by more than one, so gray code doesn't guarantee single-bit changes?
- How would you handle the case where the destination domain needs to detect that the counter has wrapped around?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** This is a situation where I need to balance technical correctness with the engineer's development and the team's dynamics. The engineer's reasoning — "the signal is stable long enough" — is a common misconception, and it's my job to help them understand why it's not safe, without making them feel attacked.

I would start by acknowledging that their observation might be true in the specific conditions they tested — the signal might indeed be stable long enough in simulation or on the bench. But I would explain that the problem is not about whether it works today; it's about whether it's guaranteed to work across all conditions: temperature, voltage, process variation, and the full range of timing. A direct connection between clock domains is a metastability risk, and metastability is a probabilistic phenomenon — it might work for millions of cycles and then fail once, and that one failure could be catastrophic in a data acquisition system.

I would then walk through the specific risk: if the signal is captured while it's transitioning, the destination flip-flop can enter a metastable state, and the output can be unpredictable — it might resolve to 0, to 1, or oscillate. A two-flop synchronizer reduces the probability of metastability propagating to an acceptable level, and for a single-bit control signal, that's usually sufficient. If the signal is multi-bit, we'd need a different approach, like a handshake or a FIFO.

I would also emphasize that this is not a criticism of their work — it's a standard design practice, and even experienced engineers sometimes overlook it. I would offer to work with them to add the synchronizer and to review the rest of the design for similar issues.

If the engineer pushed back — for example, arguing that adding a synchronizer adds latency — I would discuss the trade-off. A two-flop synchronizer adds one or two clock cycles of latency, which is usually negligible for a control signal. If the latency is truly a problem, we can explore other options, but we can't skip synchronization entirely.

Finally, I would follow up by making sure the team has a checklist or design guideline for CDC, so this doesn't happen again. The goal is not just to fix this one instance, but to build the team's understanding so they catch these issues themselves in the future.

**Possible follow-ups:**
- How would you handle it if the engineer insisted that the signal is truly asynchronous and doesn't need synchronization because it's "slow"?
- What would you do if you discovered this issue late in the project, when there's pressure to ship?