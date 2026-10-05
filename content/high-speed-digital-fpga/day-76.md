# high-speed-digital-fpga — Day 76

## Q1: How would you approach designing the power-up and configuration sequence for an FPGA that loads its bitstream from a serial configuration flash device, where the flash has a non-trivial wake-up latency and the board may be power-cycled rapidly?

**Answer:** The core problem is that the FPGA's configuration controller starts driving its configuration clock and expecting data as soon as its internal power-on-reset releases, but the flash may still be in its own internal initialization or wake-up period. If the FPGA issues read commands before the flash is ready, the configuration engine either times out or latches garbage, and the failure is often intermittent because it depends on the relative ramp rates of the two supplies.

The approach is to treat configuration as a handshake rather than an assumption. First, I'd confirm from both datasheets the actual timing windows: the FPGA's minimum configuration-start delay after its rails are valid, and the flash's maximum wake-up and first-access-ready time. If the flash's worst-case ready time exceeds the FPGA's default start delay, the sequence needs to be gated externally — typically by holding the FPGA's configuration start (or its PROGRAM_B / nCONFIG equivalent) deasserted until a power-good signal from the flash supply plus a fixed delay has elapsed. A small supervisor or sequencer IC that asserts the FPGA's release only after both rails are stable and the flash delay has passed is the cleanest solution.

Second, I'd make the sequence robust to rapid power cycling. The danger with fast cycling is that bulk capacitance on one rail may not have fully discharged while another rail has already come up, so the FPGA can see a partial brown-out condition that leaves its configuration state machine in an undefined state. A power-fail detector that holds the FPGA in reset until all rails have dropped below a threshold before allowing a new power-up cycle prevents this. Some supervisors have a built-in "reset timeout" that guarantees a minimum reset assertion time regardless of how fast the rails cycle.

Third, I'd verify the design by testing the corner cases explicitly: slow ramp on the flash rail, fast ramp on the FPGA rail, and repeated power cycles at the shortest interval the system might realistically see. If the design relies on a delay, I'd want margin — not a delay tuned to typical silicon, but one that holds across temperature and component tolerance. And I'd confirm that the FPGA's configuration error flag is monitored, so a failed configuration can trigger a retry rather than leaving the board silently dead.

**Possible follow-ups:**
- How would you decide between adding an external supervisor and simply increasing the FPGA's internal configuration start delay?
- What would you check in the flash datasheet to confirm its worst-case ready time across temperature?

## Q2: How would you approach debugging an FPGA design where the device configures successfully and runs correctly for a period of time, but then the configuration appears to be lost — the device stops responding and requires a reconfiguration to recover?

**Answer:** The first thing to establish is whether the configuration is genuinely being lost or whether the device is still configured but has entered a non-functional state that looks like a lost configuration. These have very different root causes, so I'd start by observing the configuration status pins — the DONE/INIT signals and any CRC error flag. If DONE has dropped, the configuration memory has actually been disturbed or the device has been reset. If DONE is still asserted but the design is unresponsive, the problem is in the logic or clocking, not the configuration itself.

If DONE has dropped, the likely causes are a power supply transient that dipped below the configuration retention threshold, a glitch on the configuration reset pin, or a single-event or noise-induced corruption of the configuration memory. I'd scope the FPGA's core and auxiliary rails during the failure to look for a droop or a transient. A common culprit is a large current transient from an external load — a motor, a transceiver, or a high-current I/O bank — pulling the shared rail down momentarily. The fix is usually better decoupling, a stiffer regulator, or separating the noisy load onto its own rail.

If DONE is still high but the design is unresponsive, I'd look at the clocking. A PLL losing lock, a reference clock dropping out, or a clock enable being gated off by a state machine that has entered an illegal state can all produce this symptom. I'd check the PLL lock signal and the clock monitor if the device has one. I'd also consider whether the design has a watchdog or a recovery mechanism — if a state machine can get stuck, the design should have a way to detect that and re-initialize, rather than requiring a full reconfiguration.

A third possibility is thermal. If the failure correlates with the board warming up, a marginal timing path or a marginal power supply could be the cause, and the "lost configuration" is actually a timing failure that corrupts the state. I'd correlate the failure time with board temperature and, if possible, use the device's internal temperature sensor or an external thermocouple to confirm.

The systematic approach is to instrument the design with a heartbeat or status register that the host can poll, so the failure is detected immediately rather than after the system has been unresponsive for a while. That narrows the window for scoping and makes the failure reproducible.

**Possible follow-ups:**
- If the failure only occurs after hours of operation, how would you make it reproducible enough to debug?
- What design features would you add to allow the system to recover automatically without a full power cycle?

## Q3: How would you approach designing the clock domain crossing for a multi-bit Gray-coded counter value that increments continuously in a fast domain (e.g., 250 MHz) and must be sampled by a slower domain (e.g., 50 MHz) for logging, where the sampled value must always be a coherent snapshot and never a corrupted mix of bits?

**Answer:** The key property that makes Gray coding useful here is that only one bit changes between consecutive values, so a value sampled during a transition is either the old value or the new value — never a corrupted mix. That means a simple multi-flop synchronizer on each bit is sufficient for coherence, provided the Gray code is generated correctly and the counter is the only thing driving those bits.

The design has three parts. First, the counter itself must be a true Gray-coded counter, not a binary counter with a Gray encoder bolted on the output. If the binary-to-Gray conversion is combinational and the binary value is changing, the Gray output can glitch, and a glitch on a Gray-coded bus defeats the purpose. The safe approach is to register the Gray output directly — either use a dedicated Gray counter structure or register the encoder output so the Gray bus is stable for a full clock period before it crosses.

Second, the crossing itself is a standard two-flop synchronizer per bit in the destination domain. Because only one bit changes at a time, the worst case is that the destination samples the old value or the new value, both of which are valid. There's no need for handshaking or a FIFO, which keeps latency low and logic small.

Third, the destination domain must understand that the value it reads is a snapshot that may be one count stale. For logging, that's usually fine. If the application needs to detect that the counter has wrapped or that counts have been missed, the destination can compare consecutive samples and flag a discontinuity, but that's an application-level concern, not a CDC concern.

The subtle failure mode to watch for is a Gray counter that isn't actually Gray — for example, a counter that increments by more than one, or a reset that forces multiple bits to change simultaneously. I'd verify the Gray property in simulation by checking that exactly one bit differs between consecutive values across the full count range, including the wrap. I'd also run a CDC lint tool to confirm the synchronizers are recognized and that no unsynchronized paths exist.

**Possible follow-ups:**
- What happens if the counter is reset asynchronously while the destination domain is sampling it?
- How would you extend this approach if the counter needed to be read by three different clock domains?

## Q4: How would you approach choosing between a global clock network and a regional/banked clock resource for a logic block that only needs to run at a modest rate, when the device's global clock resources are nearly exhausted?

**Answer:** The decision comes down to what the logic block actually needs from its clock, and whether a global resource provides anything the block doesn't require. Global clock networks are designed for low skew and high fanout across the entire device, which is exactly what you need for a clock that drives logic spread across many regions. But that capability comes at a cost: global resources are limited, they consume more power, and using one for a small, localized block is wasteful.

If the block is confined to a single clock region or a small number of regions, a regional or banked clock resource is usually the better choice. Regional clocks have lower skew within their region than a global clock routed to the same region, and they free up the global resource for a clock that genuinely needs device-wide distribution. The trade-off is that a regional clock can't reach logic outside its region, so the block's placement has to be constrained to stay within the region. That's a floorplanning decision, and it needs to be made early — if the block later grows or moves, the regional clock may no longer be valid.

The other consideration is whether the block's clock needs to be phase-related to a global clock. If the block is part of a synchronous pipeline that spans regions, using a regional clock for part of it can introduce skew between the regional and global portions, which complicates timing closure. In that case, it may be worth freeing up a global resource by moving some other, less critical clock to a regional resource instead.

The practical approach is to inventory the clocks in the design, identify which ones genuinely need global distribution, and then assign the rest to regional or local resources. I'd also check whether any clocks can be gated or combined — sometimes two clocks that are never active simultaneously can share a resource. And I'd confirm with the vendor's clocking documentation which resources are available in the target device and what the placement constraints are, because the answer varies significantly between families.

**Possible follow-ups:**
- How would you verify that a regional clock's skew is acceptable for the block's timing requirements?
- What are the risks of using a regional clock for a block that later needs to communicate with logic in another region?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** The first thing I'd do is separate the technical issue from the review dynamic. The engineer has made a claim about timing that is testable, and the right response is to test it rather than to assert authority. I'd ask them to walk me through the timing: how long is the signal stable relative to the destination clock period, and what is the setup and hold window of the destination flop? If the signal is stable for many destination clock periods, that's a useful data point — but it doesn't eliminate the problem, because the issue isn't whether the signal is usually captured correctly, it's what happens at the boundary.

The key concept to explain is metastability. Even if the signal is stable for a long time, the transition edge can arrive at any phase relative to the destination clock. If it arrives within the setup/hold window, the destination flop can go metastable — its output can be an indeterminate value for a period of time, and that indeterminate value can propagate into downstream logic and cause a functional failure. The probability is low per event, but over millions of events and across many boards, it becomes a real failure rate. And the failure is data-dependent and temperature-dependent, which makes it very hard to debug in the field.

I'd also point out that the fix is cheap: a two-flop synchronizer costs two flops and a small amount of latency, and it reduces the metastability failure probability to a negligible level. There's no good reason to skip it. If the signal is a multi-bit bus, a simple two-flop synchronizer per bit isn't sufficient — the bits can be captured on different cycles, producing a corrupted value — so the correct approach depends on the signal type: a single-bit level signal can use a two-flop synchronizer, a single-bit pulse needs a pulse synchronizer or a toggle-based handshake, and a multi-bit bus needs either a handshake, a FIFO, or a Gray-coded encoding if the data is suitable.

The way I'd handle the review is to make it a teaching moment rather than a correction. I'd ask the engineer to add the synchronizer and to document the CDC in the design's CDC register, so the next reviewer can see that it was considered. I'd also suggest running a CDC lint tool as part of the review process, so this class of issue is caught systematically rather than depending on a reviewer noticing it. The goal is to fix the design and to improve the process, not to make the engineer feel singled out.

**Possible follow-ups:**
- How would you handle it if the engineer pushed back and said the synchronizer adds latency the design can't afford?
- What would you add to the design review checklist to catch this class of issue earlier?