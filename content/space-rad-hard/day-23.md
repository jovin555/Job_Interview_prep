# space-rad-hard — Day 23

## Q1: How would you approach designing a fault-tolerant reset distribution network for a space-deployed system where multiple FPGAs and microcontrollers must be reset coherently after a single-event upset, but a single shared reset line could propagate a fault across all devices?

**Answer:** The core tension here is between coherent reset behavior and fault isolation. A single shared reset line is simple and guarantees synchronized restart, but it creates a single point of failure — one device pulling reset low, or one device's reset driver latching up, takes down the entire system. My approach would be to decouple the reset architecture into layers.

First, I'd give each device its own local reset generation circuit — a dedicated supervisor or RC-based reset with its own watchdog input — so that a fault in one device doesn't directly drive reset on its neighbors. Each device's reset would be triggered by its own health monitoring (watchdog timeout, voltage supervisor, or software-triggered reset).

Second, for coherent restart, I'd use a hierarchical scheme rather than a shared line. A designated "reset master" (ideally the most radiation-tolerant device, or one with a rad-hard supervisor) would coordinate system-level recovery. When it detects a need for full system restart, it would issue a sequenced reset command over a robust interface (e.g., a command message on a protected bus, or individual reset lines with series resistors and clamping) rather than a single broadcast line. This lets the master stagger resets to respect power-up sequencing requirements.

Third, I'd add isolation components — series resistors, buffer gates, or optocouplers where appropriate — on any reset path that must be shared, so a stuck-low or latched-up driver on one side can't hold the whole network in reset. I'd also consider using open-drain drivers with pull-ups so any single device can assert reset, but a failed driver can't source current into the line.

Finally, I'd verify the scheme with fault injection testing: simulate each possible failure mode (one device stuck asserting reset, one device's supervisor failing to release reset, a bus fault) and confirm the system either recovers or degrades gracefully without a full system lock-up.

**Possible follow-ups:** How would you handle the case where the reset master itself is the device that gets upset? What are the trade-offs between using a dedicated hardware reset sequencer versus implementing reset coordination in firmware?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA and a COTS voltage supervisor for the 3.3V rail. The supervisor's threshold is set to 3.0V, and the FPGA's minimum operating voltage is 3.0V. The designer argues that the supervisor will never falsely trigger because the DC-DC converter regulates tightly to 3.3V. How would you evaluate this approach?

**Answer:** This is a classic margin problem, and the designer's argument conflates nominal behavior with worst-case behavior. The supervisor threshold at 3.0V and the FPGA minimum at 3.0V leaves zero margin — any transient dip, measurement error in the supervisor's internal reference, or temperature drift in either component could cause the supervisor to either miss an undervoltage condition (if its threshold drifts low) or falsely trigger (if it drifts high).

I'd evaluate this by building a worst-case budget. The DC-DC converter has load transient response — a sudden current draw can cause a voltage dip that lasts microseconds to milliseconds. The supervisor has threshold accuracy and hysteresis — typically ±1-2% for a good part, more for a COTS part with no radiation characterization. The FPGA's minimum operating voltage is specified at the pin, but there's also IR drop across the PCB trace and any connector. When you add all these tolerances, a 3.0V threshold on a 3.3V rail is dangerously close to the edge.

I'd recommend one of three changes: (1) raise the supervisor threshold to around 3.1-3.15V to provide margin above the FPGA minimum, accounting for the supervisor's own tolerance; (2) add hysteresis to the supervisor so it doesn't chatter on noise; or (3) if the supervisor's threshold can't be adjusted, use a precision resistor divider to set a higher effective threshold. I'd also verify the supervisor's behavior over temperature and after radiation exposure — a COTS supervisor's threshold can drift with TID, and if it drifts low, it might not protect the FPGA at all.

The key principle is that protection circuits must have margin on both sides: they must trigger before the load enters an unsafe condition, but they must not trigger during normal operation including transients. Zero margin on either side is a design flaw.

**Possible follow-ups:** How would you determine the appropriate amount of margin for a voltage supervisor threshold? What additional testing would you recommend for the COTS supervisor given its lack of radiation data?

---

## Q3: How would you approach designing a radiation-tolerant data acquisition and telemetry scheme for a space-deployed system where the analog sensor data is critical, but the ADC and its reference can experience single-event transients that produce spurious readings?

**Answer:** The challenge here is distinguishing between a real sensor reading and a transient-induced artifact, and then deciding what to do with the questionable data. I'd approach this at three levels: hardware filtering, data validation, and system-level response.

At the hardware level, I'd add filtering on the analog front-end — both passive RC filtering to limit bandwidth and reject transients, and potentially a median filter or sample-and-hold circuit that can reject short-duration spikes. I'd also consider using a differential ADC input where possible, since SETs often couple common-mode noise that differential measurement can reject. The voltage reference is a particular concern — a SET on the reference can shift all readings simultaneously, so I'd use a reference with good radiation tolerance and add decoupling to minimize transient coupling.

At the data validation level, I'd implement redundancy in the measurement scheme. This could mean taking multiple samples per measurement and using median or majority voting, or using two independent ADC channels with different reference paths and comparing results. I'd also implement plausibility checks in firmware: rate-of-change limits, comparison against expected ranges, and correlation with other sensors. A single reading that jumps by 50% and returns immediately is more likely a transient than a real physical event.

At the system level, I'd design the telemetry to flag suspicious data rather than silently passing it through. Each measurement would carry a quality flag or confidence metric, and the ground station or control system could decide whether to act on it. For critical control loops, I'd require multiple consecutive valid readings before acting on a value, and I'd implement a "last known good" fallback — if the current reading is flagged as suspect, use the previous validated value.

The key insight is that you can't eliminate all transients, so the design must be able to detect, flag, and gracefully handle them without compromising the mission.

**Possible follow-ups:** How would you distinguish between a SET-induced transient and a real sensor event that happens to be brief? What if the transient occurs on the ADC's clock or control signals rather than the analog path?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA and a COTS DC-DC converter. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, and the FPGA's absolute maximum rating is 3.6V. A junior engineer argues that the 130 mV margin is acceptable because "the FPGA will never actually see 3.47V in practice — the converter will typically output 3.3V, and the FPGA's absolute maximum rating already includes some safety margin." How would you handle this disagreement?

**Answer:** I'd start by acknowledging that the engineer has a point about typical behavior — the converter will likely output close to 3.3V in most conditions. But I'd then walk through why the argument is flawed from a worst-case design perspective.

First, the absolute maximum rating on an FPGA is not a "recommended operating condition" — it's the limit beyond which damage may occur. The fact that there's a 130 mV gap between the converter's worst-case output and the FPGA's absolute maximum is not margin; it's the entire budget for everything else that can go wrong. This includes: load transients on the converter output (which can cause overshoot), IR drop variations across the PCB (which can cause the voltage at the FPGA pin to differ from the voltage at the converter output), measurement error in any monitoring circuitry, and the fact that the converter's worst-case specification may not account for all operating conditions (temperature extremes, radiation-induced drift, aging).

Second, I'd point out that the FPGA's absolute maximum rating is a stress limit, not a functional limit. Even if the FPGA doesn't permanently fail at 3.47V, it may not operate correctly — the I/O levels, internal timing, and other parameters are only guaranteed within the recommended operating range, which is typically lower than the absolute maximum. So the question isn't "will it survive?" but "will it work correctly?"

Third, I'd ask the engineer to consider what happens when you stack tolerances. The converter's 3.47V maximum is itself a worst-case number that includes line, load, temperature, and part-to-part variation. But the FPGA's absolute maximum is also a worst-case number — the actual damage threshold is likely higher, but you can't rely on that. The responsible engineering approach is to ensure that the worst-case output of the supply chain never exceeds the recommended operating range of the load, not just the absolute maximum.

I'd frame this as a risk management decision: the 130 mV gap is not "margin" — it's the entire risk budget, and it's already been consumed by the worst-case analysis. I'd recommend either selecting a converter with tighter output tolerance, adding a post-regulator, or at minimum adding a voltage monitor that can flag if the rail approaches the limit. I'd also suggest we document the analysis so the risk is explicit and accepted by the team, rather than implicitly assumed away.

**Possible follow-ups:** How would you quantify the actual risk if the converter does exceed 3.47V under some unanticipated condition? What if the FPGA's absolute maximum rating is 3.6V but the recommended operating range is 3.3V ±5% — does that change your analysis?

---

## Q5: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental requirement is that a failed or corrupted firmware update must never leave the system in an unbootable state. I'd design the update strategy around three principles: redundancy, validation, and atomicity.

For redundancy, I'd use a dual-bank or A/B partition scheme in flash. The current known-good firmware stays in one bank, and the new firmware is written to the other bank. The bootloader always boots from the "active" bank, and only after the new firmware is fully written and validated does the system switch the active pointer. This way, a corrupted update leaves the old firmware intact and bootable.

For validation, I'd implement multiple layers of checks. Before writing, verify the update image's integrity (checksum or cryptographic signature) and compatibility (version, hardware revision, memory map). After writing, read back and verify the entire image before committing the switch. The bootloader should also validate the active bank at every boot — checking a header, CRC, and possibly a self-test — before jumping to application code. If validation fails, the bootloader falls back to the other bank.

For atomicity, I'd design the bank-switch mechanism to be a single, protected operation — ideally a dedicated register or flag that's written only after all validation passes, and that can be rolled back if the new firmware fails its first boot. I'd also implement a "boot counter" or watchdog-based recovery: if the new firmware fails to signal healthy operation within a timeout, the bootloader automatically reverts to the previous bank.

I'd also consider the radiation aspects specifically. Flash memory can experience bit flips, so I'd use ECC or at least periodic scrubbing of the active firmware image. The bootloader itself should be in the most radiation-tolerant memory available, and ideally be small enough that it can be protected with ECC or triple redundancy. The update process should be resumable — if a single-event upset corrupts a block during the write, the system should be able to detect and retry that block rather than restarting the entire update.

Finally, I'd design the update protocol to be robust against communication errors: sequence numbers, acknowledgments, and the ability to resume from the last good block. And I'd test the entire process with fault injection — corrupting random bits in the flash, interrupting the update at various points, and simulating a failed first boot — to verify the system always recovers to a known-good state.

**Possible follow-ups:** How would you handle the case where both firmware banks are corrupted? What are the trade-offs between using a bootloader in rad-hard flash versus a bootloader in the FPGA configuration memory?