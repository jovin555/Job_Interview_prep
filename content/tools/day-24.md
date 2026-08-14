# tools — Day 24

## Q1: How would you approach setting up a Zephyr RTOS project to support both a production build and a development build with different sensor configurations, where the development build includes additional debug logging and a mock sensor driver, without maintaining two separate codebases?

**Answer:** The cleanest approach is to use Zephyr's Kconfig and devicetree overlay system, combined with the west build tool's ability to specify multiple configuration fragments. I'd structure the project so the base application code is hardware-agnostic, with sensor drivers selected through devicetree nodes rather than hardcoded in C.

For the production build, I'd have a default prj.conf and a production.overlay that defines the real sensor hardware. For the development build, I'd create a dev.overlay that replaces the sensor node with a mock driver implementation, and a dev.conf fragment that enables logging (`CONFIG_LOG=y`), adds debug features like thread analyzer (`CONFIG_THREAD_ANALYZER=y`), and possibly enables assertions (`CONFIG_ASSERT=y`).

The build commands would be:
- Production: `west build -b <board> -- -DOVERLAY_CONFIG=production.overlay`
- Development: `west build -b <board> -- -DOVERLAY_CONFIG=dev.overlay -DEXTRA_CONF_FILE=dev.conf`

The key is that the mock driver implements the same device driver API as the real sensor, so the application code doesn't need conditional compilation. This keeps the codebase clean and ensures the production path is exercised identically in both builds — only the underlying driver changes. I'd also use Kconfig options to gate debug features, so the production build doesn't accidentally include them if someone forgets to specify the overlay.

**Possible follow-ups:** How would you ensure the mock driver accurately simulates sensor behavior for testing edge cases? What if the production and development builds need different board definitions entirely?

---

## Q2: Walk me through your approach to using a spectrum analyzer with a near-field probe to identify whether a radiated emissions failure at 150 MHz is coming from a switching regulator's harmonic or from a digital clock, and how you would confirm your hypothesis.

**Answer:** First, I'd establish the fundamental frequencies of the suspects. If the switching regulator runs at 1 MHz, 150 MHz would be the 150th harmonic — unlikely to have significant energy that far out unless there's a resonance or poor layout. A digital clock at 25 MHz would have 150 MHz as the 6th harmonic, which is much more plausible. But I wouldn't rely on arithmetic alone.

My approach would be:
1. **Measure the actual fundamental frequencies** — probe the switching node of the regulator and the clock output with the near-field probe to confirm their exact frequencies. Switching regulators often have spread-spectrum modulation, so the fundamental might not be exactly 1 MHz.
2. **Use the spectrum analyzer's marker and delta functions** — set a marker on the 150 MHz peak, then use the delta marker to check if there's energy at 25 MHz (or whatever the clock fundamental is) and at 150 MHz ± 25 MHz. If the 150 MHz peak is a harmonic of the clock, you'd expect to see a family of peaks spaced 25 MHz apart.
3. **Perform a "power-off" test** — if the design allows, disable the clock (or put the processor in reset) and see if the 150 MHz peak disappears. Then re-enable the clock and disable the regulator to see if the peak returns. This is the most definitive test.
4. **Check for coupling paths** — if the peak persists regardless of which source is active, the issue might be coupling between the two circuits, or the probe might be picking up a third source entirely.

To confirm the hypothesis, I'd also look at the signal's characteristics. A clock harmonic tends to be narrowband with a stable amplitude, while a switching regulator harmonic might show slight frequency modulation or amplitude variation if the regulator uses spread-spectrum. I'd also move the probe along the suspected trace to see if the amplitude peaks near the clock trace or the regulator output.

**Possible follow-ups:** How would you distinguish between the clock's fundamental and its harmonics if the clock frequency is unknown? What if the 150 MHz emission is actually a beat frequency between two sources?

---

## Q3: How would you approach setting up a component library management strategy in Altium Designer for a medical device project that needs to maintain strict revision control and regulatory traceability?

**Answer:** For a medical device project, the component library isn't just a design convenience — it's part of the design history file (DHF) and needs to be traceable. I'd structure the library management around three principles: single source of truth, revision control, and auditability.

First, I'd use a **centralized managed library** (Altium 365 or an SVN-managed library server) rather than scattered local libraries. Each component would have a unique identifier, and the library itself would be versioned. This ensures everyone on the team uses the same component definitions.

Second, I'd enforce a **formal review and approval workflow** for component changes. A component can't be modified directly — changes go through a review process where the schematic symbol, PCB footprint, and 3D model are all checked against the manufacturer's datasheet. The review records who made the change, when, and why, which is essential for regulatory traceability.

Third, I'd implement **parameter completeness requirements**. Every component must have all relevant parameters populated — manufacturer part number, supplier part number, voltage/current ratings, tolerance, temperature range, and any medical-specific attributes like "sterilization compatible" or "biocompatible." This makes BOM generation and compliance documentation much easier later.

For revision control specifically, I'd use Altium's version control integration with SVN or Git. Each library release gets a version tag, and the PCB project references specific library versions. If a component changes, the project doesn't automatically use the new version — it requires an explicit update, which creates an audit trail. This is critical for medical devices where you need to know exactly which component revision was used in a given production batch.

**Possible follow-ups:** How would you handle a component that needs a footprint change after the PCB has already been released to manufacturing? How would you manage components that are approved for use but have known obsolescence risks?

---

## Q4: How would you approach using a logic analyzer to debug a CAN-FD bus where a node intermittently enters bus-off state after several hours of operation, but only when the system is under vibration?

**Answer:** This is a classic intermittent failure that requires a systematic approach. The vibration correlation suggests a mechanical issue — possibly a loose connector, a cracked solder joint, or a marginal termination — but I'd want to confirm that before opening the enclosure.

My approach would be:
1. **Set up the logic analyzer for long-duration capture** — CAN-FD at 5 Mbps needs a sampling rate of at least 50 MHz, but the key is capturing enough data. I'd use the logic analyzer's trigger and segmentation features to capture only error frames rather than all traffic. I'd trigger on the CAN error frame pattern (six consecutive dominant bits) or on the bus-off condition.

2. **Decode the CAN-FD protocol** — the logic analyzer should decode the CAN-FD frames, including the error flags, error counters, and the specific frame that preceded the error. I'd look for patterns: is it always the same node that's failing? Is it always during a specific type of frame (data vs. remote)? Is there a bit position where errors consistently occur?

3. **Correlate with vibration** — I'd run the system under vibration while capturing, and mark the timeline when vibration is applied. If the errors only occur during vibration, that strongly suggests a mechanical issue. If they occur randomly but are just more frequent during vibration, it might be an electrical issue that's exacerbated by vibration.

4. **Examine the physical layer** — once I've confirmed the error pattern, I'd look at the bus with an oscilloscope. During vibration, I'd check for:
   - Signal integrity issues: ringing, overshoot, or slow edges on the CAN_H/CAN_L lines
   - Intermittent shorts or opens in the wiring
   - Ground bounce or voltage drops on the node's power supply

5. **Check the error counters** — if the node has a diagnostic interface, I'd read the CAN controller's transmit/receive error counters over time. A node enters bus-off after 256 consecutive error events (TEC > 255), so I'd want to see if the errors are transmit-side or receive-side, and whether they're bit errors, stuff errors, or CRC errors.

The most likely culprits for vibration-induced bus-off are: a loose connector on the CAN transceiver, a cracked solder joint on the transceiver or termination resistor, or a wiring harness that's chafing against the chassis. I'd inspect those first before suspecting a firmware or configuration issue.

**Possible follow-ups:** How would you distinguish between a transmit-side and receive-side error in the CAN error counters? What if the vibration test can't be reproduced in the lab — how would you instrument the system for field testing?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the CAN-FD protocol than what the hardware actually implements — the firmware is expecting a specific data field ordering and bit-rate switch configuration, but the hardware's CAN-FD controller is configured differently. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** This is a high-pressure situation, but the first thing I'd do is resist the urge to assign blame or force a quick fix. The priority is getting to the correct answer before integration testing, even if that means delaying the start.

My approach would be:
1. **Gather the facts immediately** — I'd call a short meeting with both teams and ask them to bring their documentation: the firmware's CAN-FD configuration (data field mapping, bit-rate switch settings, nominal/data bit rates) and the hardware's CAN-FD controller configuration (from the schematic and the controller's register settings). I'd also ask for the original interface control document (ICD) or protocol specification that was supposed to define this.

2. **Determine which implementation matches the specification** — the ICD is the source of truth. If one team deviates from it, that's the error. If both deviate, we have a specification gap that needs to be resolved. I'd compare both implementations against the ICD line by line.

3. **Check if the two implementations are actually incompatible** — sometimes what looks like a disagreement is actually a misunderstanding. The firmware might be using a different data field ordering but the hardware's controller might be configured in a way that produces the same result. I'd have both teams walk through a sample frame together to see if the bytes actually match.

4. **If there's a genuine conflict, escalate with options** — I'd present the options to the team: (a) change the firmware to match the hardware, (b) change the hardware configuration to match the firmware (if it's a software-configurable controller), or (c) update the ICD and have both sides change. I'd recommend the option with the least risk and fastest implementation time, but I'd also consider which option is more correct for the product long-term.

5. **Document the decision and prevent recurrence** — regardless of the outcome, I'd ensure the ICD is updated, the decision is documented in the design history file, and we add a protocol conformance test to the integration test plan so this can't slip through again.

The key is to keep the focus on the technical issue, not on whose fault it is. In my experience, these situations are rarely one team being careless — they're usually a symptom of a communication gap in the requirements flow-down. Fixing the immediate issue is important, but fixing the process gap is what prevents it from happening again.

**Possible follow-ups:** How would you handle the situation if the firmware team's implementation is actually more correct per the ICD, but the hardware is already in fabrication and can't be changed? What would you do if the two teams continue to disagree even after reviewing the documentation?