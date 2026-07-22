# tools — Day 3

## Q1: How would you approach probing a high-speed digital signal (e.g., a 100 MHz clock) on a prototype board to get an accurate measurement without corrupting the signal?

**Answer:** For high-speed digital probing, the probing technique itself becomes part of the measurement and can introduce artifacts if done poorly. I would start by selecting the right probe: an active FET probe with low input capacitance (typically <1 pF) is preferable for signals above 50 MHz, as passive probes with 10–15 pF loading can slow edges and cause reflections. I would use a ground spring instead of the long ground lead clip—the ground lead acts as an inductor that creates ringing on fast edges. The spring keeps the ground return path short and minimizes loop inductance.

Next, I would verify the probe compensation before measuring. Most active probes have a compensation adjustment; I'd use the scope's built-in 1 kHz square wave output to ensure flat tops. For the actual measurement, I'd place the probe tip directly on the test point or use a small via if available, avoiding long wire leads. If the signal is differential (e.g., LVDS or USB), I'd use a differential probe rather than trying to measure single-ended and infer the difference. Finally, I'd check for loading effects by comparing the measured amplitude and rise time against the expected values from simulation—if the rise time is significantly slower than simulated, the probe may be loading the circuit.

**Possible follow-ups:** How would you determine whether a measured glitch is real or a probing artifact? What would you do if you don't have an active probe available for a fast edge?

---

## Q2: Walk me through your process for using a spectrum analyzer to identify an EMI emission source on a PCB during pre-compliance testing.

**Answer:** I would approach EMI sniffing systematically, starting with a near-field probe set (H-field loop and E-field tip) connected to a spectrum analyzer. First, I'd set the analyzer to a wide frequency span—say 30 MHz to 1 GHz—with a peak detector and max-hold enabled, and scan the entire board at a fixed height (e.g., 5 mm above the surface) to identify hot spots. The H-field probe is generally better for locating current loops, while the E-field probe helps identify high-impedance nodes.

Once I identify a dominant emission frequency, I'd narrow the span and reduce the RBW (resolution bandwidth) to isolate the exact frequency. Then I'd move the probe slowly over the board, watching the amplitude change to pinpoint the source. Common culprits include switching regulators (their switching frequency and harmonics), clock traces, and connector interfaces. I'd correlate the emission frequency with known clock or switching frequencies in the design—for example, a 50 MHz emission might trace back to a 50 MHz oscillator or a 100 MHz clock's second harmonic.

After locating the source, I'd try mitigation techniques on the bench: adding a ferrite bead, adjusting decoupling capacitor placement, or changing a trace routing. I'd re-scan to confirm the reduction. This is a pre-compliance step—the goal is to catch obvious issues before sending the board to a certified lab, not to replace formal testing.

**Possible follow-ups:** How would you distinguish between radiated emissions from a trace versus conducted emissions coupling onto a cable? What near-field probe design would you build or buy for this task?

---

## Q3: How would you set up a logic analyzer to debug an I2C bus where the slave device occasionally stops responding after several hours of operation?

**Answer:** I'd approach this as a long-duration, intermittent failure, so the setup needs to capture the right trigger condition efficiently. First, I'd connect the logic analyzer to the SCL and SDA lines using active flying leads with short ground springs to minimize noise. I'd set the sampling rate to at least 4x the I2C clock frequency—for a 400 kHz Fast Mode bus, 2 MHz sampling is sufficient, but I'd go higher (10 MHz) to capture glitches or edge timing violations.

The key is the trigger configuration. Instead of trying to capture hours of data, I'd set a conditional trigger: for example, trigger on a NACK condition (SDA high during the ACK bit) or on a bus timeout (SCL held low longer than the spec allows). Most modern logic analyzers support protocol-aware triggering. I'd also enable deep memory or streaming mode to capture a window around the trigger event—say 10,000 samples before and after—so I can see what led up to the failure.

If the failure is truly rare, I'd consider using the analyzer's "sequential trigger" capability: trigger on a specific address byte, then look for the failure condition within a defined number of clock cycles. I'd also probe the slave's power rail simultaneously on an oscilloscope channel to check for voltage droops coinciding with the failure. After capturing an event, I'd decode the I2C transaction and look for timing violations (rise time, hold time) or unexpected bus states that might indicate a firmware race condition or a hardware glitch.

**Possible follow-ups:** How would you distinguish between a slave that's genuinely hung and one that's just slow to respond? What if the failure only occurs when the system is in a specific operating mode?

---

## Q4: (Behavioral) Imagine you are debugging a complex firmware-hardware interaction issue on a medical device prototype, and you discover that a junior engineer on your team made a PCB layout error that is causing the problem. How would you handle communicating this finding to the team and to management?

**Answer:** I would approach this as a process improvement opportunity rather than a blame exercise. First, I'd verify the finding thoroughly—I'd want to be absolutely certain the layout error is the root cause, not just a correlation. I'd document the evidence: scope captures showing the issue, the specific layout violation (e.g., a missing return path via or an inadequate trace width), and how it maps to the observed symptom.

When communicating to the team, I'd frame it as a design review finding. In a group setting (e.g., a daily stand-up or a design review meeting), I'd present the technical facts: "We identified that the signal integrity issue on the sensor interface traces back to a layout constraint that wasn't applied in this area. Here's what we're seeing, and here's the recommended fix." I would not name the individual or imply fault—the focus is on the design, not the person. If the junior engineer is present, I'd make a point to ask for their input on the fix, turning it into a coaching moment.

For management, I'd communicate the impact on the schedule and the corrective action plan. I'd explain that we found a layout issue during debug, we have a verified fix, and we're updating our design rules and review checklist to catch similar issues earlier. This shows that we're managing risk proactively. If management asks who made the error, I'd explain that the review process is designed to catch such things, and the important outcome is that we've improved the process to prevent recurrence.

**Possible follow-ups:** What if the junior engineer becomes defensive and argues that the layout is correct? How would you handle a situation where the same engineer makes a similar error on the next revision?

---

## Q5: How would you use a thermal camera or thermocouple to validate a power supply design's thermal performance before moving to production?

**Answer:** Thermal validation is critical for reliability, especially in medical devices where patient contact or enclosed enclosures limit cooling. I'd start by identifying the components most likely to dissipate heat: the switching regulator IC, power MOSFETs, inductors, and any linear regulators. I'd also note the ambient temperature specification—for a medical device, this might be 25°C typical but could extend to 40°C or higher.

For initial characterization, I'd use a thermal camera to get a full-board thermal map. I'd set the emissivity correctly for the board materials (typically 0.95 for matte PCB surfaces, lower for shiny metal cans). I'd run the device at worst-case load—maximum current draw, highest ambient temperature the device is rated for—and let it reach thermal equilibrium (typically 30 minutes to an hour). The camera quickly shows hot spots I might not have predicted, such as a narrow PCB trace acting as a fuse or a component placed too close to a heat source.

For precise measurements on critical components, I'd use fine-gauge type-K thermocouples attached with thermally conductive epoxy or Kapton tape. I'd place them on the case of the switching IC, the inductor core, and the hottest PCB via. I'd log temperature over time using a data acquisition system to verify that steady-state temperatures stay below the component derating limits (e.g., 85°C for a 105°C-rated component, leaving margin). I'd also check thermal cycling: power the device on and off repeatedly to see if thermal expansion causes intermittent connections.

If temperatures exceed limits, I'd iterate on the thermal solution: adding a heatsink, increasing copper area on the PCB, adding thermal vias, or repositioning hot components away from temperature-sensitive sensors. I'd re-validate after each change. The goal is to have documented thermal data showing the design meets its derating requirements across the operating range.

**Possible follow-ups:** How would you account for the enclosure's effect on airflow when doing bench-top thermal testing? What if the thermal camera shows a hot spot on a component that is within its datasheet limits but near a temperature-sensitive medical sensor?