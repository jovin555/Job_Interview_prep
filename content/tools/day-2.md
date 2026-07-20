# tools — Day 2

## Q1: How do you approach selecting the right PCB design tool for a project, and what factors drive your choice between Altium Designer, Cadence Allegro, and KiCad?

**Answer:** Based on my experience, the choice depends on project complexity, team collaboration needs, and regulatory requirements. At Trudell Medical International, we used Altium Designer for Class II medical device PCBs because of its strong design rule checking, version control integration, and component management — critical for IEC60601 compliance where traceability matters. For the SOBA Heart Lung Support Machine, Altium's multi-sheet hierarchical design made it easier to manage the complex mixed-signal sections (motor control, sensor interfaces, Wi-Fi module).

For high-speed or high-layer-count designs, I'd lean toward Cadence Allegro — it handles complex constraints better. I used Allegro during my time at GE Healthcare for medical products requiring precise impedance control and differential pair routing. KiCad is excellent for open-source projects or smaller teams, but for medical devices requiring full audit trails and validated libraries, the commercial tools are usually necessary.

**Possible follow-ups:**
- Have you ever had to migrate a design between these tools? What challenges arose?
- How do you handle library management across a team using Altium?

---

## Q2: Walk me through your debugging workflow when a board comes back from assembly and doesn't power up correctly.

**Answer:** I follow a systematic approach starting with visual inspection — checking for solder bridges, tombstoned components, and polarity errors. Then I verify power rails with a multimeter before applying full power. At Vinvish Technologies, we had a high-power laser driver board that showed 0V on a critical 5V rail. Using the schematic in Altium and a bench multimeter, I traced back from the load to find a blown ferrite bead — it was rated for 300mA but the circuit was drawing 600mA during startup transients. I replaced it with a 1A rated part and added a TVS diode for protection.

For more complex issues, I use an oscilloscope to check for ripple, startup sequencing, and noise. On the Lotus Printer and Toco project at Trudell, we found during IEC60601 testing that a voltage regulator was dropping out under load. Using a four-channel scope with current probes, I correlated the dropout with a high-inrush capacitor bank on the output. The fix was adding a soft-start circuit and adjusting the layout per the regulator's datasheet recommendations.

**Possible follow-ups:**
- What specific oscilloscope features do you rely on most for power integrity debugging?
- How do you document your debugging process for regulatory compliance?

---

## Q3: How do you use simulation tools in your PCB design workflow, and when do you find them most valuable?

**Answer:** I use simulation tools primarily for power integrity and signal integrity analysis before committing to layout. On the 5W High-Reliability EDFA project for space applications, we used SPICE simulation in Altium to model the hot-swap protection circuit. The simulation revealed that the inrush current limiter MOSFET would exceed its safe operating area during startup with a 50µF capacitive load. We adjusted the gate drive timing and added a current sense resistor — the simulation saved us from a board respin that would have cost weeks and significant budget.

For signal integrity, I use the impedance calculator in Altium or Allegro's constraint manager to verify trace geometries match target impedances (typically 50Ω single-ended, 90Ω differential for USB 2.0). On the Smart OPEP Device, we had pressure sensor analog signals running near a switching regulator. A quick SI simulation showed 15mV of coupled noise — we moved the sensitive traces to an inner layer with ground plane shielding, which eliminated the issue before fabrication.

**Possible follow-ups:**
- Do you use any thermal simulation tools? How do you handle thermal management in compact medical devices?
- How do you validate that your simulation models match real-world behavior?

---

## Q4: Describe a time when a tool limitation or bug caused a significant issue in your work, and how you handled it.

**Answer:** (Behavioral/Experience question) During the Lotus Printer and Toco project at Trudell Medical International, we encountered a critical issue during IEC60601 testing where the device failed ESD immunity tests. The problem traced back to a ground plane stitching via pattern that Altium's auto-router had placed incorrectly — it had created isolated copper islands that acted as antennas rather than proper ground connections.

The situation was high-pressure because we were on a tight regulatory testing schedule. I took the following actions: First, I manually reviewed the entire ground plane layout using Altium's polygon management tools and identified 12 isolated copper regions. Second, I re-stitched the ground planes manually, adding vias at maximum 1/20th wavelength spacing for the highest expected noise frequency. Third, I updated our design rules to enforce proper via stitching patterns and added a pre-layout checklist item for ground plane review. The result was that the device passed ESD testing on the next attempt, and the design rule updates prevented similar issues on subsequent projects like the SOBA Heart Lung Support Machine.

**Possible follow-ups:**
- How do you balance using auto-routing versus manual routing in complex designs?
- What other design rule checks do you consider essential for medical devices?

---

## Q5: How do you approach firmware debugging tools and workflows when transitioning between different microcontroller platforms (STM32, PIC, etc.)?

**Answer:** I maintain a tool-agnostic debugging methodology while adapting to platform-specific tools. For STM32 projects like the 5W High-Reliability EDFA, I use Keil uVision with SEGGER J-Link debugger — the trace functionality is invaluable for real-time analysis of the external DAC/ADC communication timing. For PIC microcontrollers, I use MPLAB IDE with the ICD debugger.

The key is understanding what each toolchain offers. On the Smart OPEP Device, we used Zephyr RTOS with a command-line build system (west) and VS Code with Cortex-Debug extension. This gave us GDB-based debugging with FreeRTOS-aware thread inspection — critical for debugging the sensor fusion task that combined pressure data from multiple I2C sensors.

For protocol debugging, I rely on a Saleae logic analyzer regardless of platform. On the SOBA project, I used it to debug a Wi-Fi module initialization sequence where the SPI timing was marginal. The analyzer showed the chip select line de-asserting 50ns too early — a firmware timing fix resolved intermittent connection failures. I always keep a logic analyzer and oscilloscope on my bench as universal debugging tools that work across any microcontroller platform.

**Possible follow-ups:**
- How do you handle real-time debugging when using an RTOS like Zephyr?
- What's your approach to debugging intermittent issues that only appear in the field?