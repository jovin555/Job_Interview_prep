# tools — Day 67

## Q1: How would you approach setting up a symbol and footprint library in KiCad for a medical device project where the same component appears in multiple variants — different package sizes, tolerance grades, or temperature ratings — so the library stays maintainable and traceable across revisions?

**Answer:** The core problem is that KiCad's library model is file-based rather than database-driven, so "one part, many variants" has to be handled through naming discipline and structure rather than through a relational schema. I'd start by deciding what constitutes a single library symbol versus a family. For a component that exists in several packages or tolerance grades, I'd create one generic symbol that captures the functional pinout and electrical behavior, then create package-specific footprints as separate library entries, and link them through the symbol's footprint field defaults. That way the schematic captures intent (a precision reference, say) and the footprint assignment captures the physical variant.

For naming, I'd use a strict convention that encodes the distinguishing attributes — manufacturer part family, package, tolerance or grade, and temperature range — so that a variant is identifiable from its name alone without opening it. This matters for traceability: when a reviewer or an auditor asks "which variant did we use on this board," the answer should be legible from the BOM and the library entry, not buried in a comment field.

I'd keep the library under version control as its own repository or as a submodule of the project, with the same review discipline as firmware. Every library change gets a commit message that references the design change that motivated it. For a medical device, I'd also maintain a mapping document — even a simple spreadsheet — that ties each library entry to its manufacturer part number, datasheet revision, and the design files that instantiate it. That mapping is what makes the library auditable later.

The tricky part is avoiding duplication. If two variants differ only in tolerance, I'd resist the temptation to clone the whole symbol; instead I'd parameterize what I can and document what I can't. And I'd set up a periodic library audit — a script or a checklist — that flags orphaned entries, footprints that don't match their symbol pin count, and parts that appear in the BOM but not in the library.

**Possible follow-ups:**
- How would you handle a situation where a manufacturer discontinues one variant and you need to migrate the design to a replacement without breaking existing released revisions?
- What's your approach to reviewing a library change when the change is a footprint modification rather than a symbol change?

## Q2: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where an automated test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** The goal is a fully scripted, repeatable flow: connect, erase, flash, reset, run, detect completion or fault, capture state, disconnect. J-Link gives you the command-line tools (JLinkExe/JLink.exe with a script file, or the J-Link SDK) plus the GDB server, and Zephyr's west tooling can drive flashing through `west flash` with a J-Link runner. For automation I'd lean on the scripted JLink commander for the low-level operations and wrap it in whatever the test harness uses — Python, a shell script, or a CI job.

The sequence I'd design: a script that first verifies the probe is connected and the target is powered, then performs a connect-under-reset to guarantee a known state even if the previous run left the CPU in a fault or low-power mode. Then erase and flash the image, reset, and let the target run. The harness then either polls a UART or RTT channel for a "test complete" marker, or waits a bounded time and then halts the CPU to read out the fault registers and stack.

Failure modes I'd design around: the probe not being detected (USB enumeration, driver, or another process holding the probe); the target not responding to SWD (clock or power issue, or the debug pins repurposed in firmware); a flash operation that partially completes and leaves the device in an unknown state; the test hanging so the harness waits forever; and the crash dump being overwritten by a subsequent reset before it's read. For each of these I'd want an explicit timeout, a clear error code, and a recovery step — typically a connect-under-reset followed by a full erase — so the next run starts clean rather than inheriting the previous run's state.

I'd also make the harness log everything: the J-Link commander output, the RTT or UART stream, and the raw fault register dump. When a test fails in CI at 2 a.m., the log is the only thing anyone has.

**Possible follow-ups:**
- How would you distinguish between a target that's genuinely hung and one that's simply slow to reach the test-complete marker?
- What would you change in this setup if the same harness had to run against several hardware revisions with different memory maps?

## Q3: How would you approach setting up a power integrity simulation workflow for a mixed-signal PCB where a high-current switching regulator and a precision analog front-end share the same power distribution network, and how would you decide which results are trustworthy enough to act on?

**Answer:** Power integrity simulation on a mixed-signal board is really two questions: does the PDN deliver clean DC and low-impedance AC to each load, and does the switching regulator's noise couple into the analog domain through the shared network? I'd approach it in stages, because trying to simulate everything at once produces results nobody trusts.

First, a DC drop analysis: model the copper, the via structures, and the regulator's output impedance, and check that the voltage at each load is within tolerance under worst-case current. This is relatively trustworthy because the physics is simple and the model inputs — copper thickness, trace geometry, load currents — are known.

Second, an AC impedance sweep of the PDN: the goal is to see whether the network has any anti-resonances or high-impedance peaks in the frequency range where the regulator switches or where the analog front-end is sensitive. This is where the model starts to depend on assumptions — capacitor ESR, ESL, mounting inductance, and the accuracy of the plane models. I'd treat the impedance curve as a guide rather than a verdict, and I'd validate the peaks that matter with a real measurement (a VNA or an impedance analyzer on a bare board, or a scope with a low-inductance probe on an assembled board).

Third, if the analog front-end is sensitive enough to warrant it, a noise coupling analysis: inject the regulator's switching waveform into the PDN model and look at what appears at the analog supply pins. This is the least trustworthy stage because it depends on how well the model captures the coupling paths — conducted through the planes, radiated, or through a shared ground return. I'd use it to rank coupling paths, not to predict absolute noise levels.

The decision rule for "trustworthy enough to act on": if a simulation result points to a problem that I can also see in a measurement, or that I can explain from first principles, I'll act on it. If a simulation result is the only evidence, I'll treat it as a hypothesis and design a measurement to confirm it before committing to a layout change. And I'd always keep the analog and digital supply domains separated at the source — separate regulator outputs or at least separate filtering — so that the simulation is confirming a good architecture rather than trying to rescue a bad one.

**Possible follow-ups:**
- How would you decide where to place the boundary between the analog and digital supply domains on a board where they must ultimately share a ground?
- What measurements would you take on a first prototype to validate or refute the simulation's predictions?

## Q4: How would you approach using a spectrum analyzer with a near-field probe to locate the source of a radiated emissions failure at a specific frequency during pre-compliance testing, and how would you confirm which component is responsible?

**Answer:** The near-field probe is a localization tool, not a compliance measurement — it tells you where the field is strong, not whether the product will pass. So the workflow is: find the hot spot, then identify the source, then confirm with a change.

I'd start by setting the analyzer to the failing frequency with a narrow span and a resolution bandwidth appropriate to the standard, then move the probe slowly across the board, keeping the probe orientation consistent. The probe's sensitivity depends heavily on orientation and distance, so I'd scan the same area with the probe rotated to pick up both electric and magnetic fields, and I'd note where the field peaks. A hot spot over a switching regulator's inductor or its input loop suggests a switching source; a hot spot over a clock trace or a connector suggests a digital source.

To confirm which component is responsible, I'd use a process of elimination that doesn't require desoldering: temporarily slow or stop the suspected source (change the switching frequency, disable the clock in firmware, or gate the clock) and see whether the emission at that frequency moves or disappears. If the frequency shifts when I change the switching frequency, it's the regulator. If it disappears when I disable a clock, it's the clock. If it's a harmonic, I'd check whether the frequency is an integer multiple of a known clock or switching frequency — that arithmetic often identifies the source immediately.

I'd also check whether the emission is common-mode or differential-mode by using a current probe on the cable or by comparing the field with the probe oriented along different axes. Common-mode emissions usually point to a cable or a ground return path; differential-mode emissions usually point to a loop on the board.

Once I've identified the source, I'd confirm by making a targeted change — adding a snubber, adjusting a gate resistor, adding a ferrite, or improving the return path — and re-measuring at the same frequency with the same probe position. If the emission drops, the hypothesis was right. If it doesn't, I've learned something and I keep going.

**Possible follow-ups:**
- How would you distinguish between an emission that's coming from the board itself and one that's being picked up by a cable connected to the board?
- What would you do if the hot spot is in a location you can't easily modify, such as under a shielded component?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** The immediate priority is the release: the board house is expecting files tomorrow, and shipping an incomplete or inconsistent package would either delay the build or, worse, produce boards that don't match the design intent. So I'd separate the urgent problem from the coaching problem and handle them in that order.

First, I'd verify the scope of the issue myself rather than taking the engineer's word or my own first impression. I'd open the output job, check which outputs are actually generated, and compare the assembly drawing revision against the current schematic revision. I'd also check whether the drill table is genuinely missing or just not included in the package that was sent — sometimes it's a packaging step rather than a generation step. Knowing exactly what's wrong determines whether this is a five-minute fix or a rebuild of the output job.

Then I'd fix it. If the drill table is a matter of adding an output to the job, I'd add it and regenerate. If the assembly drawings are stale, I'd regenerate them from the current schematic and verify the revision markers. I'd do this with the engineer, not instead of the engineer — the point is that they learn what "complete" means for a release package, and they see the check that would have caught it.

Once the release is out the door, I'd have a direct conversation with the engineer. The framing matters: this isn't about blame, it's about the fact that "the Gerbers look fine" is not the same as "the release package is complete." Gerbers are one output among several, and a release package has a defined contents list. I'd walk through that list with them and ask them to build a checklist — either a written one or, better, a script or an Altium output job that generates and verifies the full set. The goal is to make the correct behavior the easy behavior.

I'd also look at whether the process failed, not just the person. If there was no release checklist, that's on the process. If there was one and it wasn't followed, that's a training issue. Either way, the fix is the same: make the release package something that can be verified mechanically, so that the next release doesn't depend on anyone's confidence.

**Possible follow-ups:**
- How would you handle it if the engineer became defensive and insisted the package was fine?
- What would you put in a release checklist for a medical device PCB, and how would you make sure it actually gets used?