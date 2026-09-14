# tools — Day 55

## Q1: How would you approach setting up a power integrity (PI) simulation workflow for a mixed-signal PCB that has a high-current switching regulator and a precision analog front-end sharing the same power distribution network, and how would you decide which results are trustworthy enough to act on?

**Answer:** I'd start by defining what question the simulation actually needs to answer — usually it's "does the impedance of the power distribution network stay below a target across the frequency band where the analog front-end is sensitive, and where do the switching harmonics land relative to that band?" That framing keeps the model scoped to the PDN rather than trying to simulate the whole board.

Practically, the workflow is: extract the PDN geometry (planes, traces, via arrays, decoupling placement) into a PI tool such as SIwave or HyperLynx PI, assign realistic component models — not ideal capacitors, but vendor S-parameter or ESR/ESL models — and drive it with a current profile representative of the switching regulator's actual load steps. The output I care about most is the impedance-versus-frequency curve at the analog supply pins, plus the resonant peaks that come from the interaction between bulk and local decoupling.

Deciding what to trust comes down to a few checks. First, mesh and frequency range: if the solve isn't converged or the band doesn't cover the switching fundamental and its first several harmonics, the result is decorative. Second, model fidelity: if I used ideal caps, I only trust the low-frequency trend, not the high-frequency peaks. Third, correlation: I'd validate against a real measurement — a VNA-based PDN impedance measurement or a scope capture of ripple at the analog rail under load — before committing to a layout change. If simulation and measurement disagree, the measurement wins and the model gets corrected.

The actionable output is usually placement and value changes: moving a decoupling cap closer to the pin, adding a ferrite or pi filter to isolate the analog rail, or splitting the plane. I'd treat any single simulation run as a hypothesis, not a verdict.

**Possible follow-ups:**
- How would you decide between adding more decoupling capacitance versus adding series impedance to isolate the analog rail?
- If your PDN impedance measurement and your simulation disagree at a specific frequency, how would you go about finding which one is wrong?

## Q2: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where the test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** The goal is a fully scriptable, headless flow, so I'd build it around J-Link Commander scripts or the J-Link SDK rather than the GUI. The sequence is: connect and reset the target, flash the built image (or use the Zephyr `west flash` runner which can invoke J-Link under the hood), reset and run, then let the test harness drive the device over its normal interface while the debugger stays attached for crash capture.

For crash capture without modifying firmware, I'd rely on the fact that a hard fault on Cortex-M leaves the fault status registers and stacked context in known locations. The harness can poll for a halt or a breakpoint on the fault handler, then read the relevant registers and memory regions and dump them to a file. If the target supports it, RTT (Real-Time Transfer) gives a low-overhead channel for logging without halting the CPU, which is often cleaner than polling.

The failure modes I'd design around: the debugger failing to connect because the target is in a low-power state or the SWD pins are repurposed — so the harness needs a recovery path, like a connect-under-reset sequence. Flash programming failing partway and leaving a half-written image — so verify after program and retry. The target hanging in a way that never triggers a fault handler — so a watchdog or timeout in the harness that forces a halt and dumps state. And resource contention if multiple test jobs share one debug probe — so serialize access or use one probe per device under test.

I'd also make the whole thing idempotent and log every step, because when a test fails at 2 a.m. in CI, the log is the only witness.

**Possible follow-ups:**
- How would you handle a target that occasionally fails to halt on a breakpoint because it's stuck in a tight loop with interrupts disabled?
- What would you change in this setup if the same harness needed to run against several hardware revisions with different memory maps?

## Q3: How would you approach setting up a cross-probe workflow between OrCAD Capture and Cadence Allegro so that a layout review can move efficiently between schematic and PCB, and what would you check to confirm the link is actually working before relying on it in a review?

**Answer:** Cross-probing depends on the two tools sharing a consistent design database, so the first thing I'd verify is that the netlist and the reference designators actually match between Capture and Allegro. If the schematic was edited after the last netlist export, cross-probing will either fail or point at the wrong part, which is worse than not having it.

Setup-wise, I'd confirm the Allegro design is opened from the same project directory that Capture expects, that the cross-probe option is enabled in both tools' preferences, and that the two are pointed at the same design. In practice this means launching Allegro from within Capture or ensuring the `.brd` and `.dsn` are linked through the project. I'd also check that the cross-probe selection mode is set the way the review needs — selecting a component in the schematic should highlight the part and its connected nets in the layout, and vice versa.

Before relying on it in a live review, I'd do a quick sanity test: pick a known component in the schematic, cross-probe to the layout, and confirm the correct footprint is highlighted. Then pick a net and confirm the ratsnest and connected pins highlight correctly. If either direction is wrong, I'd stop and fix the link rather than push through — a review where the tools disagree erodes everyone's trust in the process.

I'd also make sure the review has a fallback: a printed or PDF schematic with reference designators, so if the link drops mid-review the session can continue.

**Possible follow-ups:**
- What would you do if cross-probing works for components but not for nets?
- How would you structure a layout review so that cross-probing is used to answer specific questions rather than as a general navigation aid?

## Q4: How would you approach organizing a KiCad project for a medical device so that the schematic, PCB, footprints, and 3D models stay consistent across revisions, and how would you catch footprint-to-schematic mismatches before they reach fabrication?

**Answer:** KiCad's file-based nature means consistency has to be enforced by discipline and tooling rather than a central database. I'd start with a clear project structure: the `.kicad_pro` project file at the root, schematic and PCB files alongside it, and a project-local library directory for symbols, footprints, and 3D models that are specific to this design. Anything reused across projects goes into a shared library with its own version control.

The key discipline is that every symbol in the schematic points to a footprint in a library that's under version control, and that the footprint's pad numbering and geometry match what the symbol expects. KiCad's "Update PCB from Schematic" and the footprint assignment tools help, but they don't catch everything — a symbol can reference a footprint that exists but has the wrong pin count or a different pad naming convention.

To catch mismatches before fabrication, I'd run a layered check. First, the ERC in the schematic to catch unconnected pins and conflicting drivers. Then, in the PCB editor, the DRC plus a footprint-to-schematic comparison — KiCad has a "Update PCB from Schematic" dialog that shows differences, and I'd treat any unexpected difference as a red flag. I'd also do a visual check of the 3D view against the mechanical envelope, because a footprint can be electrically correct but physically wrong.

For a medical device, I'd add a documented review step: a checklist that includes verifying that every footprint in the BOM has a corresponding 3D model, that the 3D models are the correct variants, and that the assembly drawing matches the current revision. The goal is that no footprint reaches the fab house without a human having confirmed it against the datasheet.

**Possible follow-ups:**
- How would you handle a situation where a footprint was correct in an earlier revision but was changed in a library update, silently affecting the current design?
- What's your approach to managing 3D models for connectors where the vendor provides a model but it's not dimensionally accurate?

## Q5: (Behavioral) Imagine you are leading a project where a junior engineer has been tasked with setting up the automated firmware test environment for a medical device. On the day before a critical regression test run, you discover that the engineer has configured the test script to skip the safety-critical test cases because they were failing intermittently, and the engineer is confident this is acceptable because "the failures are just timing issues in the test harness, not real bugs." The test results will be used for a regulatory submission milestone. How would you handle this situation?

**Answer:** The immediate priority is that the test run cannot proceed with safety-critical cases silently skipped. Whatever the cause of the intermittent failures, a test environment that omits them produces a result that misrepresents the state of the device, and for a regulatory submission that's not a defensible position. So the first action is to stop the run and make the omission visible — not to punish anyone, but because the result would be invalid.

Then I'd separate the two questions the engineer has conflated: are the failures real bugs, or are they test harness timing issues? That's an empirical question, and it needs evidence, not confidence. I'd sit down with the engineer and look at the actual failure logs — what's the failure mode, is it reproducible, does it correlate with system load or specific timing, does it disappear when the test is run in isolation? If it's genuinely a harness issue, the fix is to make the harness robust — add proper synchronization, wait for events rather than fixed delays, retry with backoff where appropriate — and then re-enable the tests. If it's a real bug, it needs to be triaged and fixed or explicitly documented as a known issue with a risk assessment, not hidden.

I'd also address the process gap: the decision to skip tests should never be a unilateral one, especially for safety-critical cases. I'd make sure the team understands that disabling a test is a change to the test plan that requires review, and that the default is to investigate rather than exclude.

Finally, I'd communicate upward honestly. The milestone may slip, and that's a conversation to have with management early rather than paper over. A delayed submission with a defensible test result is far better than a submission built on a test run that quietly omitted the cases that matter most.

**Possible follow-ups:**
- How would you handle it if the engineer's assessment turned out to be correct — the failures really were harness timing issues — but the tests had already been skipped for several runs?
- What would you put in place to prevent a similar situation on the next project, without adding so much process that the team routes around it?