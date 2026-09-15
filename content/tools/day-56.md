# tools — Day 56

## Q1: How would you approach setting up a schematic symbol and footprint library in KiCad for a medical device project where the same component appears in multiple variants (e.g., different package sizes or tolerance grades), so that the library stays maintainable and traceable across revisions?

**Answer:** The core problem is that a single "part" in a medical BOM often maps to several library objects — a symbol, one or more footprints, and possibly multiple orderable MPNs — and if you collapse those into one library entry you lose traceability the moment a variant is added. I'd separate the concerns: one generic symbol per electrical function (e.g., a resistor symbol with generic pin names), and a distinct footprint per physical package. The binding between them happens at the schematic level, not inside the symbol, so the same symbol can be paired with an 0402 or 0603 footprint depending on the variant.

For traceability, I'd use KiCad's field system deliberately: a `MPN` field, a `Manufacturer` field, a `Datasheet` field, and a project-specific `Internal_PN` field that maps to the BOM. For variants, rather than duplicating symbols, I'd use alternate fields or a variant-aware BOM export so the same schematic can produce different BOMs. The library itself lives in a Git repo (or a database-backed library if the team is large enough), with each symbol/footprint change going through a review — because in a regulated context, a silent library edit that changes a pin assignment is exactly the kind of thing that must be caught before it reaches a released schematic.

The key discipline is: symbols describe function, footprints describe physical reality, and the schematic is where the two are bound together with the specific MPN. That separation is what keeps the library from exploding into hundreds of near-duplicate entries.

**Possible follow-ups:**
- How would you handle a situation where a footprint needs to change (e.g., a pad geometry correction) but the symbol stays the same — what's your process for propagating that change to existing designs?
- If two engineers edit the same library symbol simultaneously, how does your workflow prevent one edit from silently overwriting the other?

## Q2: How would you approach using a spectrum analyzer with a near-field probe to distinguish whether a radiated emissions failure at a specific frequency is coming from a switching regulator's switching harmonic versus a digital clock harmonic, and how would you confirm your hypothesis?

**Answer:** The first step is to establish what frequencies you'd *expect* from each candidate source. A switching regulator produces emissions at its switching frequency and its harmonics, plus sidebands from jitter or spread-spectrum modulation. A digital clock produces emissions at its fundamental and odd/even harmonics depending on duty cycle. So before probing, I'd list the candidate frequencies: the regulator's Fsw and its multiples, and each clock's fundamental and its multiples, and see which ones land on the failing frequency.

Then I'd probe systematically. With a near-field probe (H-field for current loops, E-field for voltage nodes), I'd scan the board and note where the amplitude at the failing frequency peaks. If the peak is over the regulator's inductor or input loop, that points to the regulator. If it's over a clock trace or the IC driving it, that points to the clock. I'd also check whether the emission shifts when I change the regulator's load or the clock's frequency — a regulator harmonic will move if you change Fsw (if adjustable) or disappear if you disable the regulator; a clock harmonic will disappear if you gate the clock.

Confirmation comes from a controlled experiment: disable one source at a time (halt the clock, put the regulator in a different mode, or substitute a clean bench supply) and re-measure. If the emission vanishes when the regulator is disabled but the clock is still running, the regulator is the source. If it vanishes when the clock is gated but the regulator is still switching, the clock is the source. The near-field probe tells you *where*; the controlled disable tells you *which*. Both together give you a defensible root cause.

**Possible follow-ups:**
- If both sources contribute to the same frequency, how would you determine which one is dominant?
- How would you distinguish a harmonic of the switching frequency from a sideband caused by jitter or spread-spectrum modulation?

## Q3: How would you approach setting up a Segger J-Link scripted flashing and test sequence for a Zephyr RTOS target, where the test harness needs to program the device, run a test, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** I'd structure this as a scripted sequence driven by the J-Link command-line tools (JLinkExe/JLink.exe with a script file, or the J-Link SDK if the harness needs finer control), wrapped by whatever test runner the team uses. The sequence is: reset and halt, erase/program the image, verify, reset and run, wait for a completion signal (UART output, GPIO toggle, or a known memory location), then read back the crash dump region if the test failed.

The failure modes I'd design around are the ones that make automated flashing unreliable in practice. First, target not responding — the script needs a timeout and a retry, and it needs to distinguish "no target" from "target in a bad state" (e.g., a previous run left it in a low-power mode). Second, flash verify failure — always verify after programming, because a marginal connection can produce a silent corruption. Third, the test hanging — the harness needs a watchdog timeout so a hung target doesn't stall the whole run. Fourth, crash dump capture — the dump region needs to be defined and stable across firmware revisions, and the script needs to read it before the next flash overwrites it. Fifth, debug interface contention — if multiple test stations share a J-Link or a debug probe, you need locking or per-station probes.

For Zephyr specifically, I'd make sure the build produces a known-good image with a stable memory map, and that the crash dump mechanism (e.g., a retained RAM region or a flash-backed coredump) is enabled in the test build. The script itself should log everything — the exact commands, the target responses, and the raw dump — so a failure can be diagnosed after the fact without re-running.

**Possible follow-ups:**
- How would you handle a target that occasionally fails to enter the debug mode after a reset — what would you check first?
- If the crash dump region is in RAM and the target resets before you read it, how would you preserve the dump across the reset?

## Q4: How would you approach setting up a cross-probe workflow between OrCAD Capture and Cadence Allegro so that a layout review can move efficiently between schematic and PCB, and what would you check to confirm the link is actually working before relying on it in a review?

**Answer:** Cross-probing depends on the two tools sharing a consistent netlist and a consistent design database, so the first thing I'd verify is that the Allegro board was imported from the *current* Capture netlist — not an older revision. If the netlist is stale, cross-probing will either fail or, worse, point to the wrong component. I'd confirm the design revision in both tools matches, then check that the cross-probe settings are enabled in both (in Capture, the cross-probe option; in Allegro, the corresponding preference), and that the two are pointed at the same design.

To confirm the link actually works before a review, I'd do a quick smoke test: select a specific component in Capture and verify Allegro highlights the correct footprint, then select a net in Allegro and verify Capture highlights the correct pins. I'd test both directions, and I'd test a component that exists in multiple instances (e.g., a decoupling cap) to make sure the instance mapping is correct, not just the part number. I'd also test a net that crosses a hierarchical sheet boundary, because that's where cross-probe mappings often break.

The reason to do this *before* the review is that a broken cross-probe turns a fast review into a manual search exercise, and it also risks the reviewer trusting a highlight that's pointing at the wrong object. If the link is broken, I'd rather spend ten minutes fixing it than have the review produce incorrect conclusions.

**Possible follow-ups:**
- What would you do if cross-probing works for components but not for nets — where would you look first?
- How would you handle a review where the schematic and PCB are in different tools that don't support native cross-probing?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** The first thing I'd do is separate the immediate problem from the process problem. The immediate problem is that the release package is incomplete and the board house is expecting it tomorrow — so I'd take ownership of getting a correct package out, not just point out the error. I'd sit down with the engineer and walk through the output job together, showing what's missing and why it matters: a drill table is required for the fab to understand the drill schedule, and assembly drawings that reference an outdated schematic revision are a traceability problem in a regulated context, not just a cosmetic one.

The "the Gerbers look fine" comment is the real issue — it suggests the engineer is validating the output by looking at one artifact rather than against a release checklist. So I'd use this as a teaching moment, not a blame moment. I'd walk through what a complete release package actually contains (Gerbers, drill files, drill table, assembly drawings, BOM, pick-and-place, fab notes) and why each one exists. Then I'd have the engineer regenerate the package against that checklist, with me reviewing it before it goes out.

For the process side, I'd add a release checklist to the project — a documented set of outputs that must be present and verified before any package goes to the board house. That way the next release doesn't depend on someone remembering. I'd also make sure the engineer understands that the goal isn't to catch them out; it's that a missing drill table or a stale assembly drawing can cause a fab delay or a build error that costs far more than the time to check.

**Possible follow-ups:**
- How would you handle it if the engineer became defensive and insisted the package was fine?
- What would you put in a release checklist to catch this class of error before it reaches the board house?