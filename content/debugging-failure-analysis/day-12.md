# debugging-failure-analysis — Day 12

## Q1: How would you approach debugging a medical device where the firmware occasionally enters a hard fault handler, and the stack trace points to a different function each time the fault occurs?

**Answer:** A hard fault with a non-deterministic stack trace is a classic symptom of memory corruption or stack overflow rather than a logic error in any single function. I'd start by treating this as a system-level issue and systematically narrow down the cause.

First, I'd check the obvious suspects: stack size allocation versus actual usage. I'd instrument the firmware to track maximum stack depth for each task or thread, and verify that the configured stack sizes have adequate headroom. Stack overflow can corrupt adjacent memory, which would explain why the fault appears in different functions each time.

Next, I'd look for memory corruption sources. I'd review the code for buffer overruns, out-of-bounds array access, use-after-free, or DMA operations writing beyond their allocated buffers. I'd also check for race conditions where multiple tasks or interrupt handlers access shared memory without proper synchronization — a classic cause of intermittent corruption.

If the code review doesn't reveal the issue, I'd use hardware-assisted debugging. I'd enable the MPU (Memory Protection Unit) to create guard regions around critical memory areas — stack regions, heap, and peripheral buffers. When the MPU triggers a fault, the fault status registers will tell me exactly which memory region was accessed illegally and by which instruction. This turns a random-looking crash into a precise event.

I'd also consider whether the corruption is electrical rather than software. Marginal power delivery, signal integrity issues on the memory bus, or noise coupling into address/data lines can cause random memory corruption. If the firmware analysis doesn't yield a clear culprit, I'd examine the power rails and bus signals with an oscilloscope, particularly during high-current events like wireless transmissions or motor activation.

The key principle is to stop guessing and start isolating. The MPU approach is particularly powerful because it converts "the stack trace points somewhere different every time" from a mystery into a specific, actionable data point.

**Possible follow-ups:**
- How would you distinguish between stack overflow and heap corruption as the root cause?
- What specific MPU configuration would you use to catch the corruption earliest?

---

## Q2: How would you approach a failure investigation where a medical device's wireless communication module works reliably on the bench but drops connection intermittently when the device is in clinical use, and the clinical environment has multiple other wireless devices operating nearby?

**Answer:** This sounds like an electromagnetic interference (EMI) or coexistence problem rather than a fundamental design flaw. The bench environment is electrically quiet, while a clinical environment has many wireless transmitters — Wi-Fi, Bluetooth, Zigbee, and potentially other medical devices — all sharing the 2.4 GHz band.

I'd start by characterizing the failure more precisely. I'd ask the clinical team to log the exact conditions when drops occur: time of day, proximity to other equipment, device orientation, and whether the drops correlate with specific activities in the room. This data might reveal a pattern — for example, drops only occur when a particular piece of equipment is active nearby.

Next, I'd reproduce the problem in a controlled environment. I'd set up multiple wireless transmitters operating on adjacent channels and test the device's connection stability. I'd also use a spectrum analyzer to measure the RF environment in the actual clinical setting — this tells me what frequencies are occupied, signal strengths, and whether there are any unexpected emitters.

If the issue is coexistence, I'd look at the device's RF design: antenna matching, receiver sensitivity, and the firmware's channel selection and hopping strategy. I'd check whether the device has a clear channel assessment mechanism and whether it's aggressive enough in a crowded spectrum. I'd also examine the protocol stack's retry and reconnection logic — sometimes the issue isn't the RF link itself but how the firmware handles transient interference.

I'd also consider whether the problem is actually RF at all. The clinical environment has different grounding, power quality, and physical layout than the bench. I'd verify that the device's power supply is clean in the clinical setting and that there's no ground loop or common-mode noise issue that only manifests when the device is connected to clinical infrastructure.

Finally, I'd review the device's shielding and filtering. If the device's own processor or other components generate noise that desensitizes the receiver, that would explain why it works on the bench (where the noise floor is lower) but fails in a busy RF environment.

**Possible follow-ups:**
- How would you determine whether the issue is receiver desensitization versus protocol-level coexistence?
- What specific measurements would you take in the clinical environment to characterize the RF spectrum?

---

## Q3: You're investigating a field failure where a medical device's pressure sensor reading drifts slowly over several hours of continuous use, eventually triggering a fault condition. The sensor is a bridge-type pressure sensor with an instrumentation amplifier front-end. How would you approach this?

**Answer:** Slow drift in a bridge sensor system over hours points to a few classic culprits: temperature effects, component aging, or a subtle electrical issue like charge buildup or leakage current. I'd approach this systematically.

First, I'd characterize the drift pattern. Is it monotonic (always increasing or decreasing)? Does it stabilize after a certain time? Does it correlate with the device's internal temperature? I'd review the device logs to see if the drift correlates with ambient temperature changes, device warm-up, or battery voltage decline.

Temperature is the most common cause of slow drift in bridge sensors. I'd examine the sensor's temperature coefficient and whether the compensation algorithm accounts for it. I'd also check the instrumentation amplifier's gain drift and offset drift specifications. If the system relies on a reference voltage, I'd verify its temperature stability — a drifting reference would directly cause the sensor reading to drift.

I'd also look at the mechanical side. Pressure sensors can drift if there's moisture ingress, if the diaphragm is gradually deforming, or if the pressure port has a slow leak. I'd examine the sensor's exposure to the measured medium and whether there's any contamination path.

If temperature doesn't explain it, I'd look at electrical leakage. Over hours, charge can accumulate on PCB surfaces, particularly in humid environments or if there's flux residue from manufacturing. This leakage can create a parasitic voltage that slowly changes the bridge output. I'd inspect the PCB for cleanliness, check the conformal coating integrity, and measure insulation resistance between the sensor traces and adjacent conductors.

I'd also consider whether the drift is actually in the sensor or in the measurement chain. I'd test the system with a precision resistor network simulating the sensor to see if the drift persists — if it does, the problem is in the analog front-end or ADC reference, not the sensor itself.

The systematic approach is to separate the sensor from the electronics, characterize each component's drift contribution, and then determine which one dominates. Once identified, the fix might be a better compensation algorithm, a different sensor, or a hardware change like improved PCB cleaning or conformal coating.

**Possible follow-ups:**
- How would you design an experiment to separate sensor drift from electronics drift?
- What specific measurements would you take to verify the temperature compensation is working correctly?

---

## Q4: How would you approach a situation where a medical device passes all its design verification tests, but during a limited field trial, a small number of units report a "sensor fault" error that clears when the device is power-cycled — and the error code points to a sensor self-test failure that should be impossible given the sensor's specifications?

**Answer:** This is a classic "impossible failure" scenario, and the first principle is to question the assumption that it's impossible. The sensor's datasheet specifications describe its behavior under specified conditions — the real device may be operating outside those conditions in ways the design verification didn't capture.

I'd start by gathering as much data as possible from the field units. I'd examine the device logs for any other anomalies around the time of the fault — voltage dips, temperature excursions, communication errors, or timing irregularities. The sensor self-test failure might be a symptom of a broader issue rather than the sensor itself.

Next, I'd try to reproduce the failure. I'd review the design verification test plan to understand what conditions were covered and what wasn't. The field environment may have conditions the lab tests didn't replicate: specific temperature/humidity combinations, power quality variations, electromagnetic interference, or mechanical stress. I'd work with the clinical sites to understand the exact usage conditions when the fault occurred.

I'd also examine the self-test implementation itself. The sensor's self-test might have marginal timing margins that only fail under specific conditions — for example, if the self-test runs while the power supply is still settling after a low-power mode transition, or if it conflicts with another operation on the same communication bus. I'd review the firmware's self-test sequence and look for race conditions or timing violations.

Another angle is the sensor's power supply. If the sensor's supply voltage is marginally below specification during certain operating modes, the self-test might fail even though normal readings are unaffected. I'd check the power supply design for transient response issues, particularly during mode transitions.

I'd also consider whether the fault is real but the error code is misleading. The firmware might be reporting a sensor self-test failure when the actual issue is a communication failure, a clock issue, or a firmware state machine problem. I'd review the error handling code to verify the error code accurately reflects the failure mode.

The key is to treat the "impossible" as a hypothesis to test, not a conclusion. I'd design experiments to stress the device under conditions that might trigger the failure — marginal supply voltage, temperature extremes, EMI exposure — and instrument the device to capture detailed data when the fault occurs.

**Possible follow-ups:**
- How would you verify that the error code accurately reflects the actual failure mode?
- What specific conditions would you test that might not have been covered in the original design verification?

---

## Q5: A senior manager asks you to lead a cross-functional root-cause investigation for a critical medical device failure that occurred in the field. The device was returned with a note that it "stopped working" — no error logs, no visible damage. The project schedule is tight, and there's pressure to find a quick fix. How would you structure this investigation?

**Answer:** This is a situation where the pressure to find a quick fix is exactly what can lead to a wrong conclusion. My approach would be to establish a structured investigation process that balances thoroughness with urgency, while making it clear that a quick fix without a verified root cause is a risk to patient safety and regulatory compliance.

First, I'd secure the failed device and preserve all evidence. I'd document its condition with photographs, note the state of all connectors and seals, and ensure it's stored in a controlled environment. I'd also gather any available contextual data — usage logs from the clinical site, maintenance records, and the device's service history.

Next, I'd assemble a cross-functional team: hardware, firmware, mechanical, quality, and regulatory. I'd assign clear roles and establish a communication cadence — daily stand-ups to share findings and a shared log to track hypotheses and evidence. I'd also establish ground rules: no conclusions without evidence, and no changes to the design or manufacturing process until root cause is confirmed.

I'd structure the investigation in phases. Phase one is evidence gathering: visual inspection, X-ray inspection, electrical testing of the returned unit, and data recovery from any non-volatile memory. Phase two is hypothesis generation: based on the evidence, the team develops a list of plausible failure mechanisms. Phase three is hypothesis testing: each hypothesis is tested through targeted experiments, fault injection, or analysis. Phase four is root cause confirmation and corrective action.

I'd also manage the schedule pressure explicitly. I'd work with the manager to define what "quick" means in this context — is there a containment action needed immediately (like a field advisory or usage restriction), or is the timeline driven by production schedules? I'd propose interim containment measures while the investigation proceeds, so patient safety is protected without rushing to a conclusion.

Finally, I'd ensure the investigation follows a formal process like 8D or a similar structured methodology. This provides a framework for documentation, which is essential for regulatory compliance and for defending the eventual corrective action. Even if the team finds a likely cause quickly, I'd insist on verifying it through testing before implementing a fix.

The key message to the team and management is: we can move quickly, but we can't skip steps. A structured investigation is actually the fastest path to a reliable fix, because it prevents the classic failure mode of implementing a fix for the wrong root cause and then having the problem recur.

**Possible follow-ups:**
- How would you handle a situation where the team identifies a likely root cause early, but the evidence isn't conclusive?
- How would you communicate interim findings to the senior manager who is pushing for a quick resolution?