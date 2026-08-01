# high-speed-digital-fpga — Day 11

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a single-bit control signal that must be transferred from a 50 MHz domain to a 200 MHz domain, where the signal changes very infrequently but must not be missed?

**Answer:** For a single-bit control signal crossing from a slower to a faster clock domain, the classic approach is a two-stage synchronizer — two flip-flops in series in the destination domain. This reduces the probability of metastability propagating to downstream logic to an acceptable level. Since the signal changes infrequently, the main concern isn't throughput but ensuring the pulse isn't missed entirely.

However, a two-stage synchronizer alone only guarantees that the output resolves to a valid logic level — it doesn't guarantee that a narrow pulse in the source domain will be captured. If the source pulse is shorter than one destination clock period, it could be missed entirely. So the first question I'd ask is: what's the minimum pulse width in the source domain? If it's guaranteed to be at least one full destination clock period wide, a simple synchronizer works. If not, I'd need to either:

1. **Use a pulse stretcher in the source domain** — hold the signal high for multiple source clock cycles so it's guaranteed to be sampled by the destination clock.
2. **Use a handshake mechanism** — the source asserts the signal, the destination acknowledges receipt, and the source de-asserts only after receiving the acknowledgment. This is more robust but adds latency.
3. **Use an asynchronous FIFO** — overkill for a single bit, but appropriate if this is part of a larger multi-bit transfer.

For a control signal like an enable or a mode change, I'd typically use the handshake approach or a pulse stretcher with a synchronizer, depending on the latency requirements. I'd also add a constraint in the timing tools to mark the synchronizer flip-flops as such, so the tools don't try to optimize the metastability recovery path.

**Possible follow-ups:**
- What if the signal changes frequently — how would your approach change?
- How would you verify that the CDC scheme is correct in simulation?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design intermittently fails to meet functional requirements only after the device has been running for several hours?

**Answer:** Intermittent failures that appear only after extended operation point toward a different class of problems than static functional bugs. I'd approach this systematically:

**First, characterize the failure.** What exactly fails? Is it a specific function, a data corruption, a state machine getting stuck? How often does it occur — once an hour, once a day? Does resetting the FPGA clear it, or does it require a full power cycle? This tells me whether it's a logic issue or something related to the physical device state.

**Second, consider temperature-related effects.** After hours of operation, the device heats up. This can cause:
- Timing margins to shrink — paths that barely met timing at room temperature may fail at elevated junction temperature. I'd check the timing reports for paths with minimal slack and compare the operating temperature against the timing analysis assumptions.
- PLL/MMCM drift — if the clock management tile is marginally locked, temperature drift could cause periodic phase errors.
- Voltage droop — if the power delivery network has marginal decoupling, increased current draw at temperature could cause supply noise that intermittently violates timing.

**Third, look for accumulation effects.** Things that build up over time:
- Counters or state machines that eventually reach an illegal state after a specific number of operations.
- FIFO pointers that drift due to a subtle CDC issue — the error only appears after enough data has flowed through.
- Memory corruption from an address decoder that fails only under specific address patterns.

**Fourth, check for configuration memory upsets.** In a radiation-sensitive environment, or even in normal operation, configuration bits can flip. I'd check the device's soft-error rate specifications and consider whether the failure pattern matches a configuration upset — for example, a specific logic block starts behaving incorrectly while the rest of the design works.

**Fifth, add instrumentation.** If the design allows, I'd add debug logic — counters, status registers, or an embedded logic analyzer — to capture the state around the failure. This often requires reproducing the failure in a controlled environment.

**Finally, I'd review the design for known failure modes:** uninitialized memory, asynchronous resets that aren't properly synchronized, or signals that can glitch under specific conditions.

The key is not to guess — it's to gather data about the failure and narrow down the hypothesis space systematically.

**Possible follow-ups:**
- How would you distinguish between a timing-related failure and a logic bug?
- What specific information would you want from the timing reports?

---

## Q3: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a finite impulse response (FIR) filter with 64 taps, and output the filtered result without any dropped samples?

**Answer:** A 64-tap FIR filter at 500 MSPS with 16-bit data is a significant throughput requirement. The key constraint is that the FPGA fabric typically can't run at 500 MHz for a multiply-accumulate chain, so I'd need to use parallelism and the DSP slice resources effectively.

**First, I'd determine the target clock frequency.** Modern FPGAs can run DSP logic at 200–400 MHz depending on the device family and the complexity of the arithmetic. If I target 250 MHz, I need a parallelism factor of 2 (500/250). If I target 125 MHz, I need a parallelism factor of 4.

**Second, I'd consider the filter architecture.** For a 64-tap FIR at high throughput, the standard approaches are:

1. **Systolic array / fully parallel** — 64 multipliers operating in parallel, with a tree of adders. This gives one output per clock cycle but uses 64 DSP slices. At 250 MHz, I'd need two of these running in parallel (time-interleaved) to handle 500 MSPS.

2. **Time-division multiplexed (TDM) approach** — Use fewer multipliers but run them at a higher clock rate. For example, 16 multipliers running at 250 MHz can compute 16 taps per cycle, requiring 4 cycles per output sample. With a parallelism factor of 2, I'd need two such engines.

3. **Polyphase decomposition** — If the filter is decimating or interpolating, polyphase decomposition can reduce the number of multipliers needed. For a straight FIR with no rate change, this doesn't directly help, but it can be combined with the parallelism approach.

**Third, I'd think about the data path.** At 500 MSPS, the input is likely coming from an ADC via LVDS or a high-speed serial interface. I'd need to deserialize the data into parallel words. For example, if the ADC sends 16 bits at 500 MSPS via 8 LVDS pairs at 1 Gbps, I'd deserialize into 16-bit words at 250 MHz (two samples per cycle) or 32-bit words at 125 MHz (four samples per cycle).

**Fourth, I'd consider the DSP slice architecture.** Modern FPGAs have DSP slices that can implement multiply-accumulate operations efficiently. I'd structure the filter to use the cascade chains within the DSP slices to avoid routing congestion and reduce power. The key is to map the filter structure to the hardware resources efficiently — understanding the specific DSP slice capabilities (pre-adder, post-adder, cascade paths) is critical.

**Fifth, I'd verify the implementation.** I'd simulate the RTL against a bit-exact C model of the filter to ensure correctness, then check timing closure. I'd also consider the I/O bandwidth — can the FPGA actually receive 8 Gbps of data (500M × 16 bits) and output the same? This might require careful I/O planning.

**Finally, I'd consider whether the filter coefficients are fixed or programmable.** If programmable, I'd need a coefficient update mechanism that doesn't disrupt the data path — typically a shadow register approach where coefficients are loaded into a temporary register and then swapped in atomically.

**Possible follow-ups:**
- How would you handle the case where the filter coefficients need to be updated in real-time without glitches?
- What's the trade-off between using more DSP slices versus running at a higher clock frequency?

---

## Q4: How would you approach designing a power-on reset (POR) circuit for an FPGA that must guarantee reliable configuration across a wide temperature range and with multiple power rails that ramp at different rates?

**Answer:** The POR circuit's job is to hold the FPGA in reset until all power rails are stable and within specification, then release reset so the configuration process can begin. The challenge is that power rails don't ramp simultaneously, and the FPGA's behavior during power-up is undefined if any rail is out of spec.

**First, I'd check the FPGA vendor's requirements.** Most FPGAs have specific power-up sequencing requirements — some require core voltage before I/O voltage, others are more tolerant. The POR circuit must enforce these requirements. I'd also check the device's POR threshold voltages — the FPGA itself has an internal POR circuit that monitors the core voltage, but external supervision is often needed for the complete rail set.

**Second, I'd design the external POR circuit.** The typical approach is:

1. **Voltage supervisors** — Dedicated supervisory ICs that monitor each rail and assert a reset signal until all monitored voltages are above their thresholds. These have built-in hysteresis and delay times to handle noise and slow ramps.

2. **RC delay circuits** — Simpler but less reliable. An RC time constant can hold reset for a fixed period after power-up, but this doesn't account for varying ramp rates across temperature. I'd avoid this for anything beyond the simplest designs.

3. **FPGA-based monitoring** — Some FPGAs can monitor their own supply rails and delay configuration until stable. This is useful as a secondary check but shouldn't be the primary mechanism.

**Third, I'd consider temperature effects.** Voltage supervisor thresholds and delays vary with temperature. I'd select components with specifications that cover the full operating temperature range and verify that the reset timing is adequate at both extremes. At cold temperatures, supply ramp rates can be slower due to increased inrush current, so the POR delay must be long enough.

**Fourth, I'd think about the reset release timing.** The reset must be held long enough for the power supplies to stabilize — including any ripple settling — but not so long that it delays system startup unnecessarily. I'd also consider whether the configuration clock needs to be stable before reset is released.

**Fifth, I'd add a watchdog or manual reset input.** For debug and field maintenance, having a manual reset button or a host-controlled reset is valuable. I'd also consider a watchdog timer that can force a reconfiguration if the FPGA fails to configure or if the application detects a fault.

**Finally, I'd verify the POR circuit.** I'd test at temperature extremes with worst-case supply ramp rates, and I'd also test with supplies ramping in different orders to ensure the circuit handles all cases. I'd also verify that the FPGA's configuration process starts reliably after reset release.

**Possible follow-ups:**
- What happens if the FPGA's internal POR and your external POR disagree?
- How would you handle a brown-out condition where the voltage dips below the threshold during operation?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has designed the clock distribution for a 250 MHz ADC interface. During the review, you notice that the engineer has routed the clock trace with a 90-degree bend, creating a potential impedance discontinuity. The engineer argues that the bend is only 10 mils wide and the clock is only 250 MHz, so it won't matter. How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical concern and the engineer's development without dismissing their work or creating defensiveness.

**First, I'd acknowledge the engineer's point.** At 250 MHz, the wavelength is roughly 60 cm in FR4, and a 10-mil bend is electrically very small — the impedance discontinuity from a 90-degree bend at that size is minimal. The engineer isn't wrong that the impact is likely negligible for this specific signal. This validates their analysis and shows I'm engaging with their reasoning, not just asserting authority.

**However, I'd then raise the broader considerations:**

1. **Design consistency** — Even if this particular bend is acceptable, establishing a rule that 90-degree bends are avoided creates consistency across the board. The next signal might be 1 GHz, and if the engineer develops the habit of using 90-degree bends, that could cause problems later. Design rules should be applied uniformly, not case-by-case.

2. **Manufacturing variability** — While the electrical impact may be negligible, 90-degree bends can cause acid trapping during PCB etching, potentially creating manufacturing defects. This is a yield concern, not just a signal integrity concern.

3. **Future-proofing** — If this board is revised or the clock frequency is increased in a future version, the routing would need to be redone. Using 45-degree bends or curved routing from the start avoids this.

**I'd then suggest a practical path forward:** If the board is already laid out and the bend is in a non-critical area, I might accept it for this revision but ask the engineer to note it as a known deviation and correct it in the next revision. If the layout is still in progress, I'd ask the engineer to re-route with 45-degree bends.

**Finally, I'd use this as a teaching moment.** I'd explain the concept of electrical length versus physical length, and how to determine when a routing feature actually matters versus when it's a rule of thumb. This helps the engineer develop better judgment for future designs.

The key is to separate the technical validity of the argument from the design practice — the engineer may be technically correct, but the design rule exists for good reasons that go beyond this specific case.

**Possible follow-ups:**
- What if the engineer is right and the bend genuinely doesn't matter — how do you balance design rules against engineering judgment?
- How would you handle this if the engineer becomes defensive and refuses to change the routing?