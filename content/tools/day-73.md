# tools — Day 73

## Q1: How would you approach setting up a logic analyzer's protocol decoder for a custom, non-standard serial protocol on a medical device, where the framing doesn't match any built-in decoder (e.g., a proprietary sensor bus with a non-byte-aligned frame header)?

**Answer:** The key insight is that a logic analyzer's built-in decoders are just pattern matchers over the captured sample stream, so a non-standard protocol is a decoding problem, not a hardware problem. I'd start by capturing raw transitions at a sample rate comfortably above the bit rate — at least 4–10× the fastest edge rate, and high enough that I can resolve the smallest pulse in the frame. Before writing any decoder, I'd characterize the physical layer on the scope: idle level, bit period, whether it's NRZ or Manchester-like, and where the frame boundaries actually fall. That tells me whether the "non-byte-aligned header" is a real framing quirk or just a clock-recovery artifact.

From there I'd build the decoder in layers. First, a bit-level extractor that samples at the center of each bit cell using the recovered clock or a known preamble. Second, a frame-level state machine that recognizes the header pattern and knows the frame length. Third, a payload parser. Most logic analyzer tools let you script this — a Python or vendor-specific decoder API — and I'd validate each layer against a known-good capture before trusting it on a failing one. The trap with custom protocols is assuming the header is fixed-length; I'd verify by capturing many frames and diffing them, because a "header" that varies in length is usually a length field or a type field in disguise.

For a medical device context, I'd also document the decoder and its assumptions, because if it's used for verification evidence, someone needs to be able to reproduce the decode independently.

**Possible follow-ups:**
- How would you handle a protocol where the clock is embedded in the data (e.g., Manchester or 8b/10b) rather than a separate clock line?
- If the decoder works on one capture but fails on another, what would you check first?

## Q2: How would you approach configuring a Keil uVision project for a medical device firmware build so that the optimization level, linker script, and startup code are locked down and auditable, rather than relying on whatever the IDE defaults to?

**Answer:** The core problem is that IDE project files are easy to change accidentally and hard to diff, so the goal is to make the build configuration explicit, version-controlled, and reproducible. I'd start by treating the `.uvprojx` (or equivalent) as a first-class artifact under version control, and I'd minimize the settings that live only in the GUI. Where the toolchain supports it, I'd move as much as possible into a command-line build script or a makefile that the IDE invokes, so the authoritative build is scriptable and can run in CI.

For the specific settings: optimization level should be pinned and documented with a rationale — for safety-critical code, `-O0` or a carefully chosen level with known behavior is often preferred, and the choice should be justified in the build documentation, not left to a default. The linker script should be checked in and referenced by an explicit path, with the memory map verified against the actual device. Startup code and vector table should be reviewed and versioned. I'd also add a post-build step that records the compiler version, flags, and a hash of the source tree into the build output, so any released binary can be traced back to exactly what produced it.

The auditability piece is what separates this from just "setting up a project." For regulatory purposes, you need to be able to say "this binary was built from this source with these tools and these flags," and that means the build must be reproducible and the configuration must be reviewable.

**Possible follow-ups:**
- How would you detect that someone changed the optimization level in the IDE without updating the build script?
- What would you do if the compiler version used for a released binary is no longer available?

## Q3: How would you approach using a spectrum analyzer's tracking generator and a directional coupler to characterize the input impedance of a custom analog front-end, and how would you decide whether the measurement is trustworthy enough to act on?

**Answer:** The tracking generator plus directional coupler gives you a return-loss (S11 magnitude) measurement, which is a proxy for input impedance. The setup matters more than the instrument: the coupler's directivity sets the floor of what you can resolve, and any mismatch in the reference plane between the coupler and the device under test will show up as ripple that isn't real. I'd start by calibrating with a known open/short/load at the exact reference plane where the DUT connects, and I'd verify the calibration by measuring a known-good load and confirming the return loss is where I expect it.

For a custom analog front-end, the interesting region is usually the band where the source impedance and the front-end impedance interact — for a sensor interface, that's often low frequency, where a spectrum analyzer's tracking generator may not go. So I'd check the instrument's frequency range first and, if it doesn't cover the band of interest, use a different method (a network analyzer, or a discrete impedance measurement with a signal generator and a scope). Assuming the range is adequate, I'd sweep slowly enough to resolve narrow features, and I'd repeat the measurement with the DUT powered and unpowered, because active devices can present very different impedances depending on bias.

The trustworthiness question comes down to: does the measurement agree with an independent method? If I can cross-check the impedance at a few spot frequencies with a different technique — say, injecting a known signal and measuring the voltage/current ratio — and the numbers agree, I'll act on it. If they don't, I'd suspect the fixture or the calibration before I'd suspect the DUT.

**Possible follow-ups:**
- How would you account for the parasitic inductance and capacitance of the fixture itself at higher frequencies?
- What would you do if the front-end is differential rather than single-ended?

## Q4: How would you approach setting up a Segger J-Link's RTT (Real-Time Transfer) logging for a Zephyr RTOS target where you need continuous debug output but the UART is already committed to a safety-critical protocol, and how would you avoid the logging itself perturbing the system's timing?

**Answer:** RTT is attractive here precisely because it doesn't consume a UART — it uses the debug probe's memory access to read a ring buffer in target RAM, so the target-side cost is just the writes into that buffer. The setup is: allocate an RTT control block and up-channel buffer in the target's memory (Zephyr has a `SEGGER_RTT` backend for its logging subsystem), configure the buffer size based on expected log volume and the host's polling rate, and connect the J-Link's RTT viewer or a scripted reader on the host side.

The timing-perturbation concern is real and worth taking seriously. Every log write is a memory write plus, depending on the implementation, possibly a lock or a memcpy, so the cost scales with message size and frequency. For a system with hard real-time constraints, I'd do three things. First, keep messages short and use a non-blocking, lock-free ring buffer so a full buffer drops messages rather than blocking the producer. Second, measure the actual cost — toggle a GPIO around a log call and look at it on the scope, or use the RTOS's timing facilities — so I know the worst-case added latency rather than assuming it's negligible. Third, run the system with logging enabled and disabled and compare timing-sensitive behavior; if the behavior changes, the logging is part of the problem, not just an observer of it.

I'd also be careful about what gets logged. Logging inside an ISR or a high-priority thread is where perturbation bites hardest, so I'd either avoid it there or use a deferred logging mechanism that hands off to a lower-priority thread.

**Possible follow-ups:**
- How would you handle the case where the RTT buffer overflows and you lose the log entries leading up to a crash?
- What's the difference between RTT and SWO trace, and when would you choose one over the other?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the lab's spectrum analyzer and near-field probe for an EMI pre-compliance scan, and you discover the resolution bandwidth and detector mode are set for a quick "get a feel for it" scan rather than the settings the test standard requires. The engineer is confident the settings are fine because "the peaks show up either way." The formal scan is scheduled for tomorrow, and the lab time is booked. How would you handle this situation?

**Answer:** The engineer isn't wrong that the peaks show up — the issue is that the amplitude and the comparison to the limit line depend on the settings, so a scan with the wrong RBW and detector can't be used as evidence of pass or fail. I'd treat this as a teaching moment rather than a blame moment, because the underlying confusion — "the peak is there, so what's the difference?" — is a very reasonable one if you haven't worked through what RBW and detector actually do.

My approach would be: first, confirm the correct settings for the target standard (RBW, detector, dwell time, frequency range, and any averaging) and write them down. Second, walk the engineer through why they matter — RBW sets the noise floor and the resolution of closely spaced emissions, and the detector (peak vs. quasi-peak vs. average) determines what amplitude you report, which is exactly what the limit is defined against. Third, re-run the scan with the correct settings tonight if the lab is available, or first thing tomorrow if it isn't, and compare the two scans so the engineer can see the difference concretely. That comparison is the lesson.

If the lab time is genuinely at risk, I'd prioritize: the formal scan is the deliverable, so it happens with correct settings. If that means the "get a feel for it" scan gets redone, that's the cost of getting it right. I'd also make sure the correct settings are documented as a preset or a procedure so the next person doesn't have to rediscover them.

**Possible follow-ups:**
- How would you decide whether a marginal emission is a real problem or a measurement artifact?
- What would you do if the correct settings reveal a failure that the quick scan missed, and the project schedule assumed a pass?