# debugging-failure-analysis — Day 46

## Q1: How would you approach a failure investigation where a medical device's USB communication works reliably during bench testing, but intermittently fails when the device is connected to a hospital's USB hub — and the failure rate increases when multiple other devices are connected to the same hub?

**Answer:** This scenario points toward a power delivery or signal integrity issue rather than a firmware logic problem, since the device works fine in isolation. I'd structure the investigation around three main hypotheses: inadequate power delivery, signal integrity degradation, or enumeration/negotiation conflicts.

First, I'd measure the voltage at the device's USB connector while connected to the hub under load — not just at the hub's output, but at the device's input after the cable and any protection circuitry. USB hubs distribute a finite amount of current, and when multiple devices draw power, the voltage at each port can sag below the USB specification. I'd look at the voltage during device enumeration, when inrush current is highest, and during active communication. A drooping VBUS would point to a power architecture issue — possibly insufficient bulk capacitance on the device's input or a hub that's current-limited.

Second, I'd examine signal integrity. Longer cable runs through a hub introduce additional capacitance and potentially impedance discontinuities. I'd check the USB data lines with an oscilloscope at the device's connector, looking at eye pattern quality, rise/fall times, and whether the signal meets the USB specification at that point. Poor signal quality could cause CRC errors or retries that manifest as intermittent failures.

Third, I'd consider the enumeration process itself. When multiple devices connect or disconnect from a hub, the hub re-enumerates all downstream devices. If the device's firmware has a timing assumption about how quickly it receives configuration requests, or if it doesn't properly handle a bus reset, it could fail to re-enumerate correctly.

I'd also check whether the failure correlates with specific hub models or configurations. Some hubs have known issues with certain device classes or power management schemes. The investigation would involve reproducing the failure in a controlled setup, instrumenting the bus to capture the exact failure mode — whether it's a voltage drop, a CRC error, a device disconnect event, or a firmware hang — and then isolating which variable triggers the failure.

**Possible follow-ups:**
- How would you distinguish between a VBUS voltage issue and a signal integrity issue if both could produce similar symptoms?
- What would you look for in the device's firmware to determine if it's handling USB bus resets correctly?

---

## Q2: How would you approach debugging a medical device where a firmware update appears to have introduced a new intermittent failure — the device occasionally resets during normal operation, and the resets began only after the update was deployed to the field?

**Answer:** This is a regression investigation, and the key advantage is that we have a known change point — the firmware update. I'd start by establishing a clear timeline and gathering data from the field: when the resets started, which units are affected, whether all units with the new firmware are affected or only a subset, and what the reset logs show.

The first step is to compare the old and new firmware versions systematically. I'd review the release notes and the actual code changes — not just the features that were added, but any changes to initialization sequences, interrupt priorities, timing loops, power management, or watchdog configuration. Often, a seemingly unrelated change — like reordering initialization or changing a compiler optimization level — can introduce a subtle timing issue.

I'd also look at the reset source. If the device has a reset status register, I'd check whether the resets are watchdog timeouts, brown-out resets, software-triggered resets, or external pin resets. Each points in a different direction. A watchdog timeout might indicate the main loop is taking longer than expected under certain conditions — perhaps a new code path blocks for too long. A brown-out reset could indicate the new firmware draws more current during certain operations, causing the supply to dip.

Next, I'd try to reproduce the failure in the lab. If the field units show a pattern — for example, resets occur during a specific feature usage — I'd create a test that exercises that feature repeatedly. If the failure is truly random, I'd run extended soak tests with the new firmware while monitoring power rails, reset lines, and the watchdog output.

I'd also consider whether the update process itself could be a factor. If the update corrupted some configuration data or left the device in an unexpected state, that could cause intermittent resets. I'd verify that the firmware image in the field matches what was released and that the update process includes proper validation.

Finally, I'd approach this as a controlled experiment: if the new firmware is suspect, I'd offer to revert a small number of field units to the previous version (with appropriate regulatory consideration for a medical device) to confirm the update is the cause. This would be done through the proper change control process, but it would provide strong evidence.

**Possible follow-ups:**
- What specific types of firmware changes would you look for first when investigating a reset regression?
- How would you handle the regulatory implications of reverting field units to a previous firmware version?

---

## Q3: How would you approach a failure investigation where a medical device's analog front-end shows an increased noise floor only when the device is connected to a specific patient monitor model, but not when connected to other monitors or test equipment?

**Answer:** This is a classic electromagnetic compatibility (EMC) interaction problem — the device works correctly in most environments but has a specific compatibility issue with one piece of equipment. I'd approach this by first characterizing the noise: its frequency content, amplitude, whether it's continuous or intermittent, and whether it appears on all analog channels or just specific ones.

The first hypothesis is that the patient monitor is emitting electromagnetic energy that couples into the device's analog front-end. I'd use a near-field probe and a spectrum analyzer to scan the device's enclosure and cabling while connected to the problematic monitor, looking for coupling paths. The noise might be entering through the patient cable, the power connection, or radiating directly into the PCB.

The second hypothesis is that the monitor is injecting noise through a common ground path. When two medical devices are connected to the same patient, they share a ground reference through the patient. If the monitor has a different ground potential or switching noise on its chassis, that noise can flow through the patient cable into the device's analog front-end. I'd measure the ground potential difference between the two devices and look at the noise on the cable shield.

The third hypothesis is that the monitor's output — perhaps a defibrillator pulse, a pacemaker signal, or a monitoring signal — is coupling into the measurement. Some patient monitors output signals that are within the bandwidth of the analog front-end, and if the front-end doesn't have adequate filtering, those signals can appear as noise.

I'd also consider the specific frequencies involved. If the monitor uses a switching power supply, the noise might be at the switching frequency or its harmonics. If it uses a display with PWM backlighting, the noise might be at the PWM frequency. Identifying the noise frequency and correlating it with known emissions from the monitor would help confirm the coupling mechanism.

The investigation would involve reproducing the issue in a controlled environment, systematically isolating the coupling path — disconnecting the patient cable, using a different power source, adding ferrites, changing cable routing — and then implementing a fix. The fix might be additional filtering on the analog inputs, better shielding of the patient cable, a ground isolation strategy, or a layout change to reduce coupling.

**Possible follow-ups:**
- How would you determine whether the noise is coupling through the patient cable or radiating directly into the device?
- What filtering strategies would you consider for the analog front-end, and what trade-offs would you evaluate?

---

## Q4: How would you approach a failure investigation where a medical device's battery charging circuit overheats, but only when the device is placed on a specific type of conductive surface (like a metal cart)? The charger IC is not damaged, and the device charges normally on a non-conductive surface.

**Answer:** This is an interesting thermal and electrical interaction problem. The fact that the charger IC isn't damaged and the device charges normally on non-conductive surfaces suggests the overheating is caused by an external condition specific to the conductive surface environment.

My first hypothesis would be that the conductive surface is creating an unintended electrical path. If the device's enclosure has any exposed metal — a connector shell, a mounting screw, a grounding point — and that metal is at a different potential than the surface, current could flow through the surface. This could be a ground loop or a short circuit path that bypasses the normal charging current path. I'd inspect the device's enclosure for any exposed conductive areas and measure the potential difference between the device's ground and the metal surface.

A related hypothesis is that the conductive surface is providing a heat sink path that's actually concentrating heat in a specific area, or conversely, that the surface is preventing heat dissipation. But since the device charges normally on other surfaces, this seems less likely unless the metal cart has a specific thermal characteristic.

Another possibility is that the metal surface is coupling electromagnetic interference into the charging circuit. If the cart is near other equipment or acts as an antenna, it could couple noise into the charger's sense lines or control loop, causing the charger to operate incorrectly — perhaps drawing more current than intended or operating in an inefficient mode. I'd measure the charging current and voltage while the device is on the metal surface and compare it to normal operation.

I'd also consider whether the metal surface is creating a capacitive coupling path that increases the device's effective ground capacitance, potentially causing instability in the charger's control loop. This could be investigated by measuring the charger's switching waveform and looking for oscillation or abnormal duty cycles.

The investigation would involve reproducing the issue, measuring temperatures at various points on the device and the surface, measuring electrical parameters (current, voltage, ground potential), and then isolating the cause. I'd also check whether the issue occurs with other conductive surfaces or only this specific cart, which would help determine if it's a general conductive-surface issue or something specific to that environment.

**Possible follow-ups:**
- What safety considerations would you prioritize when investigating a thermal issue in a medical device?
- How would you determine whether the heat is coming from the charger IC itself or from an external current path?

---

## Q5: How would you handle a situation where you're leading a cross-functional failure investigation, and you discover that the root cause points to a design decision made by a senior engineer who is still on the team — and the finding could reflect poorly on them or create tension within the group?

**Answer:** This is a situation where the technical investigation is straightforward, but the human dynamics require careful handling. The goal is to resolve the technical issue while maintaining a constructive team environment and preserving the engineer's dignity.

First, I'd ensure the evidence is solid before drawing conclusions. Root cause analysis should be based on data, not opinion. I'd want to have clear documentation — test results, measurements, analysis — that supports the finding. If there's any ambiguity, I'd acknowledge it rather than overstating the conclusion.

When presenting the findings, I'd frame the discussion around the process and the system, not the individual. Design decisions are made in a context — with the information available at the time, under schedule pressure, with certain assumptions. A design decision that's later found to be inadequate isn't necessarily a personal failure; it's an opportunity to improve the design process. I'd emphasize that the goal is to understand what happened so we can prevent similar issues in the future, not to assign blame.

I'd also consider how to communicate the finding to the broader team. If the senior engineer is respected and influential, publicly attributing the root cause to their decision could undermine their authority and create defensiveness. Instead, I'd present the root cause analysis as a team finding, focusing on the technical evidence and the corrective actions needed. If the senior engineer needs to be involved in implementing the fix, I'd work with them privately first to ensure they're aligned with the findings before presenting to the larger group.

I'd also think about the corrective action process. The goal isn't just to fix the immediate issue but to improve the design process so similar issues don't occur. This might involve updating design guidelines, adding verification steps, or improving review processes. By focusing on systemic improvements rather than individual errors, the team can move forward constructively.

Finally, I'd be mindful of the senior engineer's perspective. They may already be aware of the issue or may feel defensive. I'd approach them with respect, acknowledge the context in which the decision was made, and seek their input on the corrective action. Their experience could be valuable in developing a robust fix.

**Possible follow-ups:**
- How would you handle the situation if the senior engineer becomes defensive or disputes the findings despite the evidence?
- How would you ensure that the corrective action addresses the systemic issue without creating a culture of blame?