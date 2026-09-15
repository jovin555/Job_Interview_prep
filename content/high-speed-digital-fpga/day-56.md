# high-speed-digital-fpga — Day 56

## Q1: How would you approach designing the interface between an FPGA and an external ADC that uses a source-synchronous, double-data-rate (DDR) output bus, where the data and a forwarded clock arrive at the FPGA with an unknown but bounded skew between them?
**Answer:** The core problem is that a forwarded (source-synchronous) clock has no fixed phase relationship to the FPGA's internal clock, so the capture strategy has to tolerate the full skew budget between clock and data. I'd start by characterizing that budget: trace-length mismatch on the PCB, the ADC's output valid window (Tco, Tsu/Th), and the FPGA input sampling window. That tells me how much margin I actually have.

From there, the standard approach is to capture the DDR data in the input delay elements or IDELAY/ISERDES resources of the I/O blocks rather than in fabric registers, because those give per-bit or per-group delay taps that can be calibrated. The forwarded clock goes to a dedicated clock-capable input and drives the ISERDES in the same I/O bank, so the clock-to-data relationship is captured at the pin, not after routing through the fabric.

The key design decision is whether to do static or dynamic alignment. Static alignment — picking a delay tap from a datasheet calculation — is fragile because it doesn't account for process, voltage, and temperature drift. Dynamic alignment, where the FPGA sweeps the delay taps at startup and finds the center of the valid data eye, is more robust and is what I'd lean toward for anything above a few hundred Mbps per lane. That calibration routine needs a known training pattern from the ADC, or a way to detect the eye edges by sweeping until errors appear and then backing off to the midpoint.

I'd also make sure the clock and data are routed on the same layer with matched lengths and a controlled reference plane, and that the input standard (e.g., LVDS) matches the ADC's output. Finally, I'd verify the whole thing with an eye-diagram measurement at the FPGA pins and a bit-error-rate test over temperature, not just a functional capture test at room temperature.

**Possible follow-ups:**
- How would you decide between using the FPGA's built-in dynamic phase alignment (DPA) versus implementing your own calibration state machine?
- What would you do if the ADC's forwarded clock and data skew drifted more than expected over temperature, and the initial calibration window was no longer valid?

## Q2: How would you approach debugging an FPGA design where the transceiver link passes its built-in PRBS checker at the physical layer, but application-level data is occasionally corrupted, and the corruption only appears at full line rate?
**Answer:** The fact that PRBS passes tells me the physical layer — the SerDes, the CDR, the equalization, the eye — is fundamentally healthy. PRBS is a good PHY test but it's a poor protocol test, because it exercises the serial link in isolation and often bypasses the parts of the design that matter at the application layer. So I'd treat this as a problem above the PHY.

The first thing I'd check is the clock domain crossing between the recovered clock domain and the application clock domain. At full line rate, the FIFO or elastic buffer that bridges those domains is running at its maximum rate, and any subtle issue — a FIFO depth that's marginal, a flag that's sampled at the wrong time, a reset that isn't synchronized — will only show up when the buffer is nearly full or nearly empty. I'd look at the FIFO occupancy over time and see whether the errors correlate with the buffer approaching a boundary.

Second, I'd look at the data path itself. At full rate, the design may be pipelining differently, or a multiplexer or gearbox may be switching between lanes in a way that's timing-critical. If the corruption is a single bit or a small burst, that points to a specific lane or a specific pipeline stage; if it's a whole word, that points to a framing or alignment issue.

Third, I'd check whether the error is actually in the link or in the measurement. If the application is reading status registers or counters that are themselves crossing clock domains, the "corruption" could be a read-side artifact.

The practical debugging approach is to add error-detection logic in the application path — a checksum or sequence number on the payload — and then use the FPGA's internal logic analyzer or a built-in error counter to correlate errors with link state, FIFO occupancy, and temperature. I'd also try running the link at a reduced rate to see if the errors disappear, which would confirm it's a timing-margin issue rather than a logic bug.

**Possible follow-ups:**
- How would you distinguish between a corruption caused by the CDR losing lock momentarily versus a corruption caused by a logic error in the gearbox?
- What changes would you make to the design to make this class of error easier to diagnose in the future?

## Q3: How would you approach selecting and configuring the I/O standards and pin assignments for an FPGA bank that must simultaneously support a high-speed differential interface and several single-ended signals at different voltages, given that I/O bank voltage and standard choices are constrained by the bank's VCCO?
**Answer:** The constraint that drives everything here is that all I/O in a given bank share a common VCCO, and the choice of VCCO limits which I/O standards are legal in that bank. So the first step is to group signals by their required voltage and standard, and then see whether the grouping is compatible with the bank architecture.

A high-speed differential interface — say LVDS — typically requires a VCCO of 2.5V or 1.8V depending on the device family, and it uses dedicated differential pairs with specific pin locations. Single-ended signals at 3.3V CMOS cannot coexist in the same bank as a 1.8V VCCO, because the output high level would be wrong and the input thresholds would be violated. So if the design needs both, the answer is usually to put them in separate banks, not to try to force them together.

If the single-ended signals are at a voltage compatible with the differential interface's VCCO — for example, 1.8V LVCMOS alongside 1.8V LVDS — then they can share a bank, but I'd still check the input thresholds and the output drive strength. I'd also check whether the differential pair pins are in the same bank as the single-ended pins and whether the bank has enough I/O to accommodate both.

Pin assignment is the other half. Differential pairs must go on true differential pin pairs, and the pinout of the FPGA often constrains which pairs are available in which bank. I'd start with the differential interface because it's the least flexible, then fit the single-ended signals around it. I'd also consider whether the single-ended signals are inputs or outputs, since input-only pins and output-only pins have different constraints.

Finally, I'd verify the whole assignment against the device's I/O planning rules — the vendor's pin-planning tool will flag illegal combinations — and I'd check the signal integrity implications of putting a high-speed differential pair next to single-ended signals, since crosstalk and return-path issues can degrade the differential link even if the standards are technically compatible.

**Possible follow-ups:**
- What would you do if the design required a 3.3V single-ended signal in the same bank as a 1.8V differential interface, and there was no way to move it to another bank?
- How would you handle a situation where the differential pair you need is only available in a bank that's already fully occupied by single-ended signals?

## Q4: How would you approach designing the reset architecture for a high-speed FPGA design that contains multiple clock domains, a DDR memory controller, and high-speed transceiver links, where an improperly sequenced reset can leave the device in a non-functional state?
**Answer:** Reset architecture in a multi-domain design is really a sequencing and synchronization problem, and getting it wrong produces exactly the kind of failure where the device configures but never becomes functional. I'd approach it in layers.

First, I'd define a single, unambiguous reset source — typically an external reset pin or a power-good signal — and treat it as asynchronous. That signal then has to be synchronized into each clock domain it touches, using a standard two-flop synchronizer or a reset synchronizer that asserts asynchronously and de-asserts synchronously. The reason for asynchronous assertion is that you want the reset to take effect immediately even if the clock isn't running yet; the reason for synchronous de-assertion is that you want all flops in a domain to come out of reset on the same clock edge, avoiding the classic problem where some flops release a cycle early and the state machine starts in an illegal state.

Second, I'd define the order in which the domains are allowed to come out of reset. The DDR memory controller, for example, needs its PLLs locked and its calibration to complete before the rest of the design starts issuing transactions. The transceiver links need their reference clocks stable and their reset sequence completed before the application logic starts sending data. So I'd build a reset controller — either in fabric or using the device's built-in reset management — that holds each domain in reset until its prerequisites are met, and only then releases it.

Third, I'd make sure the reset controller itself is robust. It should have a timeout or a watchdog so that if a PLL never locks, the system doesn't hang silently. It should also provide a way to re-trigger a partial reset — for example, if a transceiver link loses lock, you may want to reset just that link without resetting the whole device.

Finally, I'd verify the reset architecture in simulation with the actual power-up sequence, including the case where the external reset is released before the clocks are stable, and I'd test it on hardware by deliberately violating the sequence — releasing reset early, power-cycling rapidly — to confirm the design recovers gracefully rather than locking up.

**Possible follow-ups:**
- How would you handle a reset that needs to cross from a domain that's already running into a domain whose clock is not yet active?
- What would you do if the DDR controller's calibration occasionally failed after a reset, and the failure was correlated with the order in which the PLLs locked?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?
**Answer:** The first thing I'd do is separate the technical issue from the interpersonal one. The technical issue is real and non-negotiable: a signal that crosses clock domains without synchronization is a metastability hazard, and "stable long enough" is not a valid argument because it depends on the phase relationship between the two clocks, which is not controlled. The interpersonal issue is that the engineer has proposed something they believe is correct, and I want to correct the design without making them defensive or shutting down the review.

So I'd start by asking questions rather than making assertions. I'd ask them to walk me through the timing: what's the setup and hold window at the destination flop, what's the clock period on each side, and what's the worst-case phase relationship? Usually, walking through the numbers makes the problem visible without me having to say "you're wrong." If the signal is truly stable for many cycles of the destination clock, that's a useful property — but it doesn't eliminate the need for synchronization; it just means a simple two-flop synchronizer is sufficient, rather than a handshake or a FIFO.

I'd then explain the specific failure mode: metastability can propagate through the design and cause intermittent, hard-to-reproduce failures that may not show up in simulation or even in bench testing, but will show up in the field. For a data acquisition board, that's a serious risk. I'd also point out that the fix is cheap — a two-flop synchronizer costs almost nothing in area or latency — so there's no good reason not to do it.

If the engineer pushed back, I'd suggest we look at it together with the vendor's CDC linting tool or a formal CDC check, which would flag the unsynchronized crossing. That turns it from a disagreement between me and them into a finding from a tool, which is easier to accept. And I'd make sure the review process itself captures this — if the CDC check isn't already part of our sign-off, that's a gap I'd want to close.

The broader lesson I'd take from this is that design reviews need to include CDC checking as a standard item, not something that depends on a reviewer happening to notice it. If a junior engineer made this mistake, it's likely because the process didn't catch it earlier, and that's on the process as much as on them.

**Possible follow-ups:**
- How would you handle it if the engineer agreed with you in the review but then didn't actually make the change before the design was frozen?
- What would you do if the signal in question was on a path where adding a synchronizer would add latency that the system couldn't tolerate?