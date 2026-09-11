# tools — Day 52

## Q1: How would you approach setting up a design rule check (DRC) and electrical rule check (ERC) strategy in KiCad for a medical device PCB, so that the checks catch real issues without drowning the team in false positives?

**Answer:** I'd treat ERC and DRC as two layers of a defense-in-depth strategy, and tune each one deliberately rather than accepting the defaults.

For ERC, the goal is catching connectivity and intent errors before layout even starts: unconnected pins, conflicting output drivers, missing power flags, and pins that are driven but never used. The default KiCad rules are a reasonable starting point, but they're generic — on a medical design I'd go through the pin-type assignments in the symbol library and make sure they reflect reality. A lot of false ERC noise comes from symbols where every pin is typed as "passive" or "unspecified," so the checker can't reason about them. Fixing the library is the real work; the rule configuration is downstream of that.

For DRC, I'd build up from the fab house's capability sheet: minimum trace width, minimum clearance, minimum annular ring, minimum drill, and via-to-copper spacing. Those become the baseline. Then I'd add project-specific rules — for example, a larger clearance class for the isolated patient-connection side of the board, or a wider trace class for the power distribution net. KiCad's net class system lets you assign rules per class rather than globally, which is how you avoid a single clearance number that's either too loose for the analog section or too tight for the digital section.

The false-positive problem is real and worth managing actively. If a check fires on something that's genuinely fine, I'd rather fix the rule or add a documented exclusion than train the team to click through warnings. The moment people start ignoring DRC output, the whole system is worthless. So I'd keep a short list of intentional exclusions, each with a comment explaining why, and review that list at each design review.

Finally, I'd make the checks part of the workflow, not a one-time event: run ERC after every schematic change, run DRC before every layout commit, and treat a clean run as a gate before generating fabrication outputs. For a regulated device, the DRC/ERC report is also part of the design history file, so having it clean and reproducible matters beyond just catching bugs.

**Possible follow-ups:**
- How would you decide whether a DRC violation is a real problem or an acceptable exception, and how would you document that decision for a regulatory audit?
- What's the difference between a rule you'd set globally and one you'd set per net class, and how do you keep the two from conflicting?

## Q2: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where the test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** The core idea is to drive the J-Link from a script or a host-side tool rather than the IDE GUI, so the whole sequence is reproducible and can run unattended in CI.

On the flashing side, I'd use the J-Link command-line tools (or the Zephyr `west flash` integration, which wraps them) to program the target from a build artifact. The key configuration points are the target device selection, the interface (SWD vs JTAG), and the reset behavior — whether the debugger resets the target after flashing or leaves it running. For a test harness, I'd want a deterministic reset-and-run so every test starts from a known state.

For running the test sequence, the harness typically needs two channels: one to control the target (flash, reset, halt, resume) and one to observe it (serial console, RTT, or a test-result output). Segger's RTT is useful here because it gives you a fast bidirectional channel without consuming a UART, and it works while the CPU is running. The harness can wait for a specific string or a structured test-result line, then move on.

For crash dumps, the important thing is that the debugger can attach and read memory after a fault without needing the firmware to have printed anything. If the target has faulted and halted, the J-Link can read the fault status registers, the stacked PC/LR, and the relevant RAM regions. If the target is in a reset loop, you need the debugger to halt on reset — that's a configuration choice, and it's the difference between catching the fault and missing it.

The failure modes I'd design around: the target not responding to the debugger (bad wiring, wrong interface, or the debug pins repurposed in firmware); the flash operation succeeding but the target not actually running the new image (stale reset configuration); the test harness hanging because it's waiting for output that never comes (needs a timeout on every wait); and the debug connection dropping mid-test (needs a retry and a clean re-attach). I'd also make sure the harness captures the debugger's own log, because when something goes wrong at 2 a.m. in CI, that log is often the only evidence of what happened.

**Possible follow-ups:**
- How would you distinguish between a target that's stuck in a hard fault and one that's simply not being clocked, using only the debugger?
- What would you change in the harness if the same test needed to run on a board where the debug pins are shared with another function?

## Q3: How would you approach setting up a via structure strategy in Cadence Allegro for a mixed-signal PCB that carries both high-speed digital signals and sensitive analog traces, and how would you verify that the vias don't compromise signal integrity or manufacturability?

**Answer:** I'd start by defining via types deliberately rather than letting the router pick defaults. On a mixed-signal board you typically want at least three classes: small microvias or laser-drilled vias for dense high-speed escape routing, standard through-vias for general signal and power, and larger thermal or power vias for high-current or heat-dissipating nets. Each class gets its own pad size, drill size, and annular ring, driven by the fab house's capability and by the impedance target for the nets that use it.

For high-speed signals, the via is a discontinuity — it adds inductance and capacitance, and on a return-path-sensitive net it can also create a stub. The two things I'd control are the via's impedance relative to the trace (by adjusting pad and antipad dimensions) and the return path. For a signal that changes reference planes, I'd place a stitching via or a decoupling capacitor near the signal via so the return current has a low-inductance path. For a via that doesn't need to go all the way through, a blind or buried via removes the stub, which matters more as edge rates get faster.

For analog traces, the concern is different: I'd keep them away from via fields where possible, because a cluster of vias is a cluster of discontinuities and a potential coupling path. Where an analog trace must change layers, I'd use a via with a clean return path and keep the via count low. I'd also avoid routing analog signals through via antipads that sit over a plane split, since that's a classic way to inject noise.

Verification is two-sided. On the signal integrity side, I'd run the layout through an SI tool — HyperLynx or Allegro's own SI analysis — to check via impedance, crosstalk, and return-path continuity on the critical nets. On the manufacturability side, I'd run the DFM rule deck against the fab house's capability: minimum annular ring, minimum drill-to-copper, via-in-pad fill requirements if I'm using them, and aspect ratio limits. The two checks catch different problems, and a via that passes SI can still fail DFM.

**Possible follow-ups:**
- How would you decide when a via stub is short enough to ignore versus when it needs a blind or buried via?
- What's the trade-off between using via-in-pad for a fine-pitch BGA and the extra fab steps it requires?

## Q4: How would you approach using a spectrum analyzer with a near-field probe to locate the source of a radiated emissions failure at a specific frequency during pre-compliance testing, and how would you confirm which component is responsible?

**Answer:** The near-field probe is a localization tool, not a compliance measurement — it tells you where the field is strong, not whether the product passes. So I'd use it to narrow down the source, then confirm with a proper far-field or chamber measurement.

The first step is to characterize the failure: what's the exact frequency, and is it narrowband or broadband? A narrowband peak at a single frequency usually points to a clock harmonic or a switching regulator's fundamental or harmonic. A broadband hump suggests something else — a data bus, a switching edge, or a resonance. Knowing the frequency lets me list candidate sources: any clock whose fundamental or harmonic lands on that frequency, and any switching regulator whose switching frequency or its harmonics land there.

Then I'd probe systematically. With the board powered and running in the failing mode, I'd move the probe slowly across the board, watching the amplitude at the target frequency on the analyzer. The probe's orientation matters — a magnetic loop probe is directional, so I'd rotate it to find the maximum. The area where the amplitude peaks is the suspect region. I'd then narrow down: probe individual components, individual traces, and individual pins in that region, and compare amplitudes. A clock trace radiating at its harmonic will show a strong field along the trace; a switching regulator will show it at the switch node and the inductor.

Confirmation is where I'd be careful. A near-field peak near a component doesn't prove that component is the source — it could be a victim or a coupling path. So I'd confirm by intervention: temporarily disabling or slowing the suspected clock, or changing the switching frequency if the regulator allows it, and seeing whether the peak moves or disappears. If it does, the source is confirmed. If it doesn't, I'd keep looking. I'd also check whether the peak is common-mode or differential-mode by comparing probe orientations and positions, since that changes the mitigation strategy.

**Possible follow-ups:**
- How would you tell the difference between a harmonic of a clock and a harmonic of a switching regulator when both land on the same frequency?
- What would you do if the near-field probe shows a strong field everywhere, with no clear peak?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** The immediate priority is the release — the board house deadline is real, and shipping incomplete or inconsistent outputs would be worse than a short delay. So I'd separate the technical fix from the conversation about how it happened.

Technically, I'd verify the outputs myself rather than take the engineer's word for it. I'd open the output job, check each output against the release checklist: Gerbers, drill files with the drill table, assembly drawings, BOM, and pick-and-place. I'd confirm the assembly drawings reference the current schematic revision, not a stale one. If the fix is quick — regenerating the outputs with the correct configuration — I'd do it, or walk the engineer through doing it, and re-verify before sending. If the fix isn't quick, I'd communicate the delay to the board house early rather than send something wrong.

On the conversation: the engineer's confidence is the real issue, not the missing drill table. "The Gerbers look fine" is a reasonable-sounding statement that misses the point — Gerbers can look fine and still be an incomplete release package. I'd want to understand whether they were never taught what a complete release package contains, or whether they were rushed and skipped the checklist. Those need different responses. If it's a knowledge gap, the fix is a documented release checklist and a walkthrough, not blame. If it's a process gap — no checklist existed, or the deadline pressure pushed them to skip it — the fix is making the checklist part of the workflow so it's not optional under time pressure.

I'd also use this as a signal about the release process itself. If a junior engineer can produce a release package that's missing critical outputs and not catch it, the process is relying too much on individual diligence. A release checklist that's actually enforced, plus a second pair of eyes on any release package before it goes out, would catch this class of error regardless of who's doing the work. That's a process improvement, not a criticism of the engineer.

**Possible follow-ups:**
- How would you structure the release checklist so it's genuinely useful and not just a box-ticking exercise?
- If the same engineer made a similar mistake again, how would your approach change?