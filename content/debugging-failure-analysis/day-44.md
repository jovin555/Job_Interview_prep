# debugging-failure-analysis — Day 44

## Q1: How would you approach a failure investigation where a medical device's analog front-end produces accurate readings at the ADC input when measured with an oscilloscope, but the firmware consistently reports values that are offset by a fixed amount — and the offset varies between different units of the same device?

**Answer:** This is a classic "the hardware looks right but the system disagrees" scenario, and the fact that the offset varies between units is a critical clue. I'd start by verifying the measurement methodology itself — an oscilloscope probe has high impedance and may not load the circuit the same way the ADC input does, so I'd check whether the ADC's input sampling structure (sample-and-hold capacitance, charge injection, input leakage) is interacting with the source impedance of whatever drives the signal. A high source impedance combined with the ADC's sampling capacitance can cause a voltage drop that doesn't appear when measuring with a scope probe.

Next, I'd look at the ADC reference — if the offset is proportional to the reading, it could be a reference accuracy or reference buffering issue; if it's a constant offset, it could be a grounding issue between the analog source and the ADC's ground reference. The unit-to-unit variation suggests a component tolerance issue — perhaps the source impedance, a series resistor, or the ADC's internal offset calibration isn't being performed or stored correctly per unit.

I'd also check the firmware's scaling and calibration constants — if there's a per-unit calibration step in production, a calibration value that isn't being written correctly, or is being read from the wrong memory location, would produce exactly this symptom. I'd compare the firmware's raw ADC code against the expected code for a known input voltage, then trace backward through the signal chain measuring at each stage with a known input. Finally, I'd review whether the ADC's input settling time is adequate for the source impedance — if the firmware configures a sampling time that's too short, the ADC will consistently read low or high depending on the direction of the charge mismatch.

**Possible follow-ups:**
- How would you determine whether the offset is a gain error versus an offset error, and why does that distinction matter for your debugging approach?
- What production test would you design to catch this issue before devices ship?

---

## Q2: How would you approach debugging a medical device where the failure occurs only when the device is used by a specific patient population — for example, elderly users who tend to hold the device in a particular way — and the failure is a touchscreen that becomes unresponsive after several minutes of use?

**Answer:** This is a human-factors-related failure that manifests as a hardware/software issue, so I'd approach it by first understanding the physical interaction pattern. The key is to identify what's different about how this population uses the device — grip position, applied pressure, whether they rest their hand on the screen, or whether they hold the device near a particular edge. I'd start by observing or video-recording actual use (with appropriate consent) to characterize the usage pattern, then try to reproduce the failure by simulating that pattern on a test unit.

Once I can reproduce it, I'd instrument the device to understand what changes during the failure — is the touch controller reporting data but the firmware not processing it, or is the touch controller itself becoming unresponsive? I'd check whether the user's grip is causing mechanical stress on the PCB that affects the touch controller's reference or ground, whether body capacitance is affecting the touch sensing, or whether the device's temperature rises due to being held, which could affect the touch controller's sensitivity thresholds.

I'd also consider whether the user's skin properties (dryness, capacitance) differ from the typical test population — touchscreens are tuned for a nominal finger capacitance, and users with very dry skin or certain medical conditions can fall outside that range. The fix might be a firmware sensitivity adjustment, a different touch controller configuration, or a hardware change like a different cover glass or sensor pattern. I'd also involve the human-factors team to understand whether a design change to the device's ergonomics could reduce the problematic interaction.

**Possible follow-ups:**
- How would you balance making the device work for this population against the risk of making it too sensitive and causing false touches for other users?
- What data would you collect from the field to confirm your fix actually resolved the issue for this population?

---

## Q3: How would you approach a failure investigation where a medical device's analog front-end shows an increased noise floor only when the device is connected to a specific patient monitor model, but not when connected to other monitors or test equipment?

**Answer:** This points to an interoperability issue, and I'd approach it by first characterizing the electrical interface between the two devices. The fact that it only happens with one specific monitor model suggests something about that monitor's electrical characteristics — its grounding scheme, its isolation topology, its internal switching frequencies, or its leakage currents. I'd start by measuring the common-mode voltage and current between the two devices' grounds when connected, since medical devices often have different grounding configurations (some grounded, some floating/isolated).

I'd use a differential probe to measure the noise at the analog front-end's output while connected to the problem monitor, and simultaneously measure on the interface lines to see what's coupling in. I'd also look at the frequency content of the noise — if it's at a specific frequency, that might match the monitor's internal switching regulator frequency, its display refresh rate, or its patient monitoring sampling rate. The coupling path could be conducted (through the signal cable or ground connection), radiated (near-field coupling between the devices), or common-mode (noise on the monitor's ground referenced to the device's ground).

I'd also check whether the monitor's patient connection is isolated and whether the isolation capacitance is creating a path for noise current. The fix might be as simple as a ferrite on the cable, a different cable shield termination, or it might require a more fundamental change to the analog front-end's input filtering or grounding architecture. I'd also verify that the noise doesn't affect the device's clinical measurements — if it's within specification but visible, the question becomes whether it's actually a problem or just cosmetically concerning.

**Possible follow-ups:**
- How would you determine whether the noise is conducted, radiated, or common-mode coupled?
- What would you do if the fix requires a hardware change but the device is already in production and regulatory testing has been completed?

---

## Q4: How would you approach a failure investigation where a medical device's battery charging circuit overheats, but only when the device is placed on a specific type of conductive surface (like a metal cart)? The charger IC is not damaged, and the device charges normally on a non-conductive surface.

**Answer:** This is a thermal management issue with an environmental trigger. The key clue is that it only happens on a conductive surface, which suggests the surface is either providing a thermal path that changes the heat distribution, or — more likely — it's creating an electrical condition that increases power dissipation. I'd start by measuring the actual temperatures at various points on the board when the device is on the conductive surface versus a non-conductive surface, using a thermal camera to get a complete picture of where heat is being generated.

I'd also measure the charging current and voltage waveforms in both conditions. A conductive surface could be creating a parasitic ground path or altering the device's ground potential, which could affect the charger IC's operation — for example, if the surface creates a ground loop that shifts the sense resistor's reference, the charger might think the battery is at a different voltage and adjust its charging current accordingly. I'd also check whether the surface is causing the device's enclosure to couple to something that affects the switching regulator's operation — perhaps increased parasitic capacitance changes the switching behavior and increases losses.

Another angle is whether the conductive surface is simply a better heat spreader that's drawing heat away from one area and concentrating it elsewhere, or whether it's preventing airflow in a way that changes the thermal profile. I'd also consider whether the surface is creating a path for electrostatic discharge or leakage current that's activating a protection circuit or causing the charger to operate in an abnormal mode. The investigation would involve measuring electrical parameters (current, voltage, switching waveforms) and thermal parameters simultaneously to correlate the overheating with a specific electrical condition.

**Possible follow-ups:**
- What safety considerations would you keep in mind while testing a device that's overheating, especially in a medical device context?
- How would you determine whether this is a design flaw that needs correction or an environmental condition that should be addressed through usage instructions?

---

## Q5: How would you approach a situation where you're leading a cross-functional failure investigation, and you discover that the root cause points to a design decision made by a senior engineer who is still on the team — and the finding could reflect poorly on them or create tension within the group?

**Answer:** This is a leadership challenge as much as a technical one. The first principle is that the investigation's goal is to find the root cause and prevent recurrence, not to assign blame. I'd frame the findings in terms of the design decision's context — what information was available at the time, what constraints existed, and why the decision made sense then. Most design decisions that later prove problematic were reasonable given what was known at the time, and the failure often involves a combination of factors that weren't foreseeable.

I'd present the findings to the senior engineer privately first, before any broader discussion, to give them the opportunity to process the information and contribute their perspective on the decision's context. This isn't about softening the message — it's about ensuring the technical discussion is complete and that the engineer isn't caught off guard in a group setting. I'd ask for their input on the analysis and whether there were factors the investigation might have missed.

When presenting to the broader team, I'd focus on the systemic factors — what process gaps allowed this decision to be made without adequate review, what testing didn't catch it, what documentation was missing — rather than on the individual decision. The corrective actions should address the system, not the person. If the engineer is defensive, I'd acknowledge their expertise and contributions while keeping the focus on the evidence and the need to prevent patient harm. The goal is to maintain a culture where people feel safe raising concerns and where failures are treated as learning opportunities, not as occasions for blame.

**Possible follow-ups:**
- How would you handle the situation if the senior engineer becomes defensive and tries to discredit the investigation's findings?
- What would you do if the corrective action requires reworking or recalling products, and the senior engineer resists the change because they still believe their original design was correct?