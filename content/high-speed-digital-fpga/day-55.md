# high-speed-digital-fpga — Day 55

## Q1: How would you approach designing the decoupling and bulk capacitance network for an FPGA's transceiver power rails, where the rails have both high-frequency switching noise and slower, larger current transients, and how would you verify the network is adequate before committing to the layout?

**Answer:** Transceiver rails are a good example of a PDN that has to satisfy two very different frequency regimes at once, so I'd approach it as a layered problem rather than a single capacitor selection exercise.

First, I'd characterize the load. The transceiver supply draws a relatively steady DC current plus high-frequency switching current from the serializers/deserializers, and it can also see slower, larger transients when channels power up, when the CDR re-locks, or when the link rate changes. Those two behaviors need different parts of the impedance curve to be low.

I'd work from the target impedance. Given the rail voltage and the allowed ripple (often a tight percentage for transceiver rails because jitter on the supply translates into jitter on the serial output), I'd compute Z_target = ΔV_allowed / ΔI_transient. That gives a ceiling on the impedance the network must present across the frequency band of interest.

Then I'd build the network in layers:
- **Bulk electrolytic or polymer caps** near the regulator to handle the low-frequency, high-energy transients and to keep the regulator's control loop stable.
- **Mid-frequency ceramics** (e.g., a spread of 1 µF–10 µF) to bridge the gap between the bulk caps and the high-frequency decoupling.
- **High-frequency ceramics** (e.g., 0.1 µF and smaller) placed as close as physically possible to each transceiver supply pin, with short, wide traces and a via directly to the ground plane for the return path.

The key insight is that the network is a parallel impedance, and the anti-resonances between capacitor values and between the caps and the plane inductance are what usually bite you. So I'd simulate the network as an impedance vs. frequency plot — including the ESL of each capacitor, the mounting inductance of the vias and traces, and the plane spreading inductance — and check that the impedance stays below Z_target across the band, with no significant anti-resonance peaks poking above it.

For verification before layout sign-off, I'd:
- Run the PDN impedance simulation with realistic parasitics extracted from the intended stack-up and placement.
- Check that each decoupling cap's loop area is small and its via pair is close together.
- Confirm the plane pair feeding the rail is continuous under the transceiver region, with no splits that force the return current to detour.
- If the tooling supports it, run a transient simulation with a representative current step to see the actual voltage excursion.

After the board comes back, I'd verify with a scope and a low-inductance probe (or a coax-mounted probe) at the transceiver pins under realistic link activity, looking at both the DC level and the AC ripple, and if possible inject a current step to measure the actual transient response. If the measured ripple is worse than predicted, the usual culprits are mounting inductance, a plane split, or a capacitor that isn't actually where the schematic says it is.

**Possible follow-ups:**
- How would you decide whether to use a single large bulk capacitor or several smaller ones in parallel for the low-frequency end?
- If the measured ripple is higher than simulation predicted, what's your systematic approach to isolating whether it's a placement issue, a plane issue, or a capacitor selection issue?

---

## Q2: How would you approach debugging an FPGA design where the transceiver link passes its built-in PRBS checker at the physical layer, but application-level data is occasionally corrupted, and the corruption only appears at full line rate?

**Answer:** This is a classic "the PHY is fine, the problem is above the PHY" situation, and the fact that it only shows up at full line rate is a strong clue that it's a timing or flow-control margin issue rather than a hard logic bug.

I'd start by confirming the boundary. The PRBS checker runs inside the transceiver's physical coding sublayer, so it's verifying the serial link and the CDR, but it's not exercising the fabric-side interface, the gearbox, the FIFO between the transceiver and the user logic, or the user logic itself. So the first thing I'd do is move the test point up: instead of relying on the built-in PRBS checker, I'd inject a known pattern from the user logic, loop it back through the transceiver, and check it in the user logic. That tells me whether the corruption is happening in the transceiver-to-fabric path or in the application logic.

If the loopback through the fabric is clean but the real application data is corrupted, the problem is likely in how the application logic handles the data — for example, a CDC between the transceiver's recovered clock domain and the application clock domain, a FIFO that's overflowing or underflowing at full rate, or a backpressure/flow-control signal that isn't being respected.

If the loopback through the fabric is also corrupted, I'd focus on the transceiver-to-fabric interface:
- **Clock domain crossing:** the transceiver's RX clock is recovered from the incoming data and is asynchronous to the application clock. If the design crosses that boundary with anything other than a proper FIFO or a handshake, marginal timing at full rate can cause occasional corruption.
- **FIFO depth and flags:** at full line rate, the FIFO between the transceiver and the user logic has the least margin. If the FIFO is too shallow, or if the almost-full/almost-empty thresholds are set wrong, you can get occasional overflow/underflow that only shows up when the link is saturated.
- **Gearbox / width conversion:** if the transceiver outputs a different width than the user logic expects, the gearbox logic can have a subtle bug that only manifests when data is flowing continuously.
- **Reset and initialization:** if the RX FIFO or the gearbox isn't properly reset after the link comes up, the first few words can be garbage, but that wouldn't explain intermittent corruption at full rate.

I'd also check the obvious: is the corruption actually corruption, or is it a framing/alignment issue where the receiver is occasionally slipping by a word? That would point to a comma/alignment problem rather than a data integrity problem.

For instrumentation, I'd use the transceiver's built-in eye scan and error counters if available, and I'd add a fabric-side checker that compares transmitted and received data with a sequence number or a known pattern, so I can catch the exact moment of corruption and correlate it with link state, FIFO flags, and clock domain activity.

**Possible follow-ups:**
- How would you distinguish between a FIFO overflow and a CDC metastability issue as the root cause?
- If the corruption only happens after the link has been running for a while, how would that change your debugging approach?

---

## Q3: How would you approach selecting and configuring the I/O standards and pin assignments for an FPGA bank that must simultaneously support a high-speed differential interface and several single-ended signals at different voltages, given that I/O bank voltage and standard choices are constrained by the bank's VCCO?

**Answer:** This is fundamentally a constraint-satisfaction problem, and the right approach is to work from the bank's electrical constraints backward to the pin assignment, not the other way around.

The first thing I'd do is understand the bank's VCCO constraint. Each I/O bank has a single VCCO supply that sets the reference for the single-ended I/O standards in that bank. Differential standards like LVDS often have their own requirements — some are true differential and don't depend on VCCO in the same way, but many FPGA families still tie the differential pair's common-mode and termination behavior to the bank's supply. So the VCCO choice is usually driven by the single-ended signals, and then I have to check whether the differential interface can live with that VCCO.

I'd build a table of every signal that needs to go in the bank:
- Signal name, direction, voltage level, standard (LVCMOS 3.3V, LVCMOS 1.8V, SSTL, LVDS, etc.), and any special requirements (true differential, internal termination, etc.).

Then I'd group them:
- **Signals that must be in the same bank** because they share a VCCO requirement.
- **Signals that can be moved** to another bank if the voltage conflict is irreconcilable.
- **Signals that have hard pin constraints** because of board routing, connector pinout, or timing.

The conflicts usually fall into a few categories:
- **VCCO conflict:** a 3.3V single-ended signal and a 1.8V single-ended signal can't share a bank unless the FPGA supports per-pin voltage selection (some do, via a separate VCCIO per pin group, but that's family-specific).
- **Differential/single-ended conflict:** some FPGA families don't allow certain differential standards in a bank that also has single-ended signals at a particular VCCO, or the differential pair's pins are fixed and can't be reassigned.
- **Reference voltage conflict:** SSTL and HSTL need a VREF, and not every pin in the bank can be a VREF pin.

My resolution strategy is usually:
1. Put the differential interface in its own bank if possible, with a VCCO that matches its requirement.
2. Group single-ended signals by voltage into banks that share a VCCO.
3. If a signal must be in a specific bank because of a hard constraint, check whether the bank's VCCO can be changed to accommodate it, and whether that breaks anything else.
4. Use level shifters on the board if the FPGA can't natively support the mix — sometimes that's cheaper than respinning the pinout.

For pin assignment, I'd use the FPGA vendor's pin planning tool to check for:
- **Bank voltage compatibility** (the tool will flag illegal combinations).
- **Differential pair pin locations** (they're usually fixed pairs, and the tool will tell you which pins can form a pair).
- **Clock-capable pins** if any of the signals need to go to a clock input.
- **I/O standard support per pin** (not every pin supports every standard).

I'd also check the board-level implications: differential pairs need controlled impedance and length matching, single-ended signals may need series termination, and the connector pinout has to match. So the pin assignment isn't done until the board layout can actually route it.

**Possible follow-ups:**
- What would you do if the differential interface and a critical single-ended signal both had to be in the same bank, but their VCCO requirements conflicted?
- How would you verify that the chosen I/O standards and pin assignments are actually legal for the target FPGA before committing to the board layout?

---

## Q4: How would you approach designing the reset architecture for a high-speed FPGA design that contains multiple clock domains, a DDR memory controller, and high-speed transceiver links, where an improperly sequenced reset can leave the device in a non-functional state?

**Answer:** Reset architecture in a multi-domain design is one of those things that's easy to get wrong and hard to debug, because the failure mode is often "it works most of the time" rather than a clean break. I'd approach it as a deliberate, documented architecture rather than a collection of ad-hoc resets.

The core principles I'd follow:

**1. Separate reset from clock domain.**
Each clock domain needs its own reset that is synchronized to that domain's clock. An asynchronous reset that's de-asserted asynchronously can cause metastability or partial reset of state machines. The standard pattern is an asynchronous assert, synchronous de-assert reset synchronizer per domain. That way the reset is asserted immediately (so the domain is held in reset even if the clock isn't running yet), but the release is synchronized to the domain's clock.

**2. Define a reset hierarchy.**
Not all resets are equal. I'd define:
- **Power-on reset (POR):** the master reset that comes from the board's power-good signal or a supervisor IC. This is the root of the tree.
- **System reset:** derived from POR, possibly gated by a software-controlled reset register or a watchdog.
- **Subsystem resets:** per-subsystem resets for the DDR controller, the transceiver links, the application logic, etc. These can be asserted independently for debug or re-initialization.
- **Local resets:** per-module resets for things like FIFOs, state machines, and counters.

**3. Sequence the release.**
The order in which subsystems come out of reset matters. For example:
- The PLLs/MMCMs need to lock before the logic they clock can be released from reset. So the reset controller should wait for the PLL lock signal before releasing the domains that depend on it.
- The DDR memory controller needs to complete its initialization and calibration before the application logic that accesses memory is released. So the DDR controller's "ready" signal should gate the release of the application domain.
- The transceiver links need to complete their reset and initialization sequence, and the CDR needs to lock, before the application logic that uses the link is released.
- If there's a processor or a configuration interface, it may need to be up before the rest of the system.

I'd implement this as a small reset controller — either a state machine or a set of counters — that sequences the release of each subsystem based on the appropriate "ready" signals, with timeouts so that a stuck subsystem doesn't hang the whole system forever.

**4. Handle the "reset while running" case.**
If a subsystem can be reset independently while the rest of the system is running, I'd make sure that:
- The reset is properly synchronized into the subsystem's clock domain.
- Any interfaces to the subsystem are quiesced before the reset is asserted, so the subsystem doesn't see a partial transaction.
- The subsystem's outputs are driven to a safe state during reset, so downstream logic doesn't see garbage.

**5. Document and verify.**
I'd draw the reset tree explicitly — which reset feeds which domain, what gates its release, and what the expected sequence is. Then I'd verify it in simulation with a test that asserts and releases resets in the expected order, and also with a test that asserts resets out of order or at random times to make sure the design doesn't lock up.

For debug, I'd bring the key reset and "ready" signals out to a debug header or a logic analyzer, so that if the board comes up non-functional, I can see which subsystem didn't release and why.

**Possible follow-ups:**
- How would you handle a situation where a subsystem's "ready" signal never asserts, so the reset controller times out — what should the system do?
- How would you verify the reset architecture in simulation without spending excessive simulation time waiting for PLL lock and DDR calibration?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** This is a situation where the technical issue and the interpersonal issue need to be handled together, because the engineer's reasoning is a common and understandable misconception, and the goal is to get them to see why it's wrong rather than to just overrule them.

First, I'd make sure I understand the design correctly. I'd ask the engineer to walk me through the signal: where it's generated, where it's consumed, what the two clock frequencies are, how often the signal changes, and what the consequences are if it's captured incorrectly. That does two things — it confirms my understanding, and it signals that I'm engaging with their design rather than just criticizing it.

Then I'd explain the actual problem, in a way that's grounded in the physics rather than just "the rules say so." The issue isn't whether the signal is stable long enough in the source domain — it's that the destination flop's setup and hold window is defined relative to the destination clock, and the source signal's transition can land anywhere relative to that window. If it lands inside the window, the flop can go metastable, and metastability can propagate unpredictably. "Stable long enough" in the source domain doesn't help if the transition happens to coincide with the destination clock edge. The probability is low per event, but over millions of events and across temperature and voltage variation, it will happen.

I'd also point out that the failure mode is exactly the kind of thing that's hard to debug: it may pass in the lab, pass in simulation (because RTL simulation doesn't model metastability), and then fail intermittently in the field. That's the worst kind of bug.

Then I'd move to the solution. For a single-bit control signal, the standard fix is a two-flop synchronizer in the destination domain, with the caveat that the signal must be stable for at least one destination clock period (or use a handshake or a pulse-stretcher if it's a pulse). For a multi-bit bus, a two-flop synchronizer per bit isn't enough — you need either a handshake, a FIFO, or a gray-coded counter, depending on the use case. I'd walk through which pattern fits their specific signal.

I'd also make it a teaching moment about the design review process: this is exactly why we review CDC paths explicitly, and I'd suggest that going forward, any signal that crosses a clock domain gets called out in the review and has a documented synchronization scheme. That turns the individual correction into a process improvement.

Finally, I'd follow up after the review to make sure the fix is implemented correctly and to check whether the engineer has other CDC paths in their design that might have the same issue. The goal is not just to fix this one signal, but to make sure the engineer internalizes the principle.

**Possible follow-ups:**
- How would you handle it if the engineer pushed back and said the two-flop synchronizer adds latency that their design can't tolerate?
- What would you do if you later found that the same engineer had used a similar unsynchronized crossing in another part of the design that had already been signed off?