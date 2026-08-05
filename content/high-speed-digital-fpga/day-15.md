# high-speed-digital-fpga — Day 15

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous and have no known frequency relationship, and the data must be transferred without corruption?

**Answer:** For truly asynchronous clock domains with no known frequency relationship, the fundamental challenge is that you cannot guarantee setup/hold timing at the destination without some form of synchronization. The standard approach is to use an asynchronous FIFO with gray-code pointers. The key design considerations are:

First, the FIFO depth must be sized based on the worst-case frequency ratio and burst characteristics. If the write clock can be much faster than the read clock, you need enough depth to absorb the maximum burst without overflow. I'd calculate this as (write_rate - read_rate) × burst_length, plus margin for synchronization latency.

Second, the read and write pointers must be synchronized across domains. Gray-code encoding ensures that only one bit changes per increment, so even if a metastable event occurs during sampling, the synchronized value will be either the old or new pointer value—never an invalid intermediate state. I'd use two flip-flop synchronizers on each gray-coded pointer.

Third, I'd add full/empty flag generation with proper synchronization. The full flag must be generated in the write domain using the synchronized read pointer, and the empty flag in the read domain using the synchronized write pointer. This introduces conservative behavior—the FIFO may appear full slightly early or empty slightly late—but prevents data corruption.

For the data path itself, the data lines don't need synchronization flip-flops because they're only sampled when the pointer comparison indicates valid data. However, I'd still verify that the data settles well before the destination clock edge captures it, accounting for the synchronization latency of the pointers.

Finally, I'd run formal CDC verification tools to prove that all crossings are properly synchronized, and I'd simulate with randomized clock phase relationships to stress-test the design.

**Possible follow-ups:**
- How would you determine the minimum FIFO depth for a specific frequency ratio and burst pattern?
- What happens if the FIFO overflows or underflows despite your sizing—how would you handle that in the design?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design operates correctly at room temperature and fails only when the board is heated to its maximum specified operating temperature?

**Answer:** Temperature-dependent failures that only appear at the high end of the operating range typically point to timing margin issues, so I'd approach this systematically.

First, I'd try to characterize the failure mode precisely. What exactly fails—is it a functional error, a data corruption, a loss of lock, or a timing violation? I'd add debug instrumentation to capture the failure signature, such as error counters, status registers, or a logic analyzer connected to key internal signals. Knowing whether the failure is gradual (e.g., increasing bit error rate) or abrupt (e.g., complete loss of function) helps narrow the cause.

Second, I'd examine the timing margins. At high temperature, transistor switching speeds slow down, which reduces setup margin. I'd check the timing report for paths that have minimal slack at the slow-slow corner, and I'd verify that the design was constrained correctly for the worst-case temperature. If there are paths with only a few picoseconds of slack, those are prime suspects. I'd also check whether the clock generation (PLL/MMCM) is maintaining lock and whether jitter increases with temperature.

Third, I'd look at power supply behavior. At high temperature, supply voltages can droop more under load, and this can exacerbate timing issues. I'd verify that all rails stay within specification across the temperature range, and I'd check for excessive IR drop or thermal-induced changes in the regulator behavior.

Fourth, I'd consider whether the issue is in the configuration or the design itself. Since the bitstream loads successfully, the configuration is likely fine, but I'd verify that the device is fully configured and that no configuration bits are being corrupted by temperature-induced issues.

Finally, I'd use a thermal chamber to reproduce the failure in a controlled way, then use incremental testing—varying temperature, supply voltage, and clock frequency—to isolate which parameter is the critical one. This often reveals whether it's a setup-time issue (sensitive to voltage and temperature) or something else like a PLL lock issue.

**Possible follow-ups:**
- How would you distinguish between a timing margin issue and a power integrity issue as the root cause?
- What specific timing reports or analyses would you request from the tools to investigate this?

---

## Q3: How would you approach designing a power distribution network (PDN) for an FPGA that has multiple voltage rails (core, I/O, auxiliary, transceiver) with different current demands and transient response requirements?

**Answer:** A proper PDN design starts with understanding the current demands of each rail, not just the average but the transient behavior. For an FPGA, the core rail typically has the highest current and the fastest transients—when large logic blocks or DSP slices switch simultaneously, the current can change in nanoseconds. The transceiver rails need very low noise because any ripple directly affects the analog performance and can cause bit errors.

I'd start by estimating the current for each rail from the FPGA vendor's power estimator tool, using realistic toggle rates and resource utilization. I'd also identify the worst-case transient scenarios—for example, when the design transitions from idle to full processing, or when a large block of logic is enabled simultaneously.

The PDN design itself has three main layers: the voltage regulator, the bulk decoupling, and the high-frequency decoupling. The regulator must be able to source the maximum current and have sufficient bandwidth to handle the low-frequency transients. I'd use a dedicated regulator for the core rail rather than sharing with other rails, because the core's transient demands would couple noise into other supplies.

For the PCB layout, I'd use dedicated power planes for each voltage rail, with the plane stack-up arranged to provide low inductance between the FPGA and the decoupling capacitors. The high-frequency decoupling capacitors (typically 100 nF and 10 nF in X7R or C0G dielectric) should be placed as close as possible to the FPGA power pins, on the same side of the board if possible, to minimize the loop inductance. I'd also add bulk capacitors (10 µF to 100 µF) distributed around the board to handle medium-frequency transients.

The critical metric is the target impedance—the maximum impedance the PDN can present at any frequency without causing the voltage to deviate beyond the specified tolerance. I'd calculate this as (allowed voltage deviation) / (maximum transient current). For a core rail with 0.85V and ±3% tolerance, and a 10A transient, that's about 2.5 mΩ. I'd use a PDN analysis tool to simulate the impedance across frequency and verify that the capacitor selection and placement achieve this target.

Finally, I'd verify the PDN on the bench by measuring the power supply noise with a high-bandwidth oscilloscope and a proper probing technique (using a coaxial probe or a dedicated power rail probe, not a standard 10× probe). I'd also check for resonance peaks between the capacitors and the board inductance, which can cause unexpected noise at specific frequencies.

**Possible follow-ups:**
- How would you determine the target impedance for a specific rail, and what happens if you can't achieve it?
- How would you handle the trade-off between decoupling capacitor count and board area?

---

## Q4: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a finite impulse response (FIR) filter with 64 taps, and output the filtered result without any dropped samples?

**Answer:** This is a classic throughput-versus-latency trade-off problem. At 500 MSPS with a 64-tap FIR, you need 32 billion multiply-accumulate operations per second. No single DSP slice can run that fast, so the design must use parallelism and pipelining.

The first decision is the target clock frequency. If the FPGA can run at 500 MHz, you could use a single multiply-accumulate per tap per clock cycle, but that's aggressive. A more practical approach is to run at a lower clock frequency and use multiple parallel processing lanes. For example, if the FPGA can comfortably run at 250 MHz, you'd need two parallel lanes, each processing every other sample. At 125 MHz, you'd need four lanes.

For the FIR implementation itself, I'd use the FPGA's DSP slices, which are designed for exactly this kind of multiply-accumulate operation. The 64-tap filter can be decomposed into a polyphase structure if you're decimating, but for a straight FIR at the same rate, I'd use a systolic array or a transposed direct-form structure. The transposed form is often preferred because it naturally pipelines well—each tap's multiply and accumulate can be registered, and the partial sums propagate through the array.

The key challenge is ensuring that the input data is distributed to the parallel lanes correctly. If I'm using two lanes at 250 MHz, I need to demultiplex the 500 MSPS input stream into two 250 MHz streams, each carrying alternating samples. The filter coefficients must also be distributed appropriately—each lane needs the full set of 64 coefficients, but applied to the appropriate samples.

I'd also need to handle the filter's internal state carefully. For a 64-tap FIR, each output depends on the current sample and the previous 63 samples. With parallel lanes, the state must be shared correctly between lanes. This is where the design gets tricky—the lane processing even samples needs the previous odd samples as part of its history.

For verification, I'd create a bit-exact reference model in C or Python, generate test vectors with known input patterns (impulses, steps, sine waves), and compare the FPGA output against the reference. I'd also verify the timing closure at the target frequency, paying attention to the DSP slice placement and routing delays.

**Possible follow-ups:**
- How would you choose between a transposed direct-form and a systolic implementation for this filter?
- How would you handle the filter state sharing between parallel lanes?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the DDR3 memory interface and is presenting the design for review. During the presentation, you notice that the engineer has not included any on-die termination (ODT) settings in the memory controller configuration, and has left the ODT pins unconnected on the schematic. When you raise this concern, the engineer responds that "the memory works fine in simulation, and ODT just adds complexity and power consumption." How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical issue and the engineer's understanding of why it matters, without dismissing their perspective entirely.

First, I'd acknowledge that the engineer is right about one thing—ODT does add complexity and power consumption. That's a legitimate trade-off to consider. But I'd explain that for DDR3, ODT is not optional; it's a fundamental part of the signal integrity design. The memory bus operates at high speed with multiple devices on the same traces, and without proper termination, reflections from the end of the bus and from the memory devices themselves will cause signal integrity problems that may not appear in simulation but will manifest on real hardware.

I'd then walk through the specific technical concerns. In a typical DDR3 topology, the data lines (DQ) are point-to-point between the controller and the memory, but the address/command lines are a multi-drop bus. Without ODT on the memory devices, the address/command signals will reflect at the end of the bus, causing ringing and potentially violating setup/hold times at the memory. The data lines are also affected—when the memory drives data, the output impedance interacts with the trace impedance, and without ODT, the signal will have poor return loss.

I'd also point out that the simulation the engineer is relying on may not accurately model the PCB parasitics, the package parasitics, or the simultaneous switching noise that occurs in a real system. Simulation is valuable, but it's only as good as the models and the assumptions. For a DDR3 interface running at 800 MHz or higher, the margin for error is very small.

Rather than simply overriding the engineer's decision, I'd ask them to investigate the issue and come back with a recommendation. I'd suggest they run a signal integrity simulation with and without ODT, using realistic PCB models, and compare the eye diagrams and timing margins. I'd also ask them to review the DDR3 JEDEC specification to understand the ODT requirements. This approach turns the review into a learning opportunity rather than a confrontation.

If the engineer comes back with data showing that ODT isn't needed for their specific configuration, I'd be open to that—but I'd want to see convincing evidence. In most cases, the analysis will show that ODT is necessary, and the engineer will have learned why it matters.

**Possible follow-ups:**
- How would you handle the situation if the engineer comes back with a simulation showing the design works without ODT?
- What specific signal integrity metrics would you ask the engineer to evaluate in their simulation?