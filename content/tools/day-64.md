# tools — Day 64

## Q1: How would you approach setting up a symbol and footprint library in KiCad for a medical device project where the same component appears in multiple variants — different package sizes, tolerance grades, or temperature ratings — so the library stays maintainable and traceable across revisions?

**Answer:** The core problem is that a single "part" in a medical BOM is really two separate concerns: the schematic symbol (functional identity) and the footprint (physical realization), and those don't map one-to-one when variants exist. I'd separate them deliberately. The symbol should represent the function — a precision op-amp, a voltage reference — with generic pin names and no package-specific pin numbering baked in. The footprint library then holds each physical variant as its own entry, named with a consistent convention that encodes package, tolerance grade, and temperature range so the variant is unambiguous from the part number alone. The link between them happens at the schematic instance level via footprint assignment, not by duplicating the symbol.

For traceability, I'd keep the library under version control as plain text (KiCad's formats are text-based, which helps), tag library revisions alongside project releases, and maintain a mapping document or database that ties each approved variant to its manufacturer part number, datasheet revision, and the design revision it was introduced in. That mapping is what a regulatory reviewer will actually ask for — they want to know which exact component was in which build. I'd also add a rule that no footprint enters the library without a verified land pattern against the manufacturer's recommended dimensions, because footprint errors are one of the most expensive classes of mistake to catch late.

The maintainability win comes from never editing a symbol to accommodate a variant. If a new package size appears, you add a footprint and a mapping entry, not a new symbol. That keeps the schematic readable and means a change to the functional symbol propagates to every variant at once.

**Possible follow-ups:**
- How would you handle a situation where a manufacturer discontinues one variant but the others remain in production?
- What checks would you put in place to catch a footprint that was created from an outdated datasheet revision?

## Q2: How would you approach setting up a power integrity simulation workflow for a mixed-signal PCB where a high-current switching regulator and a precision analog front-end share the same power distribution network, and how would you decide which results are trustworthy enough to act on?

**Answer:** I'd start by being explicit about what question the simulation is meant to answer. For a shared PDN with a switching regulator and a sensitive analog front-end, the real questions are usually: how much ripple reaches the analog rail, where are the impedance peaks in the PDN, and is there a resonance between the regulator's output network and the decoupling that could amplify noise at a specific frequency. Those are different analyses, and I'd set them up separately rather than trying to get one model to answer everything.

Practically, that means building a PDN impedance model — regulator output impedance, bulk and local decoupling with their ESR and ESL, plane capacitance, and the load current profile — and sweeping it to find where the impedance exceeds a target derived from the allowable ripple and the load's transient current. Separately, I'd run a transient simulation of the switching regulator with a realistic load step to see the actual ripple and any ringing. The analog front-end's supply rejection and its own filtering then determine how much of that ripple actually matters at the sensor.

The trustworthiness question is the important one. Simulation results are only as good as the parasitics you gave them, and at high frequency the model is usually wrong in ways that matter. So I'd treat simulation as a hypothesis generator, not a verdict: it tells me where to look and what to expect. I'd only act on a result if it's corroborated by a measurement — a bench measurement of PDN impedance with a network analyzer, or a scope measurement of ripple at the analog rail under the worst-case load condition. If simulation and measurement disagree, the measurement wins and the model gets corrected. I'd also be skeptical of any result that's sensitive to a parameter I don't actually know, like an exact capacitor ESL or a plane's high-frequency behavior.

**Possible follow-ups:**
- How would you decide the frequency range over which the PDN model needs to be accurate?
- If the simulation predicts a resonance but you can't measure it on the bench, how would you proceed?

## Q3: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where an automated test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** The goal is a fully headless, repeatable flow, so I'd build it around the J-Link command-line tools and scripting rather than the GUI. The sequence is: connect and verify target voltage and ID, erase and flash the image, reset and run, then either poll for a completion signal or wait a bounded time, and finally read out the crash state if the test failed. For the crash dump, the key is that the firmware needs to leave the fault information somewhere the debugger can retrieve it — either a reserved RAM region that survives reset, or a fault handler that writes a known structure before halting. The J-Link script then reads that region and the relevant core registers.

The failure modes are where the real engineering is. First, connection failures: the target might not be powered, the SWD lines might be held by firmware that reconfigures the pins, or the clock might not be running. The script needs to detect these and report a clear error rather than hanging. Second, flash failures: a partially written image or a verify mismatch should abort the run, not proceed to a meaningless test. Third, the "test passed but actually hung" case — a test that never completes must time out and be reported as a failure, not silently pass. Fourth, crash dump retrieval itself can fail if the fault corrupted the memory region or if a watchdog reset wiped it, so I'd design the dump region to be preserved across resets and verify that assumption.

I'd also make the whole flow idempotent and log everything — the exact image hash, the J-Link serial number, timestamps, and raw register values — because when a test fails in CI you need to reconstruct what happened without re-running it.

**Possible follow-ups:**
- How would you handle a target that occasionally fails to connect due to a firmware-controlled debug pin?
- What would you do if the crash dump region is sometimes overwritten before the debugger reads it?

## Q4: How would you approach using a spectrum analyzer with a near-field probe to locate the source of a radiated emissions failure at a specific frequency during pre-compliance testing, and how would you confirm which component is responsible?

**Answer:** The near-field probe is a localization tool, not a compliance measurement — it tells you where energy is concentrated, not whether you'll pass. So I'd use it to narrow down, then confirm with a proper setup. The process starts with characterizing the failing frequency precisely: is it a single tone, a harmonic of a known clock, or a broadband bump? That immediately suggests candidate sources. If it's a clean harmonic of a 25 MHz clock, I'm looking at clock routing, the oscillator, or a digital interface. If it's near a switching regulator's fundamental or a harmonic of it, I'm looking at the power stage and its loop area.

Then I'd probe systematically. With the board powered and running the worst-case firmware, I'd move the probe slowly across the board, watching the amplitude at the failing frequency on the analyzer, and map the hot spots. I'd pay attention to which side of the board and which layer the energy is strongest on, because that hints at whether it's a trace, a component, or a plane edge. Once I have a candidate, I'd confirm by perturbation: temporarily slowing or disabling that clock, changing the switching frequency, or adding a local shield or ferrite, and seeing whether the amplitude at that frequency drops. If it drops, I've found the source. If it doesn't, I was wrong and I keep looking.

The confirmation step matters because near-field probing is easily fooled — a strong local field can be a symptom rather than the cause, and the actual radiator might be a cable or a connector that the probe doesn't see well. So I'd always cross-check with a far-field or cable measurement before concluding.

**Possible follow-ups:**
- How would you distinguish a common-mode radiation from a differential-mode radiation using the probe?
- What would you do if the hot spot moves depending on which cable is connected?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** The immediate priority is the release — the board house deadline is real, and shipping incomplete or inconsistent outputs would be worse than a short delay. So I'd first verify the actual state of the outputs myself rather than relying on the engineer's assessment, because "the Gerbers look fine" doesn't address the drill table or the assembly revision. If the drill table is genuinely missing, that's a fabrication blocker; if the assembly drawings are stale, that's a documentation and traceability problem that matters for the device history file even if the board house doesn't strictly need it.

Then I'd handle the engineer directly and privately. The issue isn't that they made a mistake — it's that they asserted completeness without checking against the release checklist. I'd walk them through what a complete output package actually contains and why each piece matters, and I'd frame it as: the Gerbers being visually correct is necessary but not sufficient. I'd avoid making it a public correction, because the goal is to build their judgment, not to embarrass them.

Structurally, the real fix is that a release shouldn't depend on one person's confidence. I'd push for a documented output checklist and, ideally, a second-person review or an automated check that verifies the output job produces all required artifacts and that the assembly drawings match the current schematic revision. That way the next release doesn't hinge on whether someone remembered to look. I'd also make sure the engineer understands that raising uncertainty early is valued — if they weren't sure, saying so would have been the right move.

**Possible follow-ups:**
- How would you communicate the delay to the board house and to management without undermining the engineer?
- What would you put in the release checklist to prevent this class of error recurring?