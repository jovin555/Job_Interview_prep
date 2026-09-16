# tools — Day 57

## Q1: How would you approach setting up a schematic symbol and footprint library in KiCad for a medical device project where the same component appears in multiple variants (e.g., different package sizes or tolerance grades), so that the library stays maintainable and traceable across revisions?

**Answer:** The core problem is that a single physical part number can map to several schematic-visible variants, and if you clone a symbol for each one you end up with a library that drifts and becomes impossible to audit. I'd separate the concerns: one symbol per functional device, and let the variant be expressed through the footprint field and the BOM metadata rather than through duplicated symbols.

Concretely, I'd define a symbol for the device function (say, a precision resistor or an op-amp) with generic pin definitions, then attach the specific footprint and a set of custom fields — manufacturer part number, tolerance, package, temperature grade, and a lifecycle status field. In KiCad these live as symbol properties, and the variant selection happens at the schematic instance level, so the same symbol can be placed with different footprint/MPN assignments. That keeps the symbol count low and the schematic readable.

For traceability, the important discipline is that the library is version-controlled alongside the project, and every symbol and footprint carries a revision or a checksum that ties back to a released library state. I'd avoid "library on a shared drive that anyone edits" — that's where medical traceability breaks down. Instead, treat the library as a reviewed artifact: changes go through the same review and tagging process as the schematic. I'd also keep a naming convention that encodes the variant unambiguously (package and tolerance in the name or in a dedicated field), so that when a BOM is generated there's no ambiguity about which physical part was intended.

The trade-off is that instance-level variant assignment is more error-prone than a hard-coded symbol per variant — someone can forget to set the footprint. So I'd pair it with an ERC/DRC-style check or a BOM review step that flags any symbol instance missing a footprint or MPN before release.

**Possible follow-ups:**
- How would you catch a case where someone placed the right symbol but the wrong footprint variant, before it reaches fabrication?
- If two variants of the same part have different pinouts, does your single-symbol approach still hold, or would you split them?

## Q2: How would you approach setting up a cross-probe workflow between OrCAD Capture and Cadence Allegro so that a layout review can move efficiently between schematic and PCB, and what would you check to confirm the link is actually working before relying on it in a review?

**Answer:** Cross-probing is one of those features that either saves you an enormous amount of time in a review or wastes it entirely if the link is silently broken, so I'd treat "confirm the link works" as a mandatory pre-review step rather than an assumption.

The setup itself is about making sure both tools are pointed at the same design database and that the cross-probe mechanism is enabled on both sides. In the OrCAD/Allegro flow this generally means the schematic and the board share a common design reference — the netlist and reference designators must be in sync — and the cross-probe option is turned on in both applications. If the schematic has been re-annotated or the board has been back-annotated without re-syncing, cross-probing can appear to work but point at the wrong reference designator, which is worse than not working at all.

Before the review, I'd verify the link with a deliberate test: pick a specific component in the schematic, cross-probe to the board, and confirm the correct part is highlighted — not just *a* part. Then do the reverse: select a net or component in the board and confirm it highlights the right thing in the schematic. I'd also test a net-level probe, since component-level and net-level cross-probing can behave differently. If any of those three tests fail or point somewhere unexpected, I'd stop and fix the sync before the review starts, because a review where people are looking at the wrong component is actively harmful.

The reason I insist on this is that a design review is a high-cost, multi-person event. Discovering halfway through that cross-probing is misaligned means either the review is compromised or it has to be rescheduled.

**Possible follow-ups:**
- What would cause cross-probing to point at the wrong reference designator even though both tools report the design as in sync?
- How would you run a review if cross-probing simply couldn't be made to work that day?

## Q3: How would you approach using a spectrum analyzer with a near-field probe to locate the source of a radiated emissions failure at a specific frequency during pre-compliance testing, and how would you confirm which component is responsible?

**Answer:** The near-field probe is a localization tool, not a compliance measurement — it tells you *where* energy is concentrated, not whether you'll pass or fail in a real chamber. So I use it to narrow the search, then confirm with a more controlled measurement.

The first step is to characterize the failing frequency itself. I'd note the exact frequency and ask what on the board could produce it: a switching regulator's fundamental or a harmonic of it, a clock fundamental or harmonic, or a resonance. That arithmetic alone often narrows the candidate list before I even pick up the probe. For example, if the failure is at a frequency that divides evenly by a known clock, that clock is a prime suspect; if it matches a switching regulator's switching frequency or a low-order harmonic, that's the other prime suspect.

Then I'd scan the board with the near-field probe, moving slowly and keeping the probe orientation consistent, and map where the field is strongest at that frequency. The key discipline is to change one thing at a time to confirm causation: if I suspect a particular regulator, I can change its switching frequency (if the part allows it) and see whether the emission moves with it. If I suspect a clock, I can disable or spread that clock and see whether the emission drops. A source that moves when you change its frequency, or disappears when you disable it, is confirmed; a source that just happens to be near the hot spot is not.

I'd also use both H-field and E-field probes, because they respond differently — a strong H-field near a switching loop points at a current loop, while a strong E-field might point at a radiating trace or cable. And I'd be careful about the probe's own loading effects and about measuring in a way that's repeatable, since near-field readings are very position-sensitive.

**Possible follow-ups:**
- How would you distinguish a near-field hot spot caused by the actual radiator from one caused by a cable or connector acting as an antenna?
- Once you've localized the source, what are the first mitigation options you'd consider?

## Q4: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where the test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** The goal is a fully scripted, repeatable flow: flash, run, detect pass/fail or crash, and capture state — with no human in the loop. I'd build it around the J-Link command-line tools and scripting interface, driven by the test harness, rather than relying on an IDE.

The flow I'd design is roughly: reset and halt the target, flash the image, verify the flash, reset and run, then either let the test complete and read a result or wait for a crash condition. For crash capture, the important capability is being able to halt on a fault and read out the relevant memory — the fault status registers, the stacked context, and whatever RAM region holds the crash record — and dump that to a file the harness can archive. Zephyr's fault handling and any crash-logging mechanism in RAM are what make this possible without adding print statements; the debugger reads the memory directly.

The failure modes I'd design around are the ones that make automated flows unreliable. First, connection failures: the target may not be powered, may be held in reset, or the debug interface may be locked — the script needs to detect "couldn't connect" and report it distinctly from "test failed," otherwise you get false failures. Second, flash verification: always verify after programming, because a partially flashed image produces confusing downstream behavior. Third, the "target never reaches the expected state" case — the script needs a timeout, and on timeout it should capture whatever state it can rather than hanging forever. Fourth, distinguishing a genuine crash from a test that simply failed an assertion; those need different handling and different artifacts. Fifth, resource contention: if multiple test stations share debuggers or the same target, you need locking so two runs don't collide.

I'd also make the whole thing idempotent and log everything — the debugger output, the flash log, the crash dump — so that when something goes wrong at 2 a.m. in an automated run, there's enough evidence to diagnose it without re-running.

**Possible follow-ups:**
- How would you capture the last few seconds of system state before a crash without halting the CPU during normal operation?
- What would you do if the debug interface itself becomes unavailable after the crash, so you can't read out the fault registers?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** The immediate priority is to not let incomplete outputs go out, and the second priority is to handle the conversation so the engineer learns rather than shuts down. Those two things aren't in conflict if I sequence them correctly.

First, I'd stop the release. "The Gerbers look fine" is exactly the trap here — Gerbers can look visually correct while the drill table is missing and the assembly drawings are stale, and those are the kinds of omissions that cause real problems downstream: the board house can't fabricate without drill data, and assembly documentation that references the wrong schematic revision is a traceability problem, which in a medical context is serious. So the release is blocked until the outputs are complete and correct, regardless of the deadline pressure. I'd communicate that clearly and early so nobody is surprised.

Then I'd sit down with the engineer and walk through the output job together, not as a correction but as a review. I'd ask them to show me how they verified the outputs were complete — what their checklist was. Very often the gap isn't carelessness, it's that there was no checklist, or the checklist didn't include the drill table and the assembly drawing revision. That reframes it from "you made a mistake" to "the process let this through," which is both more accurate and more useful. I'd then work with them to build a release checklist that covers the full output set — fabrication data including drill, assembly drawings tied to the correct schematic revision, BOM, and a final visual sanity check — and make that checklist part of the release process going forward.

On the deadline: I'd be honest with the board house and with management about the slip rather than sending incomplete files and hoping. A one-day slip to send correct files is almost always cheaper than a respin or a documentation nonconformance. If there's genuine schedule pressure, I'd ask what specifically is driving it and whether a partial release (say, fabrication data now, assembly documentation to follow) is acceptable — but I wouldn't send fabrication data that's missing the drill table.

The tone throughout matters. The engineer is confident, which means they believe they did the work correctly. My job is to show them, concretely, what's missing and why it matters, and to fix the process so it doesn't recur — not to make them feel stupid. A junior engineer who's afraid to flag uncertainty is a much bigger long-term risk than one who missed a checklist item once.

**Possible follow-ups:**
- How would you decide whether to escalate this to management, and what would you say?
- What would you change in the release process so that a missing drill table can't reach the board house again?