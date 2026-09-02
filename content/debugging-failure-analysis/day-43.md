# debugging-failure-analysis — Day 43

## Q1: How would you approach a failure investigation where a medical device's analog measurement is accurate at power-up but drifts over several hours of continuous operation, and the drift direction reverses when the device is turned off and restarted?

**Answer:** This pattern — drift that develops over hours and resets on power cycle — strongly suggests a thermal or aging-related effect that recovers when the system cools down or when stored energy dissipates. I'd structure the investigation around separating thermal effects from electrical degradation.

First, I'd characterize the drift precisely: does it correlate with internal temperature rise, with time regardless of load, or with cumulative operating time? I'd instrument the board with thermocouples at key locations — the sensor itself, the instrumentation amplifier, the ADC reference, and the input conditioning components — and log both temperature and the measured offset simultaneously. If the drift tracks a specific component's temperature, that points to a temperature coefficient issue.

Next, I'd examine the reference and bias paths. A common cause of slow drift is a voltage reference or bias resistor network with mismatched temperature coefficients. Even components within specification individually can produce noticeable drift if their temperature coefficients aren't matched — for example, a divider network where one resistor drifts more than the other. I'd check whether the drift is in the sensor excitation, the ADC reference, or the signal chain gain.

The fact that drift reverses on restart is a useful clue. It suggests the effect is reversible — likely thermal rather than permanent degradation. I'd also consider whether the drift could be caused by self-heating of the sensor element itself, particularly if the sensor is excited continuously. Some bridge-type sensors exhibit drift as their own temperature rises from excitation current.

I'd also look at the firmware side: is the ADC doing single-ended conversions that might be affected by reference drift? Is there a self-calibration routine that runs at startup but not during operation? If the device calibrates at power-up when everything is at ambient temperature, then drifts as the system warms, that would explain the pattern.

Finally, I'd design an experiment to confirm the hypothesis: run the device at a controlled elevated ambient temperature and see if the drift appears faster, and run it with the suspected component cooled locally to see if the drift is suppressed.

**Possible follow-ups:**
- How would you distinguish between drift caused by the sensor itself versus drift in the analog front-end circuitry?
- What design changes would you consider to make the system more robust to this type of drift?

---

## Q2: How would you approach debugging a medical device where the failure occurs only when the device is used by a specific patient population — for example, elderly users who tend to hold the device in a particular way — and the failure is a touchscreen that becomes unresponsive after several minutes of use?

**Answer:** This is a classic case where the failure mode is tied to how the device is physically handled, which means the bench setup isn't reproducing the real-world conditions. I'd start by trying to understand exactly what's different about how this population uses the device.

First, I'd want to observe or interview users to understand the specific handling patterns. Are they gripping the device in a way that covers a particular area? Are they applying pressure to the enclosure that could flex the PCB? Is the device resting on a surface that could affect its thermal profile? The fact that it takes several minutes to develop suggests either a gradual thermal effect or a cumulative mechanical effect like flexing that eventually causes a marginal connection to fail.

I'd look at the mechanical design first. If the device is held in a way that flexes the PCB near the touchscreen connector or the touch controller, that could cause intermittent contact. I'd examine the board for flex indicators — stress marks near connectors, cracked solder joints, or components under mechanical strain. I'd also consider whether the enclosure is transferring pressure to specific components.

If the failure is thermal, I'd consider whether the user's hand is insulating a particular area of the device, causing a component to overheat. A touch controller or its power supply that exceeds its thermal specification would eventually stop functioning. I'd use a thermal camera to see if holding the device in the described way creates a hot spot.

I'd also consider capacitive coupling effects. If the user holds the device in a way that their hand is near the touch sensor's sensing lines, it could affect the touch controller's ability to detect touches — especially if the device is battery-powered and the user's body provides a different ground reference than the bench setup.

To reproduce the issue, I'd try to simulate the holding pattern — possibly with a fixture that applies similar pressure and coverage, or by asking a colleague to hold the device the same way. I'd instrument the device to log touch controller status, temperature, and power supply voltages during the failure to capture what's happening when it becomes unresponsive.

**Possible follow-ups:**
- How would you determine whether this is a design issue that needs a hardware fix versus a usability issue that could be addressed with guidance or training?
- What would you look for first if you suspected the issue was related to PCB flexing?

---

## Q3: You're investigating a production yield issue where approximately 2% of boards fail a functional test immediately after power-up — the microcontroller doesn't start executing code. The failures appear random across batches and don't correlate with any specific component lot. How would you approach this?

**Answer:** A 2% failure rate with no lot correlation and a symptom of "microcontroller doesn't start" points me toward a process or assembly issue rather than a component quality problem. I'd approach this systematically, starting with understanding exactly what "doesn't start" means electrically.

First, I'd characterize the failure more precisely. When the board is powered, is the microcontroller's supply rail reaching the correct voltage? Is the reset pin being released properly? Is the clock oscillating? Is the microcontroller drawing current consistent with a running device or is it in an undefined state? I'd probe several failing boards with an oscilloscope to capture the power-up sequence — supply ramp, reset release timing, and clock startup.

Since the failures are random across batches, I'd look at the assembly process variables. One common cause of intermittent "no boot" failures is marginal soldering on the microcontroller's pins — particularly the power, reset, or clock pins. A cold solder joint or insufficient solder paste could cause an intermittent connection that passes visual inspection but fails electrically. I'd X-ray a few failing boards to check for solder joint quality on the microcontroller and supporting components.

Another possibility is ESD damage during handling or test. If the microcontroller's reset or clock pins are being damaged by ESD during the assembly or test process, the device might pass initial inspection but fail to start when powered. I'd check whether the failures cluster by production shift, by test operator, or by handling equipment.

I'd also examine the firmware programming step. If the boards are programmed before functional test, a marginal programming connection could result in incomplete or corrupted firmware. I'd verify that the firmware reads back correctly from failing boards — if the flash is blank or corrupted, that points to the programming process.

Finally, I'd look at the power supply design for marginal startup conditions. If the supply has a slow ramp or the reset circuit has a marginal timeout, some boards might fail to start if the supply doesn't reach full voltage before the reset releases. This could be batch-dependent if there's variation in capacitor values or regulator startup times.

I'd structure this as a controlled experiment: take a sample of failing boards and systematically test each hypothesis — reflow the suspected joints, reprogram the firmware, replace the crystal, and see which intervention makes the board start working.

**Possible follow-ups:**
- How would you determine whether this is a design issue versus a manufacturing process issue?
- What data would you want to collect from the production line to help narrow down the cause?

---

## Q4: How would you approach a failure investigation where a medical device's wireless communication (Bluetooth) drops connection intermittently, but only when the device is held in a specific orientation relative to the patient's body? The antenna is a chip antenna on the PCB.

**Answer:** This pattern — orientation-dependent wireless failure — points to antenna detuning or RF absorption by the patient's body. When a chip antenna is placed near body tissue, the body acts as a lossy dielectric that can shift the antenna's resonant frequency and absorb radiated power. The specific orientation matters because it determines how much body tissue is in the antenna's near field and how the antenna's radiation pattern is affected.

I'd start by characterizing the RF performance in the failing orientation. Using a conducted measurement — connecting the radio's RF output directly to a spectrum analyzer or test instrument — I'd verify that the radio itself is transmitting correctly regardless of orientation. If conducted power is fine, the issue is in the antenna or the propagation path.

Next, I'd measure the antenna's impedance and resonant frequency with the device held in the failing orientation versus a known-good orientation. A network analyzer with the device in free space, then near a body phantom or an actual person, would show how much the antenna is detuned. If the resonant frequency shifts significantly or the return loss degrades, that confirms body loading is the issue.

I'd also consider the antenna's placement relative to the PCB ground plane and other components. A chip antenna needs a proper ground plane to perform well, and if the device is held in a way that places the patient's hand or body near the antenna's ground plane, it can change the effective ground and detune the antenna.

The fix would depend on what I find. If the antenna is being detuned by body proximity, options include: retuning the matching network to account for body loading, relocating the antenna to a position less affected by handling, adding a ground plane extension to shield the antenna from body tissue, or switching to an antenna type with better body immunity. If the issue is absorption rather than detuning, increasing transmit power (if within regulatory limits) or improving the receiver sensitivity might help, but those are less desirable than fixing the antenna design.

I'd also check whether the Bluetooth stack has adaptive frequency hopping that might be affected by the orientation — if the device is in an environment with interference, the hopping pattern might not be avoiding the problematic frequencies in certain orientations.

**Possible follow-ups:**
- How would you test this in a controlled way without requiring a person to hold the device for extended periods?
- What design changes would you consider to make the antenna more robust to body proximity?

---

## Q5: How would you handle a situation where you're leading a cross-functional failure investigation, and you discover that the root cause points to a design decision made by a senior engineer who is still on the team — and the finding could reflect poorly on them or create tension within the group?

**Answer:** This is a situation where the technical investigation is straightforward but the human dynamics require careful handling. The goal is to resolve the technical issue while maintaining a constructive team environment and preserving the senior engineer's dignity — not because we're protecting anyone, but because a blame-oriented culture damages the team's ability to do good work.

First, I'd make sure the evidence is solid before discussing findings with anyone. I'd want the root cause confirmed through multiple lines of evidence — not just a hypothesis, but reproducible data that clearly shows the design decision led to the failure. I'd also check whether the design decision was reasonable given the information available at the time. Many design decisions that later prove problematic were sound given what was known then; the failure might be due to changed requirements, new information, or an interaction that wasn't foreseeable.

When presenting the findings, I'd frame the discussion around the design decision and its context, not the person. I'd start by meeting with the senior engineer privately to share the evidence and get their perspective. They might have information about why the decision was made that I don't have — perhaps a constraint I'm not aware of, or a trade-off that was made deliberately. This conversation should be collaborative, not accusatory.

If the senior engineer disagrees with the finding, I'd listen to their reasoning and evaluate it honestly. If their objection has merit, I'd incorporate it. If not, I'd work to bring them along by reviewing the evidence together and addressing their concerns directly.

When presenting to the broader team, I'd focus on the technical finding and the corrective action, not on who made the original decision. The message should be: "We found a root cause, here's the evidence, here's the fix, and here's what we'll do to prevent this class of issue in the future." If the design review process should have caught this, I'd discuss process improvements rather than individual blame.

I'd also consider whether the senior engineer might benefit from being involved in developing the corrective action. Giving them ownership of the fix can turn a potentially embarrassing situation into an opportunity for them to demonstrate leadership and technical skill.

The key principle is separating the person from the problem. The investigation's purpose is to find and fix the root cause, not to assign blame. If the team sees that failures are handled constructively, they'll be more willing to surface issues early rather than hiding them — which is critical in medical device development where patient safety depends on honest reporting.

**Possible follow-ups:**
- How would you handle it if the senior engineer becomes defensive or resistant to the findings?
- What would you do if the design decision was clearly negligent — made without following established processes or ignoring obvious red flags?