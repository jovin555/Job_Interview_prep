# high-speed-digital-fpga — Day 9

## Q1: How would you approach designing a high-speed data acquisition system in an FPGA where an ADC sends 12-bit parallel data at 500 MSPS, and you need to capture, serialize, and transmit this data over a 10 Gbps optical link with minimal latency?

**Answer:** This is a challenging problem because the data rate is substantial — 500 MSPS × 12 bits = 6 Gbps raw data, plus any overhead for framing or error detection. The approach would break into several stages:

First, the parallel interface from the ADC needs careful I/O timing. At 500 MHz, the data and clock from the ADC are likely DDR (double data rate), so the FPGA's I/O buffers must be configured for DDR capture with appropriate delay calibration (IDELAY elements in Xilinx or IODELAY in Intel devices). The input timing budget is tight — I'd use the ADC's source-synchronous clock and route it to a dedicated clock-capable pin, then use the FPGA's PLL/MMCM to generate the capture clock with precise phase adjustment.

Second, the captured data needs deserialization. A 12-bit bus at 500 MSPS DDR means 24 bits per clock cycle at 250 MHz (if using DDR). I'd use ISERDES or similar dedicated deserializers to convert to a wider, slower parallel bus internally — for example, 48 bits at 125 MHz, which is more manageable for internal logic.

Third, the data must be serialized for the optical link. A 10 Gbps optical transceiver typically uses a serializer with 8B/10B or 64B/66B encoding. The raw 6 Gbps data plus encoding overhead (e.g., 64B/66B adds ~3% overhead) fits within 10 Gbps. I'd use the FPGA's high-speed transceivers (GTH/GTY or similar) configured for the appropriate line rate. The data path would include a small FIFO to absorb any clock domain crossing between the ADC capture domain and the transceiver reference clock domain.

For minimal latency, I'd avoid storing data in large buffers or DRAM. The critical path is: ADC input → deserialization → encoding → transceiver output. Each stage adds deterministic latency, and careful pipelining keeps it to tens of clock cycles. I'd also use the transceiver's internal PCS (physical coding sublayer) in a low-latency mode if available, bypassing optional features like scrambling or CRC if not required.

**Possible follow-ups:** How would you handle the clock domain crossing between the ADC capture clock and the transceiver reference clock? What if the ADC's output clock has significant jitter — how would you clean it up before using it for capture?

---

## Q2: How would you approach debugging an FPGA design where the DDR3 memory interface passes initialization and calibration but produces occasional read errors under heavy traffic patterns (e.g., sustained 80% bus utilization)?

**Answer:** This symptom — passing calibration but failing under sustained high utilization — suggests a timing margin issue that only manifests when the memory controller is under thermal or electrical stress. I'd approach the debug systematically:

First, I'd check whether the errors are temperature-dependent. Sustained high utilization increases power dissipation in both the FPGA and the DDR3 devices, raising junction temperatures. Higher temperature increases propagation delays and can shift the optimal read/write timing. I'd monitor the temperature sensors (if available) and correlate error rates with temperature. If temperature is a factor, the solution might involve adjusting the read/write leveling calibration to run at operating temperature, or adding thermal management.

Second, I'd examine the power delivery. High utilization means more simultaneous switching outputs (SSO) and higher transient current draw. I'd probe the DDR3 VDD and VTT termination voltages with an oscilloscope during heavy traffic, looking for droops or noise that could violate timing margins. A PDN impedance issue at the switching frequency of the memory bus could cause supply voltage variations that reduce timing margin.

Third, I'd look at signal integrity on the data and strobe lines. With a scope and active probe, I'd capture eye diagrams at the DDR3 pins during heavy traffic, comparing them to the pass/fail conditions. Reduced eye opening due to crosstalk from adjacent aggressor lines, or due to simultaneous switching noise, could explain intermittent failures.

Fourth, I'd check the on-die termination (ODT) settings. Under heavy traffic, the impedance of the memory bus changes as more drivers are active. The ODT values that work well at low utilization might not provide optimal impedance matching under high utilization. I'd experiment with different ODT configurations (e.g., RZQ/4 vs RZQ/6) to see if error rates change.

Finally, I'd examine the memory controller's read data capture logic. Some controllers use a per-bit deskew calibration that might have marginal settings on certain DQ bits. I'd check if the errors are concentrated on specific data bits or byte lanes, which would point to a specific timing or signal integrity issue.

**Possible follow-ups:** How would you distinguish between a signal integrity problem and a timing margin problem in this scenario? What tools would you use to measure the actual timing margin during operation?

---

## Q3: How would you approach implementing a multi-rate digital filter in an FPGA that must operate at different sample rates (e.g., 48 kHz, 96 kHz, and 192 kHz) while maintaining the same filter characteristics?

**Answer:** The key challenge is that the filter's frequency response (cutoff frequency, passband ripple, stopband attenuation) must remain constant in the analog domain even as the sample rate changes. This means the filter coefficients must be scaled relative to the sample rate.

I'd approach this by designing the filter for the highest sample rate (192 kHz) and then using coefficient scaling for lower rates. For a finite impulse response (FIR) filter, the normalized cutoff frequency (cutoff / sample_rate) must remain constant. So if the filter is designed with a normalized cutoff of 0.2 (i.e., 38.4 kHz at 192 kHz sample rate), then at 96 kHz the same normalized cutoff of 0.2 gives 19.2 kHz — which is not the same analog cutoff. To maintain the same analog cutoff, I'd need to change the normalized cutoff to 0.4 at 96 kHz (38.4 / 96 = 0.4).

There are several implementation approaches:

1. **Multiple coefficient sets**: Store separate coefficient tables for each sample rate. This is straightforward but uses more block RAM. The filter structure remains the same; only the coefficients change.

2. **Single coefficient set with interpolation**: Design the filter for the highest rate and use a polyphase structure where the coefficients are interpolated for lower rates. This is more efficient in memory but requires a polyphase filterbank implementation.

3. **Reconfigurable filter using CORDIC or distributed arithmetic**: For very flexible rate changes, a CORDIC-based filter or a filter using distributed arithmetic with reconfigurable lookup tables can adapt to different rates.

4. **Decimation/interpolation approach**: Run the filter at the highest rate and use decimation/interpolation to match the output rate. This is simple but wastes power at lower rates since the filter runs at maximum speed regardless.

For a practical implementation, I'd lean toward option 1 (multiple coefficient sets) for simplicity and deterministic timing. The filter would have a control input that selects the coefficient set based on the operating mode. The filter's clock would be derived from the sample rate — for example, running at 192 kHz × filter_taps for all modes, with the coefficient selection determining the actual response.

I'd also verify the filter's frequency response at each rate using MATLAB or Python simulations, then compare with on-chip test captures using a known test tone.

**Possible follow-ups:** How would you handle the transition between sample rates — would you allow the filter to run continuously or would you flush the filter state? How would you verify the filter's frequency response on actual hardware?

---

## Q4: How would you approach designing a finite state machine (FSM) in an FPGA that must control a multi-step calibration sequence for an analog front-end, where each step requires waiting for an external ADC conversion to complete, and the timing of each conversion is variable (1 µs to 100 µs)?

**Answer:** This is a classic problem of controlling an asynchronous external process from a synchronous FSM. The variable timing means a simple counter-based wait state won't work efficiently — you'd either waste time waiting for the maximum case or risk missing the completion signal.

I'd design the FSM as a Moore machine with the following structure:

1. **State encoding**: Use one-hot encoding for simplicity and to avoid decoding glitches. The FSM would have states like: IDLE, START_CALIBRATION, CONFIGURE_AFE, TRIGGER_CONVERSION, WAIT_FOR_COMPLETION, READ_RESULT, CHECK_CRITERIA, NEXT_STEP, COMPLETE, ERROR.

2. **Handshake mechanism**: The FSM would assert a "start conversion" signal to the ADC, then transition to a WAIT_FOR_COMPLETION state. The ADC's "conversion complete" signal (or data-ready signal) would be the input that causes the transition out of the wait state. This signal must be synchronized to the FPGA's clock domain using a two-flop synchronizer to avoid metastability.

3. **Timeout protection**: Even though the conversion time is variable, I'd include a watchdog timer that counts from the time the conversion is triggered. If the completion signal doesn't arrive within, say, 150 µs (with margin above the maximum 100 µs), the FSM transitions to an ERROR state. This prevents the system from hanging if the ADC fails.

4. **Pipelining for efficiency**: If the calibration sequence has many steps, I'd consider a pipelined approach where the FSM configures the next step while the current conversion is in progress. For example, after triggering a conversion, the FSM can set up the next AFE configuration register values, so they're ready immediately when the conversion completes.

5. **Parameterization**: I'd make the calibration parameters (register addresses, expected values, comparison thresholds) stored in a small lookup table or ROM, rather than hard-coded in the FSM logic. This makes the calibration sequence easy to modify without changing the FSM structure.

For the actual implementation, I'd use a two-process FSM style (one process for state transitions, one for output logic) or a single-process style with registered outputs. The key is that the wait state is exited based on an external event, not a fixed count.

**Possible follow-ups:** How would you handle the case where the ADC conversion completes in less than one clock cycle of the FPGA? How would you test the FSM's behavior when the conversion time varies across its full range?

---

## Q5: Behavioral question — You're the lead engineer on a high-speed FPGA design project. During a design review, a junior engineer presents a simulation showing that a critical control signal in their FSM has a glitch (a 2 ns pulse) that occurs once every 10,000 clock cycles under specific input conditions. The engineer argues that the glitch is harmless because it's too short to affect downstream logic, and fixing it would require adding an extra pipeline stage that would increase latency by one clock cycle. How do you handle this situation?

**Answer:** I'd approach this as a teaching moment and a risk assessment exercise, not simply as a directive to fix or ignore the glitch.

First, I'd acknowledge the engineer's analysis — they've identified a real issue and quantified its frequency, which shows good attention to detail. Then I'd walk through a structured evaluation of the risk:

1. **Is the glitch truly harmless?** A 2 ns pulse might be too short to propagate through combinational logic, but it depends on the fan-out and the logic paths it feeds. If the signal drives clock enables, resets, or control signals to sequential elements, even a short glitch could cause metastability or incorrect state transitions. I'd ask the engineer to trace the signal's entire fan-out and check each destination.

2. **What about process, voltage, temperature (PVT) variation?** The simulation likely used typical conditions. At the fast-fast corner (low temperature, high voltage), the 2 ns glitch could become wider as gates switch faster. At the slow-slow corner, it might disappear — but the downstream logic might also be slower, changing the propagation characteristics. I'd ask the engineer to simulate at multiple corners.

3. **What about the "once every 10,000 cycles" aspect?** This means the glitch occurs at a rate of about 0.01% of the time. In a system that runs continuously, this could translate to thousands of glitches per second. If any of those glitches cause a functional error, the mean time between failures might be unacceptably short for the application.

4. **What's the cost of fixing it?** Adding one pipeline stage adds one clock cycle of latency. In many systems, this is negligible. I'd ask the engineer to quantify the actual latency impact — is this in a control path where one cycle matters, or in a data path where it's easily absorbed? Often, the latency cost is far lower than the risk of intermittent failures.

5. **What's the alternative?** Instead of adding a pipeline stage, could the glitch be eliminated at the source? Perhaps the FSM coding style could be changed to avoid the combinational path that creates the glitch. A one-hot encoded FSM with registered outputs, for example, typically has no glitches. I'd ask the engineer to explore whether a coding change could fix the root cause without adding latency.

After this analysis, I'd guide the team to a decision. If the glitch truly has no path to any sequential element and the simulation covers all relevant corners, then documenting the analysis and accepting the risk might be reasonable. But in most cases, the safer approach is to fix it — either by adding the pipeline stage or by redesigning the FSM to eliminate the glitch. I'd frame this as: "In high-speed FPGA design, we prioritize deterministic behavior over minimal latency. A one-cycle latency increase is a small price for eliminating a failure mode that could be extremely difficult to debug in the field."

**Possible follow-ups:** How would you verify that the fix actually eliminates the glitch across all operating conditions? What documentation would you expect the engineer to produce for this decision?