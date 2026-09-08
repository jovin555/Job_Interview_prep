# tools — Day 49

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** For a medical device, the build process itself becomes part of the design history file, so reproducibility and traceability are the primary drivers. I'd start by establishing a single source of truth for the toolchain — pinning the Zephyr SDK version, the west workspace manifest, and any Python dependencies to specific commits or tags. The west manifest is particularly important because it locks the Zephyr kernel version and all module revisions, so a build performed six months later produces byte-identical output.

The build itself should be driven by a script or CI pipeline that runs in a clean environment — ideally a container or dedicated build machine — so local developer environment variations can't affect the artifact. The script would capture the git commit hash of the application code, the west manifest revision, and the toolchain version, then embed these into the firmware image itself, perhaps in a dedicated metadata section or via build-time defines. This way, the firmware can report its exact provenance at runtime.

For regulatory traceability, I'd generate a build manifest alongside the binary that records: the source commit, the manifest revision, the toolchain version, compiler flags, and a checksum of the output. This manifest gets stored with the release artifacts in a controlled repository. The release process would also tag the repository with a version number that maps to the regulatory submission. I'd also configure the build to fail on warnings and to produce deterministic builds — setting timestamps explicitly and disabling any build-path embedding — so that rebuilding from the same commit yields the same binary, which is essential for verifying that the released artifact matches what was tested.

**Possible follow-ups:**
- How would you handle signing or encryption of firmware images in this pipeline?
- What would you do if you needed to reproduce a build from six months ago and the original toolchain is no longer available?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** I'd approach this systematically, starting with time-domain measurements to establish correlation, then moving to frequency domain to identify the coupling mechanism. First, I'd set up the oscilloscope to trigger on the switching node of the regulator — using a differential probe across the inductor or the switch node to ground — and simultaneously monitor the analog sensor's output or its supply rail. The key is to look for noise events on the analog side that are time-correlated with the switching transitions. If the noise appears at the switching frequency and its harmonics, that confirms the regulator is the source.

To determine the coupling path, I'd use a combination of techniques. For conducted coupling, I'd measure the noise on the shared supply rail or ground at multiple points — probing the regulator output, the sensor's supply pin, and the ground plane at both locations. A significant voltage difference between the regulator's ground and the sensor's ground, especially at the switching frequency, suggests ground bounce or inadequate grounding. I'd also check the supply rail with a low-inductance probing technique — using a short ground spring rather than the long ground lead — to avoid picking up radiated noise in the probe itself.

For radiated coupling, I'd use a near-field probe connected to a spectrum analyzer to sniff around the board, particularly near the inductor, the switching node trace, and the analog sensor traces. If the near-field probe picks up the switching frequency near the analog circuitry, that suggests radiated coupling. To differentiate between radiated and conducted paths, I could temporarily lift the analog section's ground connection (if a ferrite bead or jumper exists) or power the analog section from a clean bench supply — if the noise disappears, it's conducted through the supply; if it persists, it's radiated or ground-coupled.

For ground plane coupling specifically, I'd measure the voltage difference between two ground points using a differential probe with the probe tips placed very close together. A common technique is to probe across a slot or a narrow section of the ground plane to see if there's a measurable impedance drop at the switching frequency. I'd also look at whether the noise amplitude changes when I move the scope probe ground connection to different locations — if the measured noise varies significantly with probe ground placement, that's a strong indicator of ground-plane noise.

**Possible follow-ups:**
- How would you distinguish between noise that's coupled through the ground plane versus noise that's coupled through the power supply trace?
- What modifications would you make to the PCB layout if you determined the coupling was primarily through the ground plane?

---

## Q3: How would you approach setting up a component library management strategy in KiCad for a medical device project that needs to maintain strict revision control and regulatory traceability, given that KiCad's library format is file-based rather than database-driven?

**Answer:** KiCad's file-based library format actually lends itself well to version control, but it requires discipline. I'd structure the libraries as a separate repository — or a clearly separated directory tree within the main project repo — containing schematic symbols, footprints, and 3D models. Each component would have its own directory or clearly named files, and I'd establish a naming convention that includes the component value, package, and a revision suffix.

The key for regulatory traceability is that every component in the design must be traceable to a specific library revision. I'd achieve this by tagging library releases — every time a library changes, it gets a version tag, and the project file records which library version was used. KiCad's project file stores the library table references, so as long as the library table is version-controlled and the project points to specific library paths, you can reconstruct the exact component definitions used in any design revision.

For the library content itself, I'd include key metadata in the symbol and footprint fields: manufacturer part number, datasheet revision, and a unique component ID that maps to the company's internal component database. The footprint files should also embed the source of the footprint — whether it was created internally or derived from the manufacturer's recommended layout — and the date of the last review. When a component is modified, the change should go through a review process similar to code review, with the commit message documenting what changed and why.

I'd also set up KiCad's ERC and DRC to check for library consistency — for example, verifying that the footprint assigned to a symbol matches the expected pin count and pin names. This catches errors where a symbol was updated but the footprint wasn't, which is a common source of board respins. For regulatory submissions, the library repository's commit history provides the audit trail showing when each component was added, modified, or reviewed.

**Possible follow-ups:**
- How would you handle a situation where a manufacturer updates a component's recommended footprint, and you need to decide whether to update the library?
- What metadata would you consider essential to embed in a symbol or footprint for regulatory traceability?

---

## Q4: How would you approach using a logic analyzer to debug a SPI bus where the master device intermittently fails to receive data from a slave, but only after the system has been running for several hours and the temperature inside the enclosure has risen?

**Answer:** This is a classic intermittent failure that's likely temperature-related, so I'd approach it as a thermal + timing problem rather than a pure protocol problem. First, I'd set up the logic analyzer to capture the SPI bus continuously — or at least with a deep buffer — and trigger on the specific failure condition, which is the master not receiving expected data. I'd capture all four SPI lines: clock, MOSI, MISO, and chip select.

The key is to look at timing margins, not just protocol correctness. I'd examine the setup and hold times relative to the clock edges, particularly on the MISO line since that's the data path that's failing. As the system heats up, trace impedance changes, driver output impedance changes, and the slave's internal timing can shift. I'd look for the MISO data transitions getting closer to the clock edge as the system warms up — if the data is changing right at the sampling edge, that's a marginal timing issue that only manifests at temperature.

I'd also check for signal integrity issues that worsen with temperature: ringing on the clock line, slow rise times on MISO due to a weak pull-up or excessive trace capacitance, or ground bounce that shifts the logic thresholds. The logic analyzer's threshold settings matter here — I'd set them to the actual logic family thresholds rather than the default 1.5V, and I'd compare the captured waveforms against the datasheet's timing requirements.

To correlate with temperature, I'd run the system in a thermal chamber or use a heat gun to accelerate the temperature rise while monitoring the bus. I'd also add a thermocouple to the slave device and the master's SPI peripheral to correlate the failure onset with specific temperatures. If the failure is timing-related, I might see the MISO data valid window shrinking as temperature rises — the data transitions might be moving relative to the clock edge.

If the protocol decode looks correct but data is still wrong, I'd check for occasional bit errors — a single corrupted bit in a multi-byte transaction — which would point to noise rather than timing. I'd also verify that the chip select timing is correct, since some slaves have a maximum CS high time or need a minimum CS low time between transactions, and these can be affected by firmware timing changes under load.

**Possible follow-ups:**
- How would you distinguish between a timing margin issue and a noise issue if both could cause intermittent data corruption?
- What changes would you consider making to the hardware design if you confirmed the issue was marginal setup/hold time at elevated temperature?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the SPI protocol than what the hardware actually implements — the firmware is expecting a specific clock polarity and phase (CPOL=0, CPHA=0), but the hardware's SPI peripheral is configured for CPOL=1, CPHA=1. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first priority is to stop the clock on assumptions and get both teams to verify their claims against the actual hardware and code, not against what they believe is correct. I'd call an immediate meeting with both the firmware lead and the hardware lead, and I'd bring the schematic, the microcontroller datasheet, and the firmware's SPI configuration code to the table. The goal isn't to assign blame but to establish ground truth quickly.

I'd start by having the firmware team show me the exact register configuration or device tree settings they're using, and I'd have the hardware team show me the schematic connections and the microcontroller's SPI peripheral documentation. The discrepancy should be resolvable in minutes by comparing the actual configuration against the datasheet's timing diagram. If the firmware is using CPOL=1, CPHA=1, that means the clock idles high and data is sampled on the falling edge — I'd ask them to trace through the timing diagram with the hardware's actual connections to see which mode the slave device requires.

Once we've confirmed which mode is correct, the question becomes: what's the fastest safe path to fix it? If the firmware can be changed to match the hardware — and the change is a simple configuration parameter — that's likely the quickest fix, but it needs to go through the proper change control process. I'd have the firmware team make the change, then run a focused test on the SPI communication with a logic analyzer to verify the actual bus timing matches the expected mode before integration testing starts.

If there's any ambiguity about which side is correct — for example, if the slave device's datasheet is unclear about its required SPI mode — I'd recommend a quick bench test with a logic analyzer to capture the actual bus behavior and compare it against both the slave's requirements and the master's configuration. This removes all doubt and gives us a definitive answer.

Throughout this, I'd emphasize that the process matters as much as the fix. Both teams need to understand how this discrepancy happened — likely a miscommunication during the design phase or a last-minute change that wasn't communicated — so we can prevent it from recurring. After the immediate issue is resolved, I'd suggest a review of how hardware-firmware interface specifications are documented and communicated, perhaps establishing a formal interface control document for the SPI bus that both teams sign off on.

**Possible follow-ups:**
- How would you handle the situation if the firmware team insists their configuration is correct because it works on the evaluation board?
- What would you do if changing the firmware to match the hardware would require significant rework and potentially delay the integration testing start date?