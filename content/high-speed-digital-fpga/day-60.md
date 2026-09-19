# high-speed-digital-fpga — Day 60

## Q1: How would you approach designing the interface between an FPGA and an external ADC that uses a source-synchronous, double-data-rate (DDR) output bus, where the data and a forwarded clock arrive at the FPGA with an unknown but bounded skew between them?
**Answer:** The core problem is that the forwarded clock and the data lanes leave the ADC with some unknown but bounded skew, and at DDR rates that skew can easily exceed a fraction of a bit period, so a fixed sampling point is not reliable. I would treat this as a per-lane timing-recovery problem rather than a single global capture.

First, I would characterize the interface: what is the forwarded clock frequency, what is the specified skew window between clock and data, and what is the FPGA's input setup/hold window for the chosen I/O standard. That tells me whether the skew budget is small enough to handle with a fixed delay or whether I need dynamic per-lane alignment.

For a source-synchronous DDR interface, the standard approach is to use the FPGA's input delay elements (IDELAY) or the dedicated input registers in the I/O blocks, and to align each data lane's sampling point to the center of its data eye. Because the forwarded clock is the timing reference, I would route it into a global or regional clock-capable input and use it to clock the capture registers, then use per-lane IDELAY taps to shift each data lane into the middle of the eye. The alignment is done at bring-up with a training pattern — typically a PRBS or a known toggling pattern — by sweeping the delay tap and finding the window where the captured data matches the expected pattern. The center of that window is the operating point.

A few practical considerations: I would keep the clock and data traces matched in length on the PCB as a first-order mitigation, but I would not rely on that alone, because the skew budget at DDR rates is usually tighter than what length matching alone can guarantee. I would also make sure the IDELAY reference clock is stable, since the delay tap resolution depends on it. And I would design the training routine to run at every power-up, not just once at the factory, because the optimal delay tap can shift with temperature and voltage.

If the skew is large enough that a single IDELAY range cannot cover it, I would consider whether the ADC supports a training pattern or a delay-locked output, or whether I need to use the FPGA's built-in source-synchronous capture primitives (like ISERDES with bitslip) to do word alignment in addition to bit alignment.

**Possible follow-ups:**
- How would you verify that the chosen delay tap remains valid across the full operating temperature range, and what would you do if the eye window shrinks at temperature extremes?
- What is the difference between using IDELAY for per-lane alignment versus using a PLL to phase-shift the capture clock, and when would you choose one over the other?

## Q2: How would you approach debugging an FPGA design where the transceiver link passes its built-in PRBS checker at the physical layer, but application-level data is occasionally corrupted, and the corruption only appears at full line rate?
**Answer:** The fact that the PRBS checker passes tells me the physical layer — the SerDes, the CDR, the equalization, the clock recovery — is fundamentally working. The corruption is happening above the physical layer, and the fact that it only appears at full line rate narrows it further: it is likely a flow-control, buffering, or clock-domain-crossing issue that only manifests when the link is saturated.

I would start by separating the problem into three layers: the transceiver's own datapath, the logic that moves data between the transceiver and the application, and the application logic itself. The PRBS checker lives inside or immediately adjacent to the transceiver, so it validates the first layer. The corruption is in the second or third.

My first hypothesis would be a CDC or FIFO issue between the transceiver's recovered clock domain and the application clock domain. At full line rate, the FIFO is being exercised at its maximum rate, and any marginal timing, insufficient depth, or incorrect flag synchronization will show up as occasional data loss or reordering. I would check the FIFO's almost-full and almost-empty thresholds, the synchronization of the read/write pointers, and whether the FIFO depth is adequate for the worst-case burst behavior — not just the average rate.

My second hypothesis would be a flow-control or backpressure issue. If the application cannot absorb data at full line rate for brief periods, and the backpressure mechanism is not propagated correctly back to the transceiver, the transceiver's internal buffer will overflow and drop or corrupt data. I would check whether the transceiver's status flags (like overflow or underflow) are being monitored, and whether the application's ready/valid handshake is being respected at all times.

My third hypothesis would be a data-path width or alignment issue that only manifests at full rate — for example, a gearbox or width converter that works at low rates but has a subtle bug when the input is continuously valid. I would look at whether the data path has any assumptions about gaps between packets or idle cycles that are violated at full line rate.

To isolate, I would instrument the design with counters at each stage: transceiver output count, FIFO write count, FIFO read count, application input count. If the counts diverge, I know where the loss is. I would also use the transceiver's built-in error injection and loopback modes to test the datapath in isolation.

**Possible follow-ups:**
- How would you distinguish between a FIFO overflow and a FIFO underflow as the root cause, and what would each tell you about the system?
- If the corruption is a single bit flip rather than a dropped word, how would that change your debugging approach?

## Q3: How would you approach designing the decoupling and bulk capacitance network for an FPGA's transceiver power rails, where the rails have both high-frequency switching noise and slower, larger current transients, and how would you verify the network is adequate before committing to the layout?
**Answer:** Transceiver rails are a good example of a power delivery problem that spans a very wide frequency range. The transceiver's internal switching produces high-frequency noise — hundreds of MHz to several GHz — while the transceiver's power state changes and the FPGA's overall current draw produce slower, larger transients in the tens to hundreds of kHz range. A single capacitor type cannot cover that range, so the network has to be designed as a cascade of capacitors with different values and different parasitic characteristics.

I would start by understanding the rail's requirements: the nominal voltage, the allowed ripple, the transient current magnitude and slew rate, and the frequency range over which the impedance must stay below a target. From there, I would design the network in layers. The bulk layer — hundreds of microfarads — handles the slow, large transients and is typically placed near the regulator. The mid-frequency layer — tens of microfarads — handles the transition between the bulk and the high-frequency layer. The high-frequency layer — hundreds of nanofarads down to tens of picofarads — handles the switching noise and must be placed as close to the FPGA's power pins as possible, with minimal loop inductance.

The critical detail is that the high-frequency capacitors are only effective if their mounting inductance is low. A 100 nF capacitor with a long trace to the via and a long via to the plane can have more parasitic inductance than the capacitor's own ESL, which pushes its self-resonant frequency down and makes it useless at the frequencies where it is needed. So I would specify the via pattern, the trace width, and the placement distance for each capacitor, and I would treat the layout of the decoupling network as part of the design, not an afterthought.

To verify before committing to layout, I would build an impedance model of the network — using the capacitor's ESR, ESL, and the mounting inductance — and plot the impedance versus frequency. The target is to keep the impedance below the rail's target impedance across the frequency range of interest. I would also run a transient simulation with the expected current profile to check that the voltage stays within the allowed ripple. If the model shows a peak in the impedance at a frequency where the transceiver has significant noise, I would add or resize capacitors to flatten it.

After layout, I would verify with a PDN measurement — using a network analyzer or a dedicated PDN probe — to confirm that the impedance profile matches the model. If there is a discrepancy, it is usually a mounting inductance issue, and the fix is to shorten the capacitor-to-via path or add more vias.

**Possible follow-ups:**
- How would you decide between using a large number of small capacitors versus a smaller number of larger capacitors for the high-frequency layer?
- What is the role of the plane capacitance in the PDN, and how would you account for it in your impedance model?

## Q4: How would you approach verifying that a high-speed FPGA design's timing constraints are complete and correct before sign-off, given that missing or incorrect constraints can produce a design that passes timing analysis but fails in hardware?
**Answer:** The danger with timing constraints is that the tool will happily report "timing met" for a design where the constraints are incomplete or wrong — it only checks what you tell it to check. So the verification of the constraints themselves is a separate activity from the timing analysis, and it has to be done deliberately.

I would start by building a constraint coverage checklist from the design's clock and interface inventory. Every clock in the design — every PLL output, every input clock, every generated clock — must have a corresponding create_clock or create_generated_clock constraint. Every input and output interface must have set_input_delay and set_output_delay constraints that reflect the actual external device's timing. Every clock domain crossing must have either a proper synchronizer with a set_false_path or set_max_delay constraint, or a set_clock_groups constraint that correctly describes the relationship. And every asynchronous reset must be handled correctly.

The next step is to review the constraints against the design's actual structure, not just the constraint file in isolation. I would cross-reference the clock list from the synthesis report against the constraint file, and I would look for any clock that appears in the design but not in the constraints. I would also look for any set_false_path or set_multicycle_path constraint and verify that it is justified — a false path on a path that actually needs to meet timing is a classic way to hide a real violation.

I would also use the tool's own checks: report_clock_networks, report_timing_requirements, and check_timing. These will flag unconstrained clocks, unconstrained endpoints, and other common issues. I would treat any warning from check_timing as a blocker until it is resolved.

Beyond the tool checks, I would do a manual review of the highest-risk interfaces: the DDR memory interface, the transceiver interfaces, and any source-synchronous interfaces. These are the places where a missing constraint is most likely to cause a hardware failure that simulation will not catch. For each, I would verify that the constraint matches the actual timing budget from the external device's datasheet, and that the board-level skew assumptions are reflected.

Finally, I would use gate-level simulation with timing annotation (SDF) on the critical interfaces as a cross-check. If the gate-level simulation passes with the same constraints, that gives additional confidence. But I would not rely on gate-level simulation alone, because it is slow and may not cover all corner cases.

**Possible follow-ups:**
- How would you handle a situation where the timing report shows a violation on a path that you believe is actually a false path, but you are not sure?
- What is the difference between set_false_path and set_clock_groups, and when would you use each?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?
**Answer:** This is a situation where the technical issue and the interpersonal issue are both important, and I would handle them together rather than treating one as secondary.

First, I would make sure I understand the engineer's reasoning. The argument that "the signal is stable long enough" is a common one, and it often comes from a place of having seen it work in simulation or on a bench. I would ask the engineer to walk me through the timing: how long is the signal stable relative to the destination clock period, and what happens if the signal changes during the setup or hold window of the destination register. The goal is not to trap them but to make the metastability risk concrete.

I would then explain the failure mode clearly: when a signal crosses from one clock domain to another without synchronization, the destination register can go metastable if the signal transitions near the clock edge. Metastability is not a simulation artifact — it is a real physical behavior, and it can cause the destination logic to see an incorrect value, or to oscillate, or to propagate an unknown state. The fact that it works most of the time is exactly what makes it dangerous, because it will fail rarely and unpredictably, and those failures are very hard to debug in the field.

I would also point out that the fix is usually cheap: a two-flop synchronizer for a single-bit control signal, or a handshake or FIFO for a multi-bit bus. The cost is a few flip-flops and a small amount of latency, which is almost always acceptable compared to the risk of an intermittent failure.

If the engineer still pushed back, I would not escalate immediately. I would suggest that we add the synchronizer and then verify the behavior in simulation with a metastability model, or on the bench with a targeted test. If the engineer's concern is latency, I would work with them to find a synchronization scheme that meets the latency budget — for example, a two-flop synchronizer adds only two destination clock cycles, which is usually negligible.

The broader point I would want to make is that this is not about being right or wrong — it is about designing for the worst case, not the typical case. A design that works most of the time is not a design that works. I would frame the synchronizer as a standard practice, not a criticism of the engineer's work, and I would use it as a teaching moment for the whole team, because this is a mistake that even experienced engineers make.

**Possible follow-ups:**
- How would you handle it if the engineer's manager disagreed with your assessment and sided with the engineer?
- What would you do if the design was already in production and the missing synchronizer was discovered during a field failure investigation?