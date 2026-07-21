# high-speed-digital-fpga — Day 2

## Q1: How would you approach the PCB layout for a high-speed digital design that includes both DDR memory and an FPGA, given tight space constraints?

**Answer:** The key is establishing a clear floorplan early, before committing to detailed routing. I would start by grouping components by their signal-speed requirements and keeping the FPGA and DDR physically close to minimize trace lengths on the memory bus. The DDR interface is typically the most timing-critical, so I'd place the FPGA and DDR on the same side of the board if possible, with the memory controller pins on the FPGA located nearest to the DDR device.

For layer stack-up, I'd use a minimum of six layers for a moderate-speed DDR3 design, or eight-plus for DDR4 or higher. The stack-up should have at least two solid ground planes adjacent to signal layers to provide controlled impedance and return paths. I'd assign the top two signal layers for the DDR bus, with the layer immediately below being a continuous ground plane. All DDR traces — data, address/command, and clock — need impedance control (typically 50Ω single-ended, 100Ω differential for clocks), and length matching within the timing budget (often ±10-20 mils for data groups relative to DQS, and longer tolerances for address/command).

For the FPGA itself, I'd pay attention to the power delivery network. FPGAs have multiple voltage rails (core, I/O banks, PLLs, transceivers) with high transient current demands. I'd place decoupling capacitors as close as possible to each power pin pair, using a mix of bulk, ceramic, and sometimes ferrite beads for sensitive analog supplies. The PCB should have dedicated power planes split by voltage domain, with sufficient copper thickness to handle the current.

Under tight space constraints, trade-offs become necessary. I might use microvias and blind/buried vias to free up routing channels on outer layers, or consider a higher layer count to reduce the footprint. I'd also evaluate whether the FPGA's pin assignment can be optimized — many FPGAs allow pin-swapping within I/O banks to simplify routing, as long as timing and signal integrity are preserved.

**Possible follow-ups:** How would you determine the required number of PCB layers? What signal integrity simulations would you run before committing to layout?

---

## Q2: How would you debug a situation where an FPGA design works correctly at slow clock speeds but fails intermittently at the target frequency?

**Answer:** This is a classic symptom of timing or signal integrity issues that only manifest when the design is pushed to its intended operating speed. I'd approach this systematically, starting with the most likely causes.

First, I'd check the static timing analysis reports from the FPGA toolchain. If the design meets timing with positive slack at the target frequency, the problem is likely signal integrity rather than logic timing. If there are timing violations, I'd examine the critical paths — they often involve combinational logic chains, wide muxes, or paths crossing clock domains without proper synchronization.

For signal integrity, I'd use an oscilloscope with sufficient bandwidth (at least 3-5x the fastest clock frequency) to probe the clock signals and suspect data lines. I'd look for overshoot, undershoot, ringing, or excessive jitter on clocks. Power supply noise is another common culprit — I'd check the FPGA core voltage and I/O bank voltages with AC coupling to see if there's ripple at the switching frequency of the voltage regulators or at the FPGA's internal clock frequency.

If the failure is temperature-dependent (works cold, fails hot, or vice versa), that points to timing margins shrinking with temperature. I'd use a thermal chamber or heat gun to characterize the failure window.

Another useful technique is to reduce the clock frequency in small steps and see where the failure disappears — that gives a rough indication of how much timing margin exists. I'd also try adjusting the output drive strength and slew rate settings on the FPGA I/Os, as these affect signal integrity at the receiver.

If the design uses external memory (DDR, SRAM), I'd verify the memory initialization and training sequences. Many DDR controllers perform calibration at startup, and marginal calibration can cause intermittent failures.

**Possible follow-ups:** How would you distinguish between a setup-time violation and a hold-time violation during debugging? What tools would you use to correlate a logic analyzer trace with the oscilloscope measurements?

---

## Q3: How would you approach clock generation and distribution in a multi-FPGA system where each FPGA operates at a different frequency, and the boards are connected by high-speed serial links?

**Answer:** The fundamental decision is whether to use a single master clock source distributed to all boards, or to have independent local oscillators with some form of synchronization. For a system requiring deterministic latency or tight synchronization between FPGAs, I'd lean toward a single master reference clock distributed via a low-skew fanout buffer over differential pairs (LVDS or LVPECL). Each FPGA would then use its own PLL to generate the specific frequencies needed internally.

The master clock should be a low-jitter oscillator, typically a temperature-compensated crystal oscillator (TCXO) or oven-controlled crystal oscillator (OCXO) if precision is critical. The fanout buffer must have low additive jitter and matched propagation delays across all outputs. I'd route the clock traces with controlled impedance, matched lengths, and proper termination (typically 100Ω differential termination at the receiver).

For the high-speed serial links between FPGAs (e.g., PCIe, Gigabit Ethernet, or custom SERDES), the clocking becomes more nuanced. Each transceiver typically uses the reference clock to drive its own PLL for the serial data rate. If the reference clocks on both ends are derived from the same source, the link can operate in synchronous mode. If they're independent, the link must handle clock tolerance through techniques like clock data recovery (CDR) and elastic buffers.

If the system requires independent local oscillators (e.g., for cost or physical distance reasons), I'd ensure each FPGA's transceiver reference clock meets the jitter specifications for the serial protocol being used. I'd also add a mechanism for frequency measurement or synchronization — for example, using a low-frequency reference signal (like a 1 PPS from a GPS receiver) to discipline the local oscillators over time.

Power supply noise on the clock distribution is critical. I'd keep clock traces away from switching power supplies and high-current digital traces, and use dedicated power planes or filtering for the clock generation and distribution circuitry.

**Possible follow-ups:** How would you handle the case where two FPGAs must share a common time base but are separated by several meters of cable? What clock jitter specifications would you look for in a datasheet for a 10 Gbps serial link?

---

## Q4: How would you design a power delivery network (PDN) for an FPGA that has multiple voltage rails with high transient current demands, and how would you verify its performance?

**Answer:** The PDN design starts with understanding the FPGA's power requirements from the datasheet — specifically, the maximum current per rail, the allowed voltage tolerance (typically ±3% or ±5% including DC and AC components), and the transient response requirements. The goal is to keep the impedance of the PDN below a target value across the frequency range of interest, from DC up to the FPGA's switching frequency and its harmonics.

I'd begin by selecting voltage regulators appropriate for each rail. Core voltages (often 0.85V-1.2V) with high current demands (tens of amps) typically require multiphase buck converters with good transient response. I/O bank voltages (1.8V, 2.5V, 3.3V) can use simpler single-phase regulators. PLL and transceiver analog supplies need low-noise linear regulators (LDOs) with excellent PSRR.

The PCB stack-up should include dedicated power planes for each major voltage rail, with the core voltage plane adjacent to the ground plane to create a low-inductance parallel-plate capacitor. The plane capacitance itself provides high-frequency decoupling. I'd add bulk decoupling capacitors (tantalum or aluminum polymer, 10-100 µF) near the regulator output, ceramic capacitors (0.1-10 µF) distributed across the board near the FPGA, and very small capacitors (0.01-0.1 µF) as close as possible to each power pin pair on the FPGA.

The number and placement of decoupling capacitors is often guided by the FPGA vendor's recommendations, but I'd also simulate the PDN impedance using SPICE or a dedicated PDN analysis tool. The simulation should model the regulator's output impedance, the PCB plane capacitance, the via inductance, and the capacitor ESL/ESR. The target impedance is calculated as Z_target = (V_rail × tolerance) / I_transient.

For verification, I'd use a vector network analyzer (VNA) to measure the PDN impedance from the FPGA's power pins looking back into the board. This measurement requires careful calibration and a low-inductance probe. I'd also use an oscilloscope with a differential probe to measure AC ripple on each rail under worst-case operating conditions — for example, running a test pattern that toggles all FPGA logic simultaneously.

If the measured impedance exceeds the target at any frequency, I'd add more capacitors at the problematic frequency range, reduce via inductance by using multiple vias per capacitor pad, or adjust the regulator's compensation network.

**Possible follow-ups:** How would you determine the worst-case transient current for an FPGA design? What is the role of the PCB plane capacitance, and how do you calculate it?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA board, and a junior engineer proposes a routing approach that you believe will cause signal integrity problems. How do you handle the situation?

**Answer:** I'd approach this as a coaching opportunity rather than simply overriding their decision. First, I'd acknowledge the work they've done and the thought process behind their proposal — it's important that junior engineers feel their contributions are valued, even when corrections are needed.

Then I'd explain my concern in specific, technical terms. For example: "I see you've routed the DDR data lines on the outer layer without a reference plane underneath for part of the route. That could create an impedance discontinuity and a poor return path, which might cause data errors at speed. Let me show you what happens in simulation." I'd walk through the signal integrity analysis together, comparing their approach with an alternative that uses a ground plane reference.

If time allows, I'd ask them to propose an alternative routing themselves, guiding them with questions rather than giving the answer directly. This builds their problem-solving skills and reinforces the learning. For example: "What if we moved the DDR bus to layer 3, which has a solid ground plane on layer 2? How would that change the stack-up and the via count?"

If the project timeline is tight and we need a decision quickly, I'd be more direct but still explain the reasoning: "For this prototype, we need to minimize risk, so let's use the ground-referenced routing approach. For the next revision, you could experiment with the outer-layer routing and compare the simulation results."

After the review, I'd follow up with resources — a relevant application note, a signal integrity textbook chapter, or a simulation tool tutorial — so they can deepen their understanding independently. The goal is to leave them better equipped for the next design, not just compliant with this one decision.

**Possible follow-ups:** How would you handle a situation where the junior engineer disagrees with your assessment and insists their approach is fine? What if the schedule doesn't allow time for a detailed explanation?