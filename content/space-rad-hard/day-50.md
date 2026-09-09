# space-rad-hard — Day 50

## Q1: How would you approach designing a fault-tolerant analog output stage for a space-deployed system where a single-event transient (SET) on a DAC's reference voltage could cause a momentary but dangerous output spike to an actuator?

**Answer:** I'd approach this by first recognizing that the reference voltage is the single most sensitive node in the analog chain — a transient there propagates directly to the output with gain. The design strategy would be layered:

**At the reference itself:** Use a precision reference with known radiation performance, and add a low-pass filter (e.g., RC or active filter) sized to attenuate transients of the expected pulse width — typically nanoseconds to microseconds for SETs. The filter bandwidth must still allow the reference to settle quickly enough for the system's update rate, so there's a trade-off between transient rejection and response time.

**At the output stage:** Add a slew-rate limiter or a clamping circuit that bounds how fast and how far the output can move. For an actuator, you might also add a hardware interlock — a window comparator that watches the output and triggers a safe state (e.g., hold last value, or drive to a known-safe level) if the output exceeds expected bounds for more than a few microseconds.

**At the system level:** Consider whether the actuator needs a "fail-safe" default state. If a momentary spike is genuinely dangerous, the design should include a watchdog-style mechanism that can force the output to a safe state within the time window that matters for the actuator's response. This might be an analog circuit rather than firmware, because firmware response time may be too slow or itself corrupted.

**Validation:** I'd inject transients at the reference node during test (e.g., with a fast pulse generator through a small coupling capacitor) and verify the output stays within safe bounds. I'd also analyze the worst-case SET pulse width for the chosen reference part and make sure the filter and clamp are sized accordingly.

**Possible follow-ups:**
- How would you choose between filtering the reference versus filtering the output?
- What if the actuator requires a fast response — how would you balance transient protection against control bandwidth?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." How would you handle this disagreement?

**Answer:** I'd start by acknowledging the engineer's point — the load is small and the rail is low-voltage, so some risks are indeed reduced. But I'd reframe the discussion around what we actually know versus what we're assuming, and what the failure consequences are.

**Key concerns to raise:**
- **TID effects:** Linear regulators can experience significant output voltage drift and increased quiescent current over total dose. Even a "simple" part may fail to regulate within specification well before the mission end.
- **Single-event effects:** Bipolar linear regulators are susceptible to single-event transients on the output — a momentary voltage spike or dropout that could corrupt an ADC reading or, worse, propagate to a control action.
- **SEL risk:** Some CMOS regulators can latch up, drawing excessive current and potentially damaging the part or the rail.
- **The "critical" qualifier:** The engineer's argument treats this as a low-risk rail, but it's feeding a critical analog function. The consequence of a failure matters as much as the probability.

**How I'd handle it constructively:**
- Ask the engineer to walk through the failure modes and what the system does if this rail misbehaves — this gets them thinking about consequences, not just likelihood.
- Propose a middle path: if we can't qualify the part, can we add mitigation? For example, a radiation-tolerant supervisor on the rail, a current limiter for SEL protection, or a filter to catch transients.
- Suggest looking for a drop-in alternative with existing radiation data — even if it costs more, the qualification cost may be lower than testing a new part.
- If budget truly constrains us to this part, I'd document the risk formally in the risk register and define acceptance criteria for what level of testing we can afford (e.g., a limited TID test at a lower dose rate).

The goal isn't to win the argument — it's to make sure the decision is made with full awareness of the risk and that we have a mitigation plan if we proceed.

**Possible follow-ups:**
- What if the engineer pushes back and says the system has a calibration routine that can handle drift?
- How would you decide when a COTS part is acceptable versus when it must be rad-hard?

---

## Q3: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The core principle is that the update path must never be the single point of failure — there must always be a way to recover, even if the update itself is corrupted mid-transfer.

**Architecture approach:**
- **Dual-bank or A/B partitioning:** Keep two copies of the application firmware in separate flash regions. The bootloader always boots from the "known-good" bank unless explicitly told otherwise. The update writes to the inactive bank, validates it, and only then flips the active pointer.
- **Bootloader independence:** The bootloader itself should be in a separate, protected region (ideally write-protected or in a different memory type) and should be simple enough to verify its own integrity. It should never be updated in the same operation as the application.
- **Validation before commit:** After writing the new image, the bootloader verifies a checksum or cryptographic signature before marking it active. If validation fails, it reverts to the previous bank and reports the error.
- **Update transaction logging:** Keep a small log of update state (e.g., "writing," "validating," "committed") in a separate area so that if power is lost mid-update, the bootloader knows what state it was in and can recover.

**Radiation-specific considerations:**
- Flash itself can experience bit flips, so the stored image should have error detection (e.g., CRC) that is checked at boot, not just after update. If a bit flip is detected in the active bank, the bootloader can fall back to the backup.
- The update transfer protocol should include retransmission and error correction, since a corrupted packet over the link could otherwise be written to flash.
- Consider scrubbing the inactive bank periodically — if it sits for months before being used, it could accumulate upsets.

**Recovery path:** Even with all this, I'd design for the worst case: a "recovery mode" triggered by a hardware pin or command that forces the bootloader into a minimal state capable of accepting a new image over a reliable, low-speed interface (e.g., UART or I²C), independent of the main communication path.

**Possible follow-ups:**
- How would you handle the case where the bootloader itself is corrupted?
- What if the flash is too small for two full application images?

---

## Q4: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** Clock distribution in a space environment has two distinct challenges: maintaining signal integrity across the network, and ensuring that a single-event upset in any clock component doesn't corrupt the timing for the whole system.

**Architecture considerations:**
- **Single source, multiple buffers:** Start with one master oscillator (ideally radiation-tolerant, or at least well-characterized) and distribute through dedicated clock buffers. This gives a coherent timing reference. The buffers should have their own supply filtering and be placed close to the loads to minimize skew.
- **Redundancy at the source:** If mission criticality justifies it, consider a redundant oscillator with automatic switchover. The switchover logic must be glitch-free — a phase hit during switchover could be as bad as losing the clock entirely. This usually means a PLL-based solution that can reacquire smoothly, or a "holdover" mode where the system continues on a local reference while the switch happens.
- **Per-device PLLs:** Each FPGA and ADC should have its own PLL to clean up any jitter introduced by the distribution network. This also provides some isolation — if one device's PLL loses lock, it doesn't drag down the others.

**Radiation-specific concerns:**
- **SETs on clock lines:** A transient on a clock line can cause a double-clock or missed-clock event, which for an ADC means a corrupted sample. For an FPGA, it could cause a metastability event or a state machine error. Mitigation: keep clock traces short and well-terminated, use differential signaling (LVDS) where possible, and consider adding a small RC filter on single-ended clock lines to reject narrow transients — but only if the clock frequency allows it.
- **SEFI in PLLs:** PLLs can experience single-event functional interrupts that cause them to lose lock or jump frequency. The system should monitor lock status and have a recovery sequence (reacquire, or reset the PLL) that doesn't require a full system reset.
- **Skew drift:** Total dose can change the propagation delay of clock buffers over the mission. Design with margin on setup/hold times and verify timing at end-of-life conditions, not just beginning-of-life.

**Synchronization approach:** For synchronized sampling across multiple ADCs, I'd use a shared sample clock plus a sync pulse that aligns all converters to the same sample boundary. The sync pulse should be generated by the master FPGA and distributed with matched delay to all ADCs. If an ADC misses the sync (due to an SET), it should be able to request a re-sync without disrupting the others.

**Possible follow-ups:**
- How would you verify that all ADCs are actually sampling simultaneously during ground test?
- What if you can't afford a dedicated clock buffer for each load — how would you daisy-chain without accumulating too much skew?

---

## Q5: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement, and how would you ensure the design review process remains constructive rather than adversarial?

**Answer:** When an engineer pushes back after a clear technical explanation, it usually means one of three things: they don't fully accept the risk analysis, they feel their design is being dismissed without fair consideration, or they're concerned about the practical implications (cost, schedule, part availability). I'd try to address all three.

**First, I'd separate the technical from the process.** I'd acknowledge that the calibration routine and ADC tolerance are legitimate points — they do reduce the impact of some failure modes. But I'd ask the engineer to walk through the specific scenario where the regulator's output drifts slowly over months due to TID. Calibration might handle a one-time offset, but if the drift is monotonic and the calibration interval is long, the system could be operating out of spec between calibrations. I'd ask: "What's the worst-case drift rate for this part, and how does that compare to your calibration schedule?" The answer is likely "we don't know" — which is exactly the point.

**Second, I'd reframe the decision as a risk acceptance question, not a design preference.** The question isn't "is this part good enough?" — it's "who is authorized to accept the risk of using an uncharacterized part in a critical function, and what's the mitigation if it fails?" In a formal design review, this means documenting the risk, assigning a severity and probability, and getting sign-off from the systems engineer or program manager. The junior engineer shouldn't be carrying that decision alone.

**Third, I'd offer a path forward that respects their constraint.** If the concern is cost or availability of a rad-hard part, I'd ask what alternatives they've considered — maybe there's a mid-grade option (a part with some radiation data, even if not fully qualified) or a way to add protection (a supervisor, a current limiter) that makes the COTS part acceptable. I'd also offer to help them find a qualified alternative rather than just rejecting their choice.

**Keeping it constructive:** I'd make sure the discussion stays focused on the design, not the person. I'd use phrases like "help me understand the trade-off you're seeing" rather than "you're wrong." I'd also make it clear that pushing back is good — we want engineers who challenge assumptions — but the challenge needs to be backed by data or analysis, not just intuition. If the engineer still disagrees after a fair hearing, I'd escalate to the formal risk review process and let the program make the call with full information.

**Possible follow-ups:**
- How would you handle this if the engineer is senior and has more experience than you?
- What if the program schedule genuinely cannot accommodate a part change — how would you proceed?