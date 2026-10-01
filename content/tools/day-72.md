# tools — Day 72

## Q1: How would you approach setting up a symbol and footprint library in KiCad for a medical device project where the same component appears in multiple variants — different package sizes, tolerance grades, or temperature ratings — so the library stays maintainable and traceable across revisions?

**Answer:** The core problem is that a "part" in a medical BOM is really two separate concepts: the schematic symbol (functional identity — pins, reference designator prefix, electrical behavior) and the physical footprint plus ordering attributes (package, tolerance, temperature grade, manufacturer part number). Conflating them is what makes variant-heavy libraries rot. So I'd separate them deliberately.

On the symbol side, I'd keep one symbol per functional device — a precision op-amp gets one symbol regardless of whether it's the SOIC-8 or the MSOP-8 variant — and let the footprint assignment happen at the schematic instance or via a variant/alternate-parts mechanism rather than by cloning the symbol. That keeps the schematic readable and means a pin-mapping fix propagates everywhere at once.

On the footprint side, I'd organize by package family with a strict naming convention that encodes the attributes that matter for traceability: package, pitch, thermal pad presence, and a revision suffix. In KiCad specifically, because libraries are file-based rather than database-driven, I'd lean on a few compensating practices: keep libraries in a Git repo with the project (or a submodule) so every revision is pinned; use KiCad's footprint and symbol fields to carry the manufacturer part number, tolerance, and temperature grade as structured fields rather than free text; and treat the library as a versioned artifact that gets tagged alongside the board revision. For a medical project, the traceability requirement means I want to be able to answer "which exact library revision produced this BOM" — that's a Git tag plus a locked library path, not tribal knowledge.

The maintainability trick is to make the *variant selection* explicit and reviewable. I'd use a variant or DNP mechanism so the schematic shows which grade is populated for which build, and I'd add a DRC/ERC-adjacent check — even a simple script — that flags any component whose assigned footprint doesn't match the symbol's expected pin count or whose required fields are empty. That catches the classic failure where someone swaps a footprint and forgets to update the ordering field.

**Possible follow-ups:**
- How would you handle a situation where a manufacturer discontinues one variant but the others remain available — what changes in the library and in the released BOM?
- If two engineers are editing the same file-based KiCad library simultaneously, how would you prevent merge conflicts from silently corrupting a footprint?

## Q2: How would you approach setting up a power integrity (PI) simulation workflow for a mixed-signal PCB where a high-current switching regulator and a precision analog front-end share the same power distribution network, and how would you decide which results are trustworthy enough to act on?

**Answer:** I'd start by being honest about what PI simulation can and can't tell you, because the biggest risk is acting on a pretty plot that's built on bad inputs. The workflow has three stages: model the PDN, drive it with realistic current, and then decide which outputs are decision-grade.

For the model, the accuracy lives or dies on the stackup and material properties. I'd extract the actual layer stackup, copper thickness, and dielectric constants from the fab drawing rather than accepting tool defaults, and I'd model the VRM as a source with its actual output impedance and control-loop bandwidth — not an ideal voltage source. The decoupling network gets modeled with real capacitor parasitics (ESL, ESR, and their frequency dependence), because at the frequencies that matter for a switching regulator's harmonics, an ideal capacitor model is fiction. The analog front-end's load is modeled as its actual input impedance and any on-chip decoupling, since that's what determines whether supply noise couples into the signal path.

For the drive, I'd use the regulator's real switching waveform — rise time, duty cycle, and load transient profile — because the PDN's response to a fast load step is usually the thing that actually breaks a precision analog front-end, not the steady-state ripple.

The trustworthiness question is the important one. I'd rank results by how much they depend on uncertain inputs. Impedance-vs-frequency plots of the PDN are relatively trustworthy because they're mostly geometry and component parasitics — good for spotting anti-resonances between bulk and ceramic caps. Time-domain noise at a specific node is much less trustworthy because it depends on the VRM model and the exact load profile, so I'd treat it as directional, not predictive. Anything that requires the tool to guess at on-die behavior I'd treat as a hypothesis to test on the bench, not a result to design around. The rule I'd apply: if a simulation result would change a layout decision, I want to confirm it with a measurement — a scope probe with a proper ground spring at the analog supply pin, or a network analyzer for the impedance — before committing to a respin.

**Possible follow-ups:**
- How would you decide where to place bulk versus ceramic decoupling to kill an anti-resonance the simulation flagged?
- What measurement would you use to validate the PDN impedance model, and what would make you distrust the measurement itself?

## Q3: How would you approach using a spectrum analyzer with a near-field probe to locate the source of a radiated emissions failure at a specific frequency during pre-compliance testing, and how would you confirm which component is responsible?

**Answer:** The near-field probe is a localization tool, not a compliance measurement — it tells you *where* energy is concentrated, not whether you'll pass. So I'd use it in a deliberate scan pattern rather than waving it around.

First, I'd set the analyzer up to make the failure repeatable: the device in its worst-case operating mode, the frequency span centered on the failing frequency with enough span to see whether it's a single tone or a modulated/harmonic-rich emission, and a resolution bandwidth and detector consistent with the test standard I'm pre-testing against. Repeatability matters more than speed here — if the emission moves when I move the probe, I need to know whether that's the probe coupling or the device behavior changing.

Then I'd scan systematically: start with the probe a fixed small distance above the board and sweep across the whole area to build a coarse map of hot spots, then narrow in. The key discriminator is *what changes the emission*. If I suspect a switching regulator, I can change its switching frequency (if the controller allows it) or its load, and watch whether the emission tracks. If I suspect a digital clock, I can gate the clock, change its frequency, or halt the relevant peripheral, and see whether the tone moves or disappears. A harmonic that shifts when I change a clock frequency is almost certainly that clock's harmonic; one that shifts with the regulator's switching frequency is the regulator.

To confirm the responsible component, I'd combine the spatial localization with a controlled experiment: probe directly over the suspect component and its immediate traces, then apply a targeted mitigation — a temporary snubber, a ferrite bead, a small shield can, or a hand-placed decoupling cap — and verify the emission drops. If the mitigation at that location kills the tone, I've confirmed the source. I'd also check whether the emission is common-mode or differential-mode by comparing probe orientation and by seeing whether a common-mode choke or a cable ferrite changes it, since that determines the fix.

**Possible follow-ups:**
- How would you distinguish a radiated emission from something being conducted out on a cable and radiating from the cable instead?
- If the failing frequency is a harmonic of two different sources, how would you separate their contributions?

## Q4: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where an automated test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** The goal is a headless, repeatable flash-run-capture cycle that a CI system or test script can drive, so I'd build it around J-Link's command-line and scripting interfaces rather than the GUI.

The basic flow: the harness invokes the J-Link commander or a scripted flash sequence to program the image, resets the target, and then either lets the firmware run and reads back results over a separate channel (UART, RTT, or a test interface) or attaches to capture state. For crash capture, I'd use the target's fault handling — Zephyr's fatal error handler can be configured to halt or to write a dump — and have the J-Link read out the relevant memory regions (stack, fault registers, the Zephyr fatal error structure) after the fault. RTT is often the cleanest channel for both test output and crash logs because it doesn't need a UART pin and doesn't halt the CPU.

The failure modes are where the real design work is, and I'd design around each:

- **Debugger can't connect.** Wrong SWD/JTAG pin assignment, target held in reset, or the debug port disabled by firmware (some low-power or security configurations lock it). I'd verify connectivity as an explicit first step and fail the test loudly rather than hanging.
- **Flash succeeds but the device doesn't run.** Reset behavior differences, boot mode pins, or the image not being valid for the target. I'd add a "device alive" check — a known RTT banner or a GPIO toggle — before declaring the flash successful.
- **Crash dump is incomplete or stale.** If the target resets after a fault, the dump is gone. I'd configure the fault handler to halt (or to persist the dump to flash/RAM that survives reset) so the harness can read it.
- **Race between flash and test start.** The harness starts reading before the device is ready. I'd use an explicit synchronization point rather than a fixed sleep.
- **Flaky connection under repeated cycles.** USB hubs, power sequencing, or the target not fully power-cycling between runs. I'd add a power-cycle step and a retry-with-backoff around the connect, and log enough to distinguish a real test failure from an infrastructure failure.

The overarching principle: the harness should never silently pass because the debugger failed to connect or the dump was empty. Every step gets a positive confirmation.

**Possible follow-ups:**
- How would you make the crash dump survive a target reset so the harness can read it after the fact?
- What would you log to distinguish a genuine firmware crash from a debug-probe or power-sequencing problem?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** The immediate priority is the release — the board house deadline is real and non-negotiable — so I'd separate "fix the files" from "address the process and the person," and handle them in that order.

First, I'd verify the actual state of the outputs myself rather than taking either the engineer's word or my own first impression. "The Gerbers look fine" is true but insufficient: Gerbers can be geometrically correct while the drill table is missing (so the fab can't drill) and the assembly drawings reference the wrong schematic revision (so assembly and inspection are working from stale information). I'd check the output job against the release checklist — drill files present and matching the Gerber layer count, assembly drawings tied to the correct schematic revision, BOM revision matching, and any fab notes. Then I'd regenerate the missing pieces and re-verify before the deadline. If there's any doubt about whether the fab can proceed, I'd rather send a corrected, complete package a few hours later than send an incomplete one on time.

Second, I'd talk to the engineer — but not as a blame exercise. The framing matters: the engineer was confident because they checked the Gerbers, which is exactly the check they knew how to do. The gap is that the release checklist either didn't exist, wasn't followed, or wasn't specific enough about what "complete" means. So the conversation is "here's what the release actually requires and why each artifact matters," not "you got it wrong." I'd walk through the drill table and the assembly drawing revision specifically, because understanding *why* those matter — the fab literally cannot drill without the drill file, and assembly can build the wrong variant from a stale drawing — is what makes the lesson stick.

Third, the systemic fix: a release checklist that's explicit and verifiable, ideally with a second set of eyes on any release that goes to a fab house. For a medical device, the output package is part of the design history file, so "complete" has a regulatory definition, not just a practical one. I'd make the checklist a gate rather than a suggestion, and I'd make sure the engineer understands that the checklist exists to protect them, not to catch them.

The tone throughout: the deadline is the emergency, the process gap is the real problem, and the engineer is a colleague who needs a better checklist, not a reprimand.

**Possible follow-ups:**
- How would you structure the release checklist so it's actually followed under deadline pressure rather than skipped?
- If the same gap recurred on a later release, how would you escalate — and how would you distinguish a training gap from a process gap?