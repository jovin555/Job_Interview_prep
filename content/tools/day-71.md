# tools — Day 71

## Q1: How would you approach setting up a scripted, repeatable flashing and test sequence for a Zephyr RTOS target using a Segger J-Link, where the harness needs to program the device, run a test, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** I'd treat this as a small automation pipeline with four distinct stages, each of which needs to be independently observable so a failure can be attributed rather than just "the script broke."

The first stage is flashing. I'd use the J-Link command-line tools driven by a script (a `.jlink` command file or the J-Link Commander in batch mode), rather than relying on an IDE. The script resets the target, halts, erases the required flash regions, programs the image, verifies it, and resets to run. Verification after programming is non-negotiable — a silent flash failure that only shows up as a hung test is the most expensive kind of false negative.

The second stage is run control. After reset, the harness needs a deterministic way to know the test has started and finished. I'd have the firmware emit a recognizable marker over a debug channel (RTT or a UART) at the start and end of the test, and have the harness wait on that marker with a timeout rather than a fixed sleep. Fixed sleeps are the classic source of flakiness in automated benches.

The third stage is crash capture. If the target faults, I want the crash dump pulled automatically. With a Cortex-M target, that means configuring the J-Link to halt on the fault vector, then reading out the stacked registers and the fault status registers (CFSR, HFSR, BFAR, MMFAR) before resetting. The key design decision is to have the firmware's fault handler stash a compact dump in a known RAM or flash region, so the harness can read it back even if the debug connection is momentarily lost.

The fourth stage is teardown and reporting: reset the target to a known state, close the debug session cleanly, and emit a machine-readable result (pass/fail plus the captured dump) so the CI system can archive it.

Failure modes I'd design around explicitly: the debug probe not being enumerated (USB re-enumeration, hub power), the target being held in reset by an external signal, a previous session leaving the debug port locked, flash protection or readout protection being enabled, the target running off a supply the harness doesn't control, and the test hanging without faulting (so the timeout path must also trigger a dump capture, not just a kill). I'd also make the script idempotent — running it twice in a row should produce the same result — because that's what makes it usable in a regression loop.

**Possible follow-ups:**
- How would you distinguish a genuine firmware crash from a debug-probe disconnect in the captured logs?
- If two test stations share one J-Link, how would you serialize access without introducing flakiness?

## Q2: How would you approach organizing a KiCad project for a medical device so the schematic, PCB, footprints, and 3D models stay consistent across revisions, and how would you catch footprint-to-schematic mismatches before they reach fabrication?

**Answer:** The core problem with KiCad is that it's file-based rather than database-driven, so consistency has to be enforced by convention plus tooling rather than by a central vault.

For organization, I'd keep the project self-contained: a single project directory with the `.kicad_pro`, `.kicad_sch`, and `.kicad_pcb` files, plus project-local `footprints/`, `symbols/`, and `3dmodels/` directories referenced by relative path. The temptation is to point at a shared global library, but for a regulated project that breaks reproducibility — a library change silently alters an old revision. Project-local libraries mean a checkout of a tagged revision reproduces exactly what was fabricated.

For revision consistency, I'd tag releases in version control and treat the tag as the source of truth for "what was built." The schematic and PCB should always be committed together, never one without the other, because a schematic-only commit is a latent mismatch.

For catching footprint-to-schematic mismatches, I'd lean on several layers. First, run ERC and DRC as a gate, not an afterthought — ERC catches unconnected pins and power-flag issues, DRC catches clearance and connectivity problems. Second, use KiCad's "Update PCB from Schematic" in a dry-run sense and inspect the diff: if the tool wants to add or remove footprints, that's a signal something drifted. Third, cross-probe between schematic and PCB and spot-check that every symbol maps to a placed footprint with the expected reference designator. Fourth, before generating Gerbers, do a footprint audit: verify pad counts, pad numbering, and courtyard dimensions against the datasheet for any part that's new or was recently changed. The courtyard check in particular catches the case where a symbol is correct but the footprint is the wrong package variant.

Finally, I'd generate the Gerbers and run them through an independent viewer (Gerbv or similar) and compare against the previous revision's output — a visual diff of the copper layers catches things the DRC won't, like a footprint that's electrically valid but physically in the wrong orientation.

**Possible follow-ups:**
- How would you handle a situation where a footprint needs to change but the board is already in fabrication?
- What's your approach to 3D model integration so the mechanical team can trust the assembly model?

## Q3: How would you approach setting up a power integrity simulation workflow for a mixed-signal PCB where a high-current switching regulator and a precision analog front-end share the same power distribution network, and how would you decide which results are trustworthy enough to act on?

**Answer:** I'd start by being clear about what PI simulation can and can't tell you, because the biggest risk is over-trusting a model built on incomplete stackup and component data.

The workflow has a few stages. First, define the power distribution network topology: the regulator output, the bulk and decoupling capacitors, the plane structures, and the load points (the analog front-end and the digital section). Second, extract the PDN impedance — either from a 2D field solver for the planes or from a lumped model if the geometry is simple — and combine it with the capacitor models including their ESR and ESL. The goal is a Z(f) curve showing where the PDN impedance peaks relative to the current draw's frequency content.

The interesting part is the interaction: a switching regulator injects ripple at its switching frequency and its harmonics, and the analog front-end has a finite power supply rejection ratio that degrades with frequency. So the question isn't just "is the impedance low" but "is the impedance low at the frequencies where the analog front-end is sensitive and the regulator is noisy." I'd overlay the regulator's ripple spectrum, the PDN impedance, and the analog front-end's PSRR to see where the margins are thin.

On trustworthiness: I'd treat the simulation as a hypothesis generator, not a verdict. The results I'd act on are the ones that are robust to reasonable parameter variation — if a resonance shows up across a range of capacitor ESR values and plane models, it's probably real. Results that depend on a single assumed value I'd flag as "needs measurement." I'd also sanity-check against a simple hand calculation: the self-resonant frequency of a decoupling capacitor, the plane capacitance, the loop inductance of a via pair. If the simulation disagrees with the hand calc by an order of magnitude, the model is wrong, not the physics.

The validation step is a real measurement: inject a known load step at the analog front-end's supply pin and measure the resulting transient with a scope, or measure the PDN impedance with a network analyzer if the setup allows. The simulation earns trust by predicting the measurement, not by looking plausible on screen.

**Possible follow-ups:**
- How would you decide whether a resonance in the PDN impedance is a real problem or a simulation artifact?
- What would you change in the layout if the simulation showed a resonance right at the analog front-end's sensitive frequency?

## Q4: How would you approach setting up a test and measurement bench for bring-up of a new mixed-signal medical device prototype, deciding which instruments to dedicate versus share, and how would you keep the setup repeatable across multiple engineers?

**Answer:** I'd start by listing what the bring-up actually needs to observe: power rails, digital buses, analog sensor signals, and the RF/EMI environment. Then I'd map instruments to those needs and decide dedicated versus shared based on how often the instrument is used and how disruptive it is to move.

Dedicated instruments are the ones that are used constantly and are painful to reconfigure: a good mixed-signal oscilloscope with the right probes, a bench power supply with current limiting and logging, and a DMM. These stay on the bench, powered, with probes already connected to the standard test points. Shared instruments are the ones used intermittently: the spectrum analyzer, the logic analyzer, the thermal camera, the LCR meter. These live on a cart or in a cabinet and get checked out.

The repeatability problem is really a documentation and labeling problem. I'd define a standard test point map for the prototype — every rail, every bus, every analog node has a labeled test point on the board and a matching entry in a bench reference document. Probes are labeled and their compensation status is recorded. The bench has a fixed layout so an engineer who hasn't used it before can find things. And there's a simple log: who used the bench, what they changed, what they observed. That log is what turns "it worked yesterday" into an actionable data point.

For multi-engineer use, I'd also standardize the scope setup: save setups for common measurements (rail ripple, bus timing, analog noise) so two engineers measuring the same thing get comparable results. And I'd enforce a rule that any instrument setting that affects a measurement gets recorded in the test log — otherwise you get the classic situation where two people measure the same signal and get different answers because one had a 20 MHz bandwidth limit on and the other didn't.

**Possible follow-ups:**
- How would you handle a situation where two engineers need the same shared instrument at the same time?
- What would you include in a bench reference document to make it genuinely useful rather than shelfware?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** The immediate priority is the release — the board house deadline is real and the outputs are not actually complete. So I'd separate the technical fix from the conversation.

Technically, I'd verify the gap myself rather than take the report at face value: open the output job, check which outputs are enabled, confirm the drill table is genuinely absent, and check the assembly drawing's revision against the current schematic. Then I'd fix the output job configuration, regenerate, and do a verification pass — open the Gerbers and drill files in an independent viewer, confirm the drill table is present and matches the drill hits, and confirm the assembly drawings reference the correct revision. If there's time, I'd have a second person verify before sending.

On the conversation: the engineer's confidence is the thing to address, not the mistake. "The Gerbers look fine" is a reasonable statement about the Gerbers and an incomplete statement about the release package — the lesson is that a release package is more than Gerbers. I'd walk through what a complete release actually contains and why each piece matters, using this as the concrete example. I'd avoid framing it as "you were wrong" and frame it as "here's the checklist we should have been using." The goal is that the next release doesn't have this gap, and that the engineer understands the reasoning rather than just the rule.

I'd also look at whether the process failed, not just the person. If there's no release checklist, that's a process gap I own. I'd put one in place — a documented release package definition with a verification step — so the next release doesn't depend on one person's memory of what "complete" means.

**Possible follow-ups:**
- How would you handle it if the engineer pushed back and argued the drill table isn't necessary?
- What would you change in the release process to catch this kind of gap earlier, before the day before the deadline?