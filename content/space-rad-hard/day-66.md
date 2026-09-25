# space-rad-hard — Day 66

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd treat this as three separable problems — source selection, fault isolation, and inrush management — and make sure each is solved independently so a failure in one doesn't cascade.

For source selection, the two 28V feeds should be ORed through a diode-OR or ideal-diode (ORing controller) scheme rather than a simple wired-OR, so that a short on one feed can't drag down the other. If I use ideal-diode controllers, I need to confirm they're either rad-tolerant or that their failure modes are benign — a controller that fails open just loses that feed, which is acceptable; one that fails short defeats the isolation. I'd also add per-feed current sensing so the system can detect and report which feed is faulted.

For fault isolation, each downstream load branch gets its own current-limiting or eFuse-style protection, sized so that a latch-up event in one load trips only that branch. The key design question is coordination: the branch protection must trip faster than the upstream feed protection, otherwise a single latched load takes out the whole rail. I'd work out the trip curves explicitly and leave margin between them.

For hot-swap, the concern is inrush into the load's bulk capacitance when a branch is enabled or when a feed is swapped in. I'd use a controlled slew-rate turn-on — either a hot-swap controller with a defined dV/dt or a series FET with a gate ramp — plus a current limit that tolerates the inrush but still catches a hard short. The bus itself shouldn't sag during this, so the upstream bulk capacitance and the source impedance need to be checked against the worst-case inrush.

Throughout, I'd derate the pass elements generously and prefer parts with either radiation data or well-understood, non-destructive failure modes. Latch-up in the protection circuitry itself is the thing that turns a single fault into a system loss, so the protection has to be at least as robust as what it's protecting.

**Possible follow-ups:**
- How would you verify the trip-coordination between branch and feed protection without actually shorting a live bus?
- If the ORing controller has no radiation data, how would you decide whether its failure mode is acceptable?

## Q2: How would you approach designing a radiation-tolerant current-sense circuit for a spacecraft power bus, where the sense resistor itself is exposed to radiation and its value may drift over the mission lifetime?

**Answer:** The core issue is that a sense resistor's value is the reference for every current measurement, so any drift — from TID, displacement damage, or thermal effects — shows up as a systematic error in every reading, not a random one. I'd approach it in layers.

First, part selection. I'd look for a sense element with radiation data, or at minimum a construction whose drift mechanism I understand. Metal-foil or bulk-metal-element resistors tend to be more stable than thin-film under radiation and temperature, but I'd want data rather than assumption. If no data exists, I'd budget for a characterization test on a sample lot.

Second, topology. A four-terminal (Kelvin) connection removes lead and solder-joint resistance from the measurement, which matters more as the sense value gets small. I'd also consider whether the sense element can be placed where it sees less dose — sometimes moving it behind a shield or away from a hot spot is cheaper than qualifying a better part.

Third, ratiometric or differential measurement. If the current-sense amplifier's gain reference and the ADC reference share the same drift, some of the error cancels. I'd look for opportunities to make the measurement ratiometric rather than absolute.

Fourth, in-situ calibration or cross-checking. If there's a second, independent way to estimate current — for example, from a known load and a measured voltage — the two can be compared and a slow drift flagged. This doesn't fix the drift but it makes it observable, which matters for a multi-year mission.

Finally, I'd derate the sense resistor's power dissipation well below its rating, since self-heating adds a thermal drift term on top of the radiation term, and the two can compound.

**Possible follow-ups:**
- How would you distinguish radiation-induced drift from thermal drift during ground testing?
- Would you consider a Hall-effect or magnetoresistive current sensor instead, and what trade-offs would that introduce?

## Q3: You are reviewing a design for a space-deployed system that uses a COTS FPGA for data processing. The design uses external configuration memory (flash) that is not radiation-hardened. How would you evaluate the risk of configuration upsets and what mitigation strategies would you recommend?

**Answer:** I'd separate the risk into two distinct failure modes, because they need different mitigations: upsets in the FPGA's own SRAM configuration memory (which the external flash doesn't protect against), and upsets in the external flash itself (which corrupt the source bitstream).

For the FPGA's configuration memory, the external flash is irrelevant — once configured, the FPGA holds its configuration in SRAM, and an SEU there can change logic behavior. Mitigations are scrubbing (periodically re-reading configuration and correcting against a golden copy), configuration memory ECC if the device supports it, and partial reconfiguration to repair detected errors. Without radiation data on the FPGA, I'd want to know its configuration-memory cross-section, or at least treat it as unknown and design for frequent detection and recovery.

For the external flash, the risk is that a bit flip in the stored bitstream means the FPGA configures incorrectly on the next boot — or worse, configures into a state that looks alive but is functionally wrong. Mitigations: store the bitstream with CRC or ECC and verify before configuration; keep a second, independent copy of the bitstream in a different physical location; and have the boot logic fall back to the redundant copy if the primary fails verification. If the flash is truly non-rad-hard, I'd also consider whether it can be scrubbed or refreshed periodically, or whether the mission profile allows a periodic re-load from a known-good source.

The overall recommendation would be: don't rely on any single mechanism. Combine configuration verification at boot, periodic scrubbing during operation, and a recovery path (reconfiguration or power-cycle) that's been tested. And I'd want the failure detection to be independent of the FPGA itself where possible, so a corrupted FPGA can't mask its own corruption.

**Possible follow-ups:**
- How would you test the recovery path on the ground without access to a radiation source?
- If the FPGA has no configuration ECC, what's your fallback for detecting configuration upsets?

## Q4: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a poor fit for a fault-tolerant space bus by default — it's single-ended, has no error detection beyond the ACK bit, and a single node holding SDA low can lock the entire bus. So the design has to add robustness that the protocol doesn't provide.

First, bus lock-up recovery. The standard technique is clock-stretching recovery: if the master detects SDA stuck low with no transaction in progress, it issues up to nine clock pulses to let the stuck slave release the line, then issues a STOP. I'd build this into the master's error handler and test it explicitly. If a node can lock the bus repeatedly, I'd want the ability to power-cycle or reset that node independently — which means each node needs its own switchable supply or reset line, not just a shared bus.

Second, data integrity. I'd add a CRC or checksum at the application layer, since I²C's ACK only confirms a byte was received, not that it was correct. Every message gets a sequence number and a CRC; the receiver rejects and requests retransmission on mismatch. For critical data, I'd consider sending it twice and comparing, or using a redundant bus.

Third, bus redundancy. If the mission can tolerate the mass and volume, two independent I²C buses with the master able to switch between them gives a clean recovery path from a bus-wide fault. The sensors would need to be on both buses, or the critical ones would.

Fourth, node-level robustness. Each sensor node should have a watchdog that resets it if it stops responding, and the master should have a timeout on every transaction so a non-responsive node doesn't stall the whole system.

Finally, I'd be honest about the limits: if the bus is truly critical, I²C may be the wrong choice and something differential with built-in error detection (RS-485, CAN) would be more appropriate. I'd raise that as a design question rather than trying to patch I²C into something it isn't.

**Possible follow-ups:**
- How would you test the bus lock-up recovery without being able to inject a real SEU?
- If you had to keep I²C for legacy reasons, what's the minimum set of mitigations you'd insist on?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the technical question from the interpersonal one. The engineer has done real work, and that deserves respect — the goal isn't to win the argument, it's to get the right answer, and the engineer may have information I don't.

I'd start by asking them to walk me through their reasoning: what margin they calculated, what assumptions they made, what data they based it on. Often the disagreement turns out to be about an assumption rather than the conclusion — maybe they assumed a part's radiation performance based on a similar part, or they used a typical value where a worst-case value is needed. Making the assumption explicit is usually more productive than arguing about the conclusion.

If the gap is real, I'd frame it as a shared problem: "Here's the concern I have — can we work out together whether it's actually a problem?" I'd bring the specific data or standard that drives my concern, not just my opinion. If I don't have data and it's a judgment call, I'd say so, and propose a way to resolve it — a test, a derating calculation, a consultation with someone who has the data.

If we still disagree after that, I'd make the decision explicit and take responsibility for it, while being clear about why. I'd also make sure the engineer understands it's not a judgment of their work — it's a risk decision that's mine to make. And I'd follow up afterward to make sure the relationship isn't damaged and that they feel heard.

The one thing I'd avoid is letting it become adversarial or personal. A design review where people are afraid to raise concerns is worse than one where they're occasionally wrong.

**Possible follow-ups:**
- What if the engineer is right and you're wrong — how would you want that to play out in the review?
- How would you handle it if the engineer escalates the disagreement above you?