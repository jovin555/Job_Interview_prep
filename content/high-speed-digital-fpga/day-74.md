# high-speed-digital-fpga — Day 74

## Q1: How would you approach designing the clock domain crossing for a multi-bit Gray-coded counter value that increments continuously in a fast domain (e.g., 250 MHz) and must be sampled by a slower domain (e.g., 50 MHz) for logging, where the sampled value must always be a coherent snapshot and never a corrupted mix of bits?

**Answer:** The key insight is that a Gray code guarantees only one bit changes per increment, so a value sampled mid-transition can be off by at most one count — it can never be a corrupted mix of unrelated bits. That property is what makes Gray coding the right encoding choice here, but it does not by itself solve metastability: the individual bits still need to be synchronized before they are recombined.

The approach is: keep the counter in binary in the fast domain, convert to Gray for the crossing, then pass each Gray bit through a two-flop synchronizer in the destination domain. Because only one bit is in flight at a time, the worst case is that the destination captures either the old or the new value — both are valid, adjacent counts. After synchronization, convert back to binary in the destination domain for logging or display.

Two things I would be careful about. First, the synchronizer must be applied to the Gray-coded value, not the binary value — synchronizing binary bits individually is exactly the failure mode this scheme exists to avoid. Second, the destination must not sample faster than the source can produce a stable Gray value; if the source increments faster than the destination's synchronizer latency, the destination can skip counts, which is usually acceptable for logging but must be understood and documented.

I would also add a small amount of margin: place the Gray conversion and the synchronizer flops close together in the floorplan, and constrain them so the tools don't retime or duplicate logic across the boundary. A CDC lint check should flag any path that crosses without a synchronizer, so I would run that as a gate before sign-off.

**Possible follow-ups:**
- What happens if the destination domain needs to detect that the counter has wrapped, and how does Gray coding affect that?
- How would you verify this CDC in simulation, given that metastability itself is not modeled in RTL?

## Q2: How would you approach debugging an FPGA design where the DDR3 memory interface passes its built-in calibration and memory test at power-up, but fails intermittently only after the device has been running for several minutes and the board has warmed up?

**Answer:** A failure that appears only after warm-up points strongly at a temperature-dependent timing or analog margin issue rather than a logic bug, so I would treat it as a margin problem first and a functional problem second.

I would start by characterizing the failure: does it correlate with a specific temperature threshold, a specific access pattern, or a specific bank? If the built-in memory test passes cold and fails warm, I would re-run the test at elevated temperature and capture which addresses or banks fail. That narrows whether it is a data-path timing issue, a calibration drift issue, or a power/thermal issue.

On the timing side, the most likely culprits are the read/write leveling and the DQS-to-DQ relationship, both of which shift with temperature because the delay elements and the I/O buffers drift. If the calibration was performed once at power-up and never re-run, the margins that were valid cold may be insufficient warm. I would check whether the controller supports periodic re-calibration or temperature-compensated delay adjustment, and whether the calibration window has enough margin on both sides.

On the analog side, I would look at the memory rail: does the supply sag or ripple more when warm, and does the VREF track correctly? I would also check the ODT and drive-strength settings — a setting that is marginal at one temperature can fail at another. And I would confirm the thermal design is actually keeping the memory and the FPGA within their specified ranges, because a thermal problem masquerading as a timing problem is easy to chase in the wrong direction.

The practical fix is usually to widen the calibration window, add temperature-aware re-calibration, or adjust the termination and drive settings so the eye has margin across the full temperature range, then verify with a soak test that runs the interface at temperature for an extended period.

**Possible follow-ups:**
- How would you distinguish a calibration-drift problem from a genuine signal-integrity problem on the board?
- What would you change in the bring-up procedure to catch this class of issue before it reaches production?

## Q3: How would you approach designing the return-current path for a high-speed digital board where a signal transitions between two reference planes (e.g., from a ground plane to a power plane) on its way through a via?

**Answer:** The return current for a high-speed signal follows the path of least impedance, which at high frequency means it flows in the reference plane directly beneath the trace. When a signal via transitions from one reference plane to another, the return current has to find a way to get from the first plane to the second — and if there is no deliberate path, it will find one through whatever parasitic capacitance or unintended coupling exists, which is exactly where EMI and signal-integrity problems come from.

The standard solution is to place a stitching capacitor (or a set of them) close to the signal via, connecting the two reference planes. The capacitor provides a low-impedance path for the return current at the frequencies of interest, so the return current does not have to detour across the board. The capacitor value and placement matter: it should be small enough to be effective at the signal's frequency content, and it should be placed within a fraction of a wavelength of the via so the loop area stays small.

If the two planes are both ground, a stitching via is usually sufficient and is preferable to a capacitor because it is a direct connection. If one plane is a power plane, a stitching capacitor is the usual answer, and I would also check whether the plane pair has enough distributed capacitance to help at higher frequencies.

I would also look at the broader stack-up: if the design has many signals transitioning between the same two planes, a single stitching capacitor may not be enough, and I would consider whether the stack-up can be arranged so that high-speed signals reference a single continuous ground plane for their entire route. That is the cleanest solution and avoids the problem entirely.

**Possible follow-ups:**
- How would you decide how many stitching capacitors to place and where?
- What are the symptoms you would expect to see in the lab if the return path were inadequate?

## Q4: How would you approach choosing between a global clock network and a regional/banked clock resource for a logic block that only needs to run at a modest rate, when the device's global clock resources are nearly exhausted?

**Answer:** The decision comes down to what the logic actually needs and what the device can afford. Global clock networks are a scarce resource, and they are valuable precisely because they reach every corner of the device with low skew. If a logic block only runs at a modest rate and is physically localized, it usually does not need that reach, so a regional or banked clock resource is the better fit — it frees the global resource for the blocks that genuinely need it.

I would start by confirming the block's actual requirements: what frequency does it run at, how much skew can it tolerate, and is it confined to one region of the floorplan? If the block is localized and the frequency is low enough that regional skew is acceptable, a regional clock is the natural choice. If the block is spread across the device or needs tight skew between distant flops, a global clock may still be necessary even at a modest rate.

I would also consider whether the block can share a clock with another block that already has a global resource, rather than consuming a new one. And I would check whether the regional clock resource can be driven from the same source as the global clock, so the two domains remain related and the CDC between them is simple.

The trade-off is not just resource count — it is also verification. A regional clock may have different skew and jitter characteristics than a global clock, so the timing constraints and the CDC analysis need to reflect that. I would make the choice explicit in the constraints and document why the regional resource was used, so a later reviewer does not "fix" it by promoting it to a global clock and consuming a resource that was needed elsewhere.

**Possible follow-ups:**
- What are the risks of using a regional clock for a block that later needs to communicate with logic in a different region?
- How would you verify that the regional clock's skew is acceptable for the block's timing?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** I would treat this as a teaching moment rather than a confrontation, because the engineer's reasoning is a common and understandable mistake — it is based on the intuition that a slow-changing signal is safe, which is not how metastability works.

First, I would make sure I understand the signal: how often does it change, how long is it stable, and what is the relationship between the two clocks? That tells me whether this is a genuine CDC violation or whether there is a legitimate reason the signal is safe (for example, if it is already synchronized elsewhere, or if it is a quasi-static configuration value that is only changed when the consuming domain is held in reset). I would not assume the engineer is wrong without checking.

If it is a genuine violation, I would explain the mechanism: a flop sampling an asynchronous input can go metastable, and the probability of that happening depends on the setup/hold window and the clock relationship, not on how long the signal is stable. A signal that is stable for milliseconds can still be captured during a transition if the transition happens to align with the sampling clock edge. The fix is a proper synchronizer — typically two flops for a single-bit signal, or a handshake or FIFO for a multi-bit bus — and the cost is small compared to the risk.

I would also make the point that this is exactly the kind of issue that a CDC lint tool is designed to catch, and that the review process exists to catch it before it becomes an intermittent field failure that is very hard to debug. I would ask the engineer to add the synchronizer and re-run the CDC check, and I would follow up to confirm it is resolved.

The tone matters: I want the engineer to leave the review understanding why the synchronizer is necessary, not feeling that they were caught out. That is how the team builds the habit of checking for this class of issue on their own.

**Possible follow-ups:**
- How would you handle it if the engineer pushed back and argued that the synchronizer adds latency the design cannot afford?
- What would you do if you found this same pattern in several places in the design, suggesting a broader gap in the team's CDC awareness?