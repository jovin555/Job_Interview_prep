# tools — Day 50

## Q1: How would you approach setting up a board-to-board interconnect strategy for a system where a main processor board and a sensor board need to carry both high-speed digital signals and sensitive analog signals through the same connector?

**Answer:** The first step is to define the signal inventory and classify each signal by its electrical characteristics — high-speed digital (clock, data buses), low-level analog (sensor outputs, references), power, and ground. This classification drives the connector pin assignment strategy.

For the connector itself, I would look for a part with adequate pin density but also sufficient pitch to allow for proper routing and shielding. The key principle is to separate signal classes physically within the connector — don't place a 100 MHz clock adjacent to a microvolt-level sensor signal. I would assign ground pins strategically between signal groups to provide shielding and a low-impedance return path. Ideally, I'd use a connector with dedicated ground pins interspersed, or plan for a ground plane on both boards that connects through multiple pins.

For high-speed digital pairs, I would route them as controlled-impedance differential pairs right up to the connector pins, and ensure the connector's rated bandwidth exceeds the signal's highest significant harmonic. For analog signals, I would consider guarding — placing ground traces or pins on either side of critical analog lines. Power pins should be grouped and adequately derated for current, with multiple parallel pins for higher-current rails to reduce inductance.

On the PCB side, the return current path is critical. Each board needs a solid ground plane, and the connector's ground pins must provide a low-inductance path between them. If the two boards are on different ground potentials, that's a separate problem to solve before the interconnect design matters.

Finally, I would review the complete path — driver output, trace on board A, connector, trace on board B, receiver input — and simulate or measure the impedance discontinuities at the connector. A connector is always a discontinuity; the goal is to make it acceptable for the signal's rise time and noise budget.

**Possible follow-ups:** How would you decide whether to use a mezzanine connector versus a cable assembly? What additional considerations apply if the boards are in a sealed enclosure with limited airflow?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** I would start by establishing a repeatable test setup. The device should be in its normal operating configuration, running the switching regulator at its typical load. I'd use two or more oscilloscope channels simultaneously — one monitoring the switching node or output ripple of the regulator, and another monitoring the analog sensor's output or its supply rail. The key is time-correlated measurement: triggering on the switching regulator's switching edge and looking for correlated activity on the analog channel.

To separate coupling mechanisms, I would use a systematic elimination approach. First, check conducted coupling on the power rails: measure the analog sensor's supply pin directly with a short ground spring (not a long ground lead), looking for ripple at the switching frequency or its harmonics. If present, that suggests inadequate filtering or poor power distribution. Next, check ground-plane coupling: measure between the sensor's ground pin and the regulator's ground return, again with careful probing technique. Voltage differences here indicate ground bounce or inadequate ground plane integrity.

For radiated coupling, I would use a near-field probe connected to a spectrum analyzer or the oscilloscope's FFT function. Move the probe along the board between the regulator and the sensor, looking for field strength at the switching frequency. If the coupling disappears when the probe is lifted away from the board but the sensor noise remains, that points away from radiated coupling.

A useful discriminating test is to temporarily disable the switching regulator and power the analog section from a linear supply — if the noise disappears, the coupling source is confirmed. Then, to distinguish conducted from radiated, I might add ferrite beads or additional filtering at the sensor's supply pin. If the noise persists with clean power, the coupling is likely radiated or through the ground plane.

The probing technique matters enormously here. Using a 10x passive probe with a long ground lead will pick up loop-antenna effects and give misleading results. I would use short ground springs or tip-and-barrel adapters, and ideally active or differential probes for low-level signals.

**Possible follow-ups:** How would you determine whether the noise is common-mode or differential-mode at the sensor input? What if the noise only appears when the sensor is actively sampling rather than in standby?

---

## Q3: How would you approach setting up a component library management strategy in KiCad for a medical device project that needs to maintain strict revision control and regulatory traceability, given that KiCad's library format is file-based rather than database-driven?

**Answer:** KiCad's file-based libraries are actually well-suited to Git-based version control, which is the foundation of the strategy. The key is establishing a disciplined structure and workflow from the start.

I would organize libraries into three tiers: vendor-supplied libraries (kept read-only, updated only with documented vendor revisions), project-specific libraries (components created or modified for this project), and a shared internal library (approved components reused across projects). Each tier has different change-control rules.

For each component, the library entry needs to carry traceability metadata. KiCad allows custom fields in symbols and footprints — I would add fields for manufacturer part number, datasheet revision, approval status, and a unique internal component ID. This ID links to the component's entry in the regulatory traceability system (which might be a separate database or document management system). The schematic and PCB files reference this ID, creating an auditable chain.

The workflow would be: a component request goes through review and approval, the approved component is added to the library with its metadata, and the library is committed to Git with a meaningful commit message referencing the approval record. Branch protection rules would require pull requests for library changes, and CI could run ERC/DRC checks on any design that uses the library.

For revision control specifically, I would use a structured Git workflow. The library repository has a main branch that only contains approved components. Feature branches are used for new component development. Tags mark regulatory submission points. Each component file's history in Git provides the complete audit trail of when and why it changed.

One practical consideration: KiCad's library format stores symbol and footprint data as plain text, which means Git diffs are meaningful and reviewable. This is a significant advantage over binary formats. I would ensure that library files are consistently formatted and that the repository excludes transient files.

Finally, I would document the entire process — the library structure, the approval workflow, the metadata schema, and the Git conventions — in a design control document that references the regulatory requirements being satisfied.

**Possible follow-ups:** How would you handle a situation where a vendor updates a component's footprint without changing the part number? How would you manage library access for external contractors who need to work on the design?

---

## Q4: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** The core requirement is reproducibility — the ability to rebuild the exact firmware binary from a known state and prove that the process is controlled. I would build this around three pillars: version-controlled source, deterministic builds, and auditable artifact generation.

For version control, the source tree — including the Zephyr RTOS version, all application code, device tree overlays, and configuration files — lives in Git. The Zephyr manifest file (west.yml) pins the exact revision of Zephyr and all modules. This is critical because Zephyr is a fast-moving project; without pinning, a rebuild months later could pull in different code.

For deterministic builds, I would use a containerized build environment. The container image specifies the exact toolchain version, Python version, and all build dependencies. The build process runs inside this container, eliminating host-environment variability. The west build command is invoked with a fixed configuration, and the build output includes a manifest of all source files and their hashes.

For auditable artifacts, the build process generates more than just the binary. I would produce: the firmware binary with a computed SHA-256 hash, a build manifest listing every source file and its Git commit hash, the west manifest with all module revisions, the toolchain version, and the build configuration (prj.conf, device tree overlays). This manifest becomes part of the design history file.

The release process would use Git tags to mark release candidates. A release candidate is built, tested, and if it passes, the tag is signed and the artifacts are archived in a document management system. The build script itself is version-controlled and reviewed — it's part of the regulated process.

For regulatory traceability, each release artifact links back to the source state via the manifest. An auditor can take the release binary, check its hash, and rebuild it from the tagged source using the documented container image. This satisfies the requirement for design traceability without relying on anyone's memory of how the build was done.

One additional consideration: the build should be reproducible on a clean system. I would periodically verify this by checking out the tagged source in a fresh container and confirming the binary hash matches the archived release.

**Possible follow-ups:** How would you handle a situation where a compiler update changes code generation and produces a different binary from the same source? What build artifacts would you archive for a regulatory submission?

---

## Q5: (Behavioral) Imagine you are leading a project where a junior engineer has been tasked with setting up the automated firmware test environment for a medical device. On the day before a critical regression test run, you discover that the engineer has configured the test script to skip the safety-critical test cases because they were failing intermittently, and the engineer is confident this is acceptable because "the failures are just timing issues in the test harness, not real bugs." The test results will be used for a regulatory submission milestone. How would you handle this situation?

**Answer:** This situation requires immediate action on two fronts: the technical decision about the test run, and the coaching conversation with the engineer. Both are urgent, but the test run decision comes first because of the regulatory implications.

My immediate action would be to stop the test run and restore the safety-critical test cases. Skipping them is not acceptable under any circumstances when the results feed a regulatory submission. An intermittent failure is exactly the kind of issue that needs investigation, not suppression. I would explain that the test results must reflect the true state of the system — if safety-critical tests are failing intermittently, that finding needs to be documented, investigated, and resolved, not hidden.

I would then work with the engineer to understand the intermittent failures. The first question is whether the failures are indeed test harness issues or actual product issues. A timing-sensitive test that fails intermittently could indicate a real race condition in the firmware, a hardware timing margin problem, or a test synchronization issue. The way to distinguish these is systematic debugging, not assumption. I would guide the engineer through collecting data: capturing the failure logs, correlating with system state, and attempting to reproduce the failure under controlled conditions.

For the immediate test run, I would propose a path forward: run the full test suite including the safety-critical cases, document any failures with full logs, and treat the run as a diagnostic session rather than a pass/fail gate. The regulatory milestone may need to be adjusted, but that decision belongs to the project leadership with full information — not to an engineer who has decided the failures don't matter.

The coaching conversation is equally important. The engineer's decision to skip tests reveals a misunderstanding of the role of testing in a regulated environment. I would explain that in medical device development, the test results are evidence. If the evidence is filtered or incomplete, the regulatory submission is compromised, and more importantly, real safety issues could be missed. The goal is not to make tests pass — it's to understand the system's true behavior. I would also acknowledge the engineer's intent (trying to keep the project on schedule) while making clear that this approach creates far greater risk than a schedule slip.

Finally, I would review the test configuration process to understand how the engineer had the authority to skip tests, and implement safeguards — such as requiring peer review of test script changes and making the skip list visible in the test report — to prevent this from happening again.

**Possible follow-ups:** How would you handle the situation if the engineer had already run the tests with the safety-critical cases skipped and the results were already shared with management? What would you do if the intermittent failures turn out to be a real firmware bug that will take weeks to fix, and the regulatory submission deadline is fixed?