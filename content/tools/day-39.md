# tools — Day 39

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** For a medical device, the build process itself becomes part of the design history file, so reproducibility and traceability are the primary goals. I'd start by establishing a clean, version-controlled build environment — this means pinning the Zephyr SDK, toolchain, and all dependencies to specific versions, ideally using a container or a dedicated build machine so that builds are deterministic regardless of who runs them or when.

The west build system supports this well. I'd create a manifest file that pins the Zephyr version and all modules to specific commits or tags, rather than floating branches. For the application itself, I'd use Kconfig and devicetree overlays to define the exact configuration for each build variant, and I'd commit the resulting `.config` and generated devicetree files as build artifacts.

For auditability, I'd tag each release with a semantic version and record the exact commit hash of the source tree, the manifest, and the toolchain version. The build script should generate a build manifest file that captures all of this metadata, along with checksums of the output binaries. This manifest gets stored alongside the firmware image in the document control system. I'd also configure the build to fail on warnings and to produce a build log that can be reviewed.

One important detail is making the build script itself part of the version-controlled repository, so that the process is reproducible and reviewable. The script should be idempotent — running it twice on the same commit should produce byte-identical output. I'd verify this by building from a clean checkout and comparing checksums.

**Possible follow-ups:**
- How would you handle signing the firmware image and integrating that into the build process?
- What would you do if you needed to reproduce a build from six months ago, and the original toolchain version is no longer available?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** This is a classic mixed-signal debugging scenario. I'd start by establishing a baseline — measure the analog sensor output with the switching regulator disabled, then enable it and measure the difference. The key is to use proper probing techniques: for the analog side, use a low-noise active probe or a passive probe with a ground spring rather than the long ground lead, which can pick up radiated noise and give false readings.

For the switching regulator, I'd probe the switch node, the inductor, and the input/output rails. The switch node is the noisiest point, and its waveform tells you the fundamental switching frequency and the ringing frequency. I'd use the oscilloscope's FFT function to look at the spectral content of both the switch node and the analog sensor output — if the same frequency peaks appear in both, that confirms coupling.

To distinguish conducted versus radiated versus ground-plane coupling, I'd use a systematic approach. First, check conducted coupling by measuring the noise on the power rails feeding the analog sensor — if the ripple on the analog supply correlates with the sensor noise, that's conducted. I'd also look at the ground potential between the regulator's ground and the sensor's ground using a differential probe; if there's a measurable voltage difference that tracks the switching activity, that points to ground-plane coupling.

For radiated coupling, I'd use a near-field probe connected to the oscilloscope's input, or a spectrum analyzer, to sniff around the board — particularly near the inductor, the switch node trace, and the analog signal traces. If the near-field probe picks up the switching frequency near the analog traces, that suggests radiated coupling.

To isolate ground-plane coupling specifically, I can temporarily lift the analog ground connection and use a jumper wire to a different ground point — if the noise changes significantly, ground coupling is involved. Another technique is to add a small ferrite bead or resistor in the analog supply path and see if the noise changes; if it does, it's conducted.

**Possible follow-ups:**
- How would you set up the oscilloscope's trigger to capture intermittent noise events?
- What if the noise only appears when the system is under load — how would you modify your approach?

---

## Q3: How would you approach setting up a hierarchical schematic design in Altium Designer for a complex mixed-signal medical device that has multiple identical sensor channels, and how would you ensure that design changes propagate correctly to all instances?

**Answer:** Hierarchical design is the right approach when you have repeated blocks, and Altium handles this well with sheet symbols and multi-channel design. I'd start by creating a single "sensor front-end" schematic sheet that contains the complete signal chain — the sensor interface, signal conditioning, ADC, and any local power filtering. This sheet gets defined with proper port labels for all external connections: power, ground, analog output, digital control signals, and any reference voltages.

In the parent sheet, I'd instantiate this as a multi-channel sheet symbol with the repeat keyword, like `repeat(sensor_front_end, 1, 4)` for four channels. Altium then automatically generates channel designators (e.g., `sensor_front_end_1`, `sensor_front_end_2`, etc.) for components and nets. This is where the power of the tool comes in — you design once and get consistent, repeatable instances.

For design changes to propagate correctly, the key is to make all edits in the child sheet. When you modify the child sheet, Altium updates all instances automatically. However, there are some important gotchas. First, I'd use net labels carefully — a net labeled `VCC` in the child sheet will connect to the global `VCC` net, which is usually what you want for power, but for signals that should be per-channel, I'd use the repeat feature for net names, like `repeat(ADC_CS)`, so each channel gets its own `ADC_CS_1`, `ADC_CS_2`, etc.

I'd also pay attention to component designators — Altium handles the channel suffixing automatically, but I'd verify that the annotation is set to "multi-channel" mode so that components get unique designators across instances. For the PCB layout, I'd use the channel offset feature to place the four channels in a repeating pattern, which makes the layout cleaner and more predictable.

Before committing to this approach, I'd run a design rule check on the hierarchical structure itself — verifying that all ports are properly connected, there are no unconnected ports, and that the repeat nets are correctly generated. I'd also generate a cross-reference report to verify the net connectivity across the hierarchy.

**Possible follow-ups:**
- How would you handle a situation where one channel needs a slightly different component value than the others?
- How would you manage the PCB layout for these repeated channels to keep them consistent?

---

## Q4: How would you approach using a logic analyzer to debug a SPI bus where the master device intermittently fails to receive data from a slave, but only after the system has been running for several hours and the temperature inside the enclosure has risen?

**Answer:** This is a classic intermittent failure that's likely temperature-related, and the logic analyzer is the right tool because it lets you capture the protocol-level behavior over extended periods. I'd start by setting up the logic analyzer to capture all four SPI signals — clock, MOSI, MISO, and chip select — at a sample rate at least 4-5 times the SPI clock frequency. For a 20 MHz SPI bus, that means at least 100 MS/s, which most modern logic analyzers can handle.

The key is to capture the failure when it happens, so I'd set up the logic analyzer with a deep buffer and trigger on the failure condition. Since the failure is that the master doesn't receive data, I'd trigger on either a missing MISO response or a chip select assertion without a corresponding MISO transaction. Some logic analyzers allow protocol-level triggering on SPI errors, which would be ideal.

I'd also instrument the system to log temperature alongside the SPI captures. A simple approach is to place a thermocouple near the slave device and log the temperature with a data acquisition system, timestamped to correlate with the logic analyzer captures. This confirms the temperature correlation and helps narrow down the mechanism.

When analyzing the captured data, I'd look at several things. First, check the timing margins — is the MISO data valid relative to the clock edges? As temperature rises, propagation delays through the slave device increase, and if the master is sampling too close to the data transition edge, it might occasionally read the wrong value. I'd measure the setup and hold times from the capture and compare them to the master's datasheet requirements.

Second, I'd look at signal integrity — is the MISO line showing ringing, overshoot, or slow edges that get worse with temperature? The logic analyzer's threshold crossing points can give you a rough idea of edge rates, though for precise analog measurements I'd use an oscilloscope with a differential probe.

Third, I'd check the chip select timing — is the slave being deselected too quickly after the last clock edge, or is there a glitch on chip select that resets the slave's internal state machine?

If the timing margins are marginal, the fix might be to reduce the SPI clock frequency, add a small series resistor to slow the edges, or adjust the master's sampling point. If it's a signal integrity issue, I'd look at the PCB layout — trace length, impedance matching, and grounding.

**Possible follow-ups:**
- How would you set up the logic analyzer to capture a failure that happens only once every few hours, without filling up the buffer?
- What if the logic analyzer's presence changes the timing enough to mask the problem?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different register map for a sensor than what the hardware actually implements — the firmware is reading from register addresses that don't exist on the hardware's sensor variant, but the firmware team says their code works on the evaluation board. The PCB is already in fabrication, and the project is on a tight schedule. How would you handle this situation?

**Answer:** This is a serious integration issue, but it's also a common one, and the key is to address it systematically without assigning blame. The first thing I'd do is verify the facts — I'd pull up the sensor datasheet for the exact hardware variant on the PCB and compare the register map to what the firmware is using. I'd also check the evaluation board's sensor variant to confirm whether it's actually different. Sometimes the firmware team is right and the hardware team made an error in the schematic or BOM; sometimes the firmware is using a different variant's datasheet. I need to establish the ground truth before taking action.

Once I've confirmed the discrepancy, I'd assess the impact. If the firmware is reading from registers that don't exist, the sensor will likely return default or garbage values, or the I2C/SPI transaction might NACK. The question is whether this affects the device's safety-critical functions or just some non-critical feature. I'd work with the team to map out which sensor readings are affected and what the clinical impact would be.

Then I'd look at the options. The PCB is already in fabrication, so changing the hardware isn't feasible without a significant schedule impact. The most practical option is usually to modify the firmware to use the correct register map for the hardware's sensor variant. This might be a simple change if the register addresses are similar, or it might require more work if the register layouts are substantially different. I'd also check if the sensor variant on the PCB has a different initialization sequence or requires different configuration registers.

I'd bring the firmware and hardware teams together to review the sensor datasheet side by side and agree on the correct register map. I'd also verify that the firmware team's evaluation board actually has the same sensor variant — if it doesn't, that explains why their code "works" on the eval board but won't work on the actual hardware.

For the process going forward, I'd implement a checklist for future integrations: before the PCB goes to fabrication, the firmware team should verify the exact component variants against the BOM and confirm register maps and pinouts. I'd also suggest adding a hardware-firmware interface review as a formal gate in the development process, where both teams sign off on the interface specification.

Finally, I'd communicate the situation to project management with a clear assessment of the impact and the proposed fix, including a realistic timeline. The key is to be transparent about the issue, focus on solving it, and put processes in place to prevent it from happening again.

**Possible follow-ups:**
- How would you handle the situation if the firmware team insists that their code is correct and the hardware team made the error?
- What would you do if the firmware fix requires more time than the schedule allows before the next integration milestone?