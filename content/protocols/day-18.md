# protocols — Day 18

## Q1: How would you approach designing a clock generation and distribution scheme for a high-speed digital board that includes multiple FPGAs, DDR memory interfaces, and high-speed serial transceivers?

**Answer:** I'd start by identifying all the distinct clock domains and their requirements—frequency, jitter tolerance, and phase relationships. For DDR interfaces, the clock must meet tight setup/hold margins and track the data strobe; for serial transceivers, the reference clock jitter directly impacts bit error rate. My approach would be:

1. **Inventory clock requirements** — list every device and its clock input specifications, including acceptable jitter, skew, and whether the device generates its own internal clocks from a reference.

2. **Select clock sources** — use low-jitter crystal oscillators or TCXOs as the primary references. For multiple frequencies, I'd consider a clock generator/PLL chip rather than many discrete oscillators, which reduces component count and allows synchronization.

3. **Distribution topology** — for a single high-speed clock fanning out to multiple devices, I'd use a dedicated clock buffer with matched output skew rather than simple fan-out, which introduces uncontrolled skew. For DDR, the clock and strobe traces need length matching to maintain timing margins.

4. **Termination and impedance control** — clock traces should be impedance-controlled and properly terminated (series or parallel, depending on topology) to minimize reflections that cause jitter.

5. **Power integrity** — clock generators and buffers need clean supply rails; I'd use dedicated LDOs or ferrite-bead-filtered supplies to isolate them from digital switching noise.

6. **Grounding and isolation** — keep clock traces away from high-current switching nodes and use ground vias alongside clock traces to provide return paths.

For the FPGA specifically, I'd verify the clock input pins support the required I/O standard (LVDS, LVPECL, etc.) and that the FPGA's internal PLLs/MMCMs can generate the derived clocks with acceptable jitter. I'd also plan for a test point on each clock domain to allow measurement during bring-up.

**Possible follow-ups:** How would you decide between using a single clock generator versus multiple discrete oscillators? What jitter specifications would you look for in a clock source for a 10 Gbps serial link?

---

## Q2: How would you approach debugging an intermittent failure in a high-speed digital system where a DDR memory interface occasionally produces single-bit errors, but only after the system has been running for 30–60 minutes?

**Answer:** This pattern—intermittent errors after warm-up—strongly suggests a thermal or timing-margin issue rather than a hard logic fault. My approach would be systematic:

1. **Reproduce and characterize** — first, I'd try to reproduce the failure under controlled conditions. I'd log the ambient temperature, board temperature at key points (memory, FPGA, clock generator), and correlate with error occurrence. If the failure is thermal, heating the board with a heat gun or placing it in a thermal chamber should accelerate it.

2. **Narrow the failing bit/address** — if the error is consistently in the same bit position or address range, that points to a specific data line, strobe, or memory device. If it's random across addresses, it's more likely a timing or power issue.

3. **Check timing margins** — the most common cause of intermittent DDR errors is marginal setup/hold timing that degrades with temperature. I'd use the FPGA's debug capabilities to measure or adjust the read/write timing calibration. Many FPGAs have dynamic reconfiguration of the memory controller's timing parameters—I'd sweep the read data valid window to find the margin.

4. **Examine power integrity** — I'd probe the VDD and VDDQ rails at the memory and FPGA with a high-bandwidth scope, looking for droop or noise that could correlate with the errors. I'd also check the supply ramp behavior during the failure window.

5. **Review signal integrity** — I'd look at the actual eye diagram on the data/strobe lines using a high-bandwidth scope with a differential probe. Temperature drift can change the eye closure if there's marginal impedance matching or crosstalk.

6. **Check thermal design** — I'd verify the junction temperatures are within spec. If the board has a heatsink or airflow issue, the timing margins can shift beyond the controller's compensation range.

7. **Software/firmware angle** — I'd verify the memory controller initialization settings are correct for the specific memory device and board layout. Sometimes a marginal setting (e.g., read latency, ODT value) works at room temperature but fails after warm-up.

If the issue is timing margin, the fix might be adjusting the controller's timing parameters, improving the PCB layout (shorter traces, better termination), or adding thermal management. If it's power-related, adding decoupling capacitance or improving the regulator's transient response would help.

**Possible follow-ups:** How would you use the FPGA's built-in debug features (e.g., ILA, VIO) to help diagnose this? What specific timing parameters would you sweep first?

---

## Q3: How would you approach implementing a board support package (BSP) for a new custom board that uses an ARM-based SoC, when the board has several peripherals that are not supported by the vendor's default kernel configuration?

**Answer:** I'd approach this as a structured bring-up effort, starting with the minimum needed to boot and then adding peripherals incrementally:

1. **Baseline boot** — I'd start with the vendor's reference BSP and get the board booting with the basic console (UART) and memory (DDR, flash). This validates the fundamental hardware—power, clocking, memory—before adding complexity.

2. **Create a device tree** — for ARM-based systems, the device tree is the primary mechanism for describing hardware. I'd create a custom device tree source (DTS) file based on the vendor's reference, modifying it to match our board's specific peripherals, memory map, and pin muxing.

3. **Identify unsupported peripherals** — for each peripheral not in the vendor's kernel, I'd determine:
   - Is there a similar driver in the kernel that can be adapted?
   - Is there a vendor-provided out-of-tree driver?
   - Does the peripheral need a custom driver written from scratch?

4. **Prioritize bring-up order** — I'd bring up peripherals in order of dependency: first the boot-critical ones (UART, flash, DDR), then those needed for development (Ethernet, USB for debugging), then application-specific peripherals.

5. **Write or adapt drivers** — for custom peripherals, I'd write a Linux kernel driver using the appropriate subsystem framework (e.g., IIO for sensors, GPIO for simple I/O, SPI/I2C for bus devices). I'd start with a minimal driver that just reads/writes registers, then add interrupt handling, DMA, and power management.

6. **Test each peripheral** — I'd create a test procedure for each peripheral to verify functionality, including edge cases like error handling and concurrent access.

7. **Version control and documentation** — I'd keep the BSP in version control with clear documentation of what was changed from the vendor baseline and why. This is critical for maintainability and for reproducing the build.

8. **Build system integration** — I'd integrate the BSP into the build system (Yocto or Buildroot), creating recipes for the kernel, bootloader, and root filesystem.

For the bootloader (U-Boot), I'd similarly configure it for the board's memory, storage, and boot media. The key is to make incremental changes and test each step, rather than trying to bring up everything at once.

**Possible follow-ups:** How would you structure the device tree to handle board revisions with different peripherals? How would you debug a kernel panic during early boot on new hardware?

---

## Q4: How would you approach developing a risk management file for a new medical device that uses a wireless communication link for transmitting patient data, following ISO 14971?

**Answer:** I'd approach this as a systematic, iterative process that starts early in development and continues through the product lifecycle:

1. **Define the intended use and scope** — I'd start by clearly documenting what the device is for, who uses it, and the clinical context. This frames all subsequent risk analysis. For a wireless link, I'd consider the intended environment (home, hospital), the data being transmitted, and the consequences of failure.

2. **Identify hazards** — I'd use structured techniques like FMEA (Failure Mode and Effects Analysis) and FTA (Fault Tree Analysis) to identify potential hazards. For a wireless link, hazards might include:
   - Data corruption or loss leading to incorrect patient monitoring
   - Interference from other wireless devices causing communication failure
   - Security breaches exposing patient data
   - Battery failure during critical monitoring
   - Latency in data delivery causing delayed alerts

3. **Estimate risk** — for each hazard, I'd assess severity (e.g., minor discomfort vs. serious injury or death) and probability of occurrence. This is typically done using a risk matrix. I'd use both qualitative and, where possible, quantitative methods.

4. **Evaluate risk acceptability** — I'd compare each risk against predefined acceptability criteria. Risks that are unacceptable must be mitigated.

5. **Implement risk controls** — for each unacceptable risk, I'd identify controls. For a wireless link, these might include:
   - Error detection and retransmission protocols (e.g., CRC, ARQ)
   - Redundant communication paths
   - Authentication and encryption for security
   - Low-battery warnings and graceful degradation
   - Real-time signal strength monitoring with alerts

6. **Verify effectiveness** — I'd verify that each risk control actually reduces the risk to an acceptable level. This might involve testing under simulated fault conditions, interference testing, and security penetration testing.

7. **Residual risk evaluation** — after controls are applied, I'd re-evaluate the residual risk to ensure it's acceptable. If not, additional controls are needed.

8. **Risk management report** — I'd compile everything into a risk management file that documents the process, decisions, and rationale. This becomes part of the regulatory submission.

9. **Post-market surveillance** — I'd establish a process for collecting and analyzing field data to identify new hazards or changes in risk levels, feeding back into the risk management process.

Throughout this, I'd maintain traceability between hazards, risk controls, verification activities, and design requirements. This is essential for regulatory review and for demonstrating due diligence.

**Possible follow-ups:** How would you handle a situation where a risk control introduces a new hazard? How would you determine the probability of occurrence for a rare but severe event?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single high-speed serial link (e.g., LVDS or SerDes) to carry both real-time sensor data and configuration commands between two boards in a medical device. The engineer argues that the high bandwidth eliminates the need for separate control and data paths. How would you guide the team to evaluate this approach?

**Answer:** I'd approach this as a design review that balances technical merit against risk and complexity, not as a simple yes/no decision. I'd guide the team through several considerations:

1. **Clarify the requirements** — first, I'd ask the team to articulate the actual requirements: what data rates are needed for sensor data, what latency is acceptable for configuration commands, and what happens if a command is delayed or lost. This grounds the discussion in facts rather than assumptions.

2. **Evaluate the single-link approach** — a single high-speed link can work, but it requires careful protocol design to multiplex real-time data and control traffic. I'd ask the engineer to explain:
   - How will the link prioritize control commands over data?
   - What happens when a large sensor data burst delays a time-critical command?
   - How will the system recover from a link error that corrupts a configuration command?

3. **Consider failure modes** — in a medical device, the consequences of a delayed or lost configuration command could be significant. I'd ask the team to consider: what if the sensor data stream saturates the link and a safety-critical command is delayed? Is there a mechanism for the control path to preempt data?

4. **Compare with alternatives** — I'd ask the team to compare against a dual-path approach (separate control and data links) or a lower-bandwidth control link alongside the high-speed data link. The trade-offs are:
   - Single link: simpler cabling, lower cost, but more complex protocol and single point of failure
   - Dual link: more robust, simpler protocol, but more hardware and cost

5. **Assess complexity and risk** — I'd ask the engineer to estimate the protocol complexity and the testing burden. A single link with multiplexing requires thorough testing of priority handling, flow control, and error recovery. In a medical device, this complexity must be justified.

6. **Consider regulatory perspective** — I'd remind the team that the design will need to demonstrate that the communication is reliable under all foreseeable conditions. A simpler design with clear separation of concerns is often easier to verify and defend in regulatory review.

7. **Decision framework** — I'd guide the team to make a decision based on:
   - Does the single-link approach meet all requirements with acceptable margin?
   - Is the added protocol complexity justified by the benefits?
   - Can the team adequately test and verify the behavior under fault conditions?

If the single-link approach is chosen, I'd recommend adding a timeout and watchdog mechanism for control commands, and clearly documenting the priority scheme. If the dual-link approach is chosen, I'd recommend defining the interface between the two paths early to avoid integration issues.

The key is to make the decision based on requirements and risk, not on the elegance of the solution. I'd also encourage the team to prototype the single-link approach early to validate the protocol before committing to it.

**Possible follow-ups:** How would you structure the protocol to ensure control commands have priority over data? What testing would you require to verify the priority scheme works under worst-case conditions?