# space-rad-hard — Day 34

## Q1: How would you approach designing a fault-tolerant analog multiplexing scheme for a space-deployed system where a single-event transient (SET) on the mux select lines could route the wrong sensor channel to a precision ADC, potentially causing an incorrect control action?

**Answer:** The core problem here is that a single-event transient on the mux select lines doesn't just corrupt data — it can cause the system to act on data from the wrong sensor, which in a control loop could be dangerous. My approach would start with understanding the failure modes: a SET could momentarily switch the mux to the wrong channel, or it could cause the mux to float between channels, producing an indeterminate output.

First, I'd look at the select line encoding. If using a binary-encoded mux, a single-bit upset could select any channel. Using a one-hot or Gray-coded scheme reduces the chance of a single upset landing on a completely unrelated channel, though it doesn't eliminate the problem. I'd also consider adding redundancy at the protocol level — for example, sending the channel selection as a coded word with a checksum, and having the firmware validate the channel ID against what was requested before accepting the reading.

Second, I'd add validation in firmware. Before acting on any ADC reading, the system should verify that the reading is plausible for the expected channel — checking against expected ranges, rate-of-change limits, and cross-correlation with other sensors. If a reading fails validation, the system should reject it and possibly trigger a re-read or a mux reset.

Third, I'd consider hardware mitigation. Adding a small RC filter on the select lines can slow transients enough that they don't propagate, though this trades off switching speed. A better approach might be to use a mux with a "chip enable" that can be held asserted only during the actual sampling window, so a transient outside that window has no effect. I'd also consider using two muxes in parallel with voting on the output, though that's expensive and may not be justified depending on the criticality.

Finally, I'd think about the system-level response. If a bad reading does get through, what happens? The control loop should have rate limiting and output clamping so a single spurious reading can't cause a dangerous actuator command. The key is defense in depth: hardware mitigation to reduce the probability, firmware validation to catch what gets through, and system-level response to bound the consequences.

**Possible follow-ups:** How would you determine whether the mux select lines or the analog signal path itself is more vulnerable to SETs in your specific design? What if the mux is inside a sealed module and you can't add external filtering?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." How would you handle this disagreement?

**Answer:** I'd start by acknowledging the engineer's point — the load is small and the voltage is modest, so the thermal and power dissipation concerns are indeed minimal. But the argument misses the key issue: radiation effects on a linear regulator aren't primarily about power handling. The failure modes we care about are total ionizing dose (TID) effects like output voltage drift and increased quiescent current, and single-event effects like transient output voltage dips or, worse, single-event latch-up (SEL) that could short the input to ground.

For a critical analog rail, even a small output voltage transient could corrupt a precision measurement. And if the regulator latches up, it could pull down the entire power bus, affecting other subsystems. So the "it's only 50mA" argument doesn't address the actual risk.

I'd walk through the risk assessment systematically. First, what is the rail powering? If it's an ADC reference or analog front-end, the accuracy requirements are likely tight enough that even a few percent drift would be unacceptable. Second, what's the consequence of a latch-up? If it takes down the whole bus, that's a mission-level event, not a local one. Third, what's the radiation environment and mission duration? A LEO mission of a few years is different from a deep-space mission.

Then I'd look at alternatives. There are radiation-characterized linear regulators available, and for 50mA the selection is broad and the cost difference is modest. If the engineer is concerned about availability or cost, I'd suggest looking at the radiation test data for similar parts from the same family or manufacturer, or considering a hybrid approach where the regulator is protected by a current-limiting circuit that would trip on latch-up.

The key point I'd make is that the decision shouldn't be based on "the risk is minimal" but on whether the risk is characterized and acceptable. Without radiation data, we can't quantify the risk, and for a critical rail, unquantified risk is unacceptable when a qualified alternative exists.

**Possible follow-ups:** What if the qualified alternative is significantly larger and heavier? How would you trade off the risk against the mass budget? What radiation test data would you accept as sufficient for a COTS part?

---

## Q3: How would you approach designing a fault-tolerant boot sequence for a space-deployed system that uses an SRAM-based FPGA with external configuration memory (flash), where both the FPGA configuration bitstream and the flash memory are susceptible to single-event upsets?

**Answer:** This is a classic problem because you have two failure domains: the flash can develop bit errors over time, and the FPGA configuration SRAM can upset during operation. The boot sequence has to handle both.

For the flash side, I'd start with error detection and correction. Using a flash device with built-in ECC is ideal, but if that's not available, I'd store the bitstream with a checksum or CRC. During boot, the configuration controller reads the bitstream, verifies the checksum, and only configures the FPGA if the check passes. If it fails, the controller should have a fallback — either a redundant copy of the bitstream in a different memory region or a second flash device. The boot controller should also be able to rewrite the corrupted flash region from the redundant copy, so the system self-heals over time.

For the FPGA configuration SRAM, the issue is that upsets can accumulate during operation. The standard mitigation is periodic scrubbing — reading back the configuration and correcting any bit errors. This can be done by the configuration controller or by the FPGA itself if it has internal scrubbing logic. The scrub rate should be fast enough that the probability of two upsets in the same frame before correction is negligible.

I'd also think about the boot sequence ordering. The configuration controller itself needs to be radiation-tolerant — if it's a microcontroller, it needs its own protection. And the sequence should be: power up, verify the configuration controller's own code, verify the bitstream checksum, configure the FPGA, verify the configuration by readback, then release the FPGA from reset and let it start executing.

One additional consideration: the flash should be write-protected during normal operation to prevent a single-event upset from corrupting the stored bitstream. If the flash has a hardware write-protect pin, it should be tied to the safe state and only released during a deliberate reconfiguration.

**Possible follow-ups:** How would you handle the case where both copies of the bitstream are corrupted? What scrub rate would you choose, and how would you determine it? How would you verify that the FPGA is actually configured correctly after the boot sequence?

---

## Q4: How would you approach designing a radiation-tolerant communication protocol between two FPGAs over a high-speed serial link, where single-event upsets can corrupt both the data payload and the link synchronization state?

**Answer:** The challenge here is that you need to protect against two distinct failure modes: data corruption and loss of link synchronization. These require different mitigation strategies.

For data corruption, the standard approach is forward error correction (FEC) combined with retransmission for uncorrectable errors. I'd use a protocol that adds CRC or BCH codes to each packet, with enough redundancy to correct single-bit errors and detect multi-bit errors. The FEC strength should be sized based on the expected upset rate and the criticality of the data. For a control link, you might want to correct single errors and request retransmission on double errors; for a telemetry link, you might accept a higher error rate and just flag bad packets.

For link synchronization, the issue is that a SET in the clock recovery circuit or the framing logic can cause the receiver to lose alignment. The protocol needs a robust framing scheme — a unique sync pattern that's long enough to be unambiguous, with the receiver continuously searching for it when out of sync. Once sync is lost, the receiver should signal the transmitter, and the transmitter should resend a sync pattern. The key is to make the sync pattern itself resistant to single-bit errors — using a pattern with good autocorrelation properties so that a single-bit error doesn't cause false sync.

I'd also think about the physical layer. Using 8b/10b or 64b/66b encoding provides DC balance and guarantees transitions, which helps the clock recovery circuit stay locked. The encoding also provides some error detection, since invalid code words can be flagged.

At the system level, I'd add a heartbeat or watchdog mechanism. If the link goes silent for a defined period, both sides should reset their link state machines and re-establish synchronization. This bounds the recovery time and prevents a stuck state.

Finally, I'd consider redundancy at the link level. If the data is critical, two independent serial links with voting at the receiving end provides protection against a single link failing entirely. This is expensive, but for a life-critical system it may be justified.

**Possible follow-ups:** How would you choose between FEC and retransmission for your specific data rate and latency requirements? What sync pattern would you use, and how would you verify its robustness? How would you test the protocol's recovery from sync loss?

---

## Q5: Imagine you are leading a design review for a space-deployed system where a junior engineer has implemented triple modular redundancy (TMR) on all flip-flops in the FPGA design, but has not applied TMR to the configuration memory or the block RAM. The engineer argues that the configuration memory is "protected by the FPGA's built-in error detection" and the block RAM is "not critical." How would you handle this disagreement?

**Answer:** I'd approach this by first acknowledging what the engineer got right — TMR on the flip-flops is a solid foundation and shows good understanding of single-event upset mitigation in the fabric. Then I'd walk through the two gaps.

On configuration memory: the built-in error detection the engineer refers to typically detects errors but doesn't correct them. Depending on the FPGA, the detection might trigger a reconfiguration, which means the device goes offline for the duration of the reconfiguration — potentially milliseconds to seconds. During that time, the system is blind. Worse, if the error detection doesn't trigger a reconfiguration automatically, the configuration error could persist indefinitely, and the TMR on the flip-flops becomes meaningless because the routing and LUT configuration that the TMR relies on is corrupted. The configuration memory is the foundation that everything else sits on — protecting the logic without protecting the configuration is like putting a vault door on a house with no walls.

On block RAM: the engineer's claim that it's "not critical" needs to be examined. What's stored in the block RAM? If it's telemetry buffers or non-critical data, then maybe TMR is overkill — but even then, the data needs to be protected from corruption, or at least detected as corrupted. If it's any kind of state information, control parameters, or data that feeds into a control loop, then a single upset could cause incorrect behavior. The standard approach is to use ECC on block RAM, which is often built into the FPGA, or to use TMR on the RAM with voting on read. The cost of ECC is much lower than TMR, so there's no good reason to skip it.

I'd also raise the question of what "critical" means in this system. The engineer's definition seems to be "does it directly affect the control output?" But in a space system, a corrupted telemetry value could cause a ground operator to make a wrong decision, or a corrupted housekeeping value could mask a developing fault. The definition of critical should be based on the system-level risk analysis, not on an individual engineer's judgment.

I'd frame this as a collaborative discussion: let's look at the system requirements and the risk analysis, and determine what level of protection each memory element needs. The goal isn't to apply TMR everywhere — it's to apply the right level of protection based on the consequences of failure.

**Possible follow-ups:** How would you determine the acceptable level of protection for different memory elements in the design? What if adding ECC to the block RAM exceeds the FPGA's available resources — how would you prioritize? How would you verify that the TMR implementation is actually effective, given that the configuration memory is still vulnerable?