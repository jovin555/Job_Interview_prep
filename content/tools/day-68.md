# tools — Day 68

## Q1: How would you approach setting up a symbol and footprint library in KiCad for a medical device project where the same component appears in multiple variants — different package sizes, tolerance grades, or temperature ratings — so the library stays maintainable and traceable across revisions?

**Answer:** The core problem is that KiCad's symbol and footprint libraries are file-based, so "the same part in several variants" can quickly turn into copy-paste sprawl where a fix to one variant never reaches the others. I'd structure it so that the *identity* of the part and the *variant* of the part are separate concerns.

Concretely, I'd keep one symbol per functional part (e.g., a generic precision op-amp symbol with the correct pin functions), and let the variant be expressed through the footprint assignment and the BOM fields rather than through duplicated symbols. If the pinout genuinely differs between packages, that's a real reason for separate symbols — but a tolerance or temperature grade change almost never changes the symbol, only the orderable part number and the footprint. So the variant lives in the footprint field plus custom fields like `MPN`, `Tolerance`, `TempGrade`, and `ApprovedVendor`, not in a forked symbol.

For footprints, I'd keep a project-local library under version control rather than relying on the global KiCad libraries, because regulatory traceability means I need to know exactly which footprint revision was used in a released design. Each footprint gets a name that encodes the package and any critical mechanical attribute, and I'd avoid "generic" footprints that silently get reused for parts with different land patterns.

The traceability piece is the part people underestimate. I'd add a custom field on every symbol that ties it to a controlled part number, and I'd make the BOM export pull those fields so that the released BOM is reproducible from the schematic alone. I'd also document the library revision in the design's release notes, so that if a footprint is later found to be wrong, I can trace which products used it.

**Possible follow-ups:**
- How would you handle a situation where a footprint needs to change after a design has already been released — do you edit in place or create a new revision, and why?
- How would you catch a mismatch between a symbol's pin count and its assigned footprint before it reaches fabrication?

## Q2: How would you approach setting up a power integrity (PI) simulation workflow for a mixed-signal PCB where a high-current switching regulator and a precision analog front-end share the same power distribution network, and how would you decide which results are trustworthy enough to act on?

**Answer:** The goal of PI simulation here is to answer two questions: how much ripple and noise actually reaches the analog front-end, and whether the PDN impedance is low enough across the frequencies that matter. Those are related but not identical, and I'd set up the workflow to address both.

First I'd define the frequency range of interest. A switching regulator's fundamental and its harmonics set the low end, and the digital switching edges of the analog front-end's own ADC or any nearby digital set the high end. I'd build the PDN model with the regulator's output impedance, the bulk and decoupling capacitors with their ESR and ESL, the plane geometry, and the load current profiles. The critical realism step is that capacitor models must include parasitics — an ideal 100 nF cap in simulation will lie to you about where the impedance actually bottoms out.

For the analog side, I'd run the simulation to look at the noise voltage at the analog supply pins, not just at the regulator output, because the plane and via inductance between them is often where the problem hides. I'd compare that against the analog front-end's supply rejection and its noise budget to decide whether the result is acceptable.

The trustworthiness question is the important one. I'd treat a PI simulation as a *relative* tool first: it's good at telling me whether adding a capacitor here or moving a plane there helps or hurts, and it's good at showing resonance peaks. It's much weaker at predicting absolute microvolt-level noise, because the model won't capture every parasitic, every load transient, and every coupling path. So I'd use it to rank design choices and to flag resonances, then validate the final design with a real measurement — a scope with a proper ground-spring probe on the analog supply, and a spectrum analyzer to see the switching harmonics. If the simulation and measurement disagree, the measurement wins, and the disagreement tells me what my model was missing.

**Possible follow-ups:**
- What would you do if the simulation showed a PDN resonance right at a frequency where the analog front-end is sensitive?
- How would you decide between adding bulk capacitance, adding a ferrite bead, or splitting the plane — and what are the trade-offs of each?

## Q3: How would you approach using a spectrum analyzer with a near-field probe to locate the source of a radiated emissions failure at a specific frequency during pre-compliance testing, and how would you confirm which component is responsible?

**Answer:** The near-field probe is a localization tool, not a compliance measurement — it tells you *where* energy is coming from, not whether the product passes. I'd use it that way and be explicit about that distinction.

I'd start by setting the analyzer to the failing frequency with a narrow span and a resolution bandwidth appropriate for a stable reading, then move the probe systematically across the board. The key technique is to keep the probe orientation consistent and to work at a fixed height, because near-field coupling is extremely sensitive to both. I'd map the board in a grid and note where the amplitude peaks.

Once I have a candidate location, the confirmation step is what separates a guess from a diagnosis. I'd use a combination of approaches: temporarily disabling or gating the suspected source (if firmware allows), changing its operating frequency or load, and observing whether the emission at that exact frequency moves or disappears. If it's a switching regulator, changing the switching frequency should shift the fundamental and its harmonics; if it's a digital clock, changing the clock rate should shift the harmonic. That frequency-tracking behavior is strong evidence of the source.

I'd also check whether the frequency is a harmonic of a known clock or a multiple of the switching frequency — that arithmetic alone often narrows it to one or two candidates. And I'd look at the probe's response: a switching node usually shows a broad, rich harmonic spectrum, while a clock harmonic tends to be a sharper, more isolated peak.

The final confirmation is to make a targeted change — add a snubber, slow an edge, add a ferrite, improve a return path — and verify the specific frequency drops. If it does, the diagnosis holds. If it doesn't, I was wrong and I go back to the map.

**Possible follow-ups:**
- How would you distinguish a near-field probe reading caused by the trace carrying the signal versus the component generating it?
- What are the limitations of near-field probing that would make you want a far-field or anechoic measurement to confirm?

## Q4: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where an automated test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** The goal is a fully headless, repeatable flow, so I'd build it around J-Link's command-line and scripting interfaces rather than the GUI, and I'd drive it from the same CI or test harness that runs the rest of the suite.

The flow has three stages. First, flashing: I'd use the J-Link Commander or the `JLinkExe`/`JLink` scripting interface with a script that connects, erases, programs, verifies, and resets. For Zephyr specifically, I'd make sure the flash loader and the target device string match the actual SoC, because a wrong device selection is a common silent failure. Second, running the test: the harness resets the target, lets it boot, and either waits for a known output on a UART/semihosting channel or polls a status register. Third, crash capture: if the target faults, I want the crash dump pulled automatically. Zephyr's fatal error handler can be configured to halt, and the J-Link can then read out the register state and memory. I'd script that readout so the harness captures it as an artifact.

The failure modes I'd design around are the ones that make automated debug flaky. Connection loss mid-test is the big one — I'd add retries and a hard timeout so a hung target doesn't stall the whole run. Target-not-halted is another: if the CPU is running when I try to read memory, I get garbage, so I'd ensure the script halts before reading. Flash-already-programmed or protected sectors can cause a program step to fail silently, so I'd verify after programming. And I'd make sure the J-Link's own state is reset between runs, because a leftover breakpoint or a stale session can corrupt the next test.

Finally, I'd log everything — the J-Link output, the target's serial output, and the crash dump — with timestamps, so that when a test fails intermittently I have the evidence to debug the test itself, not just the firmware.

**Possible follow-ups:**
- How would you capture the last several seconds of system state before a crash without halting the CPU during normal operation?
- What would you do if the J-Link connection itself is unreliable on a particular board — how would you isolate whether it's the debugger, the target, or the layout?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** The first thing I'd do is separate the immediate problem from the coaching problem, because they need different responses and the deadline makes the order matter.

Immediately, I'd verify the scope of what's actually wrong before reacting. "The Gerbers look fine" is true as far as it goes — the copper layers may be correct — but a missing drill table and stale assembly drawings are exactly the kind of gap that a board house can work around for fabrication but that will cause real problems downstream for assembly and for the device history file. So I'd check the output job against the release checklist: which outputs are present, which are missing, and which reference the wrong revision. That tells me whether this is a five-minute fix or a rebuild of the output job.

If it's fixable tonight, I'd fix it tonight — regenerate the drill files and re-point the assembly drawings at the correct schematic revision, then re-run the output job and verify against the checklist. The deadline is real, and the right call is to make the release correct rather than to make a point about process. I'd be transparent with the board house if anything slips.

The coaching part comes after the release is safe, and I'd handle it privately and specifically. The engineer's confidence wasn't arrogance — it was a reasonable conclusion from an incomplete checklist. So the fix isn't "be more careful"; it's giving them a concrete release checklist that defines what "complete" means, and walking through why the drill table and assembly revision matter for a medical device specifically. I'd frame it as: the Gerbers being fine is necessary but not sufficient, and here's the standard we hold releases to.

I'd also look at whether the process let this happen. If the output job configuration is a single point of failure with no review step, that's a process gap, not just an individual one. Adding a second pair of eyes on release outputs — even a quick checklist review — is cheap insurance for a regulated product.

**Possible follow-ups:**
- How would you structure a release checklist so that it catches this kind of gap without becoming a bureaucratic burden the team routes around?
- If the board house had already started fabrication with the incomplete outputs, how would your approach change?