# high-speed-digital-fpga — Day 8

## Q1: How would you approach designing a high-speed serial link (e.g., 10 Gbps) between two FPGAs using the built-in transceivers, where the two boards are separated by a backplane with multiple connectors?

**Answer:** This is a classic system-level challenge that spans both FPGA design and board-level signal integrity. I'd approach it in several layers:

**Transceiver configuration:** Start by selecting the appropriate transceiver mode (e.g., 8B/10B or 64B/66B encoding) based on the required DC balance and clock recovery needs. For a backplane environment, I'd typically use 8B/10B encoding for its proven DC balance and transition density, though 64B/66B offers better efficiency if the link budget allows. Set the TX equalization (pre-emphasis/de-emphasis) to an initial moderate setting, and enable the RX adaptive equalization if the transceiver supports it.

**Channel analysis:** Before committing to a design, characterize the backplane channel. This means working with the mechanical team to understand the connector specifications (insertion loss, return loss, crosstalk at 5 GHz for a 10 Gbps fundamental), and ideally running S-parameter simulations of the complete channel — from FPGA BGA balls through PCB traces, vias, backplane connectors, and the receiving board. The total channel loss budget at the Nyquist frequency (5 GHz) should be within the transceiver's equalization capability, typically 20-30 dB for modern transceivers.

**PCB layout considerations:** Route the differential pairs with controlled impedance (typically 100Ω differential), minimize the number of vias in the signal path, and use back-drilling to reduce via stubs. Keep the pairs tightly coupled and length-matched within a few mils. Place AC coupling capacitors (typically 100 nF) near the transmitter side, and ensure their pad geometry doesn't create impedance discontinuities — use smaller package sizes (0402 or 0201) with ground plane cutouts optimized for the capacitor's self-resonant frequency.

**Clocking strategy:** Use a clean reference clock source — a low-jitter oscillator (e.g., <1 ps RMS jitter) dedicated to the transceiver bank. Route the reference clock as a differential pair with its own ground isolation. The PLL bandwidth in the transceiver should be set to track the reference clock's phase noise while filtering out high-frequency jitter.

**Verification:** After initial bring-up, run bit-error-rate (BER) tests at the target line rate. Use the transceiver's built-in PRBS generators and checkers. If BER is higher than expected, sweep the RX equalization settings and TX pre-emphasis levels while monitoring the eye diagram (using the transceiver's internal eye monitor if available). Also test at temperature extremes and with the backplane fully populated to check for crosstalk degradation.

**Possible follow-ups:**
- How would you handle the situation where the backplane channel loss exceeds the transceiver's equalization capability?
- What pre-layout simulation tools would you use to estimate the channel budget before the PCB is fabricated?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully (DONE pin goes high) but the device does not enter the expected functional state — for example, all outputs remain tri-stated or in a default state?

**Answer:** This is a frustrating failure mode because the configuration appears successful, but the design isn't operating. I'd systematically isolate the cause:

**Verify configuration integrity:** First, confirm that the correct bitstream file was loaded. Compare the CRC of the bitstream on the programming host with what the FPGA computed during configuration — many FPGAs report a CRC check status. If using a configuration memory (e.g., SPI flash), read back the stored data and verify it matches the intended bitstream. A corrupted bitstream can cause the DONE pin to assert but leave the fabric in an undefined state.

**Check the INIT and DONE timing:** Use an oscilloscope to capture the INIT_B, DONE, and configuration clock signals during power-up. Look for unexpected glitches or timing violations. Some FPGAs require specific sequences — for example, INIT_B must be high before configuration begins, and DONE must transition cleanly. A marginal power supply that dips during configuration can cause partial configuration.

**Examine the user I/O behavior:** Probe a few key output pins with an oscilloscope at power-up. Are they truly tri-stated (high impedance), or are they weakly pulled to a known state? If they're weakly pulled, the FPGA might be in a user-mode state but with incorrect I/O standard settings. Check if the I/O banks have the correct VCCO voltages applied — a bank powered at 1.8V when the design expects 3.3V will leave outputs in an indeterminate state.

**Verify the clock source:** The design might configure successfully but never start because the primary clock isn't running. Probe the clock input pins with a high-bandwidth scope. If using an internal oscillator (e.g., for startup), check that the clock management tile (PLL/MMCM) is locking. A PLL that fails to lock will typically hold the design in a reset state.

**Check the global reset:** Many designs use a global reset signal that must be de-asserted after configuration. If the reset is stuck active (e.g., tied to a pin that's floating or incorrectly driven), the entire design will remain in reset. Trace the reset signal from its source through the design hierarchy.

**Use the FPGA's internal debug features:** If the FPGA supports it, insert a ChipScope or SignalTap logic analyzer core that captures key internal signals at power-up. Trigger on the DONE assertion and look at state machine states, counter values, and clock activity. This can reveal whether the design is stuck in an initialization sequence or if a particular module isn't starting.

**Possible follow-ups:**
- How would you distinguish between a configuration issue and a design logic issue in this scenario?
- What would you look for if the design works on some boards but not others?

---

## Q3: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 1 GSPS, perform a digital down-conversion (DDC) with a programmable decimation factor, and output the result over a PCIe Gen3 x4 interface?

**Answer:** This is a demanding real-time signal processing pipeline. I'd structure the design around the data rate and processing requirements:

**Input capture:** At 1 GSPS with 16-bit samples, the input data rate is 16 Gbps — too fast for a single FPGA fabric clock domain. I'd use the FPGA's high-speed transceivers or dedicated SERDES blocks to deserialize the incoming data. For a parallel ADC interface, I'd use the FPGA's I/O resources in DDR mode to capture data on both clock edges, then deserialize into a wider bus at a lower clock rate. For example, capture 8 samples per clock cycle at 125 MHz, giving a 128-bit wide bus.

**Digital down-conversion architecture:** The DDC typically consists of a numerically controlled oscillator (NCO), mixers, and decimating filters. The NCO generates sine/cosine at the desired center frequency using a lookup table or CORDIC algorithm. The mixing stage multiplies the input samples by the NCO outputs. The key challenge is the filter — a decimating low-pass filter that reduces the sample rate while removing out-of-band signals.

For a programmable decimation factor (e.g., 4 to 256), I'd use a cascaded integrator-comb (CIC) filter followed by a compensation FIR filter. The CIC filter is multiplier-free (uses only adders and registers), making it efficient for high decimation ratios. The compensation FIR corrects the CIC's passband droop and provides the final filtering. The CIC operates at the high input rate, while the FIR operates at the decimated rate, keeping resource usage manageable.

**PCIe interface:** The PCIe Gen3 x4 interface provides approximately 32 Gbps of raw bandwidth (4 lanes × 8 GT/s), which is more than sufficient for the decimated output. I'd use the FPGA vendor's PCIe hard IP block, which handles the physical layer, data link layer, and transaction layer. The key design task is the DMA engine that transfers processed data from the FPGA fabric to host memory. Use a scatter-gather DMA with descriptor rings for efficient data movement. The DMA engine should support multiple buffers to handle backpressure from the PCIe link.

**Clock domain crossing:** The design has multiple clock domains: the high-speed input domain (e.g., 125 MHz for the deserialized data), the processing domain (could be the same or a different frequency), and the PCIe domain (typically 250 MHz or 125 MHz depending on the IP). Use asynchronous FIFOs for all CDC crossings, with careful attention to the FIFO depths to handle latency variations.

**Resource planning:** Estimate the DSP slice usage — each CIC stage requires a few adders, and the compensation FIR might use 20-50 DSP slices depending on the filter order. The NCO lookup table uses block RAM. Verify that the target FPGA has sufficient resources, particularly DSP slices and block RAM, and that the design meets timing at the required clock frequencies.

**Possible follow-ups:**
- How would you handle the case where the decimation factor changes on-the-fly without dropping samples?
- What considerations would you have for the filter coefficients — would you precompute them or generate them dynamically?

---

## Q4: How would you approach designing a finite state machine (FSM) in an FPGA that must control a multi-step calibration sequence for an analog front-end, where each step requires waiting for an external ADC conversion to complete, and the timing of each conversion is variable (1 µs to 100 µs)?

**Answer:** This FSM needs to handle asynchronous, variable-latency external events reliably. I'd design it with careful attention to the interface with the external ADC and the overall state machine structure:

**FSM architecture:** Use a Moore-type FSM (outputs depend only on current state) for predictable timing. The states would represent each calibration step: IDLE, START_CALIBRATION, WAIT_ADC, READ_RESULT, APPLY_CORRECTION, CHECK_CONVERGENCE, and COMPLETE. Each state that waits for the ADC uses a timer-based approach rather than a simple counter, since the ADC conversion time is variable.

**ADC interface handling:** The ADC completion signal is asynchronous to the FPGA clock. I'd synchronize it through a two- or three-stage flip-flop chain to avoid metastability. Then, rather than polling the synchronized signal in a tight loop (which wastes power and complicates timing closure), I'd use an edge detector that generates a single-cycle pulse when the ADC conversion completes. This pulse serves as the transition condition for the FSM.

**Timeout mechanism:** Since the ADC conversion can take up to 100 µs, but could also fail (e.g., the ADC never asserts its ready signal), I'd implement a timeout counter. When entering the WAIT_ADC state, start a counter that counts to a value slightly longer than the maximum expected conversion time (e.g., 150 µs worth of clock cycles). If the ADC completion pulse arrives, transition to READ_RESULT. If the timeout expires first, transition to an ERROR state that logs the failure and either retries or signals a fault.

**Reading the ADC result:** The ADC data bus is also asynchronous. I'd register the data on the same clock cycle that detects the completion pulse, using the synchronized and edge-detected signal as a capture enable. This ensures the data is stable when captured.

**Calibration sequence control:** The FSM should support both a full calibration run and individual step retries. For example, if a particular calibration step fails (timeout or out-of-range result), the FSM can retry that step a configurable number of times before declaring a fault. Store the calibration coefficients in registers that are updated only when a step completes successfully.

**Reset and initialization:** The FSM should have a synchronous reset that returns to IDLE and clears all calibration registers. On power-up or system reset, the FSM should automatically initiate a calibration sequence, but also support a software-triggered recalibration.

**Verification:** Simulate the FSM with different ADC latency values — test the minimum (1 µs), maximum (100 µs), and several intermediate values. Also test timeout scenarios and verify the FSM transitions to the ERROR state correctly. In hardware, use an internal logic analyzer to capture the FSM state transitions and compare against the expected sequence.

**Possible follow-ups:**
- How would you handle the case where the ADC result is invalid (e.g., the conversion was interrupted by a power glitch)?
- How would you design the FSM to support pausing the calibration sequence for a higher-priority event?

---

## Q5: Behavioral question — You're the lead engineer on a high-speed FPGA design project. During a design review, a junior engineer presents a simulation showing that a critical control signal in their FSM has a glitch (a 2 ns pulse) that occurs once every 10,000 clock cycles under specific input conditions. The engineer argues that the glitch is harmless because it's too short to affect downstream logic, and fixing it would require adding an extra pipeline stage that would increase latency by one clock cycle. How do you handle this situation?

**Answer:** This is a classic engineering judgment call where I need to balance risk, design margin, and project constraints. Here's how I'd approach it:

**First, acknowledge the engineer's reasoning:** The engineer has done good work identifying the glitch and thinking about its impact. I'd start by acknowledging that — they've found a real issue and considered the trade-off. This encourages thorough analysis rather than hiding problems.

**Then, challenge the assumption that the glitch is harmless:** A 2 ns glitch might be harmless in some contexts, but in high-speed digital design, it's rarely safe to assume. I'd ask several probing questions:
- What is the fan-out of this signal? Does it drive multiple destinations?
- What are the setup and hold times of the receiving flip-flops? At what process corner and temperature?
- Could the glitch propagate through combinational logic and create wider glitches downstream?
- Is this signal used in any asynchronous path or clock domain crossing?
- What happens if the glitch occurs during a critical timing window — for example, during a state transition or when enabling a data path?

**Quantify the risk:** A glitch that occurs once every 10,000 cycles at 200 MHz means it happens about once every 50 µs. In a system that runs for hours, that's potentially millions of glitch events. Even if each glitch has only a 1% chance of causing a functional failure, the system would fail frequently. I'd ask the engineer to trace the glitch through the design to see what downstream logic it reaches.

**Explore alternative fixes:** The engineer's proposed fix (adding a pipeline stage) is one option, but there might be others with less impact:
- Can the glitch be suppressed with a different logic structure (e.g., using a different encoding for the FSM states)?
- Can a glitch filter (a small RC delay or a synchronizer) be added at the destination?
- Can the timing of the input conditions that trigger the glitch be shifted slightly to avoid the race condition?
- Can the FSM be redesigned to use one-hot encoding or a different state assignment that eliminates the glitch?

**Make a risk-based decision:** After the analysis, I'd make a call based on the system's reliability requirements. For a medical device or aerospace application, the glitch must be fixed — the cost of a field failure far outweighs the one-cycle latency increase. For a prototype or non-critical application, I might accept the glitch with documentation and a plan to monitor it in testing. But I'd never accept it without understanding the full propagation path and documenting the decision.

**Use it as a teaching moment:** Regardless of the decision, I'd use this as an opportunity to teach the engineer about design margins and the difference between "works in simulation" and "works reliably in hardware." I'd encourage them to develop a personal checklist for evaluating glitches and other timing hazards.

**Possible follow-ups:**
- How would you document this decision for future reference, especially if the design is later used in a different application with stricter requirements?
- What if the engineer pushes back and insists the glitch is harmless — how do you handle that disagreement?