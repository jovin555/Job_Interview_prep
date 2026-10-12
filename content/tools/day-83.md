# tools — Day 83

## Q1: How would you approach setting up a spectrum analyzer for a conducted emissions pre-compliance scan on a medical device's AC input, and what would you check before trusting the first measurement?

**Answer:** Conducted emissions on the AC mains input is a distinct measurement from radiated sniffing, and the setup has to be right before any number means anything. The core chain is a LISN (line impedance stabilization network) inserted between the AC source and the device under test, with the spectrum analyzer connected to the LISN's RF output port. The LISN does two jobs: it presents a defined, repeatable RF impedance to the device so results are comparable to a reference setup, and it isolates the measurement from whatever noise is riding on the building's mains.

Before trusting a single trace, I'd verify several things. First, the LISN's own noise floor — terminate the measurement port in 50 ohms and scan; if the floor is not well below the limits I'm testing against, the setup is not sensitive enough. Second, the analyzer's settings: resolution bandwidth and detector mode must match what the applicable standard calls for (quasi-peak and average detectors are typically both required, and RBW is specified per band). Third, the grounding and physical layout — the LISN bonded to a reference ground plane, the EUT positioned and cabled per the standard's setup diagram, because cable routing alone can shift results by several dB. Fourth, a known-good reference: run a pre-characterized device or a comb generator through the same chain to confirm the whole signal path behaves as expected.

Only after those checks would I start sweeping. And I'd treat the first scan as a survey, not a verdict — I'd look at where the peaks sit relative to the limit lines, then decide whether any margin is thin enough to warrant investigation before formal testing.

**Possible follow-ups:**
- How would you distinguish a real emission from the EUT versus ambient noise picked up by the setup?
- What would you do if the LISN's noise floor were marginal at the frequencies you care about?

## Q2: How would you approach setting up a logic analyzer's protocol decoder for a custom, non-standard serial protocol on a medical device, where the framing doesn't match any built-in decoder — for example, a proprietary sensor bus with a non-byte-aligned frame header?

**Answer:** When no built-in decoder fits, the first step is not to reach for the analyzer's scripting — it's to characterize the physical layer and the frame structure on paper first. I'd capture a raw trace of a known-good transaction and work out the timing: clock or no clock, idle level, bit period, how the frame header is delimited, where the payload starts, and how the frame ends. A non-byte-aligned header usually means the frame is defined in bit counts rather than bytes, so I'd build a bit-level map before writing any decoder logic.

From there, most logic analyzers let you build a custom decoder in a scripting language (Python or similar) that consumes the raw sample stream and emits decoded fields. I'd structure it in layers: a low-level layer that finds frame boundaries from the header pattern, a middle layer that slices the payload into fields according to the bit map, and a high-level layer that labels fields with human-readable names and flags protocol errors like bad checksum or unexpected length. Keeping the layers separate makes it far easier to fix a boundary-detection bug without touching field parsing.

Two practical points matter a lot here. First, sample rate: to decode reliably you generally want to oversample well above the bit rate, and you need enough capture depth to see several complete frames plus the inter-frame gaps. Second, I'd validate the decoder against a frame I can independently verify — for instance, a transaction where I already know the expected sensor value from another source — before trusting it on an intermittent failure. A decoder that's subtly wrong is worse than no decoder, because it will send you chasing phantom protocol errors.

**Possible follow-ups:**
- How would you handle a frame header that can also appear inside the payload by coincidence?
- What would you change in the decoder if the bus occasionally ran at a different bit rate during negotiation?

## Q3: How would you approach configuring a Keil uVision project for a medical device firmware build so that the optimization level, linker script, and startup code are locked down and auditable, rather than relying on whatever the IDE defaults to?

**Answer:** The underlying problem is that an IDE project file is a build artifact in its own right, and if its critical settings live only in a GUI that someone can click through, you have no audit trail and no reproducibility. So the approach is to treat the build configuration as version-controlled source, not as IDE state.

Concretely, I'd start by deciding which settings are safety-relevant and must be explicit: optimization level, the linker script (memory layout, section placement, stack and heap sizing), the startup code, preprocessor defines that select hardware variants, and any floating-point or ABI options. Those get set deliberately and documented with a rationale — for example, why a particular optimization level was chosen and what was verified at that level. Then I'd make the project file itself a tracked artifact in version control, so any change to those settings shows up as a diff in review rather than as an invisible local tweak.

For auditability, I'd add a build step that emits the effective configuration — compiler version, optimization flags, defines, linker script path and hash — into the build log or a manifest file that ships alongside the firmware image. That way, when a regulator or an internal reviewer asks "what exactly was built," the answer is a file, not a recollection. Where the toolchain supports it, I'd also consider driving the build from a command-line makefile or script that the IDE merely invokes, so the canonical build is scriptable and CI can reproduce it. The IDE then becomes a convenience front-end rather than the source of truth.

**Possible follow-ups:**
- How would you catch a case where someone changed the optimization level locally but the committed project file still shows the old value?
- What would you include in a build manifest to make a firmware image traceable back to its exact source and settings?

## Q4: How would you approach using a spectrum analyzer's tracking generator and a directional coupler to characterize the input impedance of a custom analog front-end, and how would you decide whether the measurement is trustworthy enough to act on?

**Answer:** A tracking generator plus a directional coupler lets you do a poor-man's return-loss measurement: the tracking generator sweeps a known stimulus, the directional coupler separates the forward wave from the reflected wave, and the analyzer measures the reflected power relative to the forward power. From return loss you can derive the magnitude of the input reflection coefficient, and with a reference plane and a known system impedance you can estimate the input impedance magnitude across frequency. It's a scalar measurement — it gives you magnitude, not phase — so it tells you how well matched the front-end is, not the full complex impedance.

The trustworthiness question is where most of the work is. First, I'd calibrate out the test setup: cables, connectors, and the coupler itself all contribute loss and reflections, so I'd measure a known reference — an open, a short, and a matched load — and either normalize against them or at least understand the residual error they introduce. Second, I'd check the directivity of the directional coupler, because a coupler with poor directivity will report reflected power that isn't really there, which is exactly the kind of error that makes you "fix" a problem you don't have. Third, I'd confirm the reference plane: where exactly the measurement is being made relative to the front-end's input, since a length of trace between the connector and the actual input shifts the result.

I'd decide to act on the data only if the residual error after calibration is small compared to the effect I'm trying to observe. If the front-end is supposed to be matched to 50 ohms and the measurement shows a large mismatch, that's a real signal worth chasing. If the measurement shows a small mismatch that's within the setup's uncertainty, I would not redesign anything based on it — I'd either improve the measurement or use a proper VNA that gives me phase and a cleaner calibration.

**Possible follow-ups:**
- How would you extend this to get phase information, and why does phase matter for a front-end?
- What would you do if the coupler's directivity were the dominant error source?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the lab's spectrum analyzer and near-field probe for an EMI pre-compliance scan, and you discover the resolution bandwidth and detector mode are set for a quick "get a feel for it" scan rather than the settings the test standard requires. The engineer is confident the settings are fine because "the peaks show up either way." The formal scan is scheduled for tomorrow, and the lab time is booked. How would you handle this situation?

**Answer:** The first thing I'd do is separate the technical issue from the interpersonal one, because they need different responses. Technically, the engineer is partly right — the peaks do show up either way, which is why a survey scan is useful. But a survey scan and a compliance scan answer different questions. Resolution bandwidth affects both the noise floor and the apparent amplitude of a peak, and detector mode determines whether you're reading quasi-peak, average, or peak values. A scan run with the wrong settings can show a peak that looks comfortably under the limit when the correct detector would show it over, or vice versa. So the settings aren't cosmetic; they change the pass/fail conclusion.

I'd explain that distinction rather than just asserting "you're wrong," because the engineer's instinct — that the peaks are visible — is reasonable and worth acknowledging. Then I'd frame the decision in terms of risk: the formal scan is the one whose results feed a compliance argument, and if it's run with survey settings, the data may not be defensible and the lab time is wasted anyway. That reframes fixing the settings as protecting the schedule, not as slowing it down.

Practically, I'd check whether the correct settings can be applied and the scan re-run within the booked time, or whether a short pre-scan tonight with the right settings can confirm whether any peak is close enough to the limit to need the full formal treatment. If the lab time genuinely can't accommodate a correct scan, I'd rather reschedule or rebook than submit data I don't trust. And afterward, I'd make the required settings part of a written pre-scan checklist so this becomes a process fix rather than a one-off correction — and I'd make sure the engineer understood the "why," not just the "what," so the lesson sticks.

**Possible follow-ups:**
- How would you handle it if the engineer felt you were second-guessing them in front of the team?
- What would you put on a pre-scan checklist to prevent this class of setup error?