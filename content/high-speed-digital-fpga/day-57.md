# high-speed-digital-fpga — Day 57

## Q1: How would you approach designing the interface between an FPGA and an external ADC that uses a source-synchronous, single-data-rate (SDR) output bus, where the data and a forwarded clock arrive at the FPGA with an unknown but bounded skew between them?

**Answer:** The core problem is that the forwarded clock and the data bits travel through different paths — different trace lengths, different I/O buffer delays, different package pin locations — so the clock edge arrives at the FPGA's input flip-flops at an unknown phase relative to the data eye. The design has to absorb that uncertainty without eating into the setup/hold margin.

I'd start by characterizing the skew budget. The ADC datasheet gives a data-to-clock output skew window; the board adds trace-length mismatch (which I'd convert to time using the propagation velocity of the stackup); the FPGA adds package and I/O buffer delay variation across process, voltage, and temperature. Summing those gives the total window the capture logic must tolerate. If that window is a meaningful fraction of the bit period, a fixed delay approach won't work reliably.

The standard technique is to capture the data with the forwarded clock, then use the FPGA's input delay elements (IDELAY) or a per-bit deskew scheme to align each data lane to the clock. For a parallel bus, I'd capture all bits into input registers clocked by the forwarded clock, then use a training pattern — typically a known PRBS or a toggling pattern the ADC can emit — to measure the actual per-bit skew and program the delay taps accordingly. This is essentially the same idea as read-leveling in a DDR interface, applied to a source-synchronous ADC.

An alternative is to oversample: run the capture clock at a multiple of the data rate and use the extra samples to find the data eye in the digital domain. That's simpler in some ways but costs fabric resources and only works if the oversampling ratio is high enough to resolve the eye.

I'd also pay attention to the clock input path itself. If the forwarded clock goes into a global clock buffer, its insertion delay is predictable but the buffer adds jitter. If it goes into a regional or local clock resource, the delay is smaller but the routing is less controlled. For a source-synchronous interface, I'd typically want the forwarded clock on a clock-capable pin with a direct path to the I/O logic, and I'd constrain the input delay in the timing constraints so the tool doesn't try to "fix" a path that's intentionally skewed.

**Possible follow-ups:**
- How would you verify the deskew scheme works across the full temperature range, given that the ADC's output skew and the FPGA's input delay both drift with temperature?
- What would you do if the ADC's forwarded clock has a duty-cycle distortion spec that's wider than the data eye?

## Q2: How would you approach debugging an FPGA design where the device configures successfully and runs correctly for a period of time, but then the configuration appears to be lost — the device stops responding and requires a reconfiguration to recover?

**Answer:** This is a classic "configuration loss" symptom, and the first thing I'd do is distinguish between three root causes: the configuration memory is actually being corrupted, the device is being reset or re-triggered into reconfiguration, or the device is still configured but the logic has entered a state where it no longer responds.

I'd start by monitoring the configuration status pins — INIT_B, DONE, and any error flags the device exposes. If DONE drops low, the device has genuinely lost configuration, which points to a corruption or a reconfiguration trigger. If DONE stays high but the logic is unresponsive, the problem is in the design, not the configuration.

If DONE drops, I'd look at the power rails first. A transient on the core or auxiliary rail — even a brief dip below the brownout threshold — can trigger a reconfiguration. This is especially common if the board has a large current transient (e.g., from a transceiver or DDR controller) that the PDN can't supply cleanly. I'd scope the rails with a fast probe and look for dips correlated with the failure. I'd also check the configuration flash: if the flash is being accessed by the design (e.g., for data logging) while the FPGA is also trying to read it, there could be contention that corrupts a re-read.

If the rails are clean and DONE stays high, I'd look at the design's reset architecture. A watchdog or supervisory circuit that's too aggressive can reset the device into a state where it stops responding. I'd also check for any logic that writes to configuration-related registers or triggers a reconfiguration via the ICAP primitive.

A less obvious cause is single-event upsets if the device is in a radiation environment, but for a terrestrial design, I'd focus on power integrity and reset sequencing first. The key is to instrument the board so you can see which of the three failure modes is actually occurring, rather than guessing.

**Possible follow-ups:**
- How would you design the power sequencing and brownout detection to prevent a transient from triggering reconfiguration?
- If the configuration flash is shared between the FPGA's boot path and runtime data logging, how would you arbitrate access?

## Q3: How would you approach designing the decoupling and bulk capacitance network for an FPGA's transceiver power rails, where the rails have both high-frequency switching noise and slower, larger current transients, and how would you verify the network is adequate before committing to the layout?

**Answer:** Transceiver rails are a good example of a PDN problem with two distinct frequency regimes. The high-frequency content comes from the transceiver's internal switching — the CDR, the serializer, the output driver — and it's in the hundreds of MHz to GHz range. The slower transients come from the transceiver turning on and off, or from the fabric logic that shares the rail, and they're in the kHz to low-MHz range with much larger amplitude.

The decoupling network has to present a low impedance across both regimes. For the high-frequency end, I'd use small-value, low-ESL capacitors — 0.1 µF and smaller, in the smallest package available — placed as close to the transceiver power pins as physically possible, with short, wide traces and multiple vias per pad to minimize the mounting inductance. The goal is to keep the loop inductance low enough that the capacitor can respond before the rail droops.

For the mid-frequency range, I'd add larger ceramics — 1 µF to 10 µF — distributed around the transceiver bank. These handle the transients that the small caps can't supply enough charge for. For the low-frequency, large-amplitude transients, I'd use bulk capacitance — tens to hundreds of µF — placed at the edge of the transceiver power island, with a careful eye on the ESR and ESL of the bulk caps themselves.

The verification step is where a lot of designs go wrong. Before layout, I'd build an impedance model of the PDN — the VRM output impedance, the bulk caps, the ceramics, the plane spreading inductance, and the on-die capacitance — and plot the impedance versus frequency. The target is to keep the impedance below a calculated limit (typically derived from the allowable ripple and the transient current) across the frequency range of interest. If there's a peak in the impedance curve, that's a resonance where the rail will ring, and I'd add or resize capacitors to damp it.

After layout, I'd re-extract the parasitics from the actual placement and routing and re-run the impedance simulation. If the layout introduced extra inductance — long traces to the caps, narrow planes, insufficient vias — the impedance curve will show it, and I'd fix it before fabrication. If the design is high-volume or high-risk, I'd also plan a measurement: a scope with a low-inductance probe tip on the rail, looking at the transient response under a worst-case load step.

**Possible follow-ups:**
- How would you determine the target impedance for a transceiver rail, given the allowable ripple and the worst-case transient current?
- What's the trade-off between adding more bulk capacitance and adding more ceramic capacitance for damping a PDN resonance?

## Q4: How would you approach designing a finite state machine (FSM) in an FPGA that must handle asynchronous inputs without metastability issues?

**Answer:** The fundamental issue is that an asynchronous input can transition at any time relative to the FPGA's clock, including within the setup/hold window of a flip-flop. When that happens, the flip-flop can go metastable — its output hovers between logic levels for an unpredictable time before settling. If that metastable output feeds combinational logic or multiple destinations, the design can behave unpredictably.

The first rule is that every asynchronous input must be synchronized before it's used by any logic. For a single-bit control signal, that means a two-flop synchronizer: the input goes into the first flip-flop, whose output goes into a second flip-flop, and only the second flip-flop's output is used by the rest of the design. The first flip-flop may go metastable, but the second flip-flop gives the metastability time to resolve before the signal is used. The MTBF of the synchronizer depends on the clock frequency, the metastability resolution time constant of the flip-flop, and the setup/hold window — I'd calculate it to make sure it meets the reliability target for the application.

For the FSM itself, the key is to make sure the synchronized input is treated as a single-bit signal that can only change on clock edges. If the FSM needs to detect an edge or a pulse, I'd synchronize the input first, then use edge-detection logic in the clock domain. If the input is a pulse that's shorter than the clock period, a simple two-flop synchronizer might miss it entirely — in that case I'd use a pulse-stretcher or a handshake scheme, or capture the pulse with a toggle flip-flop in the source domain and synchronize the toggle.

For multi-bit inputs, a two-flop synchronizer per bit is not enough, because the bits can resolve in different cycles and the FSM can see an inconsistent value. I'd use a handshake, a FIFO, or a gray-coded counter, depending on the data rate and the FSM's requirements.

I'd also be careful about the FSM's state encoding. If the FSM has unused states, I'd make sure it recovers to a known state rather than locking up. And I'd add a default case in the next-state logic so that an unexpected input doesn't leave the FSM in an undefined state.

**Possible follow-ups:**
- How would you calculate the MTBF of a two-flop synchronizer, and what factors would you trade off to improve it?
- If the asynchronous input is a multi-bit value that changes frequently, how would you decide between a handshake, a FIFO, and a gray-coded counter?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** The first thing I'd do is make sure the conversation is about the technical issue, not about the engineer's competence. This is a common mistake — the "it's stable long enough" argument feels intuitive, and it's easy to miss the metastability window if you haven't been bitten by it. I'd frame it as a design review finding, not a personal failing.

I'd start by asking the engineer to walk me through the timing. What's the source clock frequency? What's the destination clock frequency? How long is the signal actually stable relative to the destination clock period? The goal is to get to a shared understanding of the actual numbers, because the "stable long enough" claim usually falls apart when you quantify it. If the signal is stable for, say, 10 destination clock cycles, that's still not a guarantee — the signal can transition at any point relative to the destination clock, and if the transition happens within the setup/hold window, the destination flip-flop can go metastable. The probability is low per event, but over millions of events it becomes a real failure rate.

I'd then explain the standard solution: a two-flop synchronizer for a single-bit signal, or a handshake/FIFO for multi-bit data. I'd show the engineer how to calculate the MTBF and demonstrate that the unsynchronized version has an unacceptable failure rate for the application. If the signal is a pulse that's shorter than the destination clock period, I'd explain why a simple synchronizer isn't enough and walk through the alternatives.

The key is to make it a teaching moment, not a "you did it wrong" moment. I'd ask the engineer to update the design and come back with the fix, and I'd offer to review it with them. If the engineer pushes back, I'd escalate to a design rule — this is a safety-critical or high-reliability design, and unsynchronized clock domain crossings are a known failure mode that we can't ship. But I'd try to get there through understanding first, because an engineer who understands why the rule exists will apply it correctly in the future, whereas an engineer who just follows the rule will miss the next variant of the same problem.

**Possible follow-ups:**
- How would you set up a design review process that catches this kind of issue before it reaches a formal review?
- If the engineer's design has already been fabricated and the board is in bring-up, how would you handle the fix — respin, or a workaround in the FPGA?