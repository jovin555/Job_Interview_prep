# high-speed-digital-fpga — Day 89

## Q1: How would you approach designing the power-up and configuration sequence for an FPGA that loads its bitstream from external flash, when the flash device itself has a non-trivial access latency and the board may be power-cycled rapidly?

**Answer:** The core problem is that configuration is a multi-stage handshake with timing dependencies on both the FPGA side and the flash side, and rapid power cycling can violate assumptions in either. I'd structure the approach around four things.

First, define the power sequencing requirements explicitly. The FPGA's core, auxiliary, and I/O rails have a specified ramp order and ramp-rate window, and the configuration logic must not be released from reset until all rails are within tolerance and the device's internal power-good signal is valid. I'd use a supervisor or sequencer with a defined reset-release delay rather than relying on RC delays, and I'd make sure the flash's own supply is sequenced so it's ready before the FPGA starts issuing read commands.

Second, account for flash wake-up latency. Many serial configuration flashes have a power-up or deep-power-down exit time (tens to hundreds of microseconds) before they respond to commands. If the FPGA's configuration controller starts clocking immediately after power-good, it may see the flash as unresponsive and either retry or fail. The fix is either to hold the FPGA's configuration start (via its program/init pin or a configuration-controller delay setting) until the flash is known ready, or to use a flash part whose wake-up time is comfortably inside the FPGA's own configuration start-up window. I'd verify this against both datasheets with margin, not just typical values.

Third, handle rapid power cycling. The danger is a brownout where the FPGA resets but the flash hasn't fully discharged, so the flash is in an indeterminate state when the next configuration attempt begins. I'd add a proper brownout detector with hysteresis that holds the FPGA in reset until the supply has fallen below a threshold and recovered cleanly, and I'd ensure the flash's reset or hold pin is asserted during the low-voltage window. A dedicated reset supervisor with a minimum reset pulse width is more reliable than a simple threshold comparator here.

Fourth, verify the sequence. I'd characterize the power-up with a scope capture of all rails, the FPGA's init/done signals, and the flash's chip-select and clock activity, at both slow and fast ramp rates and at temperature extremes. I'd also deliberately test rapid power cycling — short off-times, repeated cycles — to confirm the board always configures. If the design supports a fallback image, I'd verify that path too, since a failed configuration should never leave the board unbootable.

**Possible follow-ups:** How would you decide whether to add an external reset supervisor versus relying on the FPGA's internal power-on reset? What would you check first if the board configured reliably on the bench but failed intermittently in the field after power interruptions?

## Q2: How would you approach choosing between a global clock network and a regional/banked clock resource for a logic block that only needs to run at a modest rate, when the device's global clock resources are nearly exhausted?

**Answer:** The decision is really about resource economics and clock quality trade-offs, not just "which one is available."

Global clock networks are a scarce, high-fanout resource with low skew and low jitter, and they're the right choice for clocks that must reach many destinations spread across the die — the system clock, memory controller clocks, transceiver-related clocks. Regional or banked clock resources reach a limited physical region but are more plentiful, and they can have somewhat different insertion delay and skew characteristics. When global resources are nearly exhausted, the question becomes: does this block's clock actually need to reach the whole die, or does it only need to reach logic that can be placed within one region?

I'd start by confirming the block's fanout and placement freedom. If the logic is small and can be constrained to a single clock region, a regional resource is a clean fit — I'd floorplan the block into that region and constrain it so the tool doesn't spread it. If the logic must be spread across regions, a regional clock won't reach it, and I'd need to either free up a global resource elsewhere or restructure.

Freeing a global resource is often the better answer than forcing a regional clock. Common wins: a clock that's only used by a small block can be moved to a regional resource; a divided or gated version of an existing global clock can be generated locally rather than occupying its own global net; a clock that's actually static or rarely toggling can be replaced with a synchronous enable on an existing clock instead of a separate clock domain. I'd audit the clocking architecture before adding pressure.

I'd also weigh the quality cost. If the modest-rate block is timing-tolerant, a regional clock's slightly worse skew is fine. But if it interfaces to logic on a global clock, the CDC between them still needs proper synchronization regardless of which network each side uses — the network choice doesn't excuse the CDC. And I'd check whether the regional resource can actually be reached by the clock source pin or MMCM/PLL output in question; not every clock source can drive every regional net, and the tool may silently route it suboptimally if I don't constrain it.

Finally, I'd verify with the timing report that the chosen network meets the block's setup/hold with margin, and check the clock interaction report for any unintended paths between the two networks.

**Possible follow-ups:** What are the risks of letting the tool automatically promote a regional clock to a global one, and how would you prevent that? How would you handle a block that outgrows its clock region after a later logic change?

## Q3: How would you approach mitigating via stub effects on a high-speed serial channel that must transition between the top and bottom layers of a thick backplane?

**Answer:** A via that passes through a thick backplane but is only used for a layer transition leaves an unused portion — the stub — hanging off the signal path. At multi-gigabit rates that stub is a transmission-line branch, and it produces a resonance that shows up as insertion-loss notches and return-loss peaks at frequencies determined by the stub's electrical length. The longer the stub relative to the data rate's frequency content, the more it degrades the eye.

The first-line approach is to eliminate the stub rather than compensate for it. Back-drilling (controlled-depth drilling) removes the unused barrel below the last used layer, shortening the stub dramatically. This is the standard fix for thick backplanes and is usually specified in the fabrication notes for any layer transition on a high-speed channel. The trade-off is cost and drill-depth tolerance — back-drill depth must be controlled so it doesn't damage the used portion of the barrel, and the residual stub after back-drilling still needs to be short enough for the data rate.

If back-drilling isn't available or the residual stub is still marginal, the next lever is via design itself. A smaller drill and pad reduces the stub's capacitance and the discontinuity; antipads sized correctly on unused layers reduce parasitic coupling. For very high rates, blind or buried vias — or laser-drilled microvias in an HDI stack-up — avoid the through-stub entirely, at higher fabrication cost.

The third lever is to move the transition. If the channel must go from top to bottom, routing it so the layer change happens at a connector or at a point where the stub can be kept short, or using a different layer pair that minimizes the unused barrel, reduces the problem without extra process steps.

I'd verify the result with 3D electromagnetic simulation of the via transition extracted into the channel model, then check the channel's insertion loss and return loss against the link budget, and confirm the eye at the receiver with the SerDes' equalization enabled. On hardware, I'd measure with a VNA on a test coupon or the actual channel and compare against the simulated S-parameters.

**Possible follow-ups:** How would you decide how much residual stub is acceptable for a given data rate? What would you do if simulation showed the channel marginal but the board was already fabricated?

## Q4: How would you approach designing the decoupling network for an FPGA's core voltage rail, where the rail supplies a large, fast-changing current to the fabric and must stay within a tight tolerance across a broad frequency range?

**Answer:** The core rail's decoupling problem is a broadband impedance problem: the goal is to keep the power distribution network's impedance below a target across the frequency range where the fabric draws transient current, so that the resulting voltage deviation stays within tolerance.

I'd start from the current profile. The fabric's transient demand has a magnitude and a slew rate, and the allowable voltage deviation divided by that current gives a target impedance. That target, plus the frequency band of interest, defines what the network must achieve.

Then I'd build the network in layers by frequency. Bulk capacitance handles the low-frequency end and the slower, larger transients — it's the reservoir that the regulator's control loop is too slow to supply. Ceramic decoupling capacitors handle the mid-to-high frequency range, and their placement matters as much as their value: they must be close to the FPGA's power pins with short, low-inductance connections to the planes, because the mounting inductance often dominates the capacitor's own ESL at high frequency. Multiple values in parallel spread the impedance minimums and reduce the anti-resonance peaks between them. At the very high end, the on-die and package capacitance takes over, and the PCB's job is to not get in the way — a thin dielectric between power and ground planes gives distributed plane capacitance and a low-inductance path.

The critical design discipline is modeling, not guessing. I'd extract the plane and via parasitics, include the capacitor models with their mounting inductance, and simulate the network's impedance versus frequency, checking for anti-resonance peaks that exceed the target. Capacitor placement and via count are the usual culprits when the simulated impedance has a peak — more vias per capacitor pad lowers mounting inductance, and spreading values avoids aligning their self-resonances.

I'd verify on hardware with a VNA measurement of the rail's impedance (or a PDN probe) and, more importantly, with a scope measurement of the rail voltage under realistic fabric load — a load pattern that exercises the fabric at its worst-case switching. The scope measurement with a low-inductance probe tip is the ground truth, because it captures the actual transient response including the regulator's contribution.

**Possible follow-ups:** How would you handle a rail where the simulated impedance meets target but the measured transient still exceeds tolerance? What role does the voltage regulator's control loop bandwidth play, and how would you coordinate it with the decoupling network?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** I'd treat this as a teaching moment first and a correction second, because the engineer's reasoning is a very common and understandable misconception — and the fix only sticks if they understand why the reasoning fails.

I'd start by acknowledging the intuition: yes, the signal is stable for many destination clock cycles in the nominal case, so it's tempting to think a direct connection is fine. Then I'd walk through why it isn't. The problem isn't the steady-state value; it's the transition. When the source signal changes, it can change arbitrarily close to a destination clock edge, and the destination flop can then go metastable — its output may be neither high nor low for a time, and different destination flops sampling the same signal can resolve differently. "Stable long enough" doesn't help if the change happens to land in the setup/hold window; it just makes the failure rare and intermittent, which is worse because it escapes simulation and bench testing and shows up in the field.

I'd then make it concrete with the specific case in front of us: is this a single-bit control signal or a multi-bit bus? A single bit needs a proper two-flop synchronizer (or a handshake if the destination needs to act on an edge reliably). A multi-bit bus connected directly is worse — even with per-bit synchronizers, the bits can resolve on different cycles, so the destination can capture a mix of old and new values. That needs a handshake, a Gray-coded encoding, or an asynchronous FIFO depending on the data's nature. I'd ask the engineer which category their signal falls into, so the discussion lands on their actual design rather than an abstract rule.

On process, I'd make the review outcome a required change with a clear rationale documented, and I'd add a CDC check to our review checklist and lint/CDC tooling so this class of issue is caught systematically rather than depending on a reviewer noticing. I'd frame the tooling as protecting the whole team, not singling out the engineer.

Throughout, I'd keep the tone collegial — the goal is a correct design and an engineer who internalizes the principle, not a "gotcha." I'd follow up after the fix to confirm they can explain the reasoning themselves, which is the real test of whether the lesson took.

**Possible follow-ups:** How would you handle it if the engineer pushed back and pointed to a bench test where the design "worked fine"? What would you add to the design review checklist to catch CDC issues earlier?
