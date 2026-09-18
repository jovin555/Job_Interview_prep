# tools — Day 59

## Q1: How would you approach setting up a schematic symbol and footprint library in KiCad for a medical device project where the same component appears in multiple variants — different package sizes, tolerance grades, or temperature ratings — so the library stays maintainable and traceable across revisions?

**Answer:** The core problem is that a single "part" in a medical BOM often maps to several distinct orderable items that share a symbol but differ in footprint, tolerance, or temperature grade. I'd separate the concerns rather than duplicating whole symbols.

First, I'd define the symbol around function, not around the orderable part: one schematic symbol for the functional block (e.g., a precision resistor or a regulator), with generic pin definitions. Then I'd create one footprint per physical package, and let the symbol-to-footprint mapping happen at the schematic instance level via footprint fields. That way a design change from an 0402 to an 0603 variant is a field edit, not a library fork.

For the variant attributes — tolerance, temperature grade, voltage rating — I'd carry those as structured metadata rather than encoding them in the symbol name. In KiCad that means using the symbol's field set (MPN, tolerance, temp range, and a house part number) and, where possible, driving the BOM from those fields. The key discipline is a single naming convention and a single source of truth for the house part number, so that a given orderable item always resolves to the same symbol + footprint + metadata combination.

For traceability, I'd keep the library under version control alongside the project, tag library states that correspond to released board revisions, and treat any library edit as a reviewable change. The trap to avoid is "library drift" — someone edits a shared symbol to fix one project and silently changes another. Pinning the project to a known library revision, or vendoring the library into the project, prevents that.

**Possible follow-ups:**
- How would you handle a situation where a symbol needs a new pin for one variant but not another, without breaking existing designs?
- What would you check to confirm that a footprint in the library actually matches the manufacturer's recommended land pattern before it's used in a release?

## Q2: How would you approach setting up a power integrity simulation workflow for a mixed-signal PCB where a high-current switching regulator and a precision analog front-end share the same power distribution network, and how would you decide which results are trustworthy enough to act on?

**Answer:** I'd treat this as a question of "what can the tool actually tell me, and where does its model break down." The workflow starts with getting the PDN geometry right — stackup, copper weights, plane shapes, via stitching, and the decoupling network — because a PI simulation is only as good as the parasitics it's given.

The first pass is a DC/IR-drop analysis: how much voltage droop appears at the analog front-end's supply pins under worst-case load, and whether the plane and via resistance is acceptable. That's the most trustworthy class of result because it depends mainly on geometry and current, not on component models.

The second pass is AC impedance of the PDN as seen from the load — looking for anti-resonances between the regulator's output impedance, the bulk caps, and the high-frequency ceramics. This is where I'd be most cautious: the result is very sensitive to the capacitor models (ESR, ESL, and their frequency dependence) and to how the plane capacitance is modeled. If the library models are generic rather than vendor-measured, I'd treat the absolute impedance numbers as indicative and focus on the shape — where the peaks are and whether they land near frequencies the analog front-end cares about.

The third pass, if the tool supports it, is noise coupling from the switching regulator into the analog rail. Here I'd be explicit that a simulation can show a mechanism but rarely predicts the exact microvolts you'll measure, because it depends on layout parasitics, grounding, and the regulator's real switching behavior.

The decision rule: act on DC/IR-drop results directly; act on AC impedance results to guide decoupling placement and value selection, but verify with measurement; treat coupling predictions as hypotheses to test on the bench, not as pass/fail criteria. And I'd always correlate at least one simulation result against a real measurement before trusting the model for the rest of the design.

**Possible follow-ups:**
- How would you decide where to place the boundary between "on-die/on-package" and "on-board" in the model, and what error does that introduce?
- If the simulation says the PDN is fine but the bench shows noise on the analog rail, what would you suspect first?

## Q3: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where the test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** The goal is a deterministic, headless flow: reset into a known state, flash, run, detect completion or fault, and extract evidence — all scriptable and repeatable.

I'd start by defining the interface between the test harness and the debug probe. The J-Link supports scripted operation (J-Link Commander scripts, or the J-Link SDK / pyOCD-style tooling), so the harness can invoke flash-and-run as a command and read back a result. For Zephyr specifically, I'd make sure the build produces the artifacts the harness needs — the ELF for symbol resolution and the binary/hex for flashing — and that the debug configuration (SWD vs JTAG, speed, reset behavior) is captured in a config file rather than hardcoded.

For crash capture, the key is to not depend on the firmware printing anything. On a hard fault, the CPU is in a fault handler; the useful evidence is the fault status registers, the stacked registers, and the program counter. I'd configure the flow so that on fault detection the harness halts the core, reads those registers, and resolves the addresses against the ELF to produce a symbolized report. If the target supports it, a trace buffer or a reserved RAM region for a crash log can capture the last moments before the fault without needing a live debugger attached at the moment of failure.

Failure modes I'd design around:
- **Probe not enumerated / target not powered** — the harness must detect "no connection" and fail loudly rather than hang.
- **Flash verify failure** — a partial or corrupted flash should abort the run, not proceed to a meaningless test.
- **Target stuck in a loop or never reaching the test-complete marker** — a timeout with a defined "hung" result, plus a snapshot of where it was.
- **Reset behavior differences** — some targets need a specific reset type (e.g., reset-and-halt vs reset-and-run); getting this wrong produces flaky results.
- **Concurrent access** — if multiple test jobs share a probe or a target, serialize them or give each its own hardware.

The overarching principle: every step should have a detectable success/failure signal, and the harness should never assume the previous step worked.

**Possible follow-ups:**
- How would you make the crash dump reproducible enough to compare across runs, so you can tell a new failure from a known one?
- What would you do if the target occasionally fails to connect to the probe only under certain power or temperature conditions?

## Q4: How would you approach setting up a cross-probe workflow between OrCAD Capture and Cadence Allegro so a layout review can move efficiently between schematic and PCB, and what would you check to confirm the link actually works before relying on it in a review?

**Answer:** Cross-probing is only useful if it's bidirectional and trustworthy — selecting a net or component in the schematic highlights it in the layout, and vice versa. The setup depends on both tools sharing a consistent design database, so the first requirement is that the netlist and reference designators are in sync. If the schematic and PCB have diverged, cross-probing will either fail or, worse, point at the wrong object.

I'd verify the link with a deliberate test before the review, not during it: pick a specific component by reference designator in the schematic, confirm it highlights the correct footprint in the layout, then reverse the direction. I'd do the same for a net — select a net in the schematic and confirm the correct traces and pins highlight. I'd also test a net that spans multiple pages or a component that's part of a multi-channel block, because those are the cases where cross-probing most often breaks.

Common failure points to check:
- **Stale netlist** — the PCB was updated from an older schematic revision.
- **Reference designator mismatches** — a component was renamed on one side only.
- **Multi-channel or hierarchical sheets** — the instance path isn't resolving correctly, so the wrong instance highlights.
- **Net aliases or renamed nets** — the same physical net has different names on each side.

For the review itself, I'd establish a convention: the reviewer drives from the schematic, the layout engineer follows in Allegro, and any discrepancy is logged rather than fixed live. That keeps the review moving and prevents the session from turning into an editing session. If cross-probing fails mid-review, the fallback is to navigate by reference designator and net name manually, but I'd rather catch that in the pre-check.

**Possible follow-ups:**
- How would you handle a review where the schematic and PCB are known to be slightly out of sync — proceed or stop?
- What's your approach to reviewing a net that crosses a board-to-board connector, where the two halves live in different design files?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** The immediate priority is to not send incomplete or inconsistent files to the board house — a missing drill table or an assembly drawing tied to the wrong schematic revision is exactly the kind of error that either stops fabrication or, worse, produces boards that don't match the design intent. So the first move is to pause the release, not debate it.

I'd sit down with the engineer and walk through the output job together, not to assign blame but to make the gap visible. "The Gerbers look fine" is true but incomplete — Gerbers are one output among several, and the release package has to be internally consistent. I'd show them the specific missing items: the drill table (which the fab needs to drill the board correctly) and the assembly drawing referencing an old schematic revision (which creates a documentation mismatch that matters for both manufacturing and regulatory traceability).

Then I'd treat it as a teaching moment about what "release-ready" means: a defined checklist of outputs, each verified against the current design revision, with a final consistency check across the package. The fix itself is usually quick — regenerate the drill table, re-export the assembly drawing from the current schematic — but the process gap is the real issue.

On the schedule: I'd assess whether the release can still go out on time after the fix, and if not, communicate the slip early rather than send bad files. For a medical device, a documentation mismatch isn't a cosmetic issue — it can affect the design history file and the regulatory submission. I'd rather have a short, honest delay than a fabrication run that has to be redone or a traceability problem that surfaces later.

I'd also follow up by making the output job configuration itself more robust — for example, a standard output job template with all required outputs defined, so the next release doesn't depend on someone remembering every item. And I'd review the release checklist with the whole team so this becomes a shared standard rather than a one-off correction.

**Possible follow-ups:**
- How would you structure a release checklist so that a missing output is caught before the package leaves the building?
- If the engineer felt singled out by the correction, how would you handle that while still fixing the process?