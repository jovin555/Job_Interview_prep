# space-rad-hard — Day 11

## Q1: How would you approach designing a current-limiting circuit for a 28V spacecraft power bus that must protect against single-event latch-up (SEL) in downstream loads while also surviving the inrush current of capacitive loads during power-up?

**Answer:** The fundamental tension here is that SEL protection requires fast, aggressive current limiting, while capacitive loads need controlled inrush that can look like a temporary overcurrent condition. I'd approach this with a two-tier strategy.

First, I'd implement a dedicated SEL protection circuit per load or per load group, rather than relying on a single bus-level limiter. Each protection circuit would use a series pass element—typically a radiation-tolerant MOSFET—with a current-sense resistor feeding a comparator that has a programmable threshold and a latching shutdown mechanism. The key is that once the threshold is exceeded for longer than a very short blanking window (microseconds to low milliseconds), the circuit latches off and requires either a command from the system controller or a power cycle to reset. This prevents the load from repeatedly retrying into a latch-up condition.

Second, I'd handle inrush separately. Rather than trying to make the SEL limiter tolerate inrush, I'd add a separate soft-start circuit—either an RC-controlled gate ramp on the same MOSFET or a dedicated inrush limiter—that charges the bulk capacitance gradually. The soft-start time constant is sized so that the peak inrush current stays below the SEL threshold, but the SEL circuit still responds fast enough to catch a genuine latch-up event. This separation of concerns is important: if you try to make one circuit handle both, you end up with a threshold that's too high to protect against SEL or a response time that's too slow.

I'd also consider using a foldback current-limiting approach, where the current limit drops to a lower holding value after the initial trip. This reduces power dissipation in the pass element during a fault and makes it easier to distinguish between a transient event and a sustained latch-up. Finally, I'd add telemetry—voltage and current monitoring—so the system can log fault events and distinguish between SEL events, load failures, and wiring faults during ground testing.

**Possible follow-ups:**
- How would you choose between latching shutdown and automatic retry for SEL protection?
- What considerations would you give to the pass element's safe operating area (SOA) during a fault condition?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA with internal block RAM for critical telemetry storage. The designer has implemented single-error correction and double-error detection (SEC-DED) ECC on the block RAM, but has not implemented scrubbing. How would you evaluate this approach, and what would you recommend?

**Answer:** SEC-DED ECC on block RAM is a good foundation, but without scrubbing, it has a critical weakness: the ECC can correct single-bit errors, but it cannot detect or correct the accumulation of multiple errors over time. As the mission progresses, multiple single-bit upsets can accumulate in the same word, eventually creating a double-bit error that the ECC cannot correct. The probability of this happening depends on the upset rate, the memory size, and the mission duration—but for a multi-year mission, it's not a question of *if* this will happen, but *when*.

I'd recommend adding a scrubbing mechanism. The simplest approach is a background scrubber that periodically reads every word in the block RAM, corrects any single-bit errors it finds, and writes the corrected value back. The scrub interval should be short enough that the probability of two upsets accumulating in the same word before scrubbing is acceptably low—typically this means scrubbing much faster than the expected mean time between upsets for any single word.

There are a few implementation considerations. First, the scrubber needs to arbitrate with normal read/write access from the FPGA fabric—you don't want scrubbing to interfere with real-time telemetry collection. This can be handled with a simple round-robin or priority-based arbiter. Second, the scrubber itself needs to be protected—if the scrubber's state machine gets upset, it could stop scrubbing or scrub incorrectly. Triple modular redundancy (TMR) on the scrubber controller is a reasonable mitigation. Third, I'd consider whether the block RAM contents are critical enough to warrant TMR on the data itself, rather than just ECC. For very critical data, TMR with voting provides stronger protection because it can correct multiple-bit upsets in the same word, whereas SEC-DED cannot.

Finally, I'd want to see error counters and telemetry for scrub events. Knowing how often errors are being corrected gives you insight into the actual radiation environment and can help you validate your upset-rate models during the mission.

**Possible follow-ups:**
- How would you choose the scrub interval, and what factors would influence that decision?
- What are the trade-offs between using ECC alone versus ECC plus TMR for critical data?

---

## Q3: How would you approach designing a firmware-based memory management strategy for a radiation-hardened microcontroller that has limited RAM and must maintain critical state across single-event upsets (SEUs) without using a full RTOS?

**Answer:** In a radiation environment with limited RAM and no RTOS, the key is to be deliberate about what data is critical and how it's protected. I'd start by categorizing all data structures into three tiers: critical state that must never be corrupted, important data that can tolerate occasional errors but should be detected, and non-critical data that can be allowed to corrupt and recover.

For critical state—things like control loop setpoints, safety limits, and mode-of-operation flags—I'd use triple modular redundancy (TMR) with majority voting. Each critical variable would be stored in three separate memory locations, and every read would involve reading all three copies and voting. The write path would write all three copies. To avoid common-mode upsets affecting multiple copies, I'd physically separate the copies in memory—ideally in different memory banks or at least far apart in the address space. I'd also periodically "refresh" the TMR copies by reading all three, voting, and rewriting the majority value, which prevents the accumulation of errors over time.

For important data that doesn't need TMR, I'd use checksums or CRC. Each record or data structure would have a checksum stored alongside it. On read, the checksum is verified; if it fails, the data is either recovered from a backup copy or reset to a known-safe default. This is lighter weight than TMR and works well for data that's periodically refreshed anyway, like sensor calibration values.

For memory management itself, I'd avoid dynamic allocation entirely. Static allocation with fixed memory regions is much easier to protect and verify. If dynamic allocation is unavoidable, I'd use a simple, auditable allocator with built-in integrity checks—for example, a free-list allocator where each block header includes a checksum, and the allocator validates the list integrity on every operation.

I'd also implement a periodic memory self-test that runs during idle time. This test would check for stuck bits, verify TMR consistency, and validate checksums. If corruption is detected, the system can take corrective action—reinitializing the affected data structure or triggering a system reset if critical state is unrecoverable.

Finally, I'd make sure the startup sequence includes a memory initialization routine that validates all critical data structures before the main control loop begins. If validation fails, the system should enter a safe state rather than attempting to run with corrupted data.

**Possible follow-ups:**
- How would you handle the case where two of the three TMR copies disagree—how do you determine which is correct?
- What strategies would you use to detect and recover from a single-event functional interrupt (SEFI) that corrupts the microcontroller's program counter or stack pointer?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA for data processing. A junior engineer has implemented triple modular redundancy (TMR) on all flip-flops in the design, but has not applied TMR to the configuration memory or the block RAM. The engineer argues that the configuration memory is "protected by the FPGA's built-in error detection" and the block RAM is "not critical." How would you handle this disagreement?

**Answer:** I'd start by acknowledging what the engineer got right—TMR on the flip-flops is a solid foundation and addresses single-event upsets in the logic fabric. But I'd then walk through the system-level risk, because the argument misses two important failure paths.

First, configuration memory upsets are fundamentally different from flip-flop upsets. A flip-flop upset causes a transient error that can be corrected by the TMR voting—the next clock cycle, the majority wins and the system continues. A configuration memory upset, however, changes the actual logic function of the FPGA. It can alter routing, change LUT contents, or modify the behavior of a state machine. This isn't a transient error that voting can correct—it's a persistent functional change that can cause the system to behave incorrectly indefinitely. The FPGA's built-in error detection (typically CRC-based) can detect that a configuration upset has occurred, but detection alone doesn't correct the problem. You need either configuration scrubbing (reading back and correcting the configuration memory) or full reconfiguration from external memory. And even with scrubbing, there's a window between the upset and the scrub where the FPGA is operating with corrupted logic.

Second, the claim that block RAM is "not critical" needs to be challenged. I'd ask the engineer to walk through the data flow and identify what happens if a block RAM word is corrupted. If the block RAM contains telemetry buffers, look-up tables, or intermediate computation results, a corruption could propagate into the system's outputs. Even if the block RAM isn't directly controlling actuators or generating commands, corrupted data can cause incorrect decisions downstream. The question isn't whether the block RAM is critical in isolation—it's whether the data flowing through it can affect critical outputs.

I'd frame this as a risk assessment rather than a directive. I'd ask the engineer to quantify the risk: what's the expected upset rate in the configuration memory and block RAM, what's the probability of a critical failure over the mission duration, and what's the consequence if it occurs? If the consequence is loss of the mission or a safety-critical function, then the risk is unacceptable regardless of the probability.

If the engineer is concerned about logic capacity or design complexity, I'd discuss alternatives. For configuration memory, scrubbing is often more area-efficient than TMR because it doesn't require triplicating the entire design. For block RAM, you can use ECC (which is often built into the FPGA's block RAM primitives) or TMR on just the critical data structures, rather than the entire memory. The key is to match the mitigation to the actual risk.

I'd also emphasize that this is a systems engineering decision, not just a digital design decision. The mitigation strategy needs to be consistent with the overall fault tolerance approach, the mission requirements, and the available resources. If the mission can tolerate a brief system reset on configuration upset, then scrubbing plus a reset-on-error strategy might be sufficient. If the system must operate continuously without interruption, then more aggressive mitigation is needed.

**Possible follow-ups:**
- How would you help the engineer quantify the risk of configuration memory upsets without access to radiation test data for the specific FPGA?
- What alternatives to full TMR would you consider for protecting block RAM contents, and how would you decide which to use?

---

## Q5: How would you approach developing a radiation test plan for a COTS DC-DC converter that will be used in a space-deployed system, given that the converter is not radiation-characterized and you have limited budget for testing?

**Answer:** With limited budget, the goal is to get the maximum risk-reduction information from the minimum number of test exposures. I'd start by clearly defining what we need to learn and what we can accept as residual risk.

First, I'd do a thorough literature search and datasheet review. Many COTS parts have some radiation data available from manufacturers, academic papers, or government test reports—even if it's not formal qualification data. I'd look for information on the specific part, its die revision, and similar parts from the same family or manufacturer. This can give us a baseline expectation and help us focus testing on the areas of highest uncertainty.

Next, I'd identify the dominant failure modes we're concerned about. For a DC-DC converter, the primary concerns are total ionizing dose (TID) effects—which typically manifest as output voltage drift, efficiency degradation, or loss of regulation—and single-event effects, particularly single-event transients (SETs) on the output and single-event latch-up (SEL) in the control circuitry. Displacement damage is usually less of a concern for a converter unless it uses optocouplers or other photonic components.

Given budget constraints, I'd prioritize TID testing over SEE testing for a first pass. TID testing is more predictable and can be done at a lower-cost facility, and it gives us a clear pass/fail threshold. I'd test at least three devices to get some statistical confidence, and I'd test at a dose rate and total dose that's representative of the mission—typically 50-100 krad(Si) for a low-Earth-orbit mission, with measurements taken at multiple intermediate dose steps to observe the degradation trend. I'd bias the devices during irradiation to simulate worst-case operating conditions, and I'd measure output voltage, efficiency, and ripple at each step.

For SEE testing, if budget allows, I'd focus on SEL testing first, because latch-up is potentially destructive. I'd use a heavy-ion beam and monitor supply current for latch-up events. If SEL is observed, the part is likely unusable without external mitigation. If no SEL is observed, I'd consider SET testing—looking for transients on the output that could upset downstream logic. SET testing requires more sophisticated test equipment and analysis, so I'd only do this if the part passes TID and SEL testing.

I'd also consider a "test-as-you-fly" approach: rather than testing the converter in isolation, test it as part of a representative circuit board with the actual load conditions. This gives us more realistic data but makes it harder to isolate failures to the converter itself.

Finally, I'd document the residual risk. If we can't afford full characterization, we need to be explicit about what we don't know and what mitigations we're relying on. For example, if we can't test for SETs, we might add output filtering or a voltage supervisor that can tolerate brief transients. If we can't test for SEL, we might add a current-limiting circuit that can protect the converter from latch-up damage. The test plan should inform the design mitigations, not the other way around.

**Possible follow-ups:**
- How would you decide between testing more devices at a lower dose versus fewer devices at a higher dose?
- What would you do if the TID test shows the converter fails at 30 krad(Si) but your mission requires 50 krad(Si) total dose?