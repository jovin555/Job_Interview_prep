# tools — Day 66

## Q1: How would you approach setting up a schematic symbol and footprint library in KiCad for a medical device project where the same component appears in multiple variants — different package sizes, tolerance grades, or temperature ratings — so the library stays maintainable and traceable across revisions?

**Answer:** The core problem is that KiCad's file-based library format doesn't give you a database with variant relationships, so you have to impose that structure yourself through naming conventions and directory layout. I'd start by deciding on a single canonical symbol per electrical function — one op-amp symbol, one regulator symbol — and treat package and tolerance variants as separate footprint assignments rather than separate symbols. That keeps the schematic readable and means a change to the symbol propagates everywhere it's used.

For the variants themselves, I'd use a strict naming scheme that encodes the differentiators, something like `PART_FAMILY-PACKAGE-GRADE-TEMP`, and keep a companion spreadsheet or CSV that maps each library entry to its manufacturer part number, datasheet revision, and lifecycle status. That mapping is what gives you traceability — the library file alone won't tell you which variant was approved for the design. I'd also split libraries by function (analog, power, digital, connectors) rather than dumping everything into one file, because a single monolithic library becomes unmergeable in version control once multiple engineers touch it.

For revision control, I'd keep the libraries in the same Git repository as the project, tag library states alongside schematic releases, and treat any library edit as a reviewable change with a commit message that references the design change that motivated it. The key discipline is: never edit a library in place for a released design. If a part needs to change, add a new variant and update the BOM, so the historical revision still resolves to the exact part that was qualified.

**Possible follow-ups:**
- How would you catch a situation where someone edits a shared symbol in a way that silently changes an already-released schematic?
- If two projects need slightly different versions of the same symbol, how do you avoid forking the library?

## Q2: How would you approach setting up a power integrity simulation workflow for a mixed-signal PCB where a high-current switching regulator and a precision analog front-end share the same power distribution network, and how would you decide which results are trustworthy enough to act on?

**Answer:** I'd structure this as a layered workflow rather than one big simulation, because PI tools are only as good as the model you feed them and it's easy to generate impressive-looking plots that don't correspond to reality.

The first layer is a DC drop analysis: model the regulator output, the copper geometry, and the load currents, and check that the IR drop and current density at the analog front-end's supply pins are within budget. This is the most trustworthy layer because it depends mostly on geometry and current, which you know well. The second layer is AC impedance: extract the PDN impedance from the regulator output through the planes and decoupling network, and look for impedance peaks in the frequency bands where the analog front-end is sensitive — its reference, its amplifier bandwidth, and any switching harmonics that could intermodulate. The third layer, if the tool supports it, is a noise-coupling or transient simulation that injects the regulator's ripple and switching edges and observes what reaches the analog supply.

The trust question is the important one. I'd treat any result as actionable only if it's insensitive to the parameters I'm least sure about — dielectric properties, capacitor ESR and ESL at frequency, via inductance, and the accuracy of the regulator's output impedance model. A practical way to test this is a sensitivity sweep: vary the uncertain parameters across a plausible range and see whether the conclusion changes. If the impedance peak moves or disappears, the model isn't telling me anything I can design against. I'd also always correlate at least one prediction against a bench measurement — inject a known load step or measure PDN impedance with a network analyzer on the first prototype — before trusting the model for the next revision.

**Possible follow-ups:**
- How would you decide how much decoupling is enough without over-designing the BOM?
- What would make you distrust a simulation result that looks clean?

## Q3: How would you approach using a spectrum analyzer with a near-field probe to locate the source of a radiated emissions failure at a specific frequency during pre-compliance testing, and how would you confirm which component is responsible?

**Answer:** I'd work from the assumption that the near-field probe tells me *where* energy is concentrated, not *what* is generating it, so the process is about narrowing the search space and then confirming with a targeted experiment.

First, I'd characterize the failing frequency itself. Is it a narrow CW-like peak, or is it broad and modulated? A narrow peak suggests a clock harmonic or a crystal-derived source; a broad or sideband-rich signature suggests a switching regulator or something with jitter. I'd also check whether the frequency shifts when I change operating modes — if it tracks a clock frequency, it's digital; if it tracks load current or switching frequency, it's the regulator.

Then I'd probe systematically. With the board powered and running the worst-case firmware mode, I'd move the probe slowly across the board, keeping orientation consistent, and map where the field at that frequency is strongest. I'd pay attention to cables and connectors too, because a common-mode current on an external cable often radiates more efficiently than the board itself, and the near-field probe will show a hot spot at the connector even if the actual source is elsewhere.

To confirm the culprit, I'd do an ablation test: disable or detune the suspected source and see whether the peak drops. For a clock, that might mean changing the frequency or gating it off in firmware. For a regulator, it might mean forcing it into a different mode or adding a temporary snubber. If the peak collapses when I remove the suspect, I've confirmed it. If it doesn't, I've eliminated it and move to the next candidate. The near-field probe gets me to a short list; the ablation test is what actually proves causation.

**Possible follow-ups:**
- How would you distinguish a near-field hot spot caused by the source from one caused by a resonant structure acting as an antenna?
- What would you do if the emission only appears when a specific cable is attached?

## Q4: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where an automated test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** I'd build this around the J-Link command-line tools and a scripted sequence, with the test harness treating the debug probe as just another instrument it controls.

The basic flow is: use `JLinkExe` or the J-Link scripting interface to connect, halt, erase and program the image, reset and run; then let the test run for a defined window; then either read a crash dump region from RAM/flash or attach with `JLinkGDBServer` and pull the fault registers and stack. For Zephyr specifically, I'd make sure the build produces a symbol file the harness can use to decode the dump, and I'd reserve a known RAM region or use the coredump subsystem so the crash data has a deterministic location.

The failure modes are where the real design work is. First, the target may not be in a state where the probe can connect — the firmware might have disabled the debug port, entered a low-power state, or be stuck in a fault loop. I'd design the harness to attempt a connect-under-reset, and to have a hardware reset line under the harness's control so it can force a known state. Second, the flash operation can fail partway, leaving a half-programmed device; the harness needs to verify the image after programming, not assume success. Third, the crash dump may be overwritten by a subsequent reset or by the test sequence itself, so the harness has to capture it before doing anything else. Fourth, the probe itself can drop off the USB bus or be left in a bad state by a previous run; I'd have the harness reset the probe at the start of each run and treat a failed connect as a test failure rather than a hang.

I'd also make the whole thing idempotent and log every step, because when an automated test fails at 2 a.m. the log is the only thing you have.

**Possible follow-ups:**
- How would you handle a target that occasionally fails to respond to the probe but works fine when you retry manually?
- What would you log to distinguish a firmware crash from a test-harness or probe failure?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** The immediate priority is to not send incomplete files, so I'd separate the schedule problem from the correctness problem and deal with correctness first.

I'd sit down with the engineer and walk through the output job together, not to assign blame but because the gap between "the Gerbers look fine" and "the release package is complete" is a real conceptual gap worth closing. The Gerbers being visually correct doesn't mean the drill table is present, and it certainly doesn't mean the assembly drawings match the current schematic revision. I'd show them the release checklist — what a fabrication and assembly package actually needs to contain — and let them see the two missing items themselves. That's more durable than me just fixing it.

Then I'd fix the outputs: regenerate the drill table, and either regenerate the assembly drawings from the current schematic revision or, if there isn't time, flag clearly to the board house and the assembly house which revision the drawings correspond to and confirm the discrepancy is only in the documentation, not the copper. If the copper itself is correct, the release can often proceed with a documented note; if there's any doubt about whether the Gerbers match the current schematic, that's a stop-and-verify situation regardless of schedule.

On the schedule side, I'd communicate early to the board house that the package is coming later than planned rather than sending something incomplete, and I'd tell the project lead what happened and what the realistic timeline is. The lesson I'd carry forward is that the output job configuration should be reviewed against a checklist as part of the release process, not left to one person's judgment on the day.

**Possible follow-ups:**
- How would you prevent this from happening on the next release without adding so much process that it slows the team down?
- If the copper turned out to be wrong too, how would you decide whether to delay the build or ship and rework?