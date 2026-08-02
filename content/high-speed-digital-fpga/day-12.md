# high-speed-digital-fpga — Day 12

## Q1: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design operates correctly at room temperature and fails only when the board is heated to its maximum specified operating temperature?

**Answer:** This is a classic temperature-dependent failure that typically points to timing margin degradation rather than a functional logic error. My approach would be systematic:

First, I'd confirm the failure is reproducible and characterize it — does it fail at a specific temperature threshold, and does it recover when cooled? This helps distinguish between a soft failure (timing-related, recovers) and a hard failure (solder joint, component damage, doesn't recover).

Next, I'd examine timing margins in the design. At elevated temperatures, transistor switching speeds slow down, which reduces setup timing margin. I'd look at the timing reports from the place-and-route tools, specifically checking the worst negative slack (WNS) and total negative slack (TNS) across all timing corners — particularly the slow-slow corner with high temperature, which is typically the worst case for setup timing. If the design barely meets timing at the slow corner, that's a strong suspect.

I'd also check the clock distribution. PLLs and MMCMs can have temperature-dependent jitter characteristics, and if the clock source is marginal, the added jitter at temperature could push paths over the edge. I'd verify the clock is clean using an oscilloscope or spectrum analyzer if accessible.

Another area to investigate is the power supply. At temperature, regulator efficiency drops, and if the FPGA core voltage sags under load, timing margins shrink. I'd check the actual core voltage at the FPGA pins under worst-case conditions, not just at the regulator output — board resistance and via drops matter.

If the design uses external memory (DDR, SRAM), I'd look at the memory interface calibration. Some interfaces recalibrate at startup, and if the calibration was done at room temperature, the settings might be suboptimal at temperature. I'd check whether the failure correlates with memory access patterns.

Finally, I'd review the PCB layout for thermal effects — differential pair skew can change with temperature if the traces are on different layers with different dielectric constants, and via stubs can have temperature-dependent resonance effects.

The fix depends on the root cause: adding pipeline stages to relax timing, adjusting PLL settings, improving power delivery, or adding thermal management.

**Possible follow-ups:** How would you distinguish between a setup-time failure and a hold-time failure in this scenario? What specific timing reports would you request from the FPGA tools to narrow down the problem?

---

## Q2: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus that transfers continuously at high speed (e.g., 128-bit words at 200 MHz) from one clock domain to another with a known, fixed frequency relationship (e.g., 200 MHz to 150 MHz)?

**Answer:** This is a high-throughput CDC problem where the data rate is too high for handshake-based or FIFO-based approaches that require the data to pause. Since the frequency relationship is fixed and known, I'd look for a deterministic solution.

The key question is whether the two clocks are derived from the same source (synchronous relationship) or from independent oscillators (asynchronous relationship). If they're derived from the same PLL with a known phase relationship, I could potentially use a synchronous approach with careful timing analysis — but this is risky because the phase relationship can vary across temperature and voltage.

For a truly robust solution, I'd use an asynchronous FIFO designed for high throughput. The critical design elements are:

1. **Gray-code or equivalent encoding for the read/write pointers** — this ensures that only one bit changes at a time when the pointer crosses clock domains, avoiding multi-bit CDC issues. For a 128-bit data bus, the data itself is protected by the FIFO structure; only the pointers cross domains.

2. **Proper synchronization of the pointers** — each pointer needs two or three stages of flip-flops in the destination clock domain to prevent metastability. The Gray-code encoding ensures that even if a pointer value is sampled during transition, the resulting value is either the old or new value, never an invalid intermediate.

3. **FIFO depth calculation** — the depth must accommodate the maximum burst size plus the synchronization latency. For continuous operation with a 200 MHz write and 150 MHz read, the average rates are 200/150 = 4:3, so the FIFO will fill over time unless the read side can occasionally burst faster. If the read side truly consumes at a constant 150 MHz, the FIFO will eventually overflow — so the system design must account for this, either through backpressure or by ensuring the average write rate is lower than the read rate.

4. **Full/empty flag generation** — these flags must be generated in the correct clock domain and account for the synchronization latency to avoid false full/empty conditions.

An alternative approach for this specific case is to use a "clock enable" or "rate matching" technique where the faster domain is periodically stalled to match the slower domain's rate. This works well when the frequency ratio is rational and known, but it adds complexity in the control logic.

I'd also consider whether the data path itself needs any alignment or framing — if the 128-bit words have meaning only as complete units, the FIFO approach naturally preserves word boundaries.

**Possible follow-ups:** How would you calculate the minimum FIFO depth for this scenario? What happens if the frequency ratio drifts slightly over temperature — how would you handle that?

---

## Q3: How would you approach verifying signal integrity on a high-speed serial link (e.g., 10 Gbps) during PCB layout review, before the board is manufactured?

**Answer:** Pre-manufacturing signal integrity verification is critical because fixing problems after fabrication is expensive and time-consuming. My approach combines simulation, rule-based review, and careful stack-up design.

First, I'd ensure the PCB stack-up is designed for high-speed signaling. For 10 Gbps differential pairs, I'd want a stack-up with controlled impedance (typically 85 or 100 ohms differential), a solid reference plane adjacent to the signal layer with no splits or gaps under the traces, and dielectric materials with consistent properties. I'd verify the stack-up with the manufacturer to confirm they can achieve the required impedance tolerance.

Next, I'd run 2D or 3D field solvers on the critical traces. Tools like HyperLynx, SIwave, or Polar Si8000 can extract the characteristic impedance, propagation delay, and coupling coefficients. For 10 Gbps, I'd check:

- **Impedance continuity** — any change in trace width, layer transition, or connector footprint creates a reflection. I'd verify that the impedance stays within tolerance (typically ±10%) along the entire path.
- **Differential pair skew** — the two traces in a pair must be length-matched to minimize skew. At 10 Gbps, the bit period is 100 ps, and I'd target skew well under 10 ps (ideally under 5 ps).
- **Via transitions** — vias introduce impedance discontinuities and stubs. I'd use back-drilling or blind/buried vias to minimize stub length, and I'd place ground vias near signal vias to provide a return path.
- **Return path continuity** — I'd check that the reference plane is continuous under the entire trace route, especially near vias and connector transitions.

I'd also run time-domain reflectometry (TDR) simulations on the critical paths to visualize impedance discontinuities and identify where reflections occur. This helps pinpoint specific locations that need layout changes.

For the connector and any AC coupling capacitors, I'd verify that the component footprints don't create excessive discontinuity. AC coupling caps should be small (0402 or smaller) and placed symmetrically in the differential pair.

Finally, I'd review the routing rules: keep differential pairs away from other traces (especially single-ended traces), maintain consistent spacing between the pair, avoid routing near board edges or under components, and ensure the ground return vias are placed appropriately.

If the design has multiple high-speed links, I'd also check for crosstalk between adjacent pairs — the spacing between pairs should be at least 3-5 times the dielectric height to keep crosstalk below acceptable levels.

**Possible follow-ups:** How would you decide between using a 2D field solver versus a full 3D solver for this analysis? What would you do if the simulation shows a significant impedance discontinuity at a via that you can't eliminate?

---

## Q4: How would you approach implementing a digital delay line in an FPGA that must provide precise, programmable delays (e.g., 1 ns to 100 ns in 1 ns steps) for a high-speed signal, and how would you verify its accuracy?

**Answer:** This is a challenging problem because FPGA fabric isn't naturally suited to precise analog delays — the routing delays are not well-controlled, and the delay through a logic element varies with temperature, voltage, and process. I'd approach this by considering what the delay is actually used for and what accuracy is truly needed.

The most robust approach is to avoid analog delays entirely and use a synchronous digital design. If the signal can be sampled and processed digitally, I'd use a shift register or a RAM-based delay line clocked at a frequency that gives the desired resolution. For 1 ns resolution, that would require a 1 GHz clock, which is not feasible in most FPGAs. So I'd need to think differently.

A practical alternative is to use the FPGA's dedicated delay elements. Many FPGAs have IODELAY or similar primitives in the I/O blocks that provide fine-grained, programmable delays (typically in the range of 10-100 ps per tap). These are calibrated and can be quite accurate. I'd use these if the signal is at the I/O boundary.

For delays internal to the FPGA, I'd consider:

1. **Oversampling with a faster clock** — if the signal bandwidth allows, sample at a higher rate and use a shift register. This gives delays in multiples of the clock period.

2. **Multi-phase clock approach** — use a PLL/MMCM to generate multiple clock phases (e.g., 4 phases of a 250 MHz clock gives 1 ns resolution). The signal is captured on each phase, and the delay is selected by choosing which phase's capture to use. This requires careful handling of the phase relationships and can be complex.

3. **Hybrid approach** — coarse delay using a shift register (in clock cycles) plus fine delay using IODELAY or a small analog delay line. This gives wide range with fine resolution.

For verification, I'd use a testbench that measures the actual delay through the implemented design. I'd generate a known test pattern, apply it to the delay line, and measure the time difference between input and output using the FPGA's built-in logic analyzer or by bringing the signals out to test pins. I'd also use timing analysis from the place-and-route tools to get the expected delay and compare it to the measured value.

An important consideration is temperature and voltage stability. If the delay must be accurate over the full operating range, I'd need a calibration mechanism — either a built-in self-test that measures the delay and adjusts the tap settings, or a periodic calibration routine that runs during operation.

If the delay is for a clock signal rather than data, I'd consider using the PLL/MMCM's phase-shift capability, which gives precise, well-controlled phase adjustments.

**Possible follow-ups:** How would you handle the temperature drift of the delay elements? What accuracy can you realistically achieve with an FPGA-based delay line, and how would you communicate that limitation to the system designer?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A senior engineer on your team proposes using a vendor-specific, proprietary IP core for the high-speed serial interface, arguing it will save development time. However, you're concerned about long-term maintainability and vendor lock-in. The engineer has significant experience with this vendor's tools and is confident the IP core is the right choice. How do you handle this situation?

**Answer:** This is a common tension in FPGA design — time-to-market versus long-term maintainability. My approach would be to facilitate a structured decision rather than unilaterally overriding the senior engineer's recommendation.

First, I'd acknowledge the engineer's expertise and the legitimate benefits of the vendor IP core. Vendor IP cores are typically well-tested, optimized for the specific FPGA family, and come with vendor support. For high-speed serial interfaces, they often include features that are very difficult to implement correctly from scratch, like the analog front-end calibration and equalization.

However, I'd also want to understand the full context of the decision. I'd ask the engineer to walk through the specific IP core, its licensing terms, the level of vendor support, and what the migration path would look like if the project needed to move to a different FPGA vendor. I'd also ask about the IP core's track record — has it been used in production designs, and are there known issues?

I'd then frame the discussion around the project's specific requirements. Key questions to consider:

- **What is the project timeline?** If the schedule is tight, the vendor IP core might be the pragmatic choice.
- **What is the expected product lifetime?** If this is a product that will be manufactured for 10+ years, vendor lock-in is a serious concern. If it's a prototype or short-lived product, it matters less.
- **What is the team's expertise?** If the team has deep experience with this vendor's tools and IP, the risk is lower. If the team is less experienced, the vendor IP core might actually be safer.
- **What is the fallback plan?** If the vendor discontinues the IP core or the FPGA family, what happens?

I'd also explore whether there's a middle ground. For example, could we use the vendor IP core for the initial prototype to validate the system, while developing a portable alternative in parallel? Or could we abstract the interface so that the IP core is isolated behind a well-defined boundary, making it easier to replace later?

In the review meeting itself, I'd make sure both perspectives are heard. I'd ask the engineer to present the technical merits, and I'd ask other team members for their views. I'd also check whether there are any company-level standards or preferences regarding vendor lock-in.

Ultimately, the decision should be based on the project's specific constraints. If we choose the vendor IP core, I'd document the rationale, the risks, and the mitigation plan. If we choose a portable approach, I'd ensure the team has the resources and time to do it properly.

The key is to make this a collaborative decision based on evidence and project requirements, not a power struggle. The senior engineer's experience is valuable, and their concerns about development time are legitimate — but so are the maintainability concerns.

**Possible follow-ups:** How would you document this decision for future reference? What specific criteria would you use to evaluate whether the vendor IP core is the right choice? How would you handle it if the engineer becomes defensive or resistant to the discussion?