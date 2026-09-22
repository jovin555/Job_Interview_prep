# tools — Day 63

## Q1: How would you approach setting up a symbol and footprint library in KiCad for a medical device project where the same component appears in multiple variants — different package sizes, tolerance grades, or temperature ratings — so the library stays maintainable and traceable across revisions?

**Answer:** The core problem is that a single "part" in a medical BOM is really two separate concerns: the schematic symbol (functional identity — what the pinout means) and the footprint (physical identity — how it lands on the board). When one component family spans multiple packages, tolerances, or temperature grades, the cleanest structure is to decouple those two layers rather than cloning a full symbol+footprint pair for every variant.

In KiCad specifically, I'd organize the library so that the symbol represents the function (e.g., a generic op-amp or regulator symbol with the correct pin names), and the footprint is a separate library entry keyed to the specific package. The variant selection then lives in the BOM fields — manufacturer part number, tolerance, temperature grade, and a house part number — rather than in the symbol name. That keeps the schematic readable and means a package change doesn't force a schematic rework.

For traceability, the key discipline is that every library part carries a set of mandatory fields: a unique internal part number, the manufacturer part number, a revision or date code, a datasheet reference, and a lifecycle status. Because KiCad libraries are file-based rather than database-driven, I'd treat the library files themselves as version-controlled artifacts — committed to the same repository as the design, with changes going through review rather than being edited in place. A simple approach is to keep a "library change log" or rely on Git history plus a naming convention that encodes the revision.

The other important habit is to never let a design reference a library part by a loose, editable name. Once a part is used in a released design, its definition is effectively frozen; changes create a new revision of the part, and the design is updated deliberately. This is what makes the library auditable — you can always answer "what exactly was on the board at revision X."

**Possible follow-ups:**
- How would you catch a footprint-to-schematic mismatch before it reaches fabrication, given that KiCad won't always flag a wrong-but-valid footprint?
- If two engineers edit the same library file concurrently, how would you prevent silent overwrites?

## Q2: How would you approach setting up a power integrity (PI) simulation workflow for a mixed-signal PCB where a high-current switching regulator and a precision analog front-end share the same power distribution network, and how would you decide which results are trustworthy enough to act on?

**Answer:** The goal of PI simulation here is to answer two questions: how much ripple and noise actually reaches the analog front-end, and whether the power distribution network (PDN) impedance is low enough across the relevant frequency band that the analog supply isn't being modulated by the switching regulator's current draw.

I'd start by defining the PDN as a network: the regulator output, the bulk and decoupling capacitors with their ESR/ESL, the plane and trace inductance, and the load current profile of both the digital/switching side and the analog side. The simulation then sweeps impedance versus frequency and, separately, runs a transient or AC analysis with the regulator's switching ripple as the excitation. The output of interest is the voltage noise at the analog supply pins, not at the regulator output — the difference between those two points is exactly what the decoupling network is supposed to manage.

The trustworthiness question is the hard part, and it comes down to model fidelity. A PI simulation is only as good as the capacitor models (including ESR and ESL, not just nominal capacitance), the plane parasitics, and the load model. If any of those are idealized, the result is optimistic. So I'd calibrate: build the model, then measure the real board with a scope and a low-inductance probe at the same nodes, and compare. If the simulation and measurement disagree, the model is wrong somewhere — usually the parasitics or the load — and I'd fix the model before trusting any "what-if" runs.

I'd only act on simulation results that (a) reproduce a measured behavior, or (b) predict a trend that's robust to reasonable model error — for example, "adding a capacitor here lowers impedance at this frequency" is a safe conclusion even if the absolute numbers are off. I would not act on a single absolute number like "ripple will be 3 mV" unless it's been correlated against measurement.

**Possible follow-ups:**
- How would you decide where to place the boundary between "on-die/on-package" decoupling and board-level decoupling in the model?
- If the simulation says the PDN is fine but the bench measurement shows excess noise at the analog supply, where would you look first?

## Q3: How would you approach using a spectrum analyzer with a near-field probe to locate the source of a radiated emissions failure at a specific frequency during pre-compliance testing, and how would you confirm which component is responsible?

**Answer:** The near-field probe is a localization tool, not a compliance measurement — it tells you where energy is concentrated, not whether the product passes. So the workflow is: first confirm the failure is real and reproducible in a proper setup, then use the probe to hunt.

I'd start by establishing the failing frequency precisely and noting whether it's a narrowband tone or a broad hump. A narrowband tone usually points to a clock or a switching harmonic; a broad hump often points to a switching edge or a cable resonance. Then I'd sweep the probe slowly across the board, keeping the probe orientation and height consistent so the readings are comparable, and map the field strength. The probe's orientation matters — a magnetic loop probe is sensitive to current loops, an E-field probe to voltage nodes — so I'd use the type that matches the suspected mechanism.

Once I have a hotspot, I confirm the source by correlation, not by assumption. The strongest confirmation is to change the suspected source's behavior and watch the emission move: shift the clock frequency slightly, disable the switching regulator, or change its load, and see whether the tone tracks. If the tone follows the change, that's the source. A second confirmation is to look at the harmonic structure — a clock at a known fundamental produces harmonics at integer multiples, while a switching regulator's spectrum depends on its switching frequency and duty cycle. Matching the observed harmonic spacing to a candidate source is strong evidence.

Finally, I'd remember that near-field hotspots don't always correspond to far-field failures — the actual radiator may be a cable or a connector that the near-field probe can't see well. So if the probe doesn't find an obvious source, I'd suspect a common-mode current on an external cable and check that path.

**Possible follow-ups:**
- How would you distinguish a near-field hotspot caused by the source from one caused by a resonant structure acting as an antenna?
- What would you do if disabling the suspected source changes the emission but doesn't eliminate it?

## Q4: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where an automated test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** The goal is a deterministic, repeatable sequence: connect, erase/program, reset, run, detect completion or fault, and extract the crash state — all driven by a script rather than a human clicking in an IDE.

I'd use the J-Link command-line tools (JLinkExe/JLink Commander scripts, or the J-Link SDK) so the whole flow is scriptable and version-controlled. The sequence would be: establish a stable connection at a known interface speed, program the image, verify it, reset and run, then either poll a known memory location or use the target's output (RTT or a UART log) to detect test completion. For crash capture, I'd configure the target so that a fault handler writes a known signature and a register/memory snapshot to a reserved RAM region, and the harness reads that region back over the debug interface after the fault. That avoids relying on a live debugger halt, which is fragile in automation.

The failure modes I'd design around are the ones that make automated flashing flaky:

- **Connection loss or target not responding** — the script must time out and retry rather than hang forever, and it must report a clear failure rather than a false pass.
- **Flash not fully erased or a partial program** — always verify after programming, and treat verification failure as a hard stop.
- **The target running away or resetting mid-test** — use a watchdog or a heartbeat the harness can observe, so a hung target is detected instead of silently passing.
- **Debug interface disabled by firmware** — if the application reconfigures the SWD/JTAG pins or enters a low-power state, the debugger may lose the target. The harness needs a recovery path (e.g., connect-under-reset) and the firmware should keep the debug interface alive during test builds.
- **Race between reset and connect** — connect-under-reset or a defined reset strategy avoids the target booting before the debugger is attached.

The overarching principle is that the harness must distinguish "test passed," "test failed," and "test didn't run" — conflating the last two is how automation gives false confidence.

**Possible follow-ups:**
- How would you make the crash-dump extraction robust if the fault corrupts the RAM region you reserved for the snapshot?
- How would you keep the debug interface available in a build that also needs to meet a low-power requirement?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** The immediate priority is the release — a board house deadline doesn't move, and shipping incomplete or inconsistent outputs is worse than a short delay. So I'd separate the urgent from the important: first, get a correct, complete output set generated and verified, even if that means a late night; second, address the process gap that let this happen.

In the moment, I'd avoid framing it as "you were wrong." The engineer's confidence is based on a real observation — the Gerbers do look fine — but "the Gerbers look fine" isn't the same as "the release package is complete and consistent." That's the teaching point, and it's more effective delivered as a shared standard than as a correction. I'd walk through the output job together: what a complete fabrication and assembly package actually contains (Gerbers, drill files and drill table, NC drill, assembly drawings, BOM, pick-and-place, and the revision linkage between them), and why the drill table and revision consistency matter for the fabricator and for our own traceability. Then we'd regenerate and verify against a checklist.

For the process fix, the root cause is that the release package had no independent verification step. A single person generating and self-approving outputs is a single point of failure, especially on a regulated product where the released artifacts are part of the design history. I'd introduce a release checklist and a second-person review of the output package before it goes out — not as bureaucracy, but because the cost of catching a missing drill table internally is minutes, and the cost of catching it at the board house is a respin or a delay.

I'd also make sure the engineer isn't left feeling blamed. The failure was in the process, not the person, and the right outcome is that the team now has a checklist that prevents it recurring.

**Possible follow-ups:**
- How would you verify that the assembly drawings and the schematic are actually the same revision, rather than trusting the file names?
- If the board house had already started fabrication when you found the problem, how would your approach change?