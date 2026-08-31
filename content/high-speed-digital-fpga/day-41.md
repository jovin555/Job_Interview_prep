# high-speed-digital-fpga — Day 41

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For asynchronous CDC with frequently-changing multi-bit data and low latency requirements, I'd first rule out simple two-flop synchronizers since they only work for single-bit control signals. The core challenge is that each bit of the bus can metastabilize or be sampled at slightly different times in the destination domain, producing a corrupted word.

The standard approach is an asynchronous FIFO with gray-code pointers. The data itself goes into dual-port RAM, and only the read/write pointers cross clock domains — encoded in gray code so that only one bit changes per increment, making them safe for two-flop synchronization. The FIFO provides bounded latency (a few cycles of fill/empty latency plus synchronization delay) and guarantees data integrity as long as the FIFO doesn't overflow or underflow.

However, if the data is not a continuous stream but rather discrete "words" that must be transferred atomically, I'd consider a handshake-based approach with a valid/ack protocol. The key trade-off is latency: a full 4-phase handshake can take many cycles. To minimize latency, I might use a "toggle" synchronizer where the source toggles a request line, the destination captures the data into a register, then toggles an acknowledge line. This reduces the synchronization latency to roughly 2-3 destination clock cycles per transfer.

For the lowest possible latency with continuous data, I'd look at whether the frequency relationship is truly asynchronous or just nominally different. If there's a known frequency ratio (even if not phase-aligned), I could use a synchronous FIFO with careful depth calculation. If truly asynchronous, the FIFO approach is still the safest — I'd then optimize the read-side logic to minimize the empty-to-valid latency, perhaps using "show-ahead" mode so data is available at the output before the read request is asserted.

The critical verification step would be formal CDC analysis using tools that check for proper synchronization structures, and simulation with randomized clock phase offsets to stress the boundary.

**Possible follow-ups:**
- How would you size the FIFO depth for this scenario, and what happens if the average rates are nearly equal?
- How would you handle the case where the destination needs to know when the source has stopped sending (e.g., end-of-packet indication)?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully (DONE pin goes high) but the device does not enter the expected functional state — for example, all outputs remain tri-stated or in a default state?

**Answer:** This is a classic "configuration succeeded but initialization failed" scenario. I'd approach this systematically, starting with the most likely causes.

First, I'd check the configuration status registers and the INIT_B pin behavior. If INIT_B goes high but the device doesn't start functioning, the issue is often in the startup sequence — specifically, the clock source for startup. Many FPGAs require a valid clock (either from an external oscillator or an internal oscillator) during the startup phase to release the global reset and begin configuration of the fabric. If the clock isn't present or is unstable at power-up, the device can complete configuration but never actually start.

Next, I'd verify the mode pins and configuration options. If the design uses a specific configuration mode (e.g., master SPI, slave SelectMAP), a mismatch between the bitstream settings and the actual hardware strapping can cause the device to load the bitstream but then fail to enter user mode correctly. I'd also check whether the bitstream was generated with the correct device variant and package — a bitstream for a different speed grade or package can sometimes load but behave incorrectly.

Another common cause is a global reset issue. If the design uses an external reset that's held asserted, or if the global set/reset (GSR) signal isn't properly released, all flip-flops remain in their initial state, which could keep outputs tri-stated. I'd probe the reset pin and check the reset polarity in the design.

I'd also check the DONE pin timing relative to the startup sequence. Some FPGAs allow DONE to go high before the startup sequence completes if the bitstream option is set that way. The startup sequence itself — which releases the DONE signal, enables I/O, and releases the global reset — is controlled by a startup primitive or configuration options. If the startup sequence is misconfigured (e.g., waiting for a clock that never arrives, or a bitstream option that holds the device in a "wait for DONE" state), the device can appear configured but not functional.

Finally, I'd verify the I/O standards and bank voltages. If the I/O banks aren't powered correctly, or if the I/O standard configured in the bitstream doesn't match the actual bank voltage, the outputs will remain tri-stated even though the fabric is running. I'd check the VCCO voltages on all banks and compare them to the I/O standard requirements.

**Possible follow-ups:**
- How would you distinguish between a configuration failure and a startup sequence failure using only a scope and the DONE/INIT_B pins?
- What specific bitstream generation options would you check to ensure the startup sequence is correct?

---

## Q3: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a 64-tap FIR filter, and output the filtered result without any dropped samples, while also meeting timing at the target clock frequency?

**Answer:** The fundamental challenge here is that 500 MSPS exceeds the typical FPGA fabric clock rate — most FPGAs won't close timing at 500 MHz for a 64-tap filter. The solution is to use a parallel processing architecture, specifically time-division multiplexing with multiple parallel filter lanes.

First, I'd determine the actual fabric clock frequency. If the FPGA can run at 250 MHz, I'd use a 2:1 deserialization: the input stream is split into two parallel paths, each processing alternating samples at 250 MHz. If the fabric clock is 125 MHz, I'd use 4 parallel lanes. The key is that the total throughput must equal 500 MSPS.

For the FIR filter itself, I'd use the DSP48 slices in a systolic array architecture. A 64-tap filter can be decomposed into multiple parallel sub-filters using polyphase decomposition. For a 2-lane implementation, the even samples go through one 32-tap sub-filter and the odd samples through another 32-tap sub-filter, with the results summed appropriately. This is the polyphase decomposition of the FIR filter — it's mathematically equivalent to the original filter but allows each lane to run at half the sample rate.

The DSP slice usage would be significant: 64 taps at 16-bit coefficients and 16-bit data means each tap needs one DSP slice for the multiply-accumulate operation. With 2 lanes, that's 64 DSP slices total (32 per lane). I'd pipeline the adder tree within each lane to meet timing — typically 2-3 pipeline stages for a 32-tap filter at 250 MHz.

For the input side, I'd use the FPGA's I/O serializer/deserializer (ISERDES) primitives to capture the 500 MSPS data. The ADC interface would be LVDS, with the data and clock coming in as differential pairs. The ISERDES would deserialize the data into parallel words at the fabric clock rate.

The critical verification step is ensuring no samples are dropped. I'd add a "valid" signal alongside the data path and monitor for any gaps. In simulation, I'd verify the filter output against a bit-exact C model of the filter, using both impulse response tests and random data with known frequency content.

For timing closure, the key is proper pipelining. The multiply-accumulate chain in each DSP slice has a fixed latency, and I'd need to balance the pipeline stages across all lanes so that the outputs from different lanes arrive at the summation stage in the correct cycle. I'd also use the FPGA's dedicated cascade connections between DSP slices to avoid routing delays in the accumulator chain.

**Possible follow-ups:**
- How would you handle the coefficient quantization to ensure the filter meets its frequency response specifications?
- What happens if the input data rate is not an exact integer multiple of the fabric clock rate?

---

## Q4: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** This is a challenging PDN design because the combination of high current, fast slew rate, and tight tolerance means the PDN impedance must be extremely low across a wide frequency range. The target impedance can be calculated: with 0.85V ±3%, the allowed voltage deviation is ±25.5 mV. At 20A transient, that means the maximum PDN impedance is about 1.275 mΩ across the frequency range where the transient energy exists.

I'd approach this in layers, each addressing a different frequency range:

**DC to low frequency (kHz range):** The voltage regulator module (VRM) must handle the DC current and low-frequency transients. I'd use a multi-phase buck converter with enough phases to handle 20A with good transient response. The VRM's bandwidth determines where its impedance contribution becomes negligible — typically 10-100 kHz for a good multi-phase design. The VRM's output capacitance and control loop must be designed to keep the voltage within tolerance for slow transients.

**Mid-frequency (100 kHz to 10 MHz):** This is where bulk decoupling capacitors come in. I'd use a combination of electrolytic or polymer capacitors (10-100 µF) and ceramic capacitors (1-10 µF) in parallel. The key is to have multiple capacitor values to create a low-impedance profile across the frequency range. I'd use a spreadsheet or simulation tool to model the capacitor array, accounting for each capacitor's ESL and ESR.

**High frequency (10 MHz to 100+ MHz):** This is where the FPGA's package and the PCB layout dominate. I'd place small-value ceramic capacitors (0.1 µF, 0.01 µF) as close to the FPGA power pins as possible — ideally on the bottom side of the board directly under the BGA. The mounting inductance of these capacitors is critical; I'd use small package sizes (0402 or 0201) with multiple vias to minimize the loop inductance.

**Very high frequency (above 100 MHz):** The on-die capacitance and the package capacitance handle this range. I can't change these, but I need to ensure the PCB doesn't add inductance that would create a resonance peak. This is where the power/ground plane pair comes in — the planes themselves form a distributed capacitance that provides low impedance at high frequencies.

For the PCB stack-up, I'd dedicate a full power plane for the 0.85V rail, placed adjacent to a ground plane with minimal dielectric thickness (e.g., 100 µm or less) to maximize the plane capacitance. The 0.85V rail would have its own plane — I would not share it with other rails.

For verification, I'd perform a frequency-domain simulation of the PDN using a tool like SIwave or PowerSI, plotting the impedance vs. frequency and comparing it to the target impedance curve. I'd also do a time-domain transient simulation with a current source model representing the FPGA's worst-case current draw. On the bench, I'd use a high-bandwidth oscilloscope with a low-inductance probing technique (e.g., a coaxial probe or a specialized PDN probe) to measure the voltage ripple during a controlled transient test.

One additional consideration: the slew rate of 1A/ns means the current changes by 1A every nanosecond. This creates a voltage drop across the parasitic inductance of the package and socket. The formula V = L × di/dt means even 100 pH of inductance causes 100 mV of drop — far exceeding the 25.5 mV budget. This is why the high-frequency decoupling must be as close to the die as possible, and why the plane capacitance matters.

**Possible follow-ups:**
- How would you determine the target impedance curve for this PDN?
- What measurement technique would you use to verify the PDN impedance on a physical board?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical concern and the engineer's reasoning process. The core issue isn't just the FIFO depth — it's that the engineer is relying on average rates rather than worst-case burst behavior, which is a fundamental error in real-time system design.

First, I'd acknowledge the engineer's point about the memory controller's write buffer. It's true that the DDR3 controller has internal buffering that can absorb some burstiness. But the question is whether the combination of the FIFO depth and the memory controller's buffer is sufficient for the worst-case burst scenario. The engineer hasn't demonstrated this — they've only asserted it.

I'd then walk through the analysis together. I'd ask: "What's the maximum burst size the ADC can produce? What's the DDR3 controller's sustainable write bandwidth under worst-case conditions — including refresh cycles, read/write turnaround, and bank conflicts? What's the memory controller's internal buffer depth? Let's calculate the worst-case fill rate and see if 64 words plus the controller's buffer is actually sufficient."

The key insight I'd want the engineer to reach is that the FIFO depth must be sized based on the difference between the peak write rate and the sustainable read rate, multiplied by the maximum burst duration. If the ADC can produce a burst of, say, 1000 samples at full rate, and the memory controller can only sustain 50% of the ADC rate during that period, then the FIFO needs to absorb 500 samples — far more than 64.

I'd also raise the question of what happens when the FIFO does overflow. In a data acquisition system, dropped samples might be acceptable for some applications but not others. If this is a medical or scientific instrument, losing data could be a critical failure. The engineer needs to understand the system-level requirements, not just the local timing.

In terms of the design review process, I'd frame this as a learning opportunity rather than a criticism. I'd suggest we add a burst analysis to the design documentation — a table showing worst-case write rates, read rates, and required buffering for each data path. This becomes a reusable artifact for future designs.

If the engineer continues to resist, I'd propose a simple experiment: run a simulation with a worst-case burst pattern and monitor the FIFO fill level. This is more convincing than arguing about theory. I'd also check whether there's a way to add backpressure from the FIFO to the ADC — many ADCs support a "pause" or "hold" signal that can stop data flow temporarily.

The outcome I'd want is not just a bigger FIFO, but a design process that considers worst-case behavior from the start. I'd follow up after the review to ensure the engineer has updated the design and understands the analysis.

**Possible follow-ups:**
- How would you calculate the required FIFO depth for this scenario?
- What if the engineer's analysis shows that the average rate is so low that even a 64-word FIFO would only overflow after several seconds of continuous worst-case burst — would you still require a change?