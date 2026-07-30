# tools — Day 9

## Q1: How would you approach setting up a cross-probe workflow between OrCAD Capture and Cadence Allegro to efficiently locate and inspect components during a complex PCB layout review?

**Answer:** Cross-probing between schematic and layout is essential for efficient design review, especially on dense mixed-signal boards. I would set this up by first ensuring both tools are configured to communicate through the standard inter-tool communication (ITC) mechanism that Allegro and OrCAD support. In practice, this means enabling the cross-probe option in both applications — typically under the "Options" or "Preferences" menu, where you can specify that selecting a component in OrCAD should highlight and center on that component in Allegro, and vice versa.

For a review workflow, I would start by opening both tools side-by-side on a dual-monitor setup. When reviewing a specific signal path — say, a sensitive analog sensor input — I would select the net in OrCAD to see its routing in Allegro, then use the "Show Element" or "Highlight" commands in Allegro to trace the physical path. For complex designs, I would also set up color-coded net classes in Allegro's constraint manager (e.g., red for high-speed digital, blue for analog, green for power) so that cross-probing immediately reveals whether a net is routed in an appropriate layer or near noisy aggressors.

A key technique is to use the "Cross Probe" mode with the "Auto Zoom" feature enabled, which automatically centers and scales the view in the target application. This prevents the reviewer from having to manually pan and zoom to find the component. I would also create custom scripts or use Allegro's "Skill" language to automate common cross-probe tasks, such as highlighting all components on a specific power rail or displaying the impedance profile of a selected differential pair.

**Possible follow-ups:** How would you handle cross-probing when the schematic and layout use different reference designator prefixes or naming conventions? What would you do if the cross-probe connection is not working — how would you troubleshoot the inter-tool communication?

---

## Q2: How would you approach using LTSpice to simulate the common-mode rejection ratio (CMRR) of a differential amplifier front-end for a medical sensor, and how would you validate the simulation against real measurements?

**Answer:** Simulating CMRR in LTSpice requires careful setup because the measurement is highly sensitive to component tolerances and parasitic elements. I would start by building the differential amplifier circuit using the exact component models I plan to use — including realistic op-amp SPICE models from the manufacturer, not idealized models. The simulation approach involves two steps: first, a DC sweep to verify the operating point and ensure all transistors are biased correctly, then an AC analysis to measure CMRR across frequency.

For the AC analysis, I would configure the input with a common-mode test signal — typically a 1V AC source applied to both inputs simultaneously through matched resistors. I would then probe the differential output voltage (Vout+ minus Vout-) and plot the result in dB. The CMRR at each frequency is calculated as 20*log10(Vcm_in / Vout_diff). To get meaningful results, I would sweep from 10 Hz to at least 10 kHz for a medical sensor application, since physiological signals like ECG or EMG have significant energy in that range.

To correlate with real measurements, I would build a test fixture that matches the simulation topology as closely as possible. Using a function generator with a balun or a precision resistor divider network, I would inject a common-mode signal while measuring the differential output with a spectrum analyzer or a high-resolution oscilloscope in FFT mode. The key validation points are: does the measured CMRR roll-off frequency match the simulation? Are there unexpected resonances or dips that the simulation didn't predict? Discrepancies often point to PCB parasitics — particularly stray capacitance at the input nodes or poor layout of the feedback network — that weren't modeled in the simulation.

**Possible follow-ups:** How would you model the effect of resistor mismatch on CMRR in LTSpice? What measurement technique would you use to distinguish between CMRR degradation caused by the op-amp itself versus the external component network?

---

## Q3: How would you approach setting up a Gerber file verification workflow using Gerbv to catch common fabrication issues before sending a design to manufacturing?

**Answer:** Gerber verification is a critical quality gate that should be treated with the same rigor as a design review. My workflow in Gerbv starts with loading all Gerber files — top and bottom copper layers, solder mask, silkscreen, paste layers, and the NC drill file — and ensuring they align correctly. The first check is to verify the layer stack-up: I would toggle layers on and off to confirm that the top copper aligns with the top solder mask openings and top silkscreen, and that the drill file holes match the pad locations on all copper layers.

Next, I would perform a visual inspection for common issues. I look for silkscreen text that overlaps with solder pads, which would cause soldering defects. I check that the solder mask openings are slightly larger than the copper pads (typically 2-4 mils per side) to account for registration tolerance. I also examine the board outline layer to ensure there are no gaps or overlapping segments that would confuse the fab's CAM system. For multi-layer boards, I would use Gerbv's layer transparency feature to verify that vias and through-hole components align across all layers.

A particularly important check is the drill file: I would overlay the drill symbols on the copper layers and verify that every hole has a corresponding pad on the appropriate layers, and that no holes are placed too close to the board edge or to other holes. I also check for minimum annular ring violations by zooming in on small vias and confirming the copper ring around the drill hole is visible. Finally, I would generate a composite view of all layers to simulate what the fabricated board will look like, and I would compare this against the PCB layout in the original design tool to catch any export errors.

**Possible follow-ups:** How would you handle a situation where Gerbv shows a DRC violation that your PCB design tool did not catch? What additional checks would you perform for a flex or rigid-flex PCB design?

---

## Q4: How would you approach using a Segger J-Link debugger to capture a real-time trace of a Zephyr RTOS-based system's thread scheduling behavior without halting the CPU or modifying the firmware?

**Answer:** Capturing real-time thread scheduling behavior without intrusion requires leveraging the J-Link's trace capabilities, specifically the Serial Wire Output (SWO) and, if available, the ETM (Embedded Trace Macrocell) for instruction trace. For Zephyr RTOS specifically, the most practical approach is to use the built-in logging infrastructure with SWO as the transport, combined with the J-Link's Real-Time Transfer (RTT) feature.

First, I would ensure the target microcontroller supports SWO and that the SWO pin is routed to a debug header on the PCB. In the Zephyr project configuration, I would enable the logging subsystem with SWO backend by setting `CONFIG_LOG=y` and `CONFIG_LOG_BACKEND_SWO=y`. I would also configure the thread monitoring feature (`CONFIG_THREAD_MONITOR=y`) which causes Zephyr to emit thread state change events. The J-Link software (J-Link Commander or Ozone) can then capture the SWO stream in real time.

For non-intrusive capture, I would use J-Link RTT instead of SWO if the target doesn't have SWO support. RTT uses a small ring buffer in RAM that the debugger reads via the debug interface while the CPU continues running. In Zephyr, I would enable `CONFIG_RTT_CONSOLE=y` and route the logging output to RTT. The J-Link RTT Viewer or RTT Client can then display the thread scheduling events as they happen, with timestamps accurate to microseconds.

To analyze the captured data, I would look for patterns: are high-priority threads starving lower-priority ones? Is there unexpected preemption during critical sections? Are interrupt service routines running longer than expected, delaying thread scheduling? The key advantage of this approach is that it captures the system's actual behavior under real operating conditions, without the Heisenberg effect of adding debug print statements or halting the CPU.

**Possible follow-ups:** How would you configure the J-Link to capture a specific time window of trace data triggered by a particular event, such as a thread entering a fault handler? What would you do if the SWO data rate is too high for the debug probe to capture without dropping packets?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the KiCad project has a significant discrepancy between the schematic and the PCB layout — a critical decoupling capacitor for the main microcontroller is present in the schematic but missing from the PCB layout. The junior engineer who performed the layout is confident the capacitor is unnecessary based on a manufacturer application note they found. How would you handle this situation?

**Answer:** This is a situation where technical correctness and team dynamics both need careful handling. First, I would acknowledge the junior engineer's initiative in researching the application note — that shows good engineering curiosity. I would then ask them to walk me through their reasoning and share the specific application note they found. This serves two purposes: it shows respect for their contribution, and it gives me the full context before making a judgment.

After reviewing the application note, I would explain why it might not apply to our specific design. Manufacturer application notes often assume ideal PCB layouts or specific operating conditions that may not match our design. For a medical device, we have additional constraints: the microcontroller may be operating at a higher clock frequency, the power supply may have different transient requirements, or the device must pass IEC 60601 immunity tests that demand robust decoupling. I would also point out that the schematic was reviewed and approved by the team, including the senior engineers, and that deviating from it without documented justification breaks our design control process.

To resolve the discrepancy constructively, I would propose a structured approach: we could run a simulation of the power delivery network with and without that capacitor to quantify the impact, or we could build a prototype with a placeholder footprint (0-ohm resistor or unpopulated capacitor) to allow for testing both configurations. This turns the disagreement into a learning opportunity — the junior engineer gets to see the engineering analysis process in action, and the team gets data to support the decision. If the simulation or testing shows the capacitor is genuinely unnecessary, we can update the schematic and document the rationale. If not, we add the capacitor and use this as a teaching moment about the importance of following the approved schematic in regulated medical device development.

**Possible follow-ups:** How would you document this decision in the design history file for regulatory compliance? What would you do if the junior engineer continues to argue their position after the analysis is complete?