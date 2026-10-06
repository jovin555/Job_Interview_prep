# tools — Day 77

## Q1: How would you approach setting up a logic analyzer's protocol decoder for a custom, non-standard serial protocol on a medical device, where the framing doesn't match any built-in decoder — for example, a proprietary sensor bus with a non-byte-aligned frame header?

**Answer:** The first step is to resist the temptation to force a built-in decoder onto a protocol it doesn't fit. Instead, capture raw transitions first and treat the decoder as a second-stage problem. I'd start by probing the clock and data lines with adequate sample rate — at least 4–10× the fastest edge rate, and ideally synchronous sampling on the clock if one exists — then capture a known-good transaction so I have a reference waveform to reason about. From there I'd manually annotate the capture: identify the idle level, the start condition or sync pattern, and the bit boundaries. If the frame header is non-byte-aligned, the key is to find a deterministic sync word or edge that resets the bit counter, because without a resync anchor any decoder will drift.

Once I understand the framing on paper, I'd implement a custom decoder — most logic analyzer software (Saleae, Sigrok, etc.) supports a scripting layer for this. I'd write it as a small state machine: wait for sync, count bits according to the header field, extract payload fields at their defined offsets, and emit decoded values with a checksum or CRC field validated inline. The decoder should flag framing errors rather than silently misaligning, because a decoder that produces plausible-but-wrong output is worse than no decoder at all. I'd validate the decoder against several captures, including deliberately corrupted frames, to confirm it rejects bad data.

For a medical device context, I'd also document the decoder alongside the protocol spec so it becomes a reusable verification asset — the same decoder can later be used in automated test fixtures, not just manual debugging.

**Possible follow-ups:**
- How would you handle a protocol where the bit rate isn't fixed, or where the clock is embedded rather than separate?
- What would you do if the decoder works on your bench capture but produces garbage on a different unit?

## Q2: How would you approach configuring a Keil uVision project for a medical device firmware build so that the optimization level, linker script, and startup code are locked down and auditable, rather than relying on whatever the IDE defaults to?

**Answer:** The core principle is that build configuration is a controlled artifact, not an IDE convenience. I'd start by treating the project file itself as source — checked into version control, reviewed like code, and never edited casually through the GUI without a corresponding review. In Keil specifically, that means the `.uvprojx` file and any associated scatter files are under revision control, and changes to optimization level, defines, include paths, or linker settings show up as diffs in a pull request.

For the optimization level, I'd pin it explicitly rather than leaving it at whatever the target default is. Debug and release configurations should be separate, named targets with clearly different settings — for example, `-O0` with full debug info for development, and a defined optimization level for release — and the choice should be justified in the build documentation. The reason this matters in a regulated context is that optimization can change timing behavior, expose or hide undefined behavior, and alter code size in ways that affect memory layout. If the release build uses a different optimization level than what was tested, the test evidence doesn't strictly apply to the shipped binary.

For the linker script and startup code, I'd keep them as explicit project files rather than IDE-generated, with memory regions, stack/heap sizes, and section placement documented. The startup code should be reviewed for things like vector table placement, clock initialization order, and watchdog handling. I'd also add a build-time check — a script or post-build step — that verifies the expected optimization flags and linker script were actually used, so a misconfigured build fails loudly rather than silently producing a non-conforming binary.

**Possible follow-ups:**
- How would you make the build reproducible across different developer machines and CI?
- What would you check to confirm the released binary actually matches the reviewed source and settings?

## Q3: How would you approach using a spectrum analyzer's tracking generator and a directional coupler to characterize the input impedance of a custom analog front-end, and how would you decide whether the measurement is trustworthy enough to act on?

**Answer:** The tracking generator plus directional coupler approach is essentially a poor-man's return loss / reflection measurement: the tracking generator sweeps a known signal, the directional coupler separates the incident and reflected waves, and the analyzer measures the reflected power relative to the incident. From return loss you can derive the magnitude of the reflection coefficient and, with a reference plane and a known characteristic impedance, estimate the input impedance magnitude. It's a useful sanity check, but it has real limitations that determine whether you should trust it.

The first trust question is calibration. You need to calibrate out the coupler's directivity, the cable losses, and the connector interface — ideally with an open/short/load calibration at the reference plane where you actually care about the impedance. Without that, you're measuring the test setup as much as the device. The second question is directivity: a directional coupler with modest directivity will leak incident power into the reflected port, which sets a floor on how small a reflection you can resolve. If your device is well-matched, the measurement may be dominated by coupler imperfection rather than the device.

The third question is whether the measurement is even the right tool. A tracking generator setup gives you magnitude only, not phase, so you can't fully separate resistive and reactive components of the impedance — you get a magnitude estimate, not a complex impedance. If the front-end is sensitive to phase (for example, a filter or a matching network), a VNA is the correct instrument, and I'd say so rather than over-interpreting the scalar measurement.

So my decision rule: if the goal is a coarse check — "is this input roughly 50 ohms, or is something badly wrong?" — the tracking generator method is fine, provided calibration and directivity are adequate. If the goal is to tune a matching network or verify a filter response, I'd push for a VNA or at least acknowledge the measurement can't answer the question. I'd also cross-check with a simpler method where possible, like a time-domain reflectometry measurement or a known reference load, to confirm the setup is behaving.

**Possible follow-ups:**
- How would you estimate the uncertainty in the impedance measurement from the coupler's directivity spec?
- What would you do if the measurement suggests a mismatch but the circuit works fine in practice?

## Q4: How would you approach setting up a Segger J-Link's RTT (Real-Time Transfer) logging for a Zephyr RTOS target where you need continuous debug output but the UART is already committed to a safety-critical protocol, and how would you avoid the logging itself perturbing the system's timing?

**Answer:** RTT is attractive here precisely because it uses the debug interface rather than a peripheral, so it doesn't compete with the UART. The setup is straightforward — enable the RTT control block in the firmware, point the J-Link software at it, and read the buffer — but the interesting part is making it safe and non-perturbing.

The first concern is timing perturbation. RTT writes go into a RAM buffer, and the target-side cost is a memory copy plus a buffer management check. That's cheap, but not free, and if logging happens in a tight ISR or a hard-real-time loop, even a short memcpy can matter. My approach is to keep the logging calls out of the most timing-critical paths, or to make them conditional on a compile-time flag so the release build has them compiled out entirely. I'd also size the buffer generously so the target rarely blocks waiting for the host to drain it — if the buffer fills, the target either drops messages or stalls, and stalling is the dangerous failure mode.

The second concern is that RTT itself can change behavior. If the debugger isn't attached, the target-side RTT code should degrade gracefully rather than blocking. I'd verify that the firmware runs identically with and without a debugger attached, and I'd measure the timing impact — for example, by toggling a GPIO around a logging call and looking at it on a scope — to confirm the perturbation is within budget.

The third concern is that RTT output is only as good as what you log. For a safety-critical system, I'd define a logging policy: what gets logged, at what level, and what must never be logged (for example, patient data or anything that could be misconstrued as a safety-relevant event without context). The logs are a debugging aid, not a substitute for the safety-critical protocol on the UART.

**Possible follow-ups:**
- How would you handle a situation where the RTT buffer fills faster than the host can drain it?
- What would you check to confirm the logging isn't masking a race condition or timing bug?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the lab's spectrum analyzer and near-field probe for an EMI pre-compliance scan, and you discover the resolution bandwidth and detector mode are set for a quick "get a feel for it" scan rather than the settings the test standard requires. The engineer is confident the settings are fine because "the peaks show up either way." The formal scan is scheduled for tomorrow, and the lab time is booked. How would you handle this situation?

**Answer:** The first thing I'd do is separate the technical issue from the interpersonal one. Technically, the engineer isn't entirely wrong that peaks show up either way — a wide resolution bandwidth and a peak detector will absolutely reveal that emissions exist. The problem is that the measurement isn't comparable to the standard, and pre-compliance results that aren't comparable to the standard can't be used to judge pass/fail margin. A wide RBW can smear or merge adjacent emissions, and the wrong detector can over- or under-state the amplitude relative to the quasi-peak or average limits the standard specifies. So the scan might look fine and still miss a real failure, or flag a failure that isn't one.

I'd explain that distinction directly but without making it a personal failing — this is a common and understandable shortcut, and the fix is procedural, not a matter of the engineer's competence. Then I'd make the call on the schedule. The lab time is booked and non-refundable, so cancelling outright may be wasteful. The pragmatic move is usually to keep the slot but use it correctly: reconfigure the analyzer to the standard's RBW and detector settings, and run the scan properly. If the setup can't be corrected in time, I'd rather use the slot for a properly configured scan of the highest-risk areas than run a full scan with the wrong settings and treat the results as meaningful.

I'd also treat this as a process gap rather than a one-off. If a junior engineer is setting up pre-compliance equipment, there should be a written setup checklist tied to the test standard, and a second pair of eyes on the configuration before the scan starts. I'd put that in place so the next scan doesn't depend on someone catching it in review. And I'd follow up with the engineer afterward to make sure the lesson lands as "here's how we make the measurement defensible" rather than "you got it wrong."

**Possible follow-ups:**
- How would you decide whether to use the booked lab slot or reschedule?
- What would you put in a pre-compliance setup checklist to prevent this recurring?