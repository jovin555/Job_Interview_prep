# high-speed-digital-fpga — Day 23

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** This is a classic asynchronous CDC problem where the fundamental tension is between latency and safety. The first question I'd ask is whether the data is truly continuous or if there's any handshaking or framing available — that determines which approach is viable.

If the data is truly continuous with no gaps, an asynchronous FIFO is the standard solution. The key design decisions are:
- **FIFO depth**: Must accommodate the maximum burst size plus the round-trip latency of the synchronization path. I'd calculate worst-case fill based on the frequency ratio and burst characteristics, not just average rates.
- **Gray-code pointers**: For the read/write pointers crossing domains, Gray encoding ensures only one bit changes per increment, eliminating multi-bit synchronization hazards. The pointer width needs to be one bit wider than the address width to distinguish full from empty.
- **Synchronizer stages**: Each pointer needs two flip-flop stages (three for very high MTBF requirements) in the destination clock domain. The synchronizer adds 2–3 cycles of latency, which is unavoidable.
- **Full/empty generation**: These must be generated in the respective write/read clock domains using the synchronized version of the opposite pointer, which is why the FIFO needs the extra pointer bit.

If the data rate is low enough relative to the destination clock, an alternative is a handshake-based approach (request/acknowledge with a 4-phase or 2-phase protocol), but this adds significant latency per transfer.

For minimizing latency specifically, I'd consider whether the frequency relationship is known and stable. If the source clock is always slower than the destination clock, a simpler "pulse synchronizer + register capture" scheme might work — the source asserts a valid pulse, which is synchronized to the destination domain, and the destination samples the data bus after a fixed delay. This works only if the data is stable long enough for the synchronization to complete, which requires the source clock period to be significantly longer than the total synchronization delay.

I'd also verify the design with formal CDC verification tools or at minimum with constrained-random simulation that exercises the full/empty boundary conditions and back-to-back transfers.

**Possible follow-ups:**
- How would you determine the minimum FIFO depth for a given frequency ratio and burst profile?
- What happens if the asynchronous FIFO is read when empty or written when full — how do you handle those conditions?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design intermittently produces incorrect results only when the board is subjected to mechanical vibration?

**Answer:** Vibration-induced intermittent failures point strongly to a physical/mechanical issue rather than a logic or timing problem — the design works correctly when the board is stable, so the logic itself is sound. I'd approach this systematically:

**First, characterize the failure:**
- What exactly fails — data corruption, a control signal glitch, a complete reset?
- Does the failure correlate with vibration frequency or amplitude?
- Does the system recover on its own, or does it require a reset?
- Is it reproducible with a specific vibration profile?

**Second, inspect the mechanical/electrical interfaces:**
- **Connectors**: Loose or poorly seated connectors are the prime suspect. Vibration can cause intermittent contact, especially with high-density mezzanine connectors or board-to-board interconnects. I'd check connector mating, locking mechanisms, and whether the board is properly supported.
- **Solder joints**: Marginal solder joints — especially on large BGAs, QFPs, or through-hole components — can crack or intermittently open under mechanical stress. I'd inspect for cold joints, insufficient solder, or cracked solder balls. X-ray inspection of BGA joints would be warranted.
- **Crystal oscillators**: A crystal or oscillator with marginal mechanical mounting can stop oscillating or produce frequency glitches under vibration. This would cause intermittent failures across the entire design.
- **Capacitors/inductors**: Large ceramic capacitors can crack under mechanical stress, causing power supply noise or decoupling failures.

**Third, add monitoring to localize the issue:**
- I'd add debug instrumentation — either in the FPGA logic (monitoring for unexpected resets, clock loss, or data corruption) or external probes (monitoring power rails, clock signals, and key control lines) while reproducing the vibration.
- If the failure is in a specific I/O bank or interface, that narrows the search to that area of the board.

**Fourth, consider environmental factors:**
- Vibration combined with temperature cycling can exacerbate marginal connections. If the board is also heating up during operation, thermal expansion could be contributing.

**Fifth, implement corrective actions:**
- Mechanical: Add board stiffeners, conformal coating, or better mounting. Ensure connectors are locked and cables are strain-relieved.
- Electrical: Add filtering or debouncing on signals that might be affected by intermittent connections. If a specific connector is the issue, consider a more robust connector type.
- Manufacturing: Improve soldering process controls, add 100% X-ray inspection for critical components.

The key is to avoid assuming it's a logic problem — vibration-induced failures are almost always physical, and spending time debugging RTL would be wasted effort.

**Possible follow-ups:**
- How would you distinguish between a connector issue and a solder joint issue without removing the board from the test setup?
- What if the vibration test is destructive — how would you prioritize which components to inspect first?

---

## Q3: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** This is a challenging PDN design because the core rail has both very high current and very fast transient response requirements. The ±3% tolerance on 0.85V means the voltage must stay within roughly ±25.5 mV, which is tight. I'd approach this in layers:

**First, understand the impedance target:**
The key metric is the target impedance: Z_target = ΔV / ΔI = 25.5 mV / 20A ≈ 1.3 mΩ. This must be maintained from DC up to the frequency where the on-die decoupling takes over (typically hundreds of MHz). This is a very aggressive target — it requires careful design across all frequency ranges.

**Second, design the decoupling strategy by frequency range:**
- **On-die/on-package (1 GHz+)**: The FPGA package itself provides some decoupling. I'd check the vendor's recommendations for the specific device — they typically specify the required on-board decoupling based on the package's own capacitance.
- **High-frequency on-board (10 MHz–1 GHz)**: Small-value ceramic capacitors (0402 or 0201, 100 nF–1 µF) placed as close as possible to the FPGA power pins. The parasitic inductance of the mounting and vias is critical here — I'd use multiple vias per capacitor and place them on the same side as the FPGA if possible.
- **Mid-frequency (100 kHz–10 MHz)**: Larger ceramic capacitors (10–100 µF, X7R or X5R) distributed around the FPGA. These handle the bulk of the transient current.
- **Low-frequency (DC–100 kHz)**: Bulk capacitance (tantalum or aluminum polymer, 100–1000 µF) and the power supply's output capacitance. The voltage regulator's loop bandwidth determines how much of the transient it can handle directly.

**Third, design the PCB stack-up and power plane:**
- The core rail needs a dedicated power plane with a solid adjacent ground plane, separated by a thin dielectric (e.g., 100 µm or less) to maximize plane capacitance.
- I'd calculate the plane capacitance and ensure it contributes meaningfully to the mid-frequency decoupling.
- The power plane must be split appropriately if other rails share the layer, but I'd avoid splitting the core plane if at all possible.

**Fourth, select the voltage regulator:**
- A 20A transient with 1A/ns slew rate requires a regulator with very fast transient response. A multi-phase buck converter with a high switching frequency (1–2 MHz or higher) is typically needed.
- I'd check the regulator's loop bandwidth and transient response specifications. The regulator should handle the low-frequency portion of the transient, with the bulk and ceramic capacitors handling the higher-frequency content.
- I'd also consider the regulator's current capability — it should be rated for at least 20A continuous with margin, and the inductor saturation current must exceed the peak transient current.

**Fifth, verify the design:**
- **Simulation**: I'd run a PDN simulation using the vendor's power integrity tools (e.g., Power Integrity analysis in the PCB design tool) to verify the impedance profile stays below the target across all frequencies. This requires accurate models of the capacitors (including ESL and ESR), the plane impedance, and the FPGA's current profile.
- **Measurement**: On the bench, I'd measure the core voltage with a high-bandwidth oscilloscope (1 GHz or more) using a short ground spring probe, not a long ground lead. I'd apply a load step that mimics the worst-case transient and verify the voltage stays within tolerance.
- **Thermal**: High current means significant heat — I'd verify the power plane and vias can handle the current without excessive temperature rise.

**Possible follow-ups:**
- How would you choose between placing decoupling capacitors on the top side versus bottom side of the board?
- What if the measured impedance profile shows a peak above the target at a specific frequency — how would you fix it?

---

## Q4: How would you approach implementing a finite state machine (FSM) in an FPGA that must control a multi-step calibration sequence for an analog front-end, where each step requires waiting for an external ADC conversion to complete, and the timing of each conversion is variable (1 µs to 100 µs)?

**Answer:** This is a classic FSM design problem where the key challenge is handling variable-duration waits without wasting clock cycles or missing completion events. I'd approach it as follows:

**First, define the FSM structure:**
The FSM would have states for each calibration step (e.g., IDLE, START_CONVERSION, WAIT_FOR_COMPLETE, READ_RESULT, APPLY_CORRECTION, NEXT_STEP, DONE). The critical design decision is how to handle the wait states.

**Second, choose the wait mechanism:**
There are two main approaches:

1. **Polling with a counter**: The FSM enters a WAIT state and polls the ADC's "conversion complete" signal each clock cycle. This is simple and works well if the ADC's completion signal is synchronous to the FPGA clock or can be synchronized. The FSM stays in the WAIT state until the signal is asserted. The variable timing is naturally handled — the FSM just waits as long as needed.

2. **Interrupt/event-driven with a timer**: If the ADC completion signal is asynchronous or the FSM needs to do other work while waiting, I'd use a timer to generate a timeout, and the completion signal would trigger a transition. This is more complex but allows the FSM to do other tasks during the wait.

For most calibration sequences, approach #1 is simpler and sufficient. The key is to handle the synchronization of the ADC's completion signal properly.

**Third, handle the variable timing:**
- The FSM must not assume a fixed conversion time. I'd design it to wait indefinitely for the completion signal, with a watchdog timeout to detect ADC failures.
- The timeout value should be longer than the maximum expected conversion time (e.g., 150 µs for a 100 µs max conversion) plus margin.
- On timeout, the FSM would enter an ERROR state and report the failure, rather than proceeding with invalid data.

**Fourth, address metastability:**
If the ADC's completion signal is asynchronous to the FPGA clock, I'd synchronize it with two flip-flops before feeding it to the FSM. This adds 2 clock cycles of latency, which is negligible compared to the 1–100 µs conversion time.

**Fifth, consider the FSM encoding:**
For a calibration controller, I'd use one-hot encoding for simplicity and robustness. The FSM is small (maybe 8–12 states), so the extra flip-flops are not a concern. One-hot encoding makes the state transitions easy to debug and less prone to decoding glitches.

**Sixth, add observability:**
I'd expose the current state to a debug interface (e.g., a status register readable via a control bus) so the calibration progress can be monitored during bring-up. This is invaluable for debugging — you can see exactly which step is failing or taking too long.

**Seventh, consider the reset behavior:**
The FSM must have a reliable reset that returns it to IDLE. If the calibration sequence is critical for system operation, I'd also consider what happens if the FSM is reset mid-sequence — the analog front-end might be left in an unknown state, so the reset should also reset the analog front-end or at least flag that calibration is incomplete.

**Possible follow-ups:**
- How would you handle the case where the ADC never asserts its completion signal?
- Would you use a different approach if the calibration sequence had a strict overall time budget?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where I need to address a genuine technical concern while also helping the junior engineer develop better engineering judgment. The core issue is that the engineer is reasoning about average rates when burst behavior is the real risk — this is a common and important lesson.

**First, I'd acknowledge what the engineer got right:** The average-rate analysis is a valid starting point, and it's good that they're thinking about the relationship between write and read rates. This isn't a case of carelessness — it's an incomplete analysis.

**Second, I'd walk through the burst scenario concretely:** Rather than just asserting that the FIFO is too small, I'd work through the math with the engineer. If the ADC produces a burst of, say, 256 samples at 500 MSPS, that's 256 words written into the FIFO in about 512 ns. The memory controller might have a sustainable write rate of, say, 50% of the bus bandwidth due to refresh cycles, read/write turnaround, and bank conflicts. If the memory controller can only drain the FIFO at, say, 100 words per microsecond, then a burst of 256 words would overflow a 64-word FIFO before the controller can drain it. The memory controller's write buffer helps, but it's also finite — and it's shared with other traffic.

**Third, I'd ask the engineer to quantify the burst profile:** I'd ask them to characterize the worst-case burst length and the memory controller's sustainable write rate under worst-case conditions (including refresh and bank conflicts). If they can't provide these numbers, that's the gap we need to fill. This turns the discussion from opinion into engineering analysis.

**Fourth, I'd discuss the cost of getting it wrong:** If the FIFO overflows, data is lost. In a data acquisition system, that means corrupted measurements — which could be a safety issue in a medical device context. The cost of a slightly larger FIFO is trivial compared to the cost of data loss. This is a risk-based engineering decision.

**Fifth, I'd propose a path forward:** Rather than dictating the solution, I'd suggest we work together to:
1. Characterize the worst-case burst profile from the ADC
2. Determine the memory controller's worst-case sustainable write rate (including refresh, bank conflicts, and read/write turnaround)
3. Calculate the required FIFO depth with margin
4. Consider whether a larger FIFO, a different memory controller configuration, or a rate-limiting mechanism (e.g., throttling the ADC data) is the best solution

**Sixth, I'd use this as a teaching moment:** The key lesson is that average rates are insufficient for FIFO sizing — you must analyze worst-case burst behavior. This is a fundamental principle in high-speed data path design. I'd encourage the engineer to always ask "what's the worst case?" when designing buffers and queues.

**Finally, I'd ensure the design review captures the action item:** The FIFO depth needs to be re-evaluated with proper burst analysis before the design is finalized. I'd track this to closure.

The goal is to correct the technical issue while building the engineer's capability — not to override them, but to guide them toward the right analysis.

**Possible follow-ups:**
- What if the engineer's analysis shows that the memory controller's write buffer can indeed absorb the bursts — would you still require a larger FIFO?
- How would you handle this if the engineer becomes defensive and insists their design is correct?