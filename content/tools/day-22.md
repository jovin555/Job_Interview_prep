# tools — Day 22

## Q1: How would you approach setting up a Zephyr RTOS project to support both a production build and a development build with different sensor configurations, where the development build includes additional debug logging and a mock sensor driver, without maintaining two separate codebases?

**Answer:** I'd use Zephyr's Kconfig and devicetree overlay system to handle this cleanly. The core approach is to keep the production configuration as the base, then layer development-specific settings on top using Kconfig fragments and devicetree overlays.

First, I'd define the production configuration in the board's default `defconfig` and devicetree files. The mock sensor driver would be implemented as a separate driver that conforms to the same sensor driver API as the real hardware driver — this way, the application code doesn't need to change at all. The devicetree overlay for development would swap the sensor node's `compatible` property to point to the mock driver, and the Kconfig fragment would enable `CONFIG_DEBUG` logging and any additional debug features.

The build system would use `west build` with different `-d` build directories for each configuration. For production: `west build -b my_board -d build/prod`. For development: `west build -b my_board -d build/dev -- -DOVERLAY_CONFIG=dev.conf -DDTC_OVERLAY_FILE=dev.overlay`. The key is that both builds share the same source tree and application code — only the configuration differs.

I'd also make sure the mock driver is only compiled when the devicetree actually references it, using Zephyr's `dt_compat_enabled()` or similar guards in the CMakeLists. This prevents the mock driver from being included in the production binary at all, which keeps the production footprint minimal.

**Possible follow-ups:** How would you ensure that the mock driver behaves realistically enough to catch integration issues? How would you handle the case where the development build needs different sensor calibration parameters?

---

## Q2: How would you approach using a logic analyzer to debug a USB 2.0 device that enumerates correctly on some hosts but fails on others, where the failure is intermittent and appears to be timing-related?

**Answer:** This is a classic USB signal-integrity and timing issue. I'd start by capturing the full enumeration sequence on both a host that works and one that fails, using a logic analyzer with USB 2.0 protocol decoding. The key is to capture the same events on both hosts and compare them systematically.

First, I'd check the basic electrical parameters: the rise/fall times on D+ and D−, the differential voltage levels, and the bit timing. USB 2.0 full-speed has tight timing requirements — the bit rate is 12 Mbps with a tolerance of ±0.25%, and the EOP (End of Packet) timing is critical. I'd look for any timing violations in the captured waveforms.

Next, I'd examine the enumeration sequence itself. USB enumeration involves a specific sequence: reset, device descriptor request, address assignment, configuration descriptor request, etc. I'd compare the timing between the host's requests and the device's responses on both hosts. A common issue is that the device responds too slowly to a control transfer, and some hosts have tighter timeouts than others. The USB spec requires the device to respond to a setup packet within 5 seconds for the initial descriptor request, but some hosts are much more aggressive.

I'd also look at the number of NAKs the device sends during control transfers. If the device's firmware is slow to process requests, it might NAK repeatedly, and some hosts give up after a certain number of retries. The logic analyzer would show the NAK count and the timing between them.

Finally, I'd check for bus contention or glitches during the reset sequence. Some hosts drive the bus differently during reset, and if the device's pull-up resistor isn't properly sized or the firmware isn't ready, it can cause enumeration failures on specific hosts.

**Possible follow-ups:** What specific timing parameters would you measure to distinguish between a device-side and host-side issue? How would you use the logic analyzer's trigger capabilities to capture the exact moment of failure?

---

## Q3: How would you approach setting up a component library management strategy in Altium Designer for a medical device project that needs to maintain strict revision control and regulatory traceability?

**Answer:** For a medical device project, the component library isn't just a design convenience — it's part of the Design History File (DHF) and needs to be traceable. I'd structure the library management around three principles: single source of truth, revision control, and auditability.

First, I'd establish a centralized library structure with clear separation between schematic symbols, PCB footprints, and 3D models. In Altium, this means using integrated libraries or a managed library system (like Altium 365 or a local Vault). Each component would have a unique identifier that ties the schematic symbol, footprint, and 3D model together. The key is that every component in the library has a revision history — if a footprint changes, there's a record of when and why.

For revision control, I'd use a version control system (Git or SVN) for the library files themselves. The library would live in a repository with a defined branching strategy: a `release` branch that's locked and only updated through a formal change process, and a `development` branch where new components are created and modified. Before a component moves to release, it goes through a review process — the symbol is checked against the datasheet, the footprint is verified against the manufacturer's recommended land pattern, and the 3D model is validated for mechanical fit.

For regulatory traceability, I'd implement a component approval workflow. Each component in the release library would have associated metadata: manufacturer, part number, datasheet revision, and any relevant compliance information (RoHS, REACH, etc.). In Altium, this can be managed through parameters on the component. The key is that when a design is released, the component library revision is captured as part of the design snapshot — so you can always reconstruct exactly what was used in a given design release.

I'd also implement a "no unapproved parts" rule. If a designer needs a new component, they create it in the development library, but it can't be used in a formal design release until it's been approved. This prevents the common problem of a design being built with a component that was never properly vetted.

**Possible follow-ups:** How would you handle a situation where a component needs to be changed after a design has been released to manufacturing? How would you ensure that all designers are using the correct library revision?

---

## Q4: Walk me through your process for using LTSpice to simulate the startup behavior of a buck converter powering a sensitive analog sensor in a battery-powered device, and how you would validate the simulation against real measurements.

**Answer:** Simulating startup behavior is critical for battery-powered medical devices because the inrush current and voltage overshoot during startup can affect both the power supply itself and the sensitive analog circuitry downstream.

I'd start by building a simulation model that includes not just the buck converter IC and its external components, but also the load characteristics. The analog sensor isn't a simple resistive load — it might have a bypass capacitor, a reference voltage generator, and other components that draw current in a specific pattern during startup. I'd model the load as a combination of a resistor (steady-state current) and a capacitor (inrush current), and possibly a current source that ramps up over time to simulate the sensor's power-on sequence.

The simulation would include the input power source (battery model with internal resistance), the buck converter with its compensation network, and the output load. I'd run a transient simulation with a time step small enough to capture the switching frequency but long enough to see the full startup sequence. Key things I'd look for: output voltage overshoot beyond the sensor's absolute maximum rating, inrush current that exceeds the battery's capability, and any instability during the transition from soft-start to normal operation.

For validation, I'd set up a test with an oscilloscope measuring the output voltage and input current simultaneously. I'd use a current probe on the input and a voltage probe on the output, with a trigger set to capture the moment power is applied. I'd compare the measured rise time, overshoot, and settling time against the simulation. The key is to validate the model's predictions, not just the final steady-state values.

If there's a discrepancy, I'd look at the model assumptions. Common issues include: the battery model not matching the real battery's internal resistance, the load model not capturing the sensor's actual startup current profile, or parasitic inductance in the PCB traces that isn't in the simulation. I'd refine the model based on what the measurements show.

**Possible follow-ups:** How would you model the sensor's startup current profile if you don't have the exact specification? What would you do if the measured overshoot is higher than the simulation predicted?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the RS485 protocol than what the hardware actually implements — the firmware is expecting a specific data frame format with a particular CRC calculation, but the hardware's transceiver is configured for a different frame structure. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** This is a classic integration risk that needs to be addressed immediately, but also calmly and systematically. The first thing I'd do is call a meeting with both teams — not to assign blame, but to get the facts on the table. I'd ask each team to bring their protocol specification documents, their implementation details, and any test results they have.

Before the meeting, I'd review the hardware design files myself to confirm what the transceiver is actually configured for. I'd check the datasheet, the schematic, and any configuration registers or strap pins. I want to have a clear picture of the ground truth before the discussion.

In the meeting, I'd walk through the protocol specification step by step — frame format, byte ordering, CRC polynomial, and any timing requirements. I'd have both teams point to where their implementation matches or deviates from the spec. The goal is to identify exactly where the mismatch is, not to argue about who's right.

Once we've identified the discrepancy, I'd assess the impact. Is this a simple fix that can be done in a day, or does it require a hardware change? If the hardware is already in fabrication, the fix likely needs to be in firmware — the firmware team would need to adjust their frame format and CRC calculation to match the hardware. If the hardware is still in design, we might have more flexibility.

I'd then work with both teams to develop a mitigation plan. This might involve a firmware change, a hardware change, or a combination. I'd also make sure we have a clear verification plan — not just "it works," but specific test cases that exercise the protocol end-to-end.

Finally, I'd use this as an opportunity to improve our process. I'd ask how this mismatch happened — was there a communication gap during the design phase? Was the protocol specification not clear enough? I'd want to understand the root cause so we can prevent similar issues in future projects. This might mean establishing a formal interface control document (ICD) review process, or making sure that protocol specifications are reviewed by both teams before implementation begins.

The key is to stay focused on solving the problem, not on who's at fault. The schedule pressure is real, but the priority is getting the device working correctly and safely.

**Possible follow-ups:** How would you prioritize the fix if the firmware change would take longer than the two days before integration testing? What would you do if the hardware team insists the hardware is correct and the firmware team insists the firmware is correct, and neither will budge?