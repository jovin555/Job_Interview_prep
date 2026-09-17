# tools — Day 58

## Q1: How would you approach setting up a symbol and footprint library in KiCad for a medical device project where the same component appears in multiple variants — different package sizes, tolerance grades, or temperature ratings — so the library stays maintainable and traceable across revisions?

**Answer:** The core problem is that a single "part" in the schematic sense can map to several orderable variants, and if you handle that by duplicating symbols you create a maintenance and traceability problem. I'd separate the concepts: one schematic symbol per electrical function, and separate footprint assignments driven by the variant. In KiCad terms, that means a symbol with a footprint field that is not hard-wired to a single footprint, plus a controlled set of footprints in the library, and a variant table (or a structured BOM field set) that maps the chosen variant to a specific manufacturer part number, package, and tolerance/temperature grade.

For traceability, every symbol and footprint gets a stable internal identifier that never changes even if the display name is edited, and the metadata that regulatory review cares about — manufacturer part number, description, datasheet revision, lifecycle status — lives in fields on the symbol rather than only in a spreadsheet. I'd keep the library in version control alongside the project, tag library revisions, and treat a library change as a reviewable event, because a silent footprint edit can invalidate a previously released design.

The practical discipline is: never edit a released symbol or footprint in place. If a pad geometry or pin assignment must change, create a new revision of that library item and update the design deliberately, so the schematic-to-PCB link stays honest and you can always reconstruct what a given board revision was built from. For a medical device this matters because the DHF has to show what was actually built, not what the library looks like today.

**Possible follow-ups:**
- How would you catch a footprint-to-schematic mismatch before it reaches fabrication, given that KiCad won't always flag a wrong-but-valid footprint?
- Where would you draw the line between what lives in the library versus what lives in the BOM?

## Q2: How would you approach setting up a cross-probe workflow between OrCAD Capture and Cadence Allegro so a layout review can move efficiently between schematic and PCB, and what would you check to confirm the link actually works before relying on it in a review?

**Answer:** Cross-probing depends on the two tools agreeing on the design's identity — the netlist and reference designators have to be in sync, and the cross-probe channel has to be enabled and pointed at the right session. So the setup is really two things: getting the netlist handoff clean, and verifying the live link.

On the netlist side, I'd make sure the schematic has been fully annotated, that there are no unresolved or duplicate reference designators, and that the PCB was imported from that exact netlist revision rather than an earlier one. A stale netlist is the most common reason cross-probe "works" but highlights the wrong thing or nothing at all. I'd also confirm the cross-probe preference is enabled in both tools and that they're communicating over the expected mechanism.

Before trusting it in a live review, I'd run a deliberate smoke test: pick a component in the schematic, cross-probe to the PCB, and confirm the correct part is selected and zoomed; then go the other direction from a PCB component back to the schematic. I'd do this for a couple of parts, including one that was recently added or renamed, because those are the ones most likely to expose a sync problem. I'd also verify that net-level cross-probing works, not just component-level, since a lot of review discussion is about a specific net.

The reason to test rather than assume is that a broken cross-probe in the middle of a review wastes everyone's time and undermines confidence in the tooling. If it's not working, it's usually faster to fix the netlist sync than to work around it manually.

**Possible follow-ups:**
- What would you do if cross-probe works for components but not for nets?
- How would you keep the schematic and PCB in sync if the layout engineer needs to make an ECO mid-review?

## Q3: How would you approach setting up a power integrity simulation workflow for a mixed-signal PCB where a high-current switching regulator and a precision analog front-end share the same power distribution network, and how would you decide which results are trustworthy enough to act on?

**Answer:** I'd start by being clear about what question the simulation is meant to answer, because PI simulation can produce a lot of impressive-looking output that doesn't map to a decision. The two questions that usually matter here are: does the PDN impedance stay below target across the frequency range the analog front-end cares about, and does the switching regulator's ripple and its harmonics couple into the analog supply in a way that degrades the sensor signal?

The workflow is: build an accurate stackup and copper model, assign realistic material properties, model the regulator's output impedance and the load's current profile, and place the decoupling network as it will actually be laid out — not an idealized version. Then run impedance sweeps and, if the tool supports it, a noise/ripple analysis with the switching excitation. The key discipline is that the model is only as good as its inputs: if the stackup, via model, or capacitor parasitics are wrong, the results are fiction.

Deciding what to trust comes down to correlation. I'd identify the results that are robust to reasonable input variation — for example, a resonance that appears across a range of assumed ESR values is probably real, whereas a sharp feature that moves with small parameter changes is likely a modeling artifact. I'd prioritize acting on the low-frequency PDN impedance and the placement of bulk versus high-frequency decoupling, because those are the levers I actually control and the effects are well understood. For anything marginal, I'd plan a measurement — a VNA-based PDN impedance measurement or a scope measurement of supply ripple at the analog load — to confirm before committing to a layout change. Simulation narrows the search; measurement decides.

**Possible follow-ups:**
- How would you model the switching regulator's output impedance if the vendor only provides a datasheet efficiency curve?
- At what point would you stop simulating and just build a test board to measure the PDN?

## Q4: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where the test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** The goal is a headless, repeatable sequence: connect, erase/program, reset, run, detect pass/fail, and on failure pull a crash dump — all scriptable and with a non-zero exit code when something goes wrong so CI can act on it. J-Link supports this through its command-line tools and script files, and Zephyr's build produces the artifacts (ELF, hex/bin, and the symbol information needed to interpret a fault).

I'd structure it in stages. First, a flash-and-verify stage using the J-Link command line, checking the return code and verifying the programmed image. Second, a run stage where the harness resets the target and either waits for a test-complete signal over a serial or RTT channel, or polls a known memory location. Third, a capture stage: on failure, halt the core and read out the fault registers and the relevant RAM region, then use the ELF to symbolize the stack and fault address. RTT is often the cleanest channel for both logging and triggering because it doesn't need extra pins.

The failure modes I'd design around are the ones that make automated bring-up flaky: the debugger failing to connect because the target is in a low-power state or the SWD lines are contended; the target resetting mid-test and the harness not noticing; a crash that locks the debug interface so the dump can't be read; and the harness hanging forever instead of timing out. So I'd add connection retries with a bounded count, explicit timeouts on every wait, a watchdog reset path, and a "known-good" sanity flash at the start to confirm the rig itself is healthy. I'd also make the harness log the exact J-Link and firmware versions, because "it passed yesterday" is only meaningful if the toolchain is pinned.

**Possible follow-ups:**
- How would you capture a crash dump if the fault locks up the debug interface?
- How would you make the test sequence deterministic when the firmware has asynchronous tasks running?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** First I'd separate the immediate problem from the conversation. The immediate problem is that the release package is incomplete and partly wrong, and the board house is waiting — so the priority is to fix the package correctly, not to assign blame. I'd sit down with the engineer and walk the output job together, showing specifically what's missing and why it matters: a drill table is needed for fabrication and inspection, and assembly drawings that reference an old schematic revision are a real risk because they can lead to a board built to the wrong documentation. The point isn't that the Gerbers are wrong — they may well be fine — it's that "the Gerbers look fine" isn't the same as "the release package is complete and consistent."

Then I'd treat it as a process gap rather than a personal failing. If a junior engineer can produce an incomplete release package and feel confident about it, the checklist or the output job template is probably not doing its job. So I'd want a release checklist that's actually used, and ideally an output job that's been validated once against a known-good release so the expected contents are explicit. I'd also make sure the engineer understands the regulatory angle — for a medical device, the released documentation has to match what's built, and that's not optional.

On the schedule: I'd get the corrected package out, even if it means a late night, and I'd communicate to the board house if there's any risk of slipping. I'd avoid dressing the engineer down in front of others; the goal is a fix and a lesson learned, not a demoralized team member. If the same gap recurred, that's when it becomes a performance conversation rather than a coaching one.

**Possible follow-ups:**
- How would you prevent this class of error from recurring without adding so much process that releases slow to a crawl?
- If the board house had already started fabrication on the incomplete package, how would your approach change?