# tools — Day 80

## Q1: How would you approach setting up a spectrum analyzer for a conducted emissions pre-compliance scan on a medical device's AC input, and what would you check before trusting the first measurement?

**Answer:** I'd start by treating the setup itself as the first thing to validate, because a conducted emissions scan is only as good as the measurement chain. The core elements are a LISN (line impedance stabilization network) inserted on the AC mains feeding the device under test, a spectrum analyzer with the correct input attenuation and a defined reference level, and a clean, known-good ground reference for the whole bench. Before running anything, I'd confirm the LISN is rated for the current the device draws, that its RF output is properly terminated into the analyzer's 50-ohm input, and that the mains feed to the LISN is itself reasonably quiet — otherwise I'm measuring the building's noise, not the device's.

For analyzer settings, I'd pick a resolution bandwidth and detector mode that match the test standard being targeted rather than whatever gives a fast, pretty trace. A quick "get a feel for it" scan with a wide RBW and peak detector will show peaks, but it won't tell me whether the device actually passes a quasi-peak limit. I'd also set the frequency span and sweep time so the trace is stable and repeatable, and I'd run a baseline scan with the device powered off to characterize the ambient and the LISN's own noise floor.

The key discipline is: don't trust the first trace. Run it twice, check that the ambient baseline is well below the limits I care about, and confirm the device's emissions are actually above that baseline. If the margin between ambient and device emissions is small, the measurement is not trustworthy and I need a quieter environment or a different approach before drawing conclusions.

**Possible follow-ups:**
- How would you decide whether a marginal peak is a real device emission or an artifact of the LISN or the mains supply?
- What would you change in the setup if the device is battery-powered and has no AC input to put a LISN on?

## Q2: How would you approach configuring a Keil uVision project so that the optimization level, linker script, and startup code are locked down and auditable rather than left at whatever the IDE defaults to?

**Answer:** The problem with IDE defaults is that they're invisible — a project can build and run fine for months, then someone opens it on a different machine or a newer toolchain version and the optimization level silently changes, or the linker script gets regenerated. For anything going into a regulated product, I want those settings to be explicit, version-controlled, and reviewable as text, not buried in a binary project file.

My approach is to treat the build configuration as source. The optimization level, the linker script path, the startup file, and the preprocessor defines all belong in the project file that's committed to version control, and I'd document in the project's README or a build notes file exactly what each setting is and why. I'd avoid relying on the IDE's "default" for anything safety-relevant — if the default is `-O0` for debug and `-O2` for release, I want both explicitly stated so a reviewer can see the difference and sign off on it.

I'd also separate debug and release configurations cleanly, so there's no ambiguity about which one produced a given binary. The linker script and startup code should be checked in as files the project references, not generated on the fly, so that a diff shows exactly what changed. And I'd add a build step or a script that prints the effective compiler flags and linker script path into the build log, so the artifact's provenance is auditable — if a regulator or an internal reviewer asks "what optimization level was this firmware built with," the answer is in the log, not in someone's memory.

**Possible follow-ups:**
- How would you catch a situation where the optimization level was changed but the change wasn't reviewed?
- What's the risk of testing at one optimization level and shipping at another, and how would you manage it?

## Q3: How would you approach using a spectrum analyzer's tracking generator and a directional coupler to characterize the input impedance of a custom analog front-end, and how would you decide whether the measurement is trustworthy enough to act on?

**Answer:** A tracking generator plus a directional coupler lets me measure return loss — how much of the incident signal reflects back from the front-end's input — and from that I can infer the input impedance across frequency. The setup is: tracking generator output into the coupler's input port, the coupler's through port into the front-end input, and the coupler's coupled port into the analyzer's input. The analyzer sweeps in sync with the generator, and I read the reflected power relative to the incident power.

The first thing I'd do is calibrate out the test setup itself. The coupler, the cables, and any adapters all have their own frequency response and their own reflections, and if I don't characterize them with a known load — an open, a short, and a 50-ohm termination — I'll be measuring the test bench, not the front-end. I'd run a full one-port calibration if the analyzer supports it, or at minimum a normalization sweep with a 50-ohm load at the reference plane where the front-end connects.

Whether to trust the result comes down to a few checks. Is the return loss I'm seeing well above the noise floor of the measurement? If the reflected signal is only a few dB above the analyzer's noise, the number is meaningless. Is the calibration still valid at the frequency of interest — did I calibrate at the same reference plane I'm measuring at? And does the result make physical sense? If the front-end is supposed to look like a high-impedance differential input at low frequency and I'm seeing a 50-ohm match, something is wrong with the setup or the front-end.

I'd also cross-check with a second method where possible — for example, a network analyzer if one is available, or a simple impedance measurement at a spot frequency — because agreement between two independent methods is much stronger evidence than a single trace that looks plausible.

**Possible follow-ups:**
- How would you handle a front-end that's differential rather than single-ended when using a single-ended coupler and analyzer?
- What would you do if the return loss measurement looked fine but the front-end still performed poorly in the actual application?

## Q4: How would you approach setting up a logic analyzer's protocol decoder for a custom, non-standard serial protocol on a medical device, where the framing doesn't match any built-in decoder — for example, a proprietary sensor bus with a non-byte-aligned frame header?

**Answer:** When the framing doesn't match a built-in decoder, I stop thinking about decoding and start thinking about characterizing the signal first. I'd capture the raw waveform on the relevant lines — clock, data, and any framing or enable signals — and look at the actual timing: where does the frame start, how is the header delimited, is the data MSB-first or LSB-first, is the clock idle high or low, and how many clock edges make up a frame. That gives me the ground truth the decoder has to match.

From there, I'd build the decoder in layers. The lowest layer is just edge detection and bit sampling — I'd configure the analyzer to sample on the correct clock edge and at the right point in the bit period, which usually means sampling near the middle of the bit rather than at the edge. The next layer is framing: a state machine that recognizes the header pattern and knows how many bits or bytes follow before the frame ends. The top layer is field extraction: pulling out the payload, any CRC or checksum, and the trailing bits.

The key discipline is to validate the decoder against a known-good capture before trusting it on a failing one. If I can get the device to produce a frame whose contents I already know — a fixed test pattern, or a response to a command I control — I can confirm the decoder extracts it correctly. If the decoder produces garbage on a known-good frame, the problem is the decoder, not the device. Only once the decoder is validated do I use it to debug the actual issue.

I'd also keep the raw waveform visible alongside the decoded output, because a decoder can hide timing problems. If the decoder says "valid frame" but the waveform shows the clock stretching or the data line glitching, the decoder is lying to me, and I need to see that.

**Possible follow-ups:**
- How would you handle a protocol where the frame length is variable and encoded in the header itself?
- What would you do if the decoder worked on one capture but failed on another with the same nominal protocol?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the lab's spectrum analyzer and near-field probe for an EMI pre-compliance scan, and you discover the resolution bandwidth and detector mode are set for a quick "get a feel for it" scan rather than the settings the test standard requires. The engineer is confident the settings are fine because "the peaks show up either way." The formal scan is scheduled for tomorrow, and the lab time is booked. How would you handle this situation?

**Answer:** The first thing I'd do is separate the technical issue from the interpersonal one. Technically, the engineer isn't wrong that the peaks show up either way — a wide RBW with a peak detector will reveal where the emissions are. What it won't do is tell us whether the device passes the limit, because the limit is defined at a specific RBW and detector mode, and the measured amplitude depends on both. So the scan as configured is useful for locating problems but not for making a pass/fail call, and that distinction is what I need to communicate.

I'd sit down with the engineer and walk through why the settings matter, using the standard as the reference rather than my own authority. If the standard specifies a particular RBW and quasi-peak detector, I'd show them the clause and explain that a peak-detector scan at a different RBW can over- or under-estimate the quasi-peak level by several dB — enough to turn a pass into a fail or vice versa. The goal isn't to make them feel wrong; it's to make sure we both understand what the measurement is actually telling us.

Then I'd deal with the schedule. The lab time is booked, so the practical question is whether we can reconfigure and re-run in the time available. If the scan is automated, changing the RBW and detector mode is usually a matter of a few settings and a re-sweep, which may fit in the booked window. If it doesn't, I'd rather reschedule or extend the session than submit a scan that doesn't meet the standard — a non-compliant scan is worse than no scan, because it creates a false record. I'd also use the situation as a coaching moment: the engineer now knows to check the standard's measurement requirements before setting up, and I'd ask them to write up the correct settings as a reference for the next scan.

**Possible follow-ups:**
- How would you handle it if the engineer pushed back and argued that the standard's settings were overly conservative?
- What would you put in place so that the next pre-compliance scan doesn't have the same problem?