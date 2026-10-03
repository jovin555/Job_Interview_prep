# tools — Day 74

## Q1: How would you approach setting up a logic analyzer's protocol decoder for a custom, non-standard serial protocol on a medical device, where the framing doesn't match any built-in decoder — for example, a proprietary sensor bus with a non-byte-aligned frame header?

**Answer:** The first step is to resist the temptation to force the capture into an existing decoder that "almost" fits. A non-byte-aligned frame means the built-in decoders will misalign on the header and produce garbage downstream, which is worse than no decode at all because it creates false confidence. Instead, I'd work from the physical layer up.

I'd start by capturing a long, clean trace of the bus with the analog channels enabled alongside the digital ones, so I can see the actual edge shapes and confirm the logic thresholds are set correctly for the bus voltage. Then I'd identify the frame boundaries manually — usually there's a distinctive idle pattern, a sync pulse, or a header whose width in clock cycles is consistent. Measuring that header width in samples and converting to bit periods tells me the bit rate and, critically, whether the header is an integer number of bits or something like 1.5 bits, which is what breaks byte-aligned decoders.

Once I know the bit period, I'd set up a custom decoder using the logic analyzer's scripting interface (most modern analyzers let you write a Python or C-like decoder). The decoder would implement a state machine: wait for the header pattern, then sample at the known bit period, accumulate bits into a frame, and emit the frame when the terminator or checksum is seen. I'd validate the decoder against a known-good capture first — ideally one where I can correlate the decoded values against a value I can read out over a debug interface or a second instrument. If the decoded values match, the decoder is trustworthy; if not, I iterate on the bit alignment.

A key detail: I'd make the decoder tolerant of the real-world imperfections — jitter, occasional dropped bits, resync after a glitch — rather than assuming a perfect bitstream. And I'd document the decoder alongside the protocol spec so the next person doesn't have to reverse-engineer it again.

**Possible follow-ups:**
- How would you handle a protocol where the bit period itself changes between frames (e.g., a low-power mode with a slower clock)?
- What would you do if the custom decoder works on the bench but produces different results when the device is in its enclosure and the bus is loaded?

## Q2: How would you approach configuring a Keil uVision project for a medical device firmware build so that the optimization level, linker script, and startup code are locked down and auditable, rather than relying on whatever the IDE defaults to?

**Answer:** The core problem with IDE-managed build settings is that they live in a project file that's easy to change accidentally and hard to diff meaningfully. For a medical device, that's a regulatory problem as much as an engineering one — you need to be able to demonstrate that the binary you shipped was built from a known configuration.

My approach would be to treat the build configuration as a first-class artifact. First, I'd move as much as possible out of the IDE's GUI-managed settings and into version-controlled files: the linker script, the startup assembly, and any scatter-loading files should be explicit files in the repo, referenced by the project, not generated or embedded in the project file. The optimization level and preprocessor defines I'd pin explicitly rather than leaving them at "default," because "default" changes between toolchain versions.

Second, I'd add a build-time assertion or a post-build check that verifies the actual configuration used. Keil exposes the build command line, so a post-build step can grep the map file or the build log for the expected optimization flag and fail the build if it doesn't match. That turns a silent misconfiguration into a loud build failure.

Third, I'd make the project file itself reviewable. Keil's `.uvprojx` is XML, so it can be diffed, but it's noisy. I'd keep the human-meaningful settings in a small, documented config file or a header that the project includes, and treat the `.uvprojx` as a thin wrapper. Any change to optimization level, linker script path, or startup file would then show up as a one-line diff in a file a reviewer actually reads.

Finally, I'd document the toolchain version and the exact build invocation in the release record, so the build is reproducible. For a medical device, "it built on my machine" isn't good enough — the release artifact needs to be tied to a specific, recorded configuration.

**Possible follow-ups:**
- How would you handle a situation where a third-party library ships with its own Keil project that assumes different optimization settings?
- What's your approach to verifying that the startup code actually initializes everything the application expects, without stepping through it manually every release?

## Q3: How would you approach using a spectrum analyzer's tracking generator and a directional coupler to characterize the input impedance of a custom analog front-end, and how would you decide whether the measurement is trustworthy enough to act on?

**Answer:** The tracking generator plus directional coupler gives you a return-loss (or reflection coefficient) measurement across frequency, which you can convert to impedance if you know the reference impedance and the coupler's characteristics. The measurement is conceptually simple but easy to get wrong, so the bulk of the work is in establishing trust in the setup before believing any number.

I'd start by calibrating the setup with known standards — open, short, and a precision 50-ohm load — at the reference plane where I'll connect the front-end. This establishes the systematic errors of the coupler, cables, and connectors, and lets me apply a correction. Without this, the raw return loss includes the fixture, and I'd be characterizing my cables as much as the device.

Then I'd connect the front-end and sweep the band of interest. The key sanity checks: does the result look physically plausible? A front-end with a known input network should show resonances and impedance trends that match the topology — if I see a sharp null at a frequency where there's no resonant element, something's wrong with the fixture or the calibration. I'd also check for connector repeatability by disconnecting and reconnecting a few times; if the trace moves significantly, the connection is unreliable and the measurement isn't trustworthy.

The decision to act on the result depends on the margin. If the impedance is comfortably within the range the source can drive, small measurement uncertainty doesn't matter. If it's near a boundary — say, the front-end is approaching a region where the source might become unstable — then I need the measurement to be good enough to distinguish "close to the edge" from "over the edge," and I'd tighten the calibration or use a different method (like a VNA with a proper test fixture) to reduce uncertainty.

I'd also cross-check with a time-domain measurement where possible — a step response or a TDR-style measurement can confirm the frequency-domain result and catch gross errors that a single sweep might hide.

**Possible follow-ups:**
- How would you extend this to characterize the front-end's impedance under different bias conditions, where the active devices change operating point?
- What are the limits of a directional-coupler-based measurement compared to a proper VNA, and when would you insist on the VNA?

## Q4: How would you approach setting up a Segger J-Link's RTT (Real-Time Transfer) logging for a Zephyr RTOS target where you need continuous debug output but the UART is already committed to a safety-critical protocol, and how would you avoid the logging itself perturbing the system's timing?

**Answer:** RTT is attractive here precisely because it doesn't consume a UART — it uses the debug probe's memory access to read a ring buffer out of target RAM, so the safety-critical UART stays untouched. But "doesn't consume a UART" doesn't mean "free." The logging still costs CPU cycles to format and write into the ring buffer, and it costs RAM for the buffer itself. On a medical device, both of those can matter.

The first thing I'd do is separate the logging mechanism from the logging policy. RTT gives you a channel; what you put on it is a design decision. I'd configure the RTT buffer size deliberately — large enough to absorb bursts without dropping messages, small enough not to eat into the RAM budget for the safety-critical path. I'd also decide the logging level per module: the safety-critical protocol code probably logs nothing or only errors, while less timing-sensitive modules can log more freely.

To avoid perturbing timing, I'd make the logging calls non-blocking and bounded. Zephyr's logging subsystem supports deferred modes where the formatting happens in a low-priority thread rather than in the calling context, which keeps the critical path short. If the critical path must log directly, I'd pre-format or use a fixed-size binary record rather than a printf-style call, so the worst-case execution time is predictable.

I'd also measure the impact rather than assume it. A common approach is to toggle a GPIO at the start and end of the critical section and watch it on a scope with logging on and off — if the timing changes measurably, the logging is too intrusive and needs to be deferred or removed from that path. For a safety-critical protocol, "the timing looks fine" isn't enough; I want a measurement that shows the jitter budget is still met.

Finally, I'd make sure the RTT buffer and the logging configuration are part of the build configuration, not something enabled ad hoc, so a release build can have logging compiled out entirely and the debug build can have it in — with the same code path otherwise.

**Possible follow-ups:**
- How would you handle a situation where the RTT buffer overflows during a burst of errors, and you need the earliest messages rather than the latest?
- What's your approach to correlating RTT log timestamps with an external logic analyzer capture, so you can align firmware events with bus traffic?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the lab's spectrum analyzer and near-field probe for an EMI pre-compliance scan, and you discover the resolution bandwidth and detector mode are set for a quick "get a feel for it" scan rather than the settings the test standard requires. The engineer is confident the settings are fine because "the peaks show up either way." The formal scan is scheduled for tomorrow, and the lab time is booked. How would you handle this situation?

**Answer:** The engineer's statement — "the peaks show up either way" — is actually true and also beside the point, which is the crux of how I'd handle it. A quick scan with wide resolution bandwidth and a peak detector will show you where energy is, which is useful for finding suspects. But pre-compliance against a standard requires specific RBW and detector settings because the measured amplitude depends on them. A peak that looks marginal at one setting can look compliant or non-compliant at another, and the formal test will use the standard's settings. So the risk isn't that we'll miss the peak — it's that we'll misjudge its margin and either waste the lab time chasing a non-issue or walk into the formal test unprepared.

My first move would be to separate the two concerns: the quick scan did its job (it found the suspects), and now we need a standards-compliant measurement to know the actual margin. I'd frame it that way to the engineer — not "you did it wrong," but "this scan answered a different question than the one tomorrow's test asks." That keeps it collaborative and makes the correction about the measurement's purpose rather than about the person.

Then I'd assess whether we can fix it in time. Re-running the scan with the correct RBW and detector is usually a matter of changing a few settings and re-sweeping — it doesn't require new hardware or a new setup. If the lab is available tonight, we do it tonight. If not, I'd check whether the correct settings can be applied and the scan re-run in the morning before the formal slot, or whether we need to reschedule. The decision hinges on whether the corrected scan changes our understanding of the margin — if the quick scan showed 20 dB of margin, the exact settings matter less; if it showed 2 dB, they matter a lot.

I'd also use it as a teaching moment about why the standard specifies those settings, and I'd add a checklist or a saved setup file to the lab so the next person doesn't have to rediscover it. The goal isn't to catch the mistake — it's to make the mistake harder to repeat.

**Possible follow-ups:**
- How would you decide whether to reschedule the lab time or proceed with the corrected settings applied on the fly?
- What would you put in a lab setup file or checklist to make standards-compliant scans the default rather than the exception?